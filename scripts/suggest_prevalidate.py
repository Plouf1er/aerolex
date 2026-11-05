#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suggest_prevalidate.py — PRÉ-VALIDATION EN LOT d'une file de propositions « à valider » (rapide et économique).

Au lieu d'une relecture une par une, trois étages :
  a. contrôles DÉTERMINISTES, gratuits (suggest_core / suggest_rules) : doublon, forme de base et accents, sigles développés, variantes
     interdites (trop courtes, mots grammaticaux), « voir aussi » inexistants, famille obligatoire, slug sûr, définition 2-4 phrases,
     simulation anti-ridicule (sur le corpus du lexique, ou générique sans corpus). Ce qui est mécanique est corrigé tout seul ; le reste bloque.
  b. UN SEUL PASSAGE LLM par paquets de 20 propositions (prompt compact : terme, définition, famille, variantes, voir aussi, 3 fiches
     voisines) -> JSON strict par proposition : verdict ok | corriger | rejeter, correction (champs modifiés seulement), raison, confiance.
  c. DEUXIÈME AVIS, seulement sur les cas douteux (confiance < 0,8, correction de la définition, désaccord avec un contrôle), par un
     modèle DIFFÉRENT du premier s'il est configuré ; sinon le cas reste douteux.
Résultat par proposition : « prête », « corrigée-prête », « douteuse » (avec la question posée au relecteur) ou « à rejeter » (raison).

Pré-valider n'écrit JAMAIS dans le lexique : seules la file de propositions (corrections, enregistrées dans data["prevalidation"] avec
l'état d'origine) et le journal de coût sont touchés. La SEULE écriture dans le lexique est apply_ready() (bouton « Valider les N prêtes ») :
verrou, UNE sauvegarde, import_lexique --write, UNE reconstruction, test des liens + tests de qualité, restauration automatique complète
au moindre échec, refus si le nombre de fiches baisse (suggest_core.validate_proposals).

