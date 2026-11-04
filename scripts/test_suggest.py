#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_suggest.py — tests ciblés du nouveau code « Suggérer des termes » (pas la suite complète).
Lancer : python3 scripts/test_suggest.py   (aucun appel réseau : LLM simulé ; base SQLite temporaire)"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="suggest-test-")
os.environ["AEROLEX_SUGGEST_DIR"] = _TMP
os.environ["AEROLEX_SUGGEST_TOKEN"] = "tok-test"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import suggest_core as core  # noqa: E402
import suggest_api as api    # noqa: E402

FAILS = []


def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + (" " + str(extra) if (extra and not cond) else ""))
    if not cond:
        FAILS.append(name)


# ── 1. parsing / dédoublonnage ──────────────────────────────────────────────
p = core.parse_terms("masse totale, datum; Emplanture\nAIP, emplantures, 1. chandelle , « Cumulonimbus », , cumulonimbus")
check("parse: séparateurs , ; \\n", p["terms"] == ["masse totale", "datum", "Emplanture", "AIP", "chandelle", "Cumulonimbus"], p["terms"])
check("parse: doublons (pluriel + casse) comptés", p["duplicates"] == 2, p["duplicates"])
check("parse: accents/casse -> même clé", len(core.parse_terms("Hélice, helice, HÉLICE")["terms"]) == 1)
check("parse: limite par soumission", len(core.parse_terms(",".join("t%d" % i for i in range(400)), 300)["terms"]) == 300)
long = "x " * 20
check("parse: terme trop long rejeté", core.parse_terms(long)["rejected"] != [] and core.parse_terms(long)["terms"] == [])
check("parse: puces/numéros retirés", core.parse_terms("- QNH\n* QFE\n3) QNE")["terms"] == ["QNH", "QFE", "QNE"])
check("singular: aux->al, s", core.singular("chevaux") == "cheval" and core.singular("ailerons") == "aileron" and core.singular("cumulus") == "cumulus")

# upload
r = core.parse_upload("liste.csv", "terme;def\nqnh;x\nqfe;y\n".encode("utf-8"))
check("upload csv liste", r["mode"] == "liste" and "qnh" in r["terms"], r)
prose = ("Le pilote vérifie le QNH avant le décollage. Le QNH est calé sur l'altimètre. "
         "L'ATIS donne le QNH et la piste en service. Le circuit de piste se fait à 1000 ft. " * 6)
cands = core.extract_candidates(prose)
check("candidats: sigles extraits", "QNH" in cands and "ATIS" in cands, cands[:10])
check("candidats: pas de mots vides", "le" not in cands and "de" not in cands)
r = core.parse_upload("cours.docx", b"PK") if False else None
try:
    core.parse_upload("x.exe", b"abc")
    check("upload format inconnu refusé", False)
except ValueError:
    check("upload format inconnu refusé", True)

# ── 2. comparaison à l'index (gratuit) ──────────────────────────────────────
idx = core.get_index("aero")
m = idx.match("AIP")
check("index: terme exact -> present + lien", m and m["statut"] == "present" and m["lien"].endswith(".html"), m)
check("index: casse/pluriel", idx.match("Cumulonimbus")["statut"] == "present" and idx.match("cumulonimbus")["terme"] == "cumulonimbus")
check("index: inconnu", idx.match("baguette de pain") is None)
check("index: voisins (datum -> mm aft datum)", any("datum" in n["terme"] for n in idx.neighbours("datum")), idx.neighbours("datum"))
check("index: familles existantes", "documents_bord" in idx.families)

# ── 3. contrat JSON LLM simulé ──────────────────────────────────────────────
fams = {"documents_bord": 3, "pistes": 2}
good = {"items": [
    {"terme": "chandelle", "domaine": True, "raison_domaine": "figure de voltige", "pertinent": True, "raison_pertinent": "courante",
     "origine": "", "traduction": "", "definition": "Montée très cabrée suivie d'un retour en palier, figure de voltige de base.",
     "famille": "inventée_x", "famille_nouvelle": "", "synonymes": ["wingover"], "confiance": 0.8},
    {"terme": "baguette de pain", "domaine": False, "raison_domaine": "boulangerie", "pertinent": False, "raison_pertinent": "hors sujet",
     "definition": "", "famille": "", "synonymes": [], "confiance": 0.99},
]}
out = core.parse_llm("```json\n" + json.dumps(good) + "\n```", ["chandelle", "baguette de pain"], fams)
check("llm: JSON dans un bloc markdown accepté", set(out) == {"chandelle", "baguette de pain"})
check("llm: famille inventée -> famille_nouvelle", out["chandelle"]["famille"] == "" and out["chandelle"]["famille_nouvelle"] == "inventée_x")
check("llm: classification", core.classify(out["chandelle"]) == "a_valider" and core.classify(out["baguette de pain"]) == "hors_domaine")
bad = core.validate_item({"domaine": "oui", "pertinent": "true", "definition": "court", "confiance": "abc"}, "t", fams)
check("llm: booléens texte, confiance invalide, définition trop courte -> non pertinent", bad["domaine"] and not bad["pertinent"] and bad["confiance"] == 0.0)
check("llm: HTML retiré de la définition", "<" not in core.validate_item({"domaine": True, "pertinent": True, "definition": "<b>Une définition assez longue ici</b>"}, "t", fams)["definition"])
try:
    core.parse_llm("pas du json", ["a"], fams)
    check("llm: JSON invalide -> exception", False)
