#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_batch.py — validation de propositions « à valider » EN LOT (relecture déléguée, 2026-11-05).

N'invente aucune mécanique d'écriture : tout passe par les fonctions sûres de suggest_core.py
(edit_proposal, develop_acronyms, validate_proposals = verrou + sauvegarde + import_lexique --write + chaîne de
construction + test des liens + restauration automatique + refus si le nombre de fiches baisse, apply_as_variant).
Ce script ajoute seulement :
  * un fichier de décisions (--spec) : par id, modifications (titre, définition, famille, variantes cochées, sigles…) puis action
    (valider / ajouter comme variante de X / rejeter / laisser à valider avec une note) ;
  * le regroupement par LOTS (20 par défaut) : une sauvegarde + une reconstruction par lot (au lieu d'une par fiche) ;
  * après chaque lot : test_links_resolve, test_slugs, test_familles --strict, test_matching, check_lexicon aero
    (doit rester LEXIQUE PROPRE) ; au moindre échec le lot entier est restauré (site + sources + term_expansions), les
    propositions du lot repassent « à valider », puis le lot est coupé en deux pour isoler la proposition fautive ;
  * la mesure des soulignements sur le corpus des séances (avant/après, 5 exemples aléatoires du lot).

Les contrôles de check_proposal (sigles, définition 2-4 phrases, famille, variantes interdites, anti-ridicule…) restent
BLOQUANTS : une proposition qui en garde un est exclue du lot (jamais forcée), sauf forçage ciblé et nommé dans le fichier de
décisions (clé "force": noms de contrôles) pour un faux positif documenté.

Usage :
  python3 scripts/validate_batch.py --spec decisions.py --prepare-only      # applique les modifications, liste les blocages
  python3 scripts/validate_batch.py --spec decisions.py [--lot 20] [--report rapport.json]
Le fichier de décisions définit S = {id: {...}} (voir tmp/aerolex-validate-spec.py pour le format).
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import runpy
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import suggest_core as sc  # noqa: E402

RULES = sc.RULES
DOM = sc.DEFAULT_LEX              # lexique de la racine du projet (data/lexicon.json)
KEEP_ON_FAIL = False
POST_TESTS = [
    ("test_links_resolve", ["python3", "scripts/test_links_resolve.py"]),
    ("test_slugs", ["python3", "scripts/test_slugs.py"]),
    ("test_familles --strict", ["python3", "scripts/test_familles.py", "--strict"]),
    ("test_matching", ["python3", "scripts/test_matching.py"]),
    ("check_lexicon", ["python3", "scripts/check_lexicon.py", DOM]),
]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ── base de propositions ────────────────────────────────────────────────────
def backup_db() -> Path:
    dest = sc.BACKUP_ROOT / ("suggest-%s-validate-batch.db" % time.strftime("%Y%m%d-%H%M%S"))
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sc._db_lock:
        src = sc.db()
        dst = sqlite3.connect(str(dest))
        src.backup(dst)
        dst.close()
        src.close()
    return dest


def get_row(pid: int, status: str = "pending"):
    with sc._db_lock, sc.db() as con:
        return con.execute("SELECT * FROM proposals WHERE id=? AND status=?", (pid, status)).fetchone()


def set_status(ids, status: str):
    with sc._db_lock, sc.db() as con:
        for i in ids:
            con.execute("UPDATE proposals SET status=?, upd=? WHERE id=?", (status, time.time(), i))


def put_data(pid: int, d: dict):
    with sc._db_lock, sc.db() as con:
        con.execute("UPDATE proposals SET data=?, upd=? WHERE id=?", (json.dumps(d, ensure_ascii=False), time.time(), pid))


def note_on(pid: int, key: str, text: str):
    r = get_row(pid)
    if r:
        d = json.loads(r["data"])
        d[key] = text
        put_data(pid, d)


# ── application des décisions à UNE proposition (via edit_proposal & co) ───
def prepare(pid: int, spec: dict) -> dict:
    """Applique les modifications du fichier de décisions. -> {'avert': [...]} ; lève ValueError si incohérent."""
    r = get_row(pid)
    if not r:
        raise KeyError("proposition %s introuvable (ou plus « à valider »)" % pid)
    idx = sc.get_index(DOM)
    d = json.loads(r["data"])
    avert = []
    term = r["term"]
    new_term = spec.get("term") or term
    edit: dict = {}
    if spec.get("fam"):
        if spec["fam"] != d.get("famille"):
            edit["famille"] = spec["fam"]
    for src, dst in (("orig", "origine"), ("trad", "traduction"), ("ctx", "contexte_requis"), ("homo", "homographe_courant"), ("va", "voir_aussi")):
        if src in spec and spec[src] != d.get(dst):
            edit[dst] = spec[src]
    if edit or new_term != term:
        sc.edit_proposal(pid, new_term if new_term != term else None, edit)
    # sigles du modèle (champ non éditable par edit_proposal : écriture directe, comme autofix_proposal) puis définition
    r = get_row(pid)
    d = json.loads(r["data"])
    if "sig" in spec:
        d["sigles"] = [{"sigle": s, "developpe": dv, "traduction_fr": fr, "coherent": True, "nouveau": True} for s, (dv, fr) in spec["sig"].items()]
        d["sigles_inseres"] = []
        put_data(pid, d)
    text = d.get("definition") or ""
    if spec.get("defn"):
        text = spec["defn"]
    for old, new in spec.get("rep", []):
        if old not in text:
            if new in text or not new:                   # déjà appliqué (relance du script)
                continue
            raise ValueError("remplacement introuvable dans la définition : %r" % old[:60])
        text = text.replace(old, new)
    model = sc._model_sigles(d.get("sigles"))
    text2, _rep = sc.develop_acronyms(text, new_term, idx, model)
    if text2 != d.get("definition"):
        sc.edit_proposal(pid, None, {"definition": text2})
    # variantes cochées (+ ajouts manuels si absentes)
    if spec.get("var") is not None:
        d = json.loads(get_row(pid)["data"])
        have = {RULES.exact_key(v["forme"]) for v in d.get("variantes") or [] if isinstance(v, dict)}
        wanted = list(spec["var"])
        add = [f for f in wanted if RULES.exact_key(f) not in have]
        while True:
            try:
                sc.edit_proposal(pid, None, {"variantes_ajout": add, "variantes_cochees": wanted})
                break
            except ValueError as e:                      # forme refusée par les règles : on l'écarte et on le dit
                bad = [f for f in add if "« %s »" % f in str(e)]
                if not bad:
                    raise
                avert.append("variante refusée : " + str(e)[:160])
                add = [f for f in add if f not in bad]
                wanted = [f for f in wanted if f not in bad]
    return {"avert": avert}


def blockers(pid: int, spec: dict) -> list:
    """Contrôles bloquants restants (sans appel LLM) hors forçage ciblé et nommé."""
    rep = sc.check_proposal(get_row(pid), False)
    out = []
    for c in rep["controles"]:
        blk = c["statut"] == "ko" or c.get("bloquant") or c.get("incontournable")
        if not blk:
            continue
        if c["nom"] in spec.get("force", []) and not c.get("incontournable"):
            tok = spec.get("force_tokens")             # forçage limité à des sigles précis (faux positif documenté)
            m = re.search(r"non développés : (.*?) \(", c["detail"])
            if not tok or (m and {x.strip() for x in m.group(1).split(",")} <= set(tok)):
                continue
        out.append("%s : %s" % (c["nom"], c["detail"]))
    return out


# ── mesure des soulignements (moteur dist/aerolex.js sur le corpus) ─────────
def measure() -> dict:
    idx = sc.get_index(DOM)
    cdir = RULES.corpus_dir(ROOT, idx.cfg)
    texts = RULES.corpus_texts(cdir)
    paras = RULES.corpus_paragraphs(texts)
    eng, idxp = RULES.engine_paths(ROOT, DOM)
    idx_json = json.loads(idxp.read_text("utf-8"))
    base, rules = idx_json.get("terms", {}), (idx_json.get("meta") or {}).get("rules") or {}
    inp = {"engine": str(eng), "base": base, "rules": rules, "passages": [p[1] for p in paras], "runs": {"avant": {}}}
    p = subprocess.run([RULES._node_bin(), "-e", RULES.DRIVER], input=json.dumps(inp), capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        raise RuntimeError("mesure : " + (p.stderr or p.stdout)[-300:])
    runs = json.loads(p.stdout)["avant"]
    by = Counter()
    where = {}
    for i, ms in enumerate(runs):
        for raw, canon in ms:
            by[canon] += 1
            where.setdefault(canon, []).append((i, raw))
    return {"total": sum(by.values()), "par_fiche": by, "fichiers": len(texts), "paras": paras, "where": where}


def samples(m: dict, canons, k: int = 5) -> list:
    pool = [(c, i, raw) for c in canons for (i, raw) in m["where"].get(c, [])]
    random.shuffle(pool)
    out = []
    for c, i, raw in pool[:k]:
        seance, para, _ = m["paras"][i]
        pos = para.find(raw)
        a, b = max(0, pos - 60), min(len(para), pos + len(raw) + 60)
        out.append({"fiche": c, "forme": raw, "seance": seance.replace(".html", ""), "texte": ("…" if a else "") + para[a:pos] + "[" + raw + "]" + para[pos + len(raw):b] + ("…" if b < len(para) else "")})
    return out


# ── tests après lot ─────────────────────────────────────────────────────────
def post_tests() -> list:
    res = []
    for name, cmd in POST_TESTS:
        p = subprocess.run(cmd, cwd=str(ROOT), env=sc.lex_env(DOM), capture_output=True, text=True, timeout=900)
        out = (p.stdout + p.stderr)
        ok = p.returncode == 0 and (name != "check_lexicon" or "LEXIQUE PROPRE" in out)
        res.append({"test": name, "ok": ok, "tail": out.strip()[-2500:]})
    return res


def refresh_caches():
    try:
        sc._idx_cache.clear()
        sc.reload_dev_mods()
    except Exception as e:  # noqa: BLE001 — cache seulement, rien d'écrit
        log("cache:", repr(e))



def add_curated_expansions(items: dict) -> list:
    """Ajoute à EXPANSIONS (term_expansions.py) le développé d'une fiche-sigle dont le titre contient un trait d'union
    (CS-VLA, Part-NCO…) : le calcul automatique du développé (term_display._KEY_OK) ne les couvre pas, et
    check_lexicon exige un développé pour tout titre de forme « sigle ». Même écriture atomique, relue et vérifiée
    que add_abbreviations. items = {titre: (développé, traduction)} -> titres ajoutés."""
    path = Path(os.fspath(sc.EXPANSIONS_REL))
    txt = path.read_text("utf-8")
    m = re.search(r"^EXPANSIONS = \{\n(.*?)^\}\n", txt, re.S | re.M)
    if not m:
        raise RuntimeError("EXPANSIONS introuvable dans " + path.name)
    ns: dict = {}
    exec(compile(txt, str(path), "exec"), ns)               # noqa: S102 — fichier du dépôt, relu avant/après
    lines, added = [], []
    for key, (dev, fr) in items.items():
        if key in ns["EXPANSIONS"]:
            continue
        lines.append("    %s: (%s, %s, \"\"),\n" % (json.dumps(key, ensure_ascii=False), json.dumps(dev, ensure_ascii=False), json.dumps(fr, ensure_ascii=False) if fr else "None"))
        added.append(key)
    if not added:
        return []
    head = "    # ajoutés par validate_batch (titres à trait d'union : développé non calculable automatiquement)\n" if "ajoutés par validate_batch" not in txt else ""
    new = txt[:m.end(1)] + head + "".join(lines) + txt[m.end(1):]
    ns2: dict = {}
    exec(compile(new, str(path), "exec"), ns2)              # noqa: S102 — doit rester un module valide
    if not all(a in ns2["EXPANSIONS"] for a in added):
        raise RuntimeError("ajout de développés non pris en compte")
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(new, "utf-8")
    os.replace(tmp, path)
    return added


# ── un lot ──────────────────────────────────────────────────────────────────
def run_lot(ids: list, S: dict, rep: dict, before: dict) -> dict:
    var_ids = [i for i in ids if S[i]["act"] == "var"]
    new_ids = [i for i in ids if S[i]["act"] == "v"]
    bk0 = sc.backup_site(DOM)                       # filet global du lot (data, dist, term_expansions)
    n0 = sc._count_cards(DOM)
    log("lot %s : sauvegarde %s (%d fiches)" % (ids, bk0.name, n0))
    try:
        applied = []
        for i in var_ids:
            row = get_row(i)
            r = sc.apply_as_variant(i, S[i]["to"], do_rebuild=False)
            applied.append({"id": i, "terme": row["term"], "fiche": r["fiche"], "variantes": r["variantes_ajoutees"], "simulation": r["simulation"][:300]})
        curated = {S[i]["term"] if S[i].get("term") else get_row(i)["term"]: tuple(S[i]["exp"]) for i in new_ids if S[i].get("exp")}
        if curated:
            log("développés curatés ajoutés :", add_curated_expansions(curated))
            refresh_caches()
        if new_ids:
            force = any(S[i].get("force") for i in new_ids)
            res = sc.validate_proposals(new_ids, do_rebuild=True, run_llm=False, force=force)
            if res.get("refuses") or res.get("ignores"):
                raise RuntimeError("refus/ignorés : %s %s" % (res.get("refuses"), res.get("ignores")))
        else:
            sc.rebuild(None, DOM)
        n1 = sc._count_cards(DOM)
        if n1 < n0:
            raise RuntimeError("le nombre de fiches a baissé (%d -> %d)" % (n0, n1))
        refresh_caches()
        tests = post_tests()
        bad = [t for t in tests if not t["ok"]]
        if bad:
            raise RuntimeError("tests en échec : " + " | ".join("%s : %s" % (t["test"], t["tail"][-2000:]) for t in bad))
    except Exception as e:  # noqa: BLE001 — restauration complète puis remontée
        if KEEP_ON_FAIL:                              # débogage seulement : laisse l'état pour inspection (à restaurer à la main)
            log("KEEP-ON-FAIL : état laissé tel quel ; restaurer avec restore_site(%s)" % bk0)
            raise
        sc.restore_site(bk0, DOM)
        set_status(ids, "pending")
        refresh_caches()
        try:                                          # restore_site ne remet pas dist/aerolex-index.json : on le régénère depuis data/ restauré
            sc.rebuild(None, DOM)
        except Exception as e2:  # noqa: BLE001
            log("reconstruction après restauration en échec :", repr(e2)[:200])
        log("ÉCHEC du lot, site restauré depuis %s : %s" % (bk0.name, str(e)[:400]))
        return {"ok": False, "ids": ids, "erreur": str(e)[:800], "sauvegarde": str(bk0)}
    m = measure()
    canons = set()
    for i in new_ids:
        canons.add(get_row(i, "validated")["term"])
    canons |= {a["fiche"] for a in applied}
    delta = m["total"] - before["total"]
    gained = {c: m["par_fiche"][c] - before["par_fiche"].get(c, 0) for c in canons}
    ex = samples(m, [c for c in canons if gained.get(c, 0) > 0])
    log("lot OK : %d fiches -> %d ; soulignements %d -> %d (%+d) ; tests %s" % (n0, n1, before["total"], m["total"], delta, "OK"))
    return {"ok": True, "ids": ids, "fiches": [n0, n1], "variantes": applied, "tests": [{"test": t["test"], "ok": t["ok"]} for t in tests],
            "soulignements": {"avant": before["total"], "apres": m["total"], "delta": delta, "fichiers": m["fichiers"], "par_fiche": gained, "exemples": ex},
            "sauvegarde": str(bk0), "_m": m}


def run_isolating(ids: list, S: dict, rep: dict, before: dict, lots: list):
    r = run_lot(ids, S, rep, before)
    if r["ok"]:
        lots.append({k: v for k, v in r.items() if k != "_m"})
        return r["_m"]
    lots.append({k: v for k, v in r.items() if k != "_m"})
    if len(ids) == 1:
        note_on(ids[0], "note_relecture", "Validation automatique annulée (tests ou construction en échec) : " + r["erreur"][:300])
        rep.setdefault("echecs", []).append({"id": ids[0], "erreur": r["erreur"]})
        return before
    half = len(ids) // 2
    for part in (ids[:half], ids[half:]):
        before = run_isolating(part, S, rep, before, lots)
    return before


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--lot", type=int, default=20)
    ap.add_argument("--prepare-only", action="store_true")
    ap.add_argument("--report", default="")
    ap.add_argument("--only", default="", help="ids séparés par des virgules (sous-ensemble du fichier de décisions)")
    ap.add_argument("--seed", type=int, default=20261105)
    ap.add_argument("--keep-on-fail", action="store_true", help="débogage : ne pas restaurer en cas d'échec")
    a = ap.parse_args()
    random.seed(a.seed)
    global KEEP_ON_FAIL
    KEEP_ON_FAIL = a.keep_on_fail
    S = runpy.run_path(a.spec)["S"]
    if a.only:
        S = {i: S[i] for i in (int(x) for x in a.only.split(","))}
    rep: dict = {"spec": a.spec, "debut": time.strftime("%F %T"), "rejetees": [], "gardees": [], "bloquees": [], "avert": {}}
    log("sauvegarde de la base de propositions :", backup_db())

    ready = []
    for pid, spec in S.items():
        if get_row(pid) is None:
            log("#%s déjà traitée ou absente, ignorée" % pid)
            continue
        if spec["act"] == "r":
            rep["rejetees"].append({"id": pid, "terme": get_row(pid)["term"], "raison": spec["why"]})
            continue
        if spec["act"] == "h":
            note_on(pid, "note_relecture", spec["why"] + ((" Question : " + spec["q"]) if spec.get("q") else ""))
            rep["gardees"].append({"id": pid, "terme": get_row(pid)["term"], "raison": spec["why"], "question": spec.get("q", "")})
            continue
        try:
            info = prepare(pid, spec)
        except Exception as e:  # noqa: BLE001 — une proposition mal préparée est exclue, jamais forcée
            rep["bloquees"].append({"id": pid, "terme": get_row(pid)["term"], "bloquants": ["préparation : %r" % (e,)]})
            log("#%s préparation en échec : %r" % (pid, e))
            continue
        if info["avert"]:
            rep["avert"][pid] = info["avert"]
        if spec["act"] == "v":
            bl = blockers(pid, spec)
            if bl:
                rep["bloquees"].append({"id": pid, "terme": get_row(pid)["term"], "bloquants": bl})
                log("#%s %s : BLOQUÉE — %s" % (pid, get_row(pid)["term"], " || ".join(bl)[:400]))
                continue
        ready.append(pid)
    log("prêtes : %d ; bloquées : %d ; rejetées : %d ; laissées : %d" % (len(ready), len(rep["bloquees"]), len(rep["rejetees"]), len(rep["gardees"])))
    if a.prepare_only:
        if a.report:
            Path(a.report).write_text(json.dumps({k: v for k, v in rep.items()}, ensure_ascii=False, indent=1, default=str), "utf-8")
        return 0

    # rejets (écriture dans la file uniquement : aucune fiche touchée)
    for r_ in rep["rejetees"]:
        note_on(r_["id"], "raison_rejet", r_["raison"])
        sc.reject_proposal(r_["id"])

    lots: list = []
    before = measure()
    rep["mesure_initiale"] = {"total": before["total"], "fichiers": before["fichiers"]}
    log("mesure initiale : %d soulignements sur %d pages" % (before["total"], before["fichiers"]))
    for k in range(0, len(ready), a.lot):
        before = run_isolating(ready[k:k + a.lot], S, rep, before, lots)
    rep["lots"] = lots
    rep["fin"] = time.strftime("%F %T")
    rep["valides"] = [i for l in lots if l["ok"] for i in l["ids"]]
    if a.report:
        Path(a.report).write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=str), "utf-8")
    log("terminé : %d traitées OK, %d échec(s) isolés, %d bloquées" % (len(rep["valides"]), len(rep.get("echecs", [])), len(rep["bloquees"])))
    return 0 if not rep.get("echecs") else 1


if __name__ == "__main__":
    sys.exit(main())