Réglages (aerolex.config.json de l'installation, jamais de secret) :
  "prevalidate": {"model": "xai/grok-4.3", "effort": "low", "second_model": "local", "fallback": "local",
                  "local_url": "http://hôte:11434", "local_model": "…"}
  (variables d'environnement : AEROLEX_PREVALIDATE_MODEL / _SECOND / _EFFORT). « local » = serveur compatible OpenAI (llm.local_url).
Le plafond de coût quotidien de suggest_core (DAILY_USD_CAP) est respecté ; chaque appel est journalisé dans costlog (job « prevalidate:<id> »).
"""
from __future__ import annotations

import concurrent.futures as cf
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suggest_core as sc  # noqa: E402

RULES = sc.RULES
BATCH = 20                      # propositions par appel au modèle
READY_CONF = 0.85               # confiance minimale d'une proposition « prête »
DOUBT_CONF = 0.8                # en dessous : deuxième avis
VERDICTS = ("ok", "corriger", "rejeter")
CORR_KEYS = ("terme", "definition", "famille", "voir_aussi", "variantes", "contexte_requis")
READY = ("prete", "corrigee_prete")
LABELS = {"prete": "prête", "corrigee_prete": "corrigée-prête", "douteuse": "douteuse", "a_rejeter": "à rejeter"}
PRIVATE_KINDS = ("prevalidate", "apply")
FIXABLE_BY_MODEL = ("Famille", "Définition", "Soulignements simulés", "Variantes d'appel", "Sigles développés")
_lock = threading.Lock()


class CapReached(RuntimeError):
    """Plafond de coût quotidien atteint (suggest_core.DAILY_USD_CAP)."""


# ── réglages ────────────────────────────────────────────────────────────────
def _spec(s):
    s = (s or "").strip()
    if not s or s.lower() in ("none", "non", "aucun", "off"):
        return None
    prov, _, name = s.partition("/")
    if prov in ("xai", "local"):
        return {"prov": prov, "model": name or (sc.PRIMARY_MODEL if prov == "xai" else sc.LOCAL_MODEL)}
    return {"prov": "xai", "model": s}


def label(sp) -> str:
    return "%s/%s" % (sp["prov"], sp["model"]) if sp else ""


def local_url() -> str:
    u = ((sc.INSTALL.get("prevalidate") or {}).get("local_url") or sc.LOCAL_URL or "").strip()
    if u and "/chat/completions" not in u:
        u = u.rstrip("/") + ("/chat/completions" if u.rstrip("/").endswith("/v1") else "/v1/chat/completions")
    return u


def config(model=None, second=None, effort=None, fallback=None) -> dict:
    c = sc.INSTALL.get("prevalidate") or {}
    env = os.environ.get
    m = model or env("AEROLEX_PREVALIDATE_MODEL") or c.get("model") or "xai/" + sc.PRIMARY_MODEL
    s = second if second is not None else (env("AEROLEX_PREVALIDATE_SECOND") or c.get("second_model") or ("local" if local_url() else ""))
    f = fallback if fallback is not None else (c.get("fallback") if "fallback" in c else ("local" if local_url() else ""))
    first = _spec(m)
    sec, fb = _spec(s), _spec(f)
    if sec and first and label(sec) == label(first):
        sec = None                         # un deuxième avis du MÊME modèle n'en est pas un
    if fb and first and label(fb) == label(first):
        fb = None
    return {"first": first, "second": sec, "fallback": fb, "effort": effort or env("AEROLEX_PREVALIDATE_EFFORT") or c.get("effort") or "low"}


# ── appel d'un modèle (coût journalisé) ─────────────────────────────────────
class Stats:
    def __init__(self):
        self.calls: list = []
        self.lock = threading.Lock()

    def add(self, **kw):
        with self.lock:
            self.calls.append(kw)

    @property
    def usd(self) -> float:
        return round(sum(c.get("usd", 0.0) for c in self.calls), 6)

    def by_stage(self) -> dict:
        out: dict = {}
        for c in self.calls:
            o = out.setdefault(c["stage"], {"appels": 0, "usd": 0.0, "secs": 0.0, "tok_in": 0, "tok_out": 0, "modeles": []})
            o["appels"] += 1
            o["usd"] = round(o["usd"] + c.get("usd", 0.0), 6)
            o["secs"] = round(o["secs"] + c.get("secs", 0.0), 1)
            o["tok_in"] += c.get("tok_in", 0)
            o["tok_out"] += c.get("tok_out", 0)
            if c["modele"] not in o["modeles"]:
                o["modeles"].append(c["modele"])
        return out


def _call_model(spec: dict, messages: list, jid: str, stage: str, n: int, effort: str, stats: Stats) -> str:
    """Un appel (xAI ou local compatible OpenAI) -> contenu texte. Coût réel écrit dans costlog."""
    t0 = time.time()
    usd, tin, tout, ok = 0.0, 0, 0, 0
    model_label = label(spec)
    try:
        if spec["prov"] == "xai":
            if sc.cost_today() >= sc.DAILY_USD_CAP:
                raise CapReached("plafond quotidien atteint (%.2f USD)" % sc.DAILY_USD_CAP)
            key = sc._xai_key()
            if not key:
                raise RuntimeError("XAI_API_KEY absente")
            body = {"model": spec["model"], "messages": messages, "temperature": 0.1, "response_format": {"type": "json_object"}}
            if "non-reasoning" not in spec["model"]:
                body["reasoning_effort"] = effort
            r = sc._post_json(sc.XAI_URL, body, {"Authorization": "Bearer " + key, "Content-Type": "application/json"}, 240)
            u = r.get("usage") or {}
            tin = int(u.get("prompt_tokens", 0))
            tout = int(u.get("completion_tokens", 0)) + int((u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))
            usd = (u.get("cost_in_usd_ticks") or 0) / 1e10 or (tin * sc.PRICE_IN + tout * sc.PRICE_OUT) / 1e6
        else:
            url = local_url()
            if not url:
                raise RuntimeError("modèle local non configuré (aerolex.config.json : prevalidate.local_url ou llm.local_url)")
            body = {"model": spec["model"], "messages": messages, "temperature": 0.1, "response_format": {"type": "json_object"},
                    "max_tokens": 8000, "chat_template_kwargs": {"enable_thinking": False}}
            r = sc._post_json(url, body, {"Content-Type": "application/json"}, 600)
            u = r.get("usage") or {}
            tin, tout = int(u.get("prompt_tokens", 0)), int(u.get("completion_tokens", 0))
        content = (r["choices"][0]["message"].get("content") or "")
        if not content.strip():
            raise RuntimeError("réponse vide du modèle")
        ok = 1
        return content
    finally:
        secs = time.time() - t0
        stats.add(stage=stage, modele=model_label, n=n, tok_in=tin, tok_out=tout, usd=usd, secs=secs, ok=ok)
        try:
            with sc._db_lock, sc.db() as con:
                con.execute("INSERT INTO costlog(ts,job,model,n_terms,tok_in,tok_out,usd,secs,ok) VALUES(?,?,?,?,?,?,?,?,?)",
                            (time.time(), "prevalidate:%s:%s" % (jid, stage), model_label, n, tin, tout, usd, secs, ok))
        except Exception as e:  # noqa: BLE001 — le journal ne doit jamais faire échouer l'analyse
            sys.stderr.write("costlog: %r\n" % (e,))


# ── lecture / écriture de la file (jamais du lexique) ───────────────────────
def _row(pid: int, status: str = "pending"):
    with sc._db_lock, sc.db() as con:
        return con.execute("SELECT * FROM proposals WHERE id=? AND status=?", (pid, status)).fetchone()


def _snap(pid: int) -> dict:
    r = _row(pid)
    d = json.loads(r["data"])
    return {"terme": r["term"], "definition": d.get("definition") or "",
            "famille": d.get("famille") or d.get("famille_nouvelle") or "",
            "voir_aussi": list(d.get("voir_aussi") or []), "variantes": RULES.retained_forms(d),
            "contexte_requis": list(d.get("contexte_requis") or [])}


def _put_record(pid: int, rec) -> None:
    with sc._db_lock, sc.db() as con:
        r = con.execute("SELECT data FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
        if not r:
            return
        d = json.loads(r["data"])
        if rec is None:
            d.pop("prevalidation", None)
        else:
            d["prevalidation"] = rec
        con.execute("UPDATE proposals SET data=? WHERE id=?", (json.dumps(d, ensure_ascii=False), pid))   # "upd" inchangé : la file garde son ordre


def fingerprint(pid: int) -> str:
    return hashlib.sha1(json.dumps(_snap(pid), sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _short(v, n=120) -> str:
    s = re.sub(r"\s+", " ", v if isinstance(v, str) else (", ".join(map(str, v)) if isinstance(v, list) else str(v or ""))).strip()
    return s if len(s) <= n else s[:n - 1] + "…"


# ── étage a : contrôles déterministes ───────────────────────────────────────
class P:
    """État d'une proposition au fil de l'analyse."""

    def __init__(self, pid: int, lex: str):
        self.id, self.lex = pid, lex
        r = _row(pid)
        self.term0 = r["term"]
        self.orig = _snap(pid)
        self.fixes: list = []                 # [{champ, avant, apres, origine, motif}]
        self.blockers: list = []              # [(nom, detail)]
        self.warns: list = []
        self.final = None                     # statut définitif atteint à l'étage a
        self.reason = ""
        self.question = ""
        self.avis: list = []                  # [{etape, modele, verdict, confiance, raison}]
        self.refused: list = []               # corrections du modèle refusées (non mécaniques)
        self.existing = ""                    # fiche dont le terme serait une variante

    @property
    def term(self) -> str:
        return _row(self.id)["term"]


def _apply(p: P, origine: str, motif: str, fn) -> bool:
    """Exécute une modification de la file et en garde l'avant/après champ par champ."""
    before = _snap(p.id)
    fn()
    after = _snap(p.id)
    changed = False
    for k in before:
        if before[k] != after[k]:
            changed = True
            p.fixes.append({"champ": k, "avant": before[k], "apres": after[k], "origine": origine, "motif": motif})
    return changed


def _develop(p: P) -> None:
    """Sigles développés à la 1re occurrence (même fonction que la validation)."""
    r = _row(p.id)
    d = json.loads(r["data"])
    idx = sc.get_index(p.lex)
    text = d.get("definition") or ""
    if not text:
        return
    new, _rep = sc.develop_acronyms(text, r["term"], idx, sc._model_sigles(d.get("sigles")))
    if new != text:
        _apply(p, "automatique", "sigle développé à sa 1re occurrence", lambda: sc.edit_proposal(p.id, None, {"definition": new}))


def mechanical(p: P) -> None:
    """Auto-corrections MÉCANIQUES : forme de base / accents, variantes interdites décochées, voir aussi inexistants, sigles développés,
    variantes à risque décochées / contexte proposé d'après la définition (même code que new_lexicon : autofix_proposal)."""
    idx = sc.get_index(p.lex)
    r = _row(p.id)
    d = json.loads(r["data"])
    fb = d.get("forme_base_proposee")
    if fb and fb != r["term"]:
        _apply(p, "automatique", "forme de base : %s" % (d.get("forme_base_motif") or "accents / singulier"), lambda: sc.edit_proposal(p.id, fb, {}))
    r = _row(p.id)
    d = json.loads(r["data"])
    bad = [f for f in RULES.retained_forms(d) if RULES.forbidden_variant(f, r["term"])]
    if bad:
        keep = [f for f in RULES.retained_forms(d) if f not in bad]
        _apply(p, "automatique", "variante interdite retirée (%s)" % ", ".join("« %s » : %s" % (f, RULES.forbidden_variant(f, r["term"])) for f in bad),
               lambda: sc.edit_proposal(p.id, None, {"variantes_cochees": keep}))
    cur = list(d.get("voir_aussi") or [])
    clean = sc._names(cur, idx, r["term"], sc.MAX_VOIR_AUSSI)
    if clean != cur:
        _apply(p, "automatique", "« voir aussi » : fiche(s) inexistante(s) retirée(s)", lambda: sc.edit_proposal(p.id, None, {"voir_aussi": clean}))
    _develop(p)
    before = _snap(p.id)
    notes = sc.autofix_proposal(p.id, adopt_base=False)
    after = _snap(p.id)
    for k in before:
        if before[k] != after[k]:
            p.fixes.append({"champ": k, "avant": before[k], "apres": after[k], "origine": "automatique", "motif": " ; ".join(notes)[:300]})


def slug_check(term: str) -> str:
    """'' si le slug de la fiche sera sûr ; sinon la raison."""
    try:
        import slugify as SL
    except Exception:  # noqa: BLE001
        return ""
    if SL.slug_ok(SL.slugify(term)):
        return ""
    return "slug non exploitable pour « %s » (symbole, trop court ou générique) : un slug de repli serait fabriqué" % term


def det_check(p: P) -> None:
    """Contrôles gratuits (sans modèle) : met à jour blockers / warns / final. Ne modifie rien."""
    r = _row(p.id)
    idx = sc.get_index(p.lex)
    p.blockers, p.warns, p.existing = [], [], ""
    p.final = None
    m = idx.match(r["term"])
    if m and m["statut"] == "present":
        p.final, p.reason = "a_rejeter", "doublon : « %s » existe déjà (fiche « %s »)." % (r["term"], m["terme"])
        return
    rep = sc.check_proposal(r, run_llm=False)
    for c in rep["controles"]:
        nom = c["nom"]
        if nom == "Cohérence avec les fiches liées":
            continue
        blk = c["statut"] == "ko" or c.get("bloquant") or c.get("incontournable")
        if nom == "Terme inexistant" and c["statut"] == "ko":
            p.final, p.reason = "a_rejeter", "doublon : " + c["detail"]
            return
        if nom == "Fiche existante":
            p.existing = (json.loads(r["data"]).get("variante_candidats") or [{}])[0].get("fiche", "")
            p.blockers.append((nom, c["detail"]))
            continue
        if blk:
            p.blockers.append((nom, c["detail"]))
        elif c["statut"] == "warn":
            p.warns.append((nom, c["detail"]))
    why = slug_check(r["term"])
    if why:
        p.blockers.append(("Slug", why))


def stage_a(p: P) -> None:
    det_check(p)
    if p.final:
        return
    mechanical(p)
    det_check(p)


def _blk_text(p: P) -> str:
    return " ; ".join("%s : %s" % b for b in p.blockers)


# ── étage b / c : le modèle ─────────────────────────────────────────────────
def build_review_prompt(lex: str, items: list, second: bool = False) -> list:
    """items : [{n, id, probleme?, doute?}] -> messages. Un seul passage pour <= 20 propositions."""
    cfg = sc.LEXICONS[lex]
    idx = sc.get_index(lex)
    fams = ", ".join("%s (%s)" % (f, idx.family_labels.get(f, f)) for f in idx.families)
    system = (
        "Tu relis des PROPOSITIONS de fiches pour le lexique « %s » (public : %s ; domaine : %s). Pour chaque proposition numérotée, "
        "décide si elle peut être publiée telle quelle.\n"
        "Critères : exactitude technique de la définition (aucune erreur de fait, de sigle, de grandeur ni d'unité), terme réellement du domaine, "
        "définition claire de 2 à 4 phrases non circulaire, famille adaptée (liste ci-dessous), « voir aussi » pertinents, cohérence avec les "
        "fiches voisines données (pas de contradiction), variantes d'appel raisonnables (jamais un mot courant qui ferait souligner à tort).\n"
        "Verdicts : \"ok\" = publiable telle quelle ; \"corriger\" = publiable après les corrections que tu fournis ; \"rejeter\" = fausse, "
        "hors sujet, doublon d'une fiche voisine ou inexploitable.\n"
        "\"correction\" : UNIQUEMENT les champs à modifier, parmi : terme (accents ou singulier SEULEMENT), definition (texte complet réécrit, "
        "2 à 4 phrases, sigles en majuscules), famille (un slug de la liste), voir_aussi (liste de fiches EXISTANTES), variantes (liste des "
        "variantes À CONSERVER, sous-ensemble des variantes actuelles), contexte_requis (mots qui doivent figurer autour pour souligner). "
        "N'invente rien : corrige seulement ce qui est faux ou imprécis.\n"
        "\"confiance\" : ta certitude (0 à 1) que ton verdict est juste ; mets moins de 0,8 dès que tu doutes d'un fait.\n"
        "Réponds UNIQUEMENT par un objet JSON {\"items\":[{\"n\":1,\"verdict\":\"ok|corriger|rejeter\",\"correction\":{},\"raison\":\"1 phrase\","
        "\"confiance\":0.9}]} avec exactement un item par proposition, même numérotation.\n"
        "Familles : %s." % (cfg["label"], cfg["audience"], cfg["scope"], fams))
    parts = []
    for it in items:
        r = _row(it["id"])
        d = json.loads(r["data"])
        near = idx.similar(r["term"], d.get("definition") or "", 3)
        neigh = " | ".join("%s : %s" % (t, _short(re.sub(r"<[^>]+>", "", idx.glossaire[t].get("definition", "") or ""), 110)) for t in near if t in idx.glossaire)
        fam = d.get("famille") or d.get("famille_nouvelle") or "(aucune)"
        line = ("#%d TERME : %s\nFamille : %s\nDéfinition : %s\nVariantes : %s\nVoir aussi : %s\n%sVoisines : %s\n" % (
            it["n"], r["term"], fam, _short(d.get("definition"), 700), ", ".join(RULES.retained_forms(d)) or "—",
            ", ".join(d.get("voir_aussi") or []) or "—",
            ("Contexte requis : %s\n" % ", ".join(d["contexte_requis"])) if d.get("contexte_requis") else "", neigh or "—"))
        if it.get("probleme"):
            line += "Problème détecté par les contrôles : %s\n" % it["probleme"]
        if it.get("doute"):
            line += "Un premier relecteur a hésité : %s\n" % it["doute"]
        parts.append(line)
    return [{"role": "system", "content": system}, {"role": "user", "content": "\n".join(parts)}]


def parse_review(content: str, ns: list) -> dict:
    """JSON strict -> {n: {verdict, correction, raison, confiance}} ; lève ValueError si inutilisable."""
    try:
        j = json.loads(sc._strip_json(content))
    except (ValueError, TypeError) as e:
        raise ValueError("JSON invalide : %s" % str(e)[:100])
    arr = j.get("items") if isinstance(j, dict) else j
    if not isinstance(arr, list) or not arr:
        raise ValueError("pas de liste « items »")
    out: dict = {}
    for it in arr:
        if not isinstance(it, dict):
            continue
        try:
            n = int(it.get("n"))
        except (TypeError, ValueError):
            continue
        v = str(it.get("verdict") or "").strip().lower()
        v = {"corrige": "corriger", "correct": "corriger", "reject": "rejeter", "rejete": "rejeter", "rejet": "rejeter"}.get(v, v)
        if n not in ns or v not in VERDICTS:
            continue
        try:
            conf = max(0.0, min(1.0, float(it.get("confiance"))))
        except (TypeError, ValueError):
            continue
        corr = it.get("correction") if isinstance(it.get("correction"), dict) else {}
        corr = {k: val for k, val in corr.items() if k in CORR_KEYS and val not in (None, "", [])}
        if v == "ok":
            corr = {}
        out[n] = {"verdict": v, "correction": corr, "raison": str(it.get("raison") or "").strip()[:300], "confiance": round(conf, 2)}
    if not out:
        raise ValueError("aucun item exploitable")
    return out


def review_batch(items: list, specs: list, effort: str, jid: str, stage: str, stats: Stats, second: bool = False) -> tuple:
    """Un passage sur <= 20 propositions. Nouvelle tentative (même modèle puis repli) si JSON invalide ou items manquants.
    -> ({n: avis}, [erreurs])"""
    lex = items[0]["lex"]
    results: dict = {}
    errors: list = []
    pending = {it["n"]: it for it in items}
    for spec in specs:
        if not pending:
            break
        try:
            msgs = build_review_prompt(lex, list(pending.values()), second)
            content = _call_model(spec, msgs, jid, stage, len(pending), effort, stats)
            got = parse_review(content, list(pending))
        except CapReached as e:
            errors.append(str(e))
            continue
        except Exception as e:  # noqa: BLE001 — réseau, HTTP, JSON invalide : tentative suivante
            errors.append("%s : %s" % (label(spec), str(e)[:160]))
            continue
        for n, rec in got.items():
            rec["modele"] = label(spec)
            results[n] = rec
            pending.pop(n, None)
        if pending:
            errors.append("%d proposition(s) absente(s) de la réponse de %s" % (len(pending), label(spec)))
    return results, errors


def apply_correction(p: P, corr: dict, motif: str) -> bool:
    """Applique une correction du modèle à la file, par les fonctions sûres ; ce qui n'est pas mécanique est refusé (-> douteuse)."""
    idx = sc.get_index(p.lex)
    ok = True
    for k in CORR_KEYS:
        if k not in corr:
            continue
        v = corr[k]
        r = _row(p.id)
        d = json.loads(r["data"])
        try:
            if k == "terme":
                new = sc.clean_term(str(v))
                if new == r["term"]:
                    continue
                if sc.ckey(new) != sc.ckey(r["term"]):
                    raise ValueError("renommage non mécanique « %s » -> « %s »" % (r["term"], new))
                _apply(p, "modèle", motif, lambda: sc.edit_proposal(p.id, new, {}))
            elif k == "definition":
                text = re.sub(r"<[^>]+>", "", str(v)).strip()
                if len(text) < 20:
                    raise ValueError("définition proposée trop courte")
                _apply(p, "modèle", motif, lambda: sc.edit_proposal(p.id, None, {"definition": text}))
                _develop(p)
            elif k == "famille":
                f = str(v).strip()
                if f not in idx.families:
                    raise ValueError("famille inconnue « %s »" % f)
                _apply(p, "modèle", motif, lambda: sc.edit_proposal(p.id, None, {"famille": f}))
            elif k == "voir_aussi":
                lst = [str(x) for x in v] if isinstance(v, list) else []
                _apply(p, "modèle", motif, lambda: sc.edit_proposal(p.id, None, {"voir_aussi": lst}))
            elif k == "variantes":
                have = {RULES.exact_key(h) for h in RULES.retained_forms(d)}
                keep = [f for f in (str(x) for x in v) if RULES.exact_key(f) in have]
                _apply(p, "modèle", motif, lambda: sc.edit_proposal(p.id, None, {"variantes_cochees": keep}))
            elif k == "contexte_requis":
                lst = [str(x) for x in v] if isinstance(v, list) else []
                _apply(p, "modèle", motif, lambda: sc.edit_proposal(p.id, None, {"contexte_requis": lst}))
        except (ValueError, KeyError) as e:
            ok = False
            p.refused.append("%s : %s" % (k, str(e)[:160]))
    return ok


# ── décision finale ─────────────────────────────────────────────────────────
def _fmt(c: float) -> str:
    return ("%.2f" % c).replace(".", ",")


def needs_second(p: P, a1) -> bool:
    if not a1 or p.final or p.blockers or p.refused:
        return False
    return (a1["verdict"] == "rejeter" or a1["confiance"] < DOUBT_CONF or "definition" in (a1.get("correction") or {})
            or any(n == "Confiance" for n, _ in p.warns))


def decide(p: P, a1, a2) -> tuple:
    """-> (statut, raison, question)."""
    if p.final == "a_rejeter":
        return "a_rejeter", p.reason, ""
    if p.blockers:
        if p.existing:
            return "douteuse", "« %s » semble être une forme d'appel de la fiche « %s »." % (p.term, p.existing), \
                "« %s » est-il une variante de « %s » (bouton « Ajouter comme variante ») ou une vraie nouvelle fiche ?" % (p.term, p.existing)
        return "douteuse", "contrôle bloquant : " + _blk_text(p)[:400], "Ce contrôle bloque la publication : corriger à la main, ou rejeter ?"
    if a1 is None:
        return "douteuse", "aucune réponse exploitable du modèle (%s)." % (p.reason or "erreur"), "Le modèle n'a pas pu relire cette proposition : la relire à la main ?"
    if p.refused:
        return "douteuse", "correction du modèle non mécanique, refusée : " + " ; ".join(p.refused), \
            "Le modèle propose une correction que l'outil n'applique pas seul (%s) : l'accepter ?" % a1["raison"][:120]
    v1, c1 = a1["verdict"], a1["confiance"]
    corr_def = "definition" in (a1.get("correction") or {})
    if not needs_second(p, a1):
        if c1 < READY_CONF:
            return "douteuse", "confiance du modèle %s (< %s) : %s" % (_fmt(c1), _fmt(READY_CONF), a1["raison"]), \
                "Le modèle valide mais sans certitude (confiance %s) : %s Publier ?" % (_fmt(c1), a1["raison"])
        return ("corrigee_prete" if p.fixes else "prete"), a1["raison"], ""
    why1 = {"rejeter": "le modèle propose de rejeter", "corriger": "le modèle a réécrit la définition" if corr_def else "le modèle corrige",
            "ok": ("confiance %s" % _fmt(c1)) if c1 < DOUBT_CONF else "doute sur la proposition"}[v1]
    if a2 is None:
        why = "%s (%s) ; aucun deuxième avis disponible." % (why1, a1["raison"])
        q = {"rejeter": "Le modèle propose de rejeter : %s Rejeter ou garder ?" % a1["raison"],
             "corriger": "Le modèle a réécrit la définition (voir le diff) : %s La garder ?" % a1["raison"]}.get(
                 v1, "Le modèle hésite (confiance %s) : %s Publier ?" % (_fmt(c1), a1["raison"]))
        return "douteuse", why, q
    v2, c2 = a2["verdict"], a2["confiance"]
    if v1 == "rejeter":
        if v2 == "rejeter":
            return "a_rejeter", "deux modèles s'accordent : %s / %s" % (a1["raison"], a2["raison"]), ""
        return "douteuse", "désaccord : le premier modèle rejette (%s), le second ne rejette pas (%s)." % (a1["raison"], a2["raison"]), \
            "Un modèle rejette (%s), l'autre non (%s) : trancher." % (a1["raison"], a2["raison"])
    if v2 == "ok" and c2 >= READY_CONF:
        return ("corrigee_prete" if p.fixes else "prete"), "confirmé par un deuxième avis (%s) : %s" % (a2["modele"], a2["raison"]), ""
    if v2 == "rejeter":
        return "douteuse", "désaccord : %s ; le second modèle rejette (%s)." % (a1["raison"], a2["raison"]), \
            "Le second modèle rejette cette fiche (%s) : la garder ?" % a2["raison"]
    return "douteuse", "deuxième avis non concluant (%s, confiance %s) : %s" % (v2, _fmt(c2), a2["raison"]), \
        "Le second modèle n'a pas confirmé (%s) : %s" % (v2, a2["raison"])


def _merge_fixes(p: P) -> list:
    """Un seul enregistrement par champ : premier « avant », dernier « après », motifs cumulés."""
    out: dict = {}
    for f in p.fixes:
        o = out.get(f["champ"])
        if not o:
            out[f["champ"]] = dict(f)
        else:
            o["apres"] = f["apres"]
            if f["motif"] and f["motif"] not in o["motif"]:
                o["motif"] += " ; " + f["motif"]
            if f["origine"] != o["origine"]:
                o["origine"] = "automatique + modèle"
    return [f for f in out.values() if f["avant"] != f["apres"]]


# ── orchestration ───────────────────────────────────────────────────────────
def _job_set(jid: str, done=None, **info) -> None:
    if not jid:
        return
    with sc._db_lock, sc.db() as con:
        r = con.execute("SELECT info FROM jobs WHERE id=?", (jid,)).fetchone()
        if not r:
            return
        i = json.loads(r["info"])
        i.update(info)
        if done is None:
            con.execute("UPDATE jobs SET info=?, upd=? WHERE id=?", (json.dumps(i, ensure_ascii=False), time.time(), jid))
        else:
            con.execute("UPDATE jobs SET done=?, info=?, upd=? WHERE id=?", (done, json.dumps(i, ensure_ascii=False), time.time(), jid))


def select_ids(lex: str, ids) -> list:
    with sc._db_lock, sc.db() as con:
        rows = con.execute("SELECT id FROM proposals WHERE domain=? AND status='pending' ORDER BY ts", (lex,)).fetchall()
    pend = [r["id"] for r in rows]
    if ids in (None, "all", "tout"):
        return pend
    have = set(pend)
    return [i for i in (int(x) for x in ids) if i in have]


def prevalidate(lex_id: str, ids="all", jid: str = "", cfg=None, progress=None) -> dict:
    """Pré-validation de la file (ou d'une sélection). N'écrit JAMAIS dans le lexique. -> rapport (groupes, coût, durée)."""
    if lex_id not in sc.LEXICONS:
        raise KeyError("lexique inconnu : " + lex_id)
    cfg = cfg or config()
    if not cfg["first"]:
        raise ValueError("aucun modèle configuré")
    jid = jid or secrets.token_hex(8)
    stats = Stats()
    t0 = time.time()
    pids = select_ids(lex_id, ids)
    total = len(pids)
    done_set: set = set()

    def tick(etape: str, pid=None, frac=None):
        with _lock:
            if pid is not None:
                done_set.add(pid)
            extra = {"progress": round(frac, 3)} if frac is not None else {}
            _job_set(jid, len(done_set), etape=etape, usd=stats.usd, **extra)
            if progress:
                progress(len(done_set), total, etape)

    states = {pid: P(pid, lex_id) for pid in pids}
    # ── a. déterministe (gratuit) ──
    tick("contrôles automatiques (0/%d)" % total, frac=0.0)
    a_done = 0
    with cf.ThreadPoolExecutor(min(6, max(1, total))) as ex:
        futs = {ex.submit(stage_a, p): p for p in states.values()}
        for f in cf.as_completed(futs):
            p = futs[f]
            a_done += 1
            try:
                f.result()
            except Exception as e:  # noqa: BLE001 — une proposition illisible ne bloque pas les autres
                p.final, p.reason = "douteuse", "contrôles automatiques en échec : %r" % (e,)
                p.question = "Cette proposition n'a pas pu être contrôlée : la relire à la main."
            tick("contrôles automatiques (%d/%d)" % (a_done, total), p.id if p.final else None, 0.55 * a_done / max(1, total))
    # ── b. un seul passage LLM, paquets de 20 (un blocage que le modèle ne peut pas réparer est définitif : pas d'appel) ──
    to_llm = [p for p in states.values() if not p.final and all(n in FIXABLE_BY_MODEL for n, _ in p.blockers)]
    first_av: dict = {}
    batches = [to_llm[i:i + BATCH] for i in range(0, len(to_llm), BATCH)]
    specs = [cfg["first"], cfg["first"]] + ([cfg["fallback"]] if cfg["fallback"] else [])
    etape_b = "relecture par le modèle (%s)" % label(cfg["first"])
    tick(etape_b, frac=0.55)
    b_done = [0]

    def run_b(batch):
        items = [{"n": k + 1, "id": p.id, "lex": lex_id, "probleme": _blk_text(p)} for k, p in enumerate(batch)]
        got, errs = review_batch(items, specs, cfg["effort"], jid, "b", stats)
        return batch, got, errs

    def finish_b(batch, got, errs):
        for k, p in enumerate(batch):
            a = got.get(k + 1)
            if a is None:
                p.reason = "; ".join(errs)[:200] or "pas de réponse"
                continue
            first_av[p.id] = a
            p.avis.append({"etape": "1", "modele": a["modele"], "verdict": a["verdict"], "confiance": a["confiance"], "raison": a["raison"]})
            if a["verdict"] == "corriger" and a["correction"]:
                apply_correction(p, a["correction"], a["raison"])
            if a["verdict"] != "rejeter":
                det_check(p)                      # re-contrôle après correction

    with cf.ThreadPoolExecutor(sc.PARALLEL_BATCHES) as ex:
        for fut in cf.as_completed([ex.submit(run_b, b) for b in batches]):
            batch, got, errs = fut.result()
            finish_b(batch, got, errs)
            b_done[0] += 1
            tick(etape_b, frac=0.55 + 0.3 * b_done[0] / max(1, len(batches)))
    # ── c. deuxième avis sur les douteux seulement ──
    second_av: dict = {}
    doubt = [p for p in to_llm if needs_second(p, first_av.get(p.id))]
    if doubt and cfg["second"]:
        tick("deuxième avis (%s) sur %d cas" % (label(cfg["second"]), len(doubt)), frac=0.85)

        def run_c(batch):
            items = [{"n": k + 1, "id": p.id, "lex": lex_id, "doute": first_av[p.id]["raison"]} for k, p in enumerate(batch)]
            got, errs = review_batch(items, [cfg["second"]], cfg["effort"], jid, "c", stats, second=True)
            return batch, got, errs

        with cf.ThreadPoolExecutor(sc.PARALLEL_BATCHES) as ex:
            for fut in cf.as_completed([ex.submit(run_c, doubt[i:i + BATCH]) for i in range(0, len(doubt), BATCH)]):
                batch, got, errs = fut.result()
                for k, p in enumerate(batch):
                    a = got.get(k + 1)
                    if a:
                        second_av[p.id] = a
                        p.avis.append({"etape": "2", "modele": a["modele"], "verdict": a["verdict"], "confiance": a["confiance"], "raison": a["raison"]})
    # ── décision + enregistrement dans la file ──
    groups: dict = {k: [] for k in LABELS}
    for p in states.values():
        a1, a2 = first_av.get(p.id), second_av.get(p.id)
        if p.final == "douteuse":
            statut, raison, question = "douteuse", p.reason, p.question
        else:
            statut, raison, question = decide(p, a1, a2)
        corr = _merge_fixes(p)
        conf = (a2 or a1 or {}).get("confiance")
        rec = {"job": jid, "statut": statut, "raison": raison, "question": question, "confiance": conf, "corrections": corr,
               "controles": {"bloquants": ["%s : %s" % b for b in p.blockers], "avertissements": ["%s : %s" % w for w in p.warns]},
               "avis": p.avis, "empreinte": "", "ts": time.time(), "terme_initial": p.term0}
        try:
            rec["empreinte"] = fingerprint(p.id)
            _put_record(p.id, rec)
        except Exception as e:  # noqa: BLE001
            sys.stderr.write("enregistrement prevalidation #%s: %r\n" % (p.id, e))
        groups[statut].append({"id": p.id, "terme": p.term, "terme_initial": p.term0, "statut": statut, "raison": raison, "question": question,
                               "confiance": conf, "corrections": corr, "avis": p.avis})
        done_set.add(p.id)
    secs = round(time.time() - t0, 1)
    report = {"job": jid, "lexique": lex_id, "total": total, "groupes": groups, "comptes": {k: len(v) for k, v in groups.items()},
              "usd": stats.usd, "secs": secs, "etages": stats.by_stage(), "appels": len(stats.calls),
              "modeles": {"premier": label(cfg["first"]), "second": label(cfg["second"]), "repli": label(cfg["fallback"])},
              "deuxieme_avis": len(doubt) if cfg["second"] else 0, "douteux_sans_second_avis": 0 if cfg["second"] else len(doubt),
              "ecrit_dans_le_lexique": False}
    _job_set(jid, total, etape="terminé", usd=stats.usd, secs=secs, comptes=report["comptes"], modeles=report["modeles"], etages=report["etages"],
             appels=report["appels"], deuxieme_avis=report["deuxieme_avis"])
    return report


# ── l'UNIQUE écriture : « Valider les N prêtes » ────────────────────────────
POST_TESTS = [
    ("test_links_resolve", ["python3", "scripts/test_links_resolve.py"]),
    ("test_slugs", ["python3", "scripts/test_slugs.py"]),
    ("test_familles --strict", ["python3", "scripts/test_familles.py", "--strict"]),
    ("test_matching", ["python3", "scripts/test_matching.py"]),
    ("check_lexicon", ["python3", "scripts/check_lexicon.py", "{lex}"]),
]


def post_tests(lex: str, tests=None) -> list:
    """Tests de qualité après reconstruction ; lève RuntimeError au moindre échec (-> restauration complète par validate_proposals)."""
    res, bad = [], []
    for name, cmd in (tests if tests is not None else POST_TESTS):
        cmd = [c.replace("{lex}", lex) for c in cmd]
        p = subprocess.run(cmd, cwd=str(sc.lex_root(lex)), env=sc.lex_env(lex), capture_output=True, text=True, timeout=900)
        out = p.stdout + p.stderr
        ok = p.returncode == 0 and (name != "check_lexicon" or "LEXIQUE PROPRE" in out)
        res.append({"test": name, "ok": ok})
        if not ok:
            bad.append("%s : %s" % (name, out.strip()[-600:]))
    if bad:
        raise RuntimeError("tests en échec : " + " | ".join(bad))
    return res


def ready_ids(lex: str, ids=None) -> tuple:
    """Propositions réellement « prêtes » : enregistrement de pré-validation + inchangées depuis + contrôles déterministes toujours verts.
    -> (ids, ignorées [{id, terme, raison}])."""
    ok, skipped = [], []
    for pid in select_ids(lex, ids if ids else "all"):
        r = _row(pid)
        rec = json.loads(r["data"]).get("prevalidation") or {}
        if rec.get("statut") not in READY:
            if ids:
                skipped.append({"id": pid, "terme": r["term"], "raison": "pas « prête » (statut : %s)" % LABELS.get(rec.get("statut"), "non pré-validée")})
            continue
        if rec.get("empreinte") != fingerprint(pid):
            skipped.append({"id": pid, "terme": r["term"], "raison": "modifiée depuis la pré-validation : à re-pré-valider"})
            continue
        rep = sc.check_proposal(r, run_llm=False)
        if not rep["ok"]:
            skipped.append({"id": pid, "terme": r["term"], "raison": "contrôle bloquant : " + "; ".join(rep["bloquants"])[:200]})
            continue
        ok.append(pid)
    return ok, skipped


def apply_ready(lex_id: str, ids=None, jid: str = "", tests=None) -> dict:
    """UNE opération : toutes les propositions prêtes passent ensemble (verrou, UNE sauvegarde, import --write, UNE reconstruction, tests,
    restauration automatique complète si un test échoue, refus si le nombre de fiches baisse). Jamais appelée sans clic du relecteur."""
    t0 = time.time()
    ready, skipped = ready_ids(lex_id, ids)
    out = {"lexique": lex_id, "demandees": len(ready) + len(skipped), "ignorees": skipped, "valides": [], "ok": False}
    if not ready:
        out["erreur"] = "aucune proposition prête à valider"
        return out
    _job_set(jid, None, etape="sauvegarde, écriture, reconstruction et tests (%d fiches)…" % len(ready))
    try:
        res = sc.validate_proposals(ready, do_rebuild=True, run_llm=False, post_check=lambda d: post_tests(d, tests))
    except sc.ValidationError as e:
        # validate_proposals a restauré data/ et dist/<lexique>/ ; l'index global peut avoir été reconstruit avec les fiches ajoutées : on le régénère
        try:
            sc._idx_cache.clear()
            sc.rebuild(None, lex_id)
        except Exception as e2:  # noqa: BLE001
            out["avertissement"] = "reconstruction après restauration : %r" % (e2,)
        out["erreur"] = str(e)
        out["restaure"] = True
        out["secs"] = round(time.time() - t0, 1)
        return out
    sc._idx_cache.clear()
    out.update({"ok": True, "valides": res.get("valides", []), "refuses": [{"terme": x["terme"], "bloquants": x.get("bloquants")} for x in res.get("refuses", [])],
                "fiches": res.get("fiches"), "sauvegarde": res.get("sauvegarde"), "sigles_ajoutes": res.get("sigles_ajoutes", []),
                "secs": round(time.time() - t0, 1)})
    return out


def reject_flagged(lex_id: str, ids) -> dict:
    """« Rejeter les N à rejeter » (confirmation côté interface) : seulement celles que la pré-validation a classées « à rejeter »."""
    done, skipped = [], []
    for pid in select_ids(lex_id, ids):
        r = _row(pid)
        d = json.loads(r["data"])
        rec = d.get("prevalidation") or {}
        if rec.get("statut") != "a_rejeter":
            skipped.append({"id": pid, "terme": r["term"], "raison": "pas « à rejeter »"})
            continue
        d["raison_rejet"] = rec.get("raison", "")
        with sc._db_lock, sc.db() as con:
            con.execute("UPDATE proposals SET data=? WHERE id=?", (json.dumps(d, ensure_ascii=False), pid))
        sc.reject_proposal(pid)
        done.append(r["term"])
    return {"rejetes": done, "ignores": skipped}


# ── jobs asynchrones (même table que les soumissions en lot) ────────────────
def _running(lex: str) -> bool:
    with sc._db_lock, sc.db() as con:
        rows = con.execute("SELECT info FROM jobs WHERE domain=? AND state='running' AND upd>?", (lex, time.time() - 1800)).fetchall()
    return any((json.loads(r["info"]).get("kind") in PRIVATE_KINDS) for r in rows)


def start_job(lex: str, kind: str, total: int, fn) -> str:
    if lex not in sc.LEXICONS:
        raise KeyError("lexique inconnu : " + lex)
    if _running(lex):
        raise ValueError("une pré-validation ou une validation est déjà en cours pour ce lexique")
    jid = secrets.token_hex(8)
    now = time.time()
    with sc._db_lock, sc.db() as con:
        con.execute("INSERT INTO jobs(id,domain,state,total,done,results,info,ts,upd) VALUES(?,?,?,?,?,?,?,?,?)",
                    (jid, lex, "running", total, 0, "{}", json.dumps({"kind": kind, "etape": "démarrage"}), now, now))

    def run():
        try:
            res = fn(jid)
            _job_set(jid, None, resultat=res)
            state = "done"
        except Exception as e:  # noqa: BLE001 — l'échec est rendu au relecteur, jamais avalé
            sys.stderr.write("job %s %s: %r\n" % (kind, jid, e))
            _job_set(jid, None, erreur=str(e)[:400])
            state = "error"
        with sc._db_lock, sc.db() as con:
            con.execute("UPDATE jobs SET state=?, upd=? WHERE id=?", (state, time.time(), jid))

    threading.Thread(target=run, daemon=True, name="%s-%s" % (kind, jid)).start()
    return jid


def start_prevalidate(lex: str, ids="all", cfg=None) -> str:
    n = len(select_ids(lex, ids))
    if not n:
        raise ValueError("aucune proposition à pré-valider")

    def fn(jid):
        rep = prevalidate(lex, ids, jid=jid, cfg=cfg)
        return {k: rep[k] for k in ("comptes", "usd", "secs", "total")}

    return start_job(lex, "prevalidate", n, fn)


def start_apply(lex: str, ids=None) -> str:
    ready, _sk = ready_ids(lex, ids)
    if not ready:
        raise ValueError("aucune proposition prête à valider")
    return start_job(lex, "apply", len(ready), lambda jid: apply_ready(lex, ids, jid))


def job_view(jid: str):
    with sc._db_lock, sc.db() as con:
        r = con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not r:
        return None
    info = json.loads(r["info"])
    if info.get("kind") not in PRIVATE_KINDS:
        return None
    return {"id": r["id"], "domaine": r["domain"], "etat": r["state"], "total": r["total"], "fait": r["done"], "info": info,
            "duree": round((r["upd"] if r["state"] != "running" else time.time()) - r["ts"], 1)}


def summary(lex: str) -> dict:
    """Synthèse de la DERNIÈRE pré-validation du lexique, reconstruite depuis la file (survit au rechargement de la page)."""
    with sc._db_lock, sc.db() as con:
        jobs = con.execute("SELECT * FROM jobs WHERE domain=? AND state='done' ORDER BY ts DESC LIMIT 40", (lex,)).fetchall()
    last = next(((j, json.loads(j["info"])) for j in jobs if json.loads(j["info"]).get("kind") == "prevalidate"), None)
    groups: dict = {k: [] for k in LABELS}
    stale = 0
    props = sc.list_proposals(lex, "pending")
    for p in props:
        rec = (p["data"] or {}).get("prevalidation")
        if not rec or not last or rec.get("job") != last[0]["id"]:
            continue
        try:
            if rec.get("empreinte") != fingerprint(p["id"]):
                stale += 1
                continue
        except Exception:  # noqa: BLE001
            continue
        d = p["data"]
        groups.get(rec["statut"], groups["douteuse"]).append({
            "id": p["id"], "terme": p["terme"], "terme_initial": rec.get("terme_initial", ""), "raison": rec.get("raison", ""),
            "question": rec.get("question", ""), "confiance": rec.get("confiance"), "corrections": rec.get("corrections", []),
            "avis": rec.get("avis", []), "controles": rec.get("controles", {}), "definition": d.get("definition", ""),
            "famille": d.get("famille") or d.get("famille_nouvelle") or ""})
    out = {"lexique": lex, "groupes": groups, "comptes": {k: len(v) for k, v in groups.items()}, "modifiees_depuis": stale, "pending_total": len(props)}
    if last:
        j, info = last
        out["job"] = {"id": j["id"], "usd": info.get("usd", 0), "secs": info.get("secs", 0), "modeles": info.get("modeles", {}),
                      "etages": info.get("etages", {}), "appels": info.get("appels", 0), "deuxieme_avis": info.get("deuxieme_avis", 0), "ts": j["upd"]}
    return out