except Exception:
    check("llm: JSON invalide -> exception", True)
partial = core.parse_llm(json.dumps({"items": [good["items"][0]]}), ["chandelle", "autre"], fams)
check("llm: terme manquant détecté", "autre" not in partial)

# ── 4. appels simulés : secours, cache, coût ────────────────────────────────
CALLS = []


def fake_provider(name, messages, n):
    CALLS.append(name)
    terms = [l[2:] for l in messages[1]["content"].splitlines() if l.startswith("- ")]
    if name == "xai" and os.environ.get("FAKE_XAI_DOWN"):
        raise RuntimeError("503")
    items = []
    for t in terms:
        ok = "pain" not in t
        items.append({"terme": t, "domaine": ok, "raison_domaine": "r", "pertinent": ok, "raison_pertinent": "r",
                      "definition": ("Définition simulée suffisamment longue pour %s." % t) if ok else "",
                      "famille": "pistes" if ok else "", "synonymes": [t + " bis"], "confiance": 0.9})
    return json.dumps({"items": items}), {"in": 100, "out": 50}, ("grok-4.3" if name == "xai" else "local@local"), (0.001 if name == "xai" else 0.0)


core._call_provider = fake_provider
core.UNIT_SYNC_MAX = 3

v = core.submit("aero", "emplanture")
check("unitaire: réponse synchrone terminée", v["etat"] == "done" and v["resultats"][0]["statut"] == "analyse", v["etat"])
check("unitaire: 1 appel LLM", CALLS == ["xai"], CALLS)
check("unitaire: proposition en file", [x["terme"] for x in core.list_proposals("aero")] == ["emplanture"])
CALLS.clear()
v = core.submit("aero", "emplantures")        # pluriel du même terme : cache
check("cache: pluriel déjà analysé -> aucun appel", CALLS == [] and v["resultats"][0].get("cache") is True, CALLS)
check("cache: pas de doublon de proposition", len(core.list_proposals("aero")) == 1)

CALLS.clear()
v = core.submit("aero", "masse totale, levier, emplanture, AIP, chandelle, cumulonimbus, baguette de pain", )
for _ in range(100):
    v = core.job_view(v["id"])
    if v["etat"] == "done":
        break
    time.sleep(0.1)
by = {r["terme"]: r for r in v["resultats"]}
check("lot: job terminé, 7 résultats", v["etat"] == "done" and len(by) == 7 and v["fait"] == 7, v["etat"])
check("lot: AIP et cumulonimbus déjà présents (gratuit)", by["AIP"]["statut"] == "present" and by["cumulonimbus"]["statut"] == "present")
check("lot: baguette de pain hors domaine", by["baguette de pain"]["verdict"] == "hors_domaine")
check("lot: 4 termes restants -> 2 appels parallèles de 2 (emplanture en cache)", len(CALLS) == 2, CALLS)
# « datum » est désormais une fiche (validée) : on teste les voisins avec un terme absent (levier -> bras de levier)
check("lot: levier voisins (bras de levier)", by["levier"].get("voisins"))
check("lot: coût journalisé", core.stats()["usd_total"] > 0)
check("lot: hors domaine jamais en file", "baguette de pain" not in [x["terme"] for x in core.list_proposals("aero")])

# repli local quand xAI tombe
os.environ["FAKE_XAI_DOWN"] = "1"
CALLS.clear()
v = core.submit("aero", "ressource")
check("secours: xai x2 puis local", CALLS == ["xai", "xai", "local"], CALLS)
check("secours: résultat obtenu, modèle local", v["resultats"][0].get("modele", "").endswith("@local"), v["resultats"][0])
del os.environ["FAKE_XAI_DOWN"]

# plafond quotidien
old = core.DAILY_USD_CAP
core.DAILY_USD_CAP = 0.0
CALLS.clear()
core.llm_batch("aero", ["zzz"], fams)
check("plafond: xai non appelé, secours local", "xai" not in CALLS and "local" in CALLS, CALLS)
core.DAILY_USD_CAP = old

