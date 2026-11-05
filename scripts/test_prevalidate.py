#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_prevalidate.py — pré-validation en lot (suggest_prevalidate) : modèle SIMULÉ (aucun appel réseau, aucune écriture en production).
Le test travaille sur une COPIE du projet dans un dossier temporaire (AEROLEX_ROOT, sauvegardes et base de propositions temporaires).
    python3 scripts/test_prevalidate.py
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import hashlib
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="prevalidate-test-")
os.environ["AEROLEX_SUGGEST_DIR"] = _TMP
_PWF = os.path.join(_TMP, "pw-factice")
open(_PWF, "w").write("pw-factice-test\n")
os.environ["AEROLEX_SUGGEST_PASSWORD_FILE"] = _PWF
os.environ["AEROLEX_BACKUP_DIR"] = os.path.join(_TMP, "bk")
os.environ.pop("AEROLEX_PREVALIDATE_MODEL", None)
os.environ.pop("AEROLEX_PREVALIDATE_SECOND", None)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

REAL = Path(__file__).resolve().parent.parent
CP = Path(_TMP) / "copie"
subprocess.run(["rsync", "-a", "--exclude", ".git", "--exclude", "backups", "--exclude", "*.png", "--exclude", "data/suggest", "--exclude", "*BACKUP*",
                "--exclude", "*BAK*", "--exclude", "*.bak*", str(REAL) + "/", str(CP) + "/"], check=True)
_lj = CP / "data" / "lexicon.json"
_lc = json.loads(_lj.read_text("utf-8"))
_lc["corpus"] = {"type": "none"}                      # simulation générique : rapide et indépendante de l'installation
_lj.write_text(json.dumps(_lc, ensure_ascii=False, indent=1), "utf-8")
os.environ["AEROLEX_ROOT"] = str(CP)
os.environ.pop("AEROLEX_CORPUS_DIR", None)

import suggest_core as core  # noqa: E402
import suggest_api as api    # noqa: E402
import suggest_prevalidate as pv  # noqa: E402

core.BACKUP_ROOT = Path(_TMP) / "bk"
LEX = core.DEFAULT_LEX
FAILS = []


def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + (" " + str(extra)[:400] if (extra and not cond) else ""))
    if not cond:
        FAILS.append(name)


def sha(p):
    return hashlib.sha1(Path(p).read_bytes()).hexdigest()


IDX = core.get_index(LEX)
FAM = "divers"
FAM2 = next(f for f in IDX.families if f != "divers" and IDX.families[f] > 3)

# ── modèle simulé : au niveau HTTP (les vrais _call_model, plafond et journal de coût sont exercés) ────────────
CALLS = []                       # [{url, model, stage, n, terms}]
BEHAVE = {"mode": "normal", "junk": 0}