# lot > UNIT_SYNC_MAX : asynchrone avec progression
terms = ["t%d" % i for i in range(45)]
v = core.submit("aero", ",".join(terms))
check("lot async: état initial running ou done avec total 45", v["total"] == 45)
for _ in range(100):
    v = core.job_view(v["id"])
    if v["etat"] == "done":
        break
    time.sleep(0.1)
check("lot async: 45 traités", v["fait"] == 45 and v["etat"] == "done")
check("lot: taille de lot adaptative", core.batch_size(1) == 2 and core.batch_size(4) == 2 and core.batch_size(45) == 12 and core.batch_size(300) == 20)

# ── 5. file de propositions, revue, validation ──────────────────────────────
props = core.list_proposals("aero")
pid = next(x["id"] for x in props if x["terme"] == "emplanture")
core.edit_proposal(pid, None, {"definition": "Zone de jonction de l'aile et du fuselage, modifiée.", "synonymes": "racine d'aile, emplanture d'aile", "famille": "pistes"})
e = next(x for x in core.list_proposals("aero") if x["id"] == pid)
check("revue: modification enregistrée", e["data"]["definition"].endswith("modifiée.") and e["data"]["synonymes"] == ["racine d'aile", "emplanture d'aile"])
pid2 = next(x["id"] for x in props if x["terme"] == "chandelle")
core.reject_proposal(pid2)
check("revue: rejet", "chandelle" not in [x["terme"] for x in core.list_proposals("aero")] and len(core.list_proposals("aero", "rejected")) == 1)

# validation sur une COPIE de la source (jamais le vrai fichier)
src = Path(_TMP) / "data_glossaire.py"
shutil.copy(core.ROOT / "data" / "data_glossaire.py", src)
core.LEXICONS["aero"]["source"] = os.path.relpath(src, core.ROOT)
r = core.validate_proposals([pid, 999999][:1], do_rebuild=False)
txt = src.read_text("utf-8")
ns = {}
exec(compile(txt.replace("from glos_utils import dev_mode", "dev_mode=lambda *a,**k: False"), "src", "exec"), ns) if False else None
import ast
ast.parse(txt)
check("validation: valide la proposition", r["valides"] == ["emplanture"], r)
check("validation: entrée écrite dans la source, fichier toujours valide", '"emplanture"' in txt and "racine d'aile" in txt)
check("validation: statut validated", core.list_proposals("aero", "validated")[0]["terme"] == "emplanture")
try:
    core.validate_proposals([pid], do_rebuild=False)
    check("validation: déjà validée -> erreur", False)
except KeyError:
    check("validation: déjà validée -> erreur", True)
e1 = core.render_entry("AIP2", {"definition": "Texte assez long pour test.", "origine": "Aeronautical Information Publication", "traduction": "publication d'information aéronautique", "famille": "pistes", "synonymes": ["aip2", "AIP bis"]})
check("render_entry: développé en préfixe, synonymes sans le terme", "<em>Aeronautical Information Publication</em> — « publication" in e1 and '"variantes": ["AIP bis"]' in e1, e1)
try:
    core.rebuild([["python3", "-c", "import sys; sys.exit(3)"]])
    check("rebuild: échec remonté", False)
except RuntimeError:
    check("rebuild: échec remonté", True)

# ── 6. API : jeton + routes ─────────────────────────────────────────────────
H = lambda t=None: {"X-Suggest-Token": t} if t else {}
check("api: lexicons public", api.route("GET", "/api/suggest/lexicons", {}, b"")[0] == 200)
check("api: 401 sans jeton", api.route("POST", "/api/suggest/submit", H(), b"{}")[0] == 401)
check("api: 401 mauvais jeton", api.route("GET", "/api/suggest/proposals", H("nope"), b"")[0] == 401)
check("api: 400 sans terme", api.route("POST", "/api/suggest/submit", H("tok-test"), b'{"text":" , "}')[0] == 400)
s, o = api.route("POST", "/api/suggest/submit", H("tok-test"), json.dumps({"domain": "aero", "text": "AIP"}).encode())
check("api: submit déjà présent", s == 200 and o["resultats"][0]["statut"] == "present")
check("api: job inconnu 404", api.route("GET", "/api/suggest/job/" + "0" * 16, H("tok-test"), b"")[0] == 404)
check("api: lexique inconnu 404", api.route("POST", "/api/suggest/submit", H("tok-test"), b'{"domain":"med","text":"x"}')[0] == 404)
s, o = api.route("POST", "/api/suggest/parse?filename=a.txt", H("tok-test"), b"qnh, qfe")
check("api: parse upload", s == 200 and o["terms"] == ["qnh", "qfe"])

shutil.rmtree(_TMP, ignore_errors=True)
print("\n%d échec(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