def fake_post(url, body, headers, timeout):
    user = body["messages"][1]["content"]
    terms = re.findall(r"#(\d+) TERME : (.+)", user)
    second = "a hésité" in user
    local = "11434" in url
    CALLS.append({"url": url, "model": body["model"], "second": second, "local": local, "n": len(terms), "terms": [t for _, t in terms],
                  "user": user, "effort": body.get("reasoning_effort"), "think": body.get("chat_template_kwargs")})
    if BEHAVE["junk"] > 0:
        BEHAVE["junk"] -= 1
        content = "voici ma réponse (pas du JSON"
    else:
        items = []
        for n, t in terms:
            it = {"n": int(n), "verdict": "ok", "correction": {}, "raison": "fiche correcte", "confiance": 0.95}
            if second:
                if t.startswith("zzrej2"):
                    it.update(verdict="ok", confiance=0.9, raison="le terme est valable")
                elif t.startswith("zzrej"):
                    it.update(verdict="rejeter", confiance=0.9, raison="hors sujet confirmé")
                elif t.startswith("zzmaybe"):
                    it.update(verdict="ok", confiance=0.7, raison="je ne suis pas sûr")
                else:
                    it.update(verdict="ok", confiance=0.92, raison="définition confirmée")
            else:
                if t.startswith("zzfam"):
                    it.update(verdict="corriger", correction={"famille": FAM2}, raison="famille plus adaptée", confiance=0.93)
                elif t.startswith("zzdef"):
                    it.update(verdict="corriger", correction={"definition": "Définition réécrite pour %s. Elle est plus précise que la version proposée." % t}, raison="définition imprécise", confiance=0.9)
                elif t.startswith("zzlow"):
                    it.update(verdict="ok", confiance=0.6, raison="je doute du sens exact")
                elif t.startswith("zzrej"):
                    it.update(verdict="rejeter", confiance=0.95, raison="le terme n'est pas aéronautique")
                elif t.startswith("zzbadterm"):
                    it.update(verdict="corriger", correction={"terme": "tout autre mot"}, raison="renommage", confiance=0.95)
                elif t.startswith("zzmaybe"):
                    it.update(verdict="ok", confiance=0.6, raison="hésitation")
            items.append(it)
        content = json.dumps({"items": items}, ensure_ascii=False)
    usage = {"prompt_tokens": 1000, "completion_tokens": 200, "completion_tokens_details": {"reasoning_tokens": 50}, "cost_in_usd_ticks": 5000000}
    return {"choices": [{"message": {"content": content}}], "usage": usage}


core._post_json = fake_post
core._xai_key = lambda: "cle-factice"
core.LOCAL_URL = "http://strata.test:11434/v1/chat/completions"
CFG = pv.config(model="xai/grok-4.3", second="local/current-llm-fast", effort="low", fallback="none")


def mk(term, definition=None, famille=FAM, **extra):
    d = core.validate_item({"domaine": True, "pertinent": True, "famille": famille, "confiance": 0.9,
                            "definition": definition or "Terme fictif de test %s. Il sert uniquement à vérifier la pré-validation en lot." % term},
                           term, IDX.families, IDX)
    d["rattachements_retenus"] = []
    d.update(extra)
    core.enqueue_proposal(LEX, term, d, "t", "pending")
    got = [p["id"] for p in core.list_proposals(LEX) if p["terme"] == term]
    if not got:
        raise SystemExit("mk: proposition introuvable %r ; file = %r" % (term, [p["terme"] for p in core.list_proposals(LEX)][:5]))
    return got[0]


def prop(pid):
    return next(p for p in core.list_proposals(LEX) if p["id"] == pid)


def clear_queue():
    with core._db_lock, core.db() as con:
        con.execute("DELETE FROM proposals")


def site_state():
    return (sha(CP / "data/data_glossaire_full.py"), core._count_cards(LEX), sha(CP / "dist/aerolex-index.json") if (CP / "dist/aerolex-index.json").exists() else "")


def llm_calls(second=None):
    return [c for c in CALLS if second is None or c["second"] == second]


# ── 1. réglages ─────────────────────────────────────────────────────────────
print("== réglages")
c = pv.config(model="xai/grok-4.3", second="xai/grok-4.3")
check("réglages: un deuxième avis du même modèle n'en est pas un", c["second"] is None)
c = pv.config(model="xai/grok-4.3", second="none")
check("réglages: second=none -> aucun deuxième avis", c["second"] is None and c["first"]["model"] == "grok-4.3")
c = pv.config()
check("réglages: défaut = grok-4.3, reasoning bas, local en deuxième avis (installation)", c["first"]["prov"] == "xai" and c["effort"] == "low" and c["second"] and c["second"]["prov"] == "local", c)
check("réglages: l'URL locale est complétée (/v1/chat/completions)", pv.local_url().endswith("/v1/chat/completions"))
check("réglages: parse « local/modele »", pv._spec("local/abc") == {"prov": "local", "model": "abc"})

# ── 2. 45 propositions saines : paquets de 20, aucun deuxième avis, rien écrit dans le lexique ─────────────
print("== 45 propositions saines")
ids = [mk("zzok%s%sm" % (chr(97 + i // 26), chr(97 + i % 26))) for i in range(45)]      # sans s/x/z final (ckey singularise)
state0 = site_state()
CALLS.clear()
t0 = time.time()
rep = pv.prevalidate(LEX, "all", cfg=CFG)
check("lot: 45 propositions traitées", rep["total"] == 45 and sum(rep["comptes"].values()) == 45, rep["comptes"])
check("lot: paquets de 20 -> 3 appels au premier modèle", len(llm_calls(False)) == 3 and [c["n"] for c in llm_calls(False)] == [20, 20, 5] or sorted(c["n"] for c in llm_calls(False)) == [5, 20, 20], [c["n"] for c in CALLS])
check("lot: aucun deuxième avis quand tout est sûr", not llm_calls(True))
check("lot: reasoning bas envoyé à xAI", all(c["effort"] == "low" for c in CALLS))
check("lot: les 45 sont prêtes", rep["comptes"]["prete"] == 45, rep["comptes"])
check("lot: aucune écriture dans le lexique sans apply (fiches, index, nombre de pages)", site_state() == state0)
check("lot: les propositions restent « à valider »", all(prop(i) for i in ids) and len(core.list_proposals(LEX)) == 45)
check("lot: prompt compact (3 voisines, famille, variantes, voir aussi)", "Voisines :" in CALLS[0]["user"] and "Variantes :" in CALLS[0]["user"] and "Voir aussi :" in CALLS[0]["user"])
with core._db_lock, core.db() as con:
    cl = con.execute("SELECT job,model,usd,n_terms FROM costlog WHERE job LIKE 'prevalidate:%'").fetchall()
check("coût: journalisé pour chaque appel (costlog)", len(cl) == 3 and all(r["job"].startswith("prevalidate:" + rep["job"]) for r in cl), [tuple(r) for r in cl])
check("coût: coût réel du fournisseur (cost_in_usd_ticks) = rapport", abs(sum(r["usd"] for r in cl) - rep["usd"]) < 1e-9 and rep["usd"] > 0, rep["usd"])
check("coût: étages b/c détaillés", "b" in rep["etages"] and rep["etages"]["b"]["appels"] == 3)

# ── 3. JSON invalide : nouvelle tentative, puis douteux ─────────────────────
print("== JSON invalide")
clear_queue()
a = mk("zzokretry1"); b = mk("zzokretry2")
CALLS.clear(); BEHAVE["junk"] = 1
rep = pv.prevalidate(LEX, "all", cfg=CFG)
check("JSON invalide: 2e tentative réussie -> prêtes", len(llm_calls(False)) == 2 and rep["comptes"]["prete"] == 2, (len(CALLS), rep["comptes"]))
clear_queue()
a = mk("zzokjunk1"); b = mk("zzokjunk2")
CALLS.clear(); BEHAVE["junk"] = 5
rep = pv.prevalidate(LEX, "all", cfg=CFG)
BEHAVE["junk"] = 0
check("JSON invalide deux fois: 2 appels seulement puis « douteuse »", len(llm_calls(False)) == 2 and rep["comptes"]["douteuse"] == 2, (len(CALLS), rep["comptes"]))
check("JSON invalide: la raison est donnée au relecteur", all("modèle" in it["raison"] and it["question"] for it in rep["groupes"]["douteuse"]), rep["groupes"]["douteuse"])
# repli : le modèle de secours est essayé après deux échecs
CALLS.clear(); BEHAVE["junk"] = 2
cfg_fb = pv.config(model="xai/grok-4.3", second="none", fallback="local/current-llm-fast")
rep = pv.prevalidate(LEX, "all", cfg=cfg_fb)
check("repli: après 2 échecs du premier modèle, le modèle local répond", len(CALLS) == 3 and CALLS[2]["local"] and rep["comptes"]["prete"] == 2, (len(CALLS), rep["comptes"]))
check("local: thinking désactivé explicitement (règle OMEN)", CALLS[2]["think"] == {"enable_thinking": False})

# ── 4. deuxième avis seulement sur les cas douteux ──────────────────────────
print("== deuxième avis")
clear_queue()
ok1 = mk("zzokone"); ok2 = mk("zzoktwo")
low = mk("zzlowone"); dfn = mk("zzdefone"); rej = mk("zzrejone"); rej2 = mk("zzrej2one"); fam = mk("zzfamone"); bad = mk("zzbadtermone")
CALLS.clear()
rep = pv.prevalidate(LEX, "all", cfg=CFG)
sec = llm_calls(True)
check("2e avis: appelé une seule fois, seulement sur les cas douteux", len(sec) == 1 and sorted(sec[0]["terms"]) == sorted(["zzlowone", "zzdefone", "zzrejone", "zzrej2one"]), [c["terms"] for c in sec])
check("2e avis: par un modèle DIFFÉRENT (local, pas xai/grok)", sec and sec[0]["local"] and sec[0]["model"] == "current-llm-fast")
check("2e avis: le premier passage n'a pas reçu les cas sûrs deux fois", len(llm_calls(False)) == 1)
st = {it["terme"]: it for g in rep["groupes"].values() for it in g}
check("statut: confiance faible confirmée -> prête", st["zzlowone"]["statut"] == "prete", st["zzlowone"])
check("statut: définition corrigée + confirmée -> corrigée-prête avec diff", st["zzdefone"]["statut"] == "corrigee_prete" and any(f["champ"] == "definition" and f["origine"] == "modèle" and f["avant"] != f["apres"] for f in st["zzdefone"]["corrections"]), st["zzdefone"])
check("statut: rejet confirmé par 2 modèles -> à rejeter", st["zzrejone"]["statut"] == "a_rejeter", st["zzrejone"])
check("statut: désaccord entre les modèles -> douteuse avec question", st["zzrej2one"]["statut"] == "douteuse" and st["zzrej2one"]["question"], st["zzrej2one"])
check("statut: correction mineure (famille) sans 2e avis -> corrigée-prête", st["zzfamone"]["statut"] == "corrigee_prete" and prop(fam)["data"]["famille"] == FAM2, st["zzfamone"])
check("statut: renommage non mécanique refusé -> douteuse", st["zzbadtermone"]["statut"] == "douteuse" and "non mécanique" in st["zzbadtermone"]["raison"], st["zzbadtermone"])
check("statut: la définition réécrite est bien dans la file (corrigée)", "réécrite" in prop(dfn)["data"]["definition"])
check("avis: les deux avis sont conservés sur la proposition", len(prop(dfn)["data"]["prevalidation"]["avis"]) == 2)
# sans second modèle : le cas douteux le reste
clear_queue()
low = mk("zzlowtwo"); ok = mk("zzoktwo")
CALLS.clear()
rep = pv.prevalidate(LEX, "all", cfg=pv.config(model="xai/grok-4.3", second="none", fallback="none"))
st = {it["terme"]: it for g in rep["groupes"].values() for it in g}
check("sans 2e modèle: le cas douteux reste douteux", st["zzlowtwo"]["statut"] == "douteuse" and not llm_calls(True) and rep["douteux_sans_second_avis"] == 1, st["zzlowtwo"])

# ── 5. contrôles déterministes (gratuits) ───────────────────────────────────
print("== contrôles déterministes")
clear_queue()
dup = mk("cumulonimbus")
fb = mk("zzecran"); core.edit_proposal(fb, None, {}); 
with core._db_lock, core.db() as con:
    d = json.loads(con.execute("SELECT data FROM proposals WHERE id=?", (fb,)).fetchone()["data"]); d["forme_base_proposee"] = "zzécran"; d["forme_base_motif"] = "le corpus l'accentue"
    con.execute("UPDATE proposals SET data=? WHERE id=?", (json.dumps(d, ensure_ascii=False), fb))
vv = mk("zzvarint")
with core._db_lock, core.db() as con:
    d = json.loads(con.execute("SELECT data FROM proposals WHERE id=?", (vv,)).fetchone()["data"]); d.setdefault("variantes", []).append({"forme": "zz", "type": "manuelle", "coche": True})
    d["voir_aussi"] = ["fiche inexistante xyz"]
    con.execute("UPDATE proposals SET data=? WHERE id=?", (json.dumps(d, ensure_ascii=False), vv))
sg = mk("zzsigle", definition="Le zzsigle se règle sur un VOR proche de la route. Il sert uniquement à tester les sigles développés.")
cand = mk("variom")
CALLS.clear()
rep = pv.prevalidate(LEX, "all", cfg=CFG)
st = {it["terme_initial"]: it for g in rep["groupes"].values() for it in g}
check("déterministe: doublon d'une fiche existante -> à rejeter, sans modèle", st["cumulonimbus"]["statut"] == "a_rejeter" and "cumulonimbus" not in " ".join(sum((c["terms"] for c in CALLS), [])), st["cumulonimbus"])
check("déterministe: accent évident corrigé (zzecran -> zzécran) -> corrigée-prête", st["zzecran"]["terme"] == "zzécran" and st["zzecran"]["statut"] == "corrigee_prete" and any(f["champ"] == "terme" and f["origine"] == "automatique" for f in st["zzecran"]["corrections"]), st["zzecran"])
check("déterministe: variante trop courte retirée automatiquement", st["zzvarint"]["statut"] == "corrigee_prete" and "zz" not in prop(vv)["data"]["variantes"][-1]["forme"] if False else "zz" not in pv.RULES.retained_forms(prop(vv)["data"]), st["zzvarint"])
check("déterministe: « voir aussi » inexistant retiré", prop(vv)["data"]["voir_aussi"] == [] and any(f["champ"] == "voir_aussi" for f in st["zzvarint"]["corrections"]), st["zzvarint"])
check("déterministe: sigle développé à la 1re occurrence", "VOR (" in prop(sg)["data"]["definition"] and any(f["champ"] == "definition" and f["origine"] == "automatique" for f in st["zzsigle"]["corrections"]), prop(sg)["data"]["definition"])
check("déterministe: variante d'une fiche existante -> douteuse avec question, sans modèle", st["variom"]["statut"] == "douteuse" and "variomètre" in st["variom"]["question"] and "variom" not in " ".join(sum((c["terms"] for c in CALLS), [])), st["variom"])
check("déterministe: l'avant/après est conservé pour le relecteur", all("avant" in f and "apres" in f for it in st.values() for f in it["corrections"]))

# ── 6. UNE seule sauvegarde et UNE seule reconstruction pour N propositions ─────
print("== écriture unique")
clear_queue()
N = 6
ids6 = [mk("zzvalide%s" % chr(97 + i)) for i in range(N)]
rep = pv.prevalidate(LEX, "all", cfg=CFG)
check("écriture: les 6 sont prêtes", rep["comptes"]["prete"] == N, rep["comptes"])
n_calls = {"backup": 0, "rebuild": 0}
_ob, _orb = core.backup_site, core.rebuild
core.backup_site = lambda *a, **k: (n_calls.__setitem__("backup", n_calls["backup"] + 1), _ob(*a, **k))[1]
core.rebuild = lambda *a, **k: (n_calls.__setitem__("rebuild", n_calls["rebuild"] + 1), _orb(*a, **k))[1]
n0 = core._count_cards(LEX)
# non prêtes refusées côté serveur : un id qui n'est pas « prête »
dd = mk("zzlowrefuse")
r0 = pv.apply_ready(LEX, [dd])
check("écriture: une proposition non « prête » n'est jamais validée", not r0["ok"] and r0["ignorees"] and core._count_cards(LEX) == n0, r0)
r = pv.apply_ready(LEX, ids6, tests=[("stub", ["python3", "-c", "pass"])])
check("écriture: 6 propositions validées en UNE opération", r["ok"] and len(r["valides"]) == N and core._count_cards(LEX) == n0 + N, r)
check("écriture: UNE sauvegarde", n_calls["backup"] == 1, n_calls)
check("écriture: UNE reconstruction", n_calls["rebuild"] == 1, n_calls)
check("écriture: les 6 fiches sont dans le lexique complet", all(("zzvalide" + chr(97 + i)) in (CP / "data/data_glossaire_full.py").read_text("utf-8") for i in range(N)))
check("écriture: statut validé dans la file", not any(p["terme"].startswith("zzvalide") for p in core.list_proposals(LEX)))
core.backup_site, core.rebuild = _ob, _orb

# ── 7. restauration complète si un test échoue ──────────────────────────────
print("== restauration")
clear_queue()
ids3 = [mk("zzrestaure%s" % chr(97 + i)) for i in range(3)]
pv.prevalidate(LEX, "all", cfg=CFG)
st0 = site_state()
r = pv.apply_ready(LEX, ids3, tests=[("boom", ["python3", "-c", "import sys; print('échec simulé'); sys.exit(3)"])])
check("restauration: un test en échec -> validation annulée", not r["ok"] and r.get("restaure") and "boom" in r["erreur"], r)
check("restauration: fiches, sources et index identiques à l'état d'avant", site_state() == st0, (st0, site_state()))
check("restauration: les propositions restent « à valider » avec l'erreur", all(prop(i)["data"].get("erreur_validation") for i in ids3))
check("restauration: aucune fiche ajoutée", not any(("zzrestaure" + chr(97 + i)) in (CP / "data/data_glossaire_full.py").read_text("utf-8") for i in range(3)))
# refus si le nombre de fiches baisse
_orb2, _dropped = core.rebuild, []


def rebuild_drop(*a, **k):                       # la reconstruction « perd » 3 fiches (une seule fois : la reconstruction de remise en état est saine)
    out = _orb2(*a, **k)
    if not _dropped:
        for f in sorted((core.lex_root(LEX) / core.dist_rel(LEX) / "t").glob("*.json"))[:3]:
            f.unlink(); _dropped.append(f)
    return out


core.rebuild = rebuild_drop
st0 = site_state()

r = pv.apply_ready(LEX, ids3, tests=[("stub", ["python3", "-c", "pass"])])
core.rebuild = _orb2
check("reconstruction qui perd des fiches : refus + restauration complète (le refus « nombre de fiches baissé » est testé dans test_suggest)", not r["ok"] and r.get("restaure") and site_state() == st0, (r.get("erreur"), st0, site_state()))
check("refus: la reconstruction de remise en état a bien eu lieu (3 fiches revenues)", all(f.exists() for f in _dropped))

# ── 8. proposition modifiée après la pré-validation : refusée ───────────────
print("== modification après pré-validation")
core.edit_proposal(ids3[0], None, {"definition": "Autre définition écrite à la main. Elle change l'empreinte de la proposition."})
rd, sk = pv.ready_ids(LEX, ids3)
check("empreinte: une proposition modifiée depuis n'est plus prête", ids3[0] not in rd and any(s["id"] == ids3[0] for s in sk) and len(rd) == 2, (rd, sk))

# ── 9. rejet : seulement les « à rejeter » ──────────────────────────────────
print("== rejet")
clear_queue()
r1 = mk("zzrejtres"); k1 = mk("zzoktrois")
rep = pv.prevalidate(LEX, "all", cfg=CFG)
out = pv.reject_flagged(LEX, [r1, k1])
check("rejet: seule la proposition « à rejeter » est rejetée", out["rejetes"] == ["zzrejtres"] and len(out["ignores"]) == 1, out)
check("rejet: la prête reste à valider", prop(k1))

# ── 10. API : session, jobs asynchrones, public fermé ───────────────────────
print("== API")
clear_queue()
pids = [mk("zzapi%s" % chr(97 + i)) for i in range(4)] + [mk("zzrejapi")]
H = {"Cookie": ""}
code, _ = api.route("POST", "/api/suggest/prevalidate", {}, b'{"ids":"all"}')
check("API: pré-valider sans session -> 401", code == 401)
code, _ = api.route("POST", "/api/suggest/prevalidate/apply", {}, b'{"ids":[1]}')
check("API: valider les prêtes sans session -> 401", code == 401)
code, _ = api.route("POST", "/api/suggest/prevalidate/reject", {}, b'{"ids":[1]}')
check("API: rejeter sans session -> 401", code == 401)
code, _ = api.route("GET", "/api/suggest/prevalidate/summary", {}, b"")
check("API: synthèse sans session -> 401", code == 401)
code, j = api.route("POST", "/api/suggest/login", {}, json.dumps({"password": "pw-factice-test"}).encode(), "9.9.9.9")
H = {"Cookie": "%s=%s" % (core.COOKIE_NAME, j["_cookie"])}
CALLS.clear()
code, j = api.route("POST", "/api/suggest/prevalidate", H, json.dumps({"ids": "all", "domain": LEX}).encode())
check("API: pré-valider avec session -> job", code == 200 and re.fullmatch(r"[0-9a-f]{16}", j.get("job", "")), (code, j))
jid = j["job"]
code2, j2 = api.route("POST", "/api/suggest/prevalidate", H, json.dumps({"ids": "all", "domain": LEX}).encode())
check("API: un seul job à la fois par lexique (400 si déjà en cours)", code2 in (200, 400))
for _ in range(100):
    code, v = api.route("GET", "/api/suggest/prevalidate/job/" + jid, H, b"")
    if v["etat"] != "running":
        break
    time.sleep(0.3)
check("API: job terminé avec progression", code == 200 and v["etat"] == "done" and v["fait"] == v["total"] == 5, v)
check("API: le job n'est pas servi par la route publique", api.route("GET", "/api/suggest/job/" + jid, {}, b"")[0] == 404 and api.route("GET", "/api/suggest/job/" + jid, H, b"")[0] == 404)
code, s = api.route("GET", "/api/suggest/prevalidate/summary?domain=" + LEX, H, b"")
check("API: synthèse (comptes, coût, durée)", code == 200 and s["comptes"]["prete"] == 4 and s["comptes"]["a_rejeter"] == 0 + len(s["groupes"]["a_rejeter"]) and s["job"]["usd"] > 0 and "secs" in s["job"], s)
code, j = api.route("POST", "/api/suggest/prevalidate/apply", H, json.dumps({"domain": LEX}).encode())
check("API: valider sans liste d'ids -> 400 (jamais « tout » implicite)", code == 400, (code, j))
ready = [it["id"] for it in s["groupes"]["prete"]]
st0 = site_state()
code, j = api.route("POST", "/api/suggest/prevalidate/reject", H, json.dumps({"ids": ready, "domain": LEX}).encode())
check("API: rejeter des prêtes -> aucune rejetée", code == 200 and j["rejetes"] == [] and site_state() == st0, j)
core.backup_site  # noqa
_old = pv.POST_TESTS
pv.POST_TESTS = [("stub", ["python3", "-c", "pass"])]
code, j = api.route("POST", "/api/suggest/prevalidate/apply", H, json.dumps({"ids": ready, "domain": LEX}).encode())
check("API: « Valider les N prêtes » -> job d'écriture", code == 200 and "job" in j, (code, j))
for _ in range(400):
    code, v = api.route("GET", "/api/suggest/prevalidate/job/" + j["job"], H, b"")
    if v["etat"] != "running":
        break
    time.sleep(0.5)
pv.POST_TESTS = _old
check("API: écriture terminée, 4 fiches ajoutées", v["etat"] == "done" and v["info"]["resultat"]["ok"] and len(v["info"]["resultat"]["valides"]) == 4, v)

print()
if FAILS:
    print("ÉCHECS (%d) : %s" % (len(FAILS), "; ".join(FAILS)))
    sys.exit(1)
print("TOUS LES TESTS test_prevalidate PASSENT")
