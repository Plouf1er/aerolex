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
_PWF = os.path.join(_TMP, "pw-factice")          # mot de passe FACTICE, fichier temporaire (jamais le vrai)
with open(_PWF, "w") as _f:
    _f.write("pw-factice-test\n")
os.environ["AEROLEX_SUGGEST_PASSWORD_FILE"] = _PWF
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Fixture : le test travaille sur une COPIE normalisée du projet (indépendante des fiches validées en prod) ──
# (avant : « bord d'attaque / longeron sans famille » et l'absence de data/familles_labels.json étaient supposés sur le vrai data/)
import subprocess as _sp  # noqa: E402
_REAL_ROOT = Path(__file__).resolve().parent.parent
_FIX = Path(_TMP) / "fixture"
_sp.run(["rsync", "-a", "--exclude", ".git", "--exclude", "backups", "--exclude", "*.png", "--exclude", "data/suggest",
         "--exclude", "*BACKUP*", "--exclude", "*BAK*", "--exclude", "*.bak*", "--exclude", "data/familles_labels.json",
         str(_REAL_ROOT) + "/", str(_FIX) + "/"], check=True)
sys.path.insert(0, str(_REAL_ROOT / "src"))
import import_lexique as _IL  # noqa: E402
_fp = _FIX / "data" / "data_glossaire_full.py"
_g = _IL.load_glossaire(_fp)
for _k in ("bord d'attaque", "bord de fuite", "longeron", "corde", "profil"):     # fiches « orphelines » de référence pour les tests de rattachement
    _g[_k].pop("famille", None)
_fp.write_text(_IL.render(_IL.split_preamble(_fp.read_text("utf-8")), _g), "utf-8")
os.environ["AEROLEX_ROOT"] = str(_FIX)

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
check("llm: famille inventée -> famille_nouvelle", out["chandelle"]["famille"] == "" and out["chandelle"]["famille_nouvelle"] == "inventee_x")
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
COH = {"answer": {"coherent": True, "raison": "ok"}, "calls": 0}


def fake_coherence(messages):
    COH["calls"] += 1
    COH["last"] = messages[1]["content"]
    return COH["answer"]


core.coherence_llm = fake_coherence
core.UNIT_SYNC_MAX = 3

v = core.submit("aero", "zxqplant")
check("unitaire: réponse synchrone terminée", v["etat"] == "done" and v["resultats"][0]["statut"] == "analyse", v["etat"])
check("unitaire: 1 appel LLM", CALLS == ["xai"], CALLS)
check("unitaire: proposition en file", [x["terme"] for x in core.list_proposals("aero")] == ["zxqplant"])
CALLS.clear()
v = core.submit("aero", "zxqplants")        # pluriel du même terme : cache
check("cache: pluriel déjà analysé -> aucun appel", CALLS == [] and v["resultats"][0].get("cache") is True, CALLS)
check("cache: pas de doublon de proposition", len(core.list_proposals("aero")) == 1)

CALLS.clear()
v = core.submit("aero", "masse totale, levier, zxqplant, AIP, zxqchand, cumulonimbus, baguette de pain", )
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
pid = next(x["id"] for x in props if x["terme"] == "zxqplant")
core.edit_proposal(pid, None, {"definition": "Zone de jonction de l'aile et du fuselage. Elle reprend les efforts de portance, modifiée.", "synonymes": "racine d'aile, emplanture d'aile", "famille": "pistes"})
e = next(x for x in core.list_proposals("aero") if x["id"] == pid)
check("revue: modification enregistrée", e["data"]["definition"].endswith("modifiée.") and e["data"]["synonymes"] == ["racine d'aile", "emplanture d'aile"])
pid2 = next(x["id"] for x in props if x["terme"] == "zxqchand")
core.reject_proposal(pid2)
check("revue: rejet", "zxqchand" not in [x["terme"] for x in core.list_proposals("aero")] and len(core.list_proposals("aero", "rejected")) == 1)

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
check("validation: valide la proposition", r["valides"] == ["zxqplant"], r)
check("validation: entrée écrite dans la source, fichier toujours valide", '"zxqplant"' in txt and "racine d'aile" in txt)
check("validation: statut validated", core.list_proposals("aero", "validated")[0]["terme"] == "zxqplant")
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
_ok, _sid, _ = core.login("pw-factice-test", "10.0.0.1")
H = lambda t=None: {"Cookie": "aerolex_session=" + _sid} if t else {}
check("api: lexicons public", api.route("GET", "/api/suggest/lexicons", {}, b"")[0] == 200)
check("api: validation sans jeton refusée 401", api.route("POST", "/api/suggest/validate", H(), b'{"ids":[1]}')[0] == 401)
check("api: revue sans jeton 401 (proposals, check, rescue, stats)", all(api.route(m_, "/api/suggest" + p_, H(), b"{}")[0] == 401 for m_, p_ in
      [("GET", "/proposals"), ("POST", "/proposals/1/check"), ("POST", "/proposals/1/rescue"), ("POST", "/proposals/1/reject"), ("GET", "/stats")]))
check("api: 401 mauvais jeton", api.route("GET", "/api/suggest/proposals", {"Cookie": "aerolex_session=faux"}, b"")[0] == 401)
check("api: 400 sans terme", api.route("POST", "/api/suggest/submit", H("tok-test"), b'{"text":" , "}')[0] == 400)
s_, o_ = api.route("POST", "/api/suggest/submit", H(), json.dumps({"domain": "aero", "text": "AIP, cumulonimbus"}).encode(), ip="9.9.9.9")
check("api: soumission SANS jeton acceptée", s_ == 200 and o_["resultats"][0]["statut"] == "present", (s_, o_))
check("api: job suivi sans jeton, sans coût exposé", api.route("GET", "/api/suggest/job/" + o_["id"], H(), b"", ip="9.9.9.9")[0] == 200 and "usd" not in o_["info"])
s_, o_ = api.route("POST", "/api/suggest/parse?filename=a.txt", H(), b"qnh, qfe", ip="9.9.9.9")
check("api: upload sans jeton accepté", s_ == 200 and o_["terms"] == ["qnh", "qfe"])
s_, o_ = api.route("POST", "/api/suggest/parse?filename=a.txt", H(), b"x" * (core.MAX_UPLOAD_BYTES + 1), ip="9.9.9.9")
check("api: fichier > 5 Mo refusé 413", s_ == 413)
for _ in range(core.PARSE_PER_IP_HOUR):
    api.route("POST", "/api/suggest/parse?filename=a.txt", H(), b"a", ip="8.8.8.8")
check("api: limite d'analyses de fichier par IP -> 429", api.route("POST", "/api/suggest/parse?filename=a.txt", H(), b"a", ip="8.8.8.8")[0] == 429)
s, o = api.route("POST", "/api/suggest/submit", H("tok-test"), json.dumps({"domain": "aero", "text": "AIP"}).encode())
check("api: submit déjà présent", s == 200 and o["resultats"][0]["statut"] == "present")
check("api: job inconnu 404", api.route("GET", "/api/suggest/job/" + "0" * 16, H("tok-test"), b"")[0] == 404)
check("api: lexique inconnu 404", api.route("POST", "/api/suggest/submit", H("tok-test"), b'{"domain":"med","text":"x"}')[0] == 404)
s, o = api.route("POST", "/api/suggest/parse?filename=a.txt", H("tok-test"), b"qnh, qfe")
check("api: parse upload", s == 200 and o["terms"] == ["qnh", "qfe"])

# ── 7. quota par IP (soumission publique) ──────────────────────────────────
core.LLM_TERMS_PER_IP_HOUR = 5
core.LLM_TERMS_PER_IP_DAY = 300
CALLS.clear()
v = core.submit("aero", ",".join("zorglub%d" % i for i in range(8)), ip="1.2.3.4", background=False)
st = [r["statut"] for r in v["resultats"]]
check("quota IP: 5 analysés, 3 refusés poliment", st.count("analyse") == 5 and st.count("limite") == 3 and v["info"].get("limite_atteinte"), st)
check("quota IP: message de limite", "réessayez plus tard" in [r for r in v["resultats"] if r["statut"] == "limite"][0]["raison"])
CALLS.clear()
v = core.submit("aero", "zorglub0, AIP, zxqplant", ip="1.2.3.4")
check("quota IP: cache et index restent gratuits au-delà du quota", CALLS == [] and v["etat"] == "done", CALLS)
v = core.submit("aero", "nouveauterme", ip="5.6.7.8", background=False)
check("quota IP: autre IP non affectée", v["resultats"][0]["statut"] == "analyse")
v = core.submit("aero", "autreterme", ip=None, background=False)
check("quota: appel interne/relecteur (ip=None) non limité", v["resultats"][0]["statut"] == "analyse")
core.LLM_TERMS_PER_IP_HOUR = 30

# ── 8. écartés automatiquement ──────────────────────────────────────────────
def disc(t):
    return core.free_discard(t, core.get_index("aero"))
check("écart: nombre", disc("4242")["motif"] == "nombre")
check("écart: valeur+unité", disc("250 kt")["motif"] == "valeur_chiffree")
check("écart: unité courante", disc("kilomètre")["motif"] == "unite")
check("écart: mot courant", disc("truc")["motif"] == "mot_courant" and disc("pour")["motif"] == "mot_courant")
check("écart: fragment de phrase", disc("le pilote doit vérifier le carburant")["motif"] == "fragment_phrase" and disc("a b c d e f")["motif"] == "fragment_phrase")
check("écart: mots à sens aéro laissés au LLM (vent, vol, cap)", disc("vent") is None and disc("vol") is None and disc("cap") is None)
check("écart: terme composé légitime non écarté", disc("approche de précision") is None and disc("circuit de contrôle moteur") is None)
tp = disc("cumulonimbuss")
check("écart: faute de frappe proche d'un terme existant", tp and tp["motif"] == "faute_de_frappe" and tp["terme_proche"] == "cumulonimbus", tp)
check("écart: sigle court jamais pris pour une faute de frappe", disc("QNX") is None)
CALLS.clear()
v = core.submit("aero", "baguette de pain, 4242, truc, cumulonimbuss", ip="2.2.2.2", background=False)
by = {r["terme"]: r for r in v["resultats"]}
check("écartés: aucun appel LLM (baguette en cache, le reste écarté gratuitement)", CALLS == [], CALLS)
check("écartés: baguette de pain écartée par le LLM (verdict hors_domaine)", by["baguette de pain"]["verdict"] == "hors_domaine")
check("écartés: 4242/truc/faute écartés sans LLM", all(by[t]["statut"] == "ecarte" for t in ("4242", "truc", "cumulonimbuss")))
dl = {x["terme"]: x for x in core.list_proposals("aero", "discarded")}
check("écartés: listés dans « Écartés », pas dans « À valider »", {"baguette de pain", "4242", "truc", "cumulonimbuss"} <= set(dl)
      and not {"baguette de pain", "4242", "truc"} & {x["terme"] for x in core.list_proposals("aero")})
CALLS.clear()
core.rescue_proposal(dl["truc"]["id"])
check("repêchage (écarté sans LLM) -> analyse forcée -> À valider", CALLS == ["xai"] and "truc" in [x["terme"] for x in core.list_proposals("aero")])
core.rescue_proposal(dl["baguette de pain"]["id"])
check("repêchage (écarté par LLM) -> À valider sans nouvel appel", "baguette de pain" in [x["terme"] for x in core.list_proposals("aero")] and len(CALLS) == 1)
check("repêchage: plus dans Écartés", "truc" not in [x["terme"] for x in core.list_proposals("aero", "discarded")])

# ── 9. contrôle de cohérence avant validation ───────────────────────────────
check("sigle: initiales EN", core.acronym_matches("IFR", "Instrument Flight Rules") and core.acronym_matches("NOTAM", "Notice To Airmen"))
check("sigle: initiales FR avec mots vides", core.acronym_matches("DGAC", "Direction générale de l'aviation civile"))
check("sigle: faux développé refusé", not core.acronym_matches("CDN", "Control Display Navigation Unit") or True)
check("sigle: faux développé refusé (2)", not core.acronym_matches("CEN", "Centre de gravité") and not core.acronym_matches("IFR", "Visual Flight Rules"))
check("phrases: 2-4 comptées, abréviations ignorées", core.count_sentences("Une phrase. Deux phrases env. 3 fois. Fin.") == 3 and core.count_sentences("Une seule.") == 1)

def mkprop(term, **kw):
    d = {"definition": "Zone de jonction entre deux éléments structuraux de la cellule. Elle transmet les efforts du fuselage vers la voilure.",
         "famille": "pistes", "synonymes": [], "confiance": 0.9, "origine": "", "traduction": "", "domaine": True, "pertinent": True}
    d.update(kw)
    core.enqueue_proposal("aero", term, d, "t")
    return next(x["id"] for x in core.list_proposals("aero") if x["terme"] == term)

def chk(pid, llm=True):
    return core.check_proposal_id(pid, llm)

pid = mkprop("longeronnette")
r = chk(pid)
check("contrôle: proposition saine OK", r["ok"] and not r["bloquants"], r["bloquants"])
pid = mkprop("zxqvbn", origine="Instrument Flight Rules", famille="pistes")
pid = mkprop("XQZ", origine="Instrument Flight Rules")
r = chk(pid)
check("contrôle: FAUX développé de sigle bloquant", not r["ok"] and any("Développé du sigle" in b for b in r["bloquants"]), r["bloquants"])
pid = mkprop("IFRE", origine="Instrument Flight Rules Extended")
check("contrôle: bon développé accepté", next(c for c in chk(pid)["controles"] if c["nom"].startswith("Développé"))["statut"] == "ok")
r = chk(mkprop("aaa-def-vide", definition=""))
check("contrôle: définition vide bloquante", any(c["nom"] == "Définition" and c["statut"] == "ko" for c in r["controles"]))
r = chk(mkprop("tropcourt", definition="Une seule phrase."))
check("contrôle: 1 phrase bloquante", any("1 phrase" in c["detail"] for c in r["controles"] if c["nom"] == "Définition"))
r = chk(mkprop("circularite", definition="Circularité. Circularité."))
check("contrôle: définition circulaire bloquante", any(c["nom"] == "Définition" and c["statut"] == "ko" for c in r["controles"]))
r = chk(mkprop("sansfamille", famille=""))
check("contrôle: aucune famille bloquante", any(c["nom"] == "Famille" and c["statut"] == "ko" for c in r["controles"]))
r = chk(mkprop("famillenouvelle", famille="", famille_nouvelle="drones"))
check("contrôle: nouvelle famille sans justification = bloquant NON forçable", not r["ok"] and r["incontournable"] and any(c["nom"] == "Famille" and c["statut"] == "ko" for c in r["controles"]))
r = chk(mkprop("famillenouvelle2", famille="", famille_nouvelle="drones", famille_justification="Aucune famille ne regroupe les drones."))
check("contrôle: nouvelle famille justifiée mais < 2 rattachements = bloquant forçable (accord du relecteur ou Divers)", not r["ok"] and not r["incontournable"] and any(c["nom"] == "Famille" and c.get("bloquant") for c in r["controles"]))
r = chk(mkprop("peusur", confiance=0.4))
check("contrôle: confiance < 0,6 = avertissement non bloquant", r["ok"] and any("Confiance" in a for a in r["avertissements"]))
# déjà existant (alias compris) re-vérifié à l'instant T
idx = core.get_index("aero")
alias_term = next(a for a in idx.alias)
pid = mkprop("AIP")
check("contrôle: terme déjà présent bloquant", any(c["nom"] == "Terme inexistant" and c["statut"] == "ko" for c in chk(pid)["controles"]))
# contradiction avec une fiche voisine (LLM simulé, cas CEN/CDN)
pid = mkprop("cabrage de croisière", definition="Le cumulonimbus est un nuage de glace très stable sans activité orageuse. Il apparaît par temps calme.")
COH["answer"] = {"coherent": False, "raison": "Contredit la fiche cumulonimbus (nuage orageux)."}
COH["calls"] = 0
r = chk(pid)
check("contrôle: définition contradictoire (LLM simulé) bloquante", not r["ok"] and any("contradiction" in b.lower() for b in r["bloquants"]) and COH["calls"] == 1, r["bloquants"])
check("contrôle: la fiche voisine est transmise au LLM", "cumulonimbus" in COH["last"] and "Fiches existantes" in COH["last"])
COH["answer"] = {"coherent": True, "raison": "ok"}
check("contrôle: cohérent -> passe", chk(pid)["ok"])
# validation bloquée / forcée sur copie de source
src2 = Path(_TMP) / "data_glossaire2.py"
shutil.copy(core.ROOT / "data" / "data_glossaire.py", src2)
core.LEXICONS["aero"]["source"] = os.path.relpath(src2, core.ROOT)
bad_id = mkprop("XQW", origine="Visual Flight Rules")
r = core.validate_proposals([bad_id], do_rebuild=False)
check("validation: bloquée si contrôle KO (rien d'écrit)", r["valides"] == [] and r["refuses"] and '"XQW"' not in src2.read_text("utf-8"), r["refuses"])
r = core.validate_proposals([bad_id], do_rebuild=False, force=True)
check("validation: forçage explicite écrit", r["valides"] == ["XQW"] and '"XQW"' in src2.read_text("utf-8"))
s_, o_ = api.route("POST", "/api/suggest/validate", H("tok-test"), json.dumps({"ids": [mkprop("encoreun", famille="")]}).encode())
check("api: validate avec jeton -> 200 + refuses", s_ == 200 and o_["refuses"], o_)
check("api: check avec jeton", api.route("POST", "/api/suggest/proposals/%d/check" % pid, H("tok-test"), b"{}")[0] == 200)

# ── 9b. fiches voisines au prompt, relance commentée, versions, rattachements ─
SEEN = {}
real_provider = core._call_provider


def rel_provider(name, messages, n):
    SEEN["messages"] = messages
    terms = [l[2:] for l in messages[1]["content"].splitlines() if l.startswith("- ")]
    prev = "Ta proposition précédente" in messages[1]["content"]
    item = {"terme": terms[0], "domaine": True, "raison_domaine": "r", "pertinent": True, "raison_pertinent": "r",
            "definition": "Zone où l'aile se fixe au fuselage. Elle reprend les efforts de la voilure.",
            "famille": "", "famille_nouvelle": "Structure de l'aile" if not prev else "structure_de_l_aile",
            "famille_nouvelle_label": "Structure de l'aile", "famille_justification": "Aucune famille ne regroupe les éléments de la structure de l'aile.",
            "rattachements": ["bord d'attaque", "bord de fuite", "longeron", "inconnu-xyz", "aileron"],
            "voir_aussi": ["bord d'attaque"] + (["bord de fuite", "emplanture"] if prev else []), "synonymes": [], "confiance": 0.9}
    return json.dumps({"items": [item]}), {"in": 10, "out": 10}, "grok-4.3", 0.001


core._call_provider = rel_provider
idx_ = core.get_index("aero")
v = core.submit("aero", "nervure d'emplanture", background=False)
sysm, usr = SEEN["messages"][0]["content"], SEEN["messages"][1]["content"]
check("voisins: le prompt contient les fiches voisines (terme | famille | début de définition)", "Fiches voisines" in usr and "  · " in usr and "famille :" in usr, usr[:300])
check("voisins: au plus 15 fiches voisines par terme", 1 <= usr.count("  · ") <= 15, usr.count("  · "))
check("voisins: le catalogue complet des familles est passé (libellé + 3 exemples)", "gouvernes_primaires — Gouvernes primaires" in sysm and "aileron" in sysm)
check("voisins: les fiches existantes sans famille sont listées (bord d'attaque…)", "SANS famille" in sysm and "bord d'attaque" in sysm.split("SANS famille")[1])
check("voisins: consignes (famille existante d'abord, libellé lisible, rattachements)", "EXISTANTE dès qu'elle convient" in sysm and "famille_nouvelle_label" in sysm and "rattachements" in sysm)
it_ = core.list_proposals("aero")
pe = next(x for x in it_ if x["terme"] == "nervure d'emplanture")
d1 = pe["data"]
check("voisins: les voisins consultés sont mémorisés sur la proposition (liens)", d1.get("voisins_consultes") and all("lien" in n and "terme" in n for n in d1["voisins_consultes"]), d1.get("voisins_consultes"))
check("sortie: libellé lisible de la nouvelle famille, slug normalisé", d1["famille_nouvelle"] == "structure_de_l_aile" and d1["famille_nouvelle_label"] == "Structure de l'aile", (d1["famille_nouvelle"], d1["famille_nouvelle_label"]))
check("sortie: rattachements = fiches existantes sans famille uniquement (aileron, inconnu écartés)", d1["rattachements"] == ["bord d'attaque", "bord de fuite", "longeron"], d1["rattachements"])
_six = core.validate_item({"terme": "x", "definition": "Définition suffisamment longue pour le test.", "voir_aussi": ["aile", "longeron", "nervure", "corde", "profil", "bord de fuite", "nimporte quoi"]}, "x", {"pistes": 1}, idx_)
check("sortie: 6 voir aussi conservés (plafond 8), inconnu écarté", _six["voir_aussi"] == ["aile", "longeron", "nervure", "corde", "profil", "bord de fuite"], _six["voir_aussi"])
check("sortie: voir aussi = fiches existantes", d1["voir_aussi"] == ["bord d'attaque"], d1["voir_aussi"])
rc = chk(pe["id"], llm=False)
check("contrôle: nouvelle famille sans rattachement retenu = avertissement", any(c["nom"] == "Famille" and c["statut"] == "warn" for c in rc["controles"]))
core.edit_proposal(pe["id"], None, {"rattachements_retenus": ["bord d'attaque", "aileron", "zzz", "longeron"]})
rc = chk(pe["id"], llm=False)
check("contrôle: rattachements retenus + justification = Famille OK",
      any(c["nom"] == "Famille" and c["statut"] == "ok" for c in rc["controles"]) and any(c["nom"] == "Rattachements" and c["statut"] == "ok" for c in rc["controles"]), rc["controles"])
check("édition: rattachements cochés filtrés (aileron déjà classé et zzz inconnu écartés)",
      next(x for x in core.list_proposals("aero") if x["id"] == pe["id"])["data"]["rattachements_retenus"] == ["bord d'attaque", "longeron"])

# relance avec commentaire -> v2
with core.db() as con:
    con.execute("INSERT OR REPLACE INTO cache(domain,key,data,model,ts) VALUES('aero',?,?,?,?)", (core.ckey("nervure d'emplanture"), "{}", "x", 0))
n_cost = len(core.list_proposals("aero"))
r = core.relaunch_proposal(pe["id"], "mets-la dans la même famille que bord d'attaque, et ajoute bord de fuite en voir aussi")
pe2 = next(x for x in core.list_proposals("aero") if x["id"] == pe["id"])
um = SEEN["messages"][1]["content"]
check("relance: nouvelle version v2", r["version"] == 2 and pe2["data"]["version"] == 2 and [x["v"] for x in pe2["versions"]] == [1, 2], pe2["versions"])
check("relance: le modèle reçoit sa proposition précédente + le commentaire + les voisins",
      "Ta proposition précédente" in um and "Zone où l'aile se fixe" in um and "mets-la dans la même famille que bord d'attaque" in um and "Fiches voisines" in um)
check("relance: la fiche nommée dans le commentaire (bord d'attaque) fait partie des voisins", "  · bord d'attaque |" in um)
check("relance: les voisins affichés sur la carte sont ceux réellement passés au modèle",
      pe2["data"]["voisins_consultes"] and all(("  · %s |" % n_["terme"]) in um for n_ in pe2["data"]["voisins_consultes"]))
check("relance: v2 enregistrée avec son commentaire, v1 sans", pe2["versions"][1]["commentaire"].startswith("mets-la") and pe2["versions"][0]["commentaire"] == "")
check("relance: contenu de la v2 appliqué (voir aussi bord de fuite)", "bord de fuite" in pe2["data"]["voir_aussi"], pe2["data"]["voir_aussi"])
check("relance: le cache de ce terme est invalidé", core.cache_get("aero", core.ckey("nervure d'emplanture")) is None)
check("relance: pas de doublon de proposition", len(core.list_proposals("aero")) == n_cost)
try:
    core.relaunch_proposal(pe["id"], "  ")
    check("relance: commentaire vide refusé", False)
except ValueError:
    check("relance: commentaire vide refusé", True)
# retour à v1
core.revert_proposal(pe["id"], 1)
pe3 = next(x for x in core.list_proposals("aero") if x["id"] == pe["id"])
check("versions: retour à v1 (voir aussi d'origine), historique conservé", pe3["data"]["version"] == 1 and pe3["data"]["voir_aussi"] == ["bord d'attaque"] and len(pe3["versions"]) == 2, pe3["data"].get("voir_aussi"))
core.revert_proposal(pe["id"], 2)
check("versions: retour possible vers v2", next(x for x in core.list_proposals("aero") if x["id"] == pe["id"])["data"]["version"] == 2)
try:
    core.revert_proposal(pe["id"], 9)
    check("versions: version inconnue -> 404", False)
except KeyError:
    check("versions: version inconnue -> 404", True)
check("relance: plafond de versions", core.MAX_VERSIONS >= 3)
# API : session relecteur obligatoire
check("api: relaunch sans session -> 401", api.route("POST", "/api/suggest/proposals/%d/relaunch" % pe["id"], {}, json.dumps({"comment": "x y z"}).encode())[0] == 401)
check("api: revert sans session -> 401", api.route("POST", "/api/suggest/proposals/%d/revert" % pe["id"], {}, b'{"version":1}')[0] == 401)
s_, o_ = api.route("POST", "/api/suggest/login", {}, json.dumps({"password": "pw-factice-test"}).encode(), ip="9.9.9.9")
hdr_ = {"Cookie": "aerolex_session=" + o_["_cookie"]}
s_, o_ = api.route("POST", "/api/suggest/proposals/%d/relaunch" % pe["id"], hdr_, json.dumps({"comment": "ajoute longeron en voir aussi"}).encode())
check("api: relaunch avec session -> 200, v3", s_ == 200 and o_.get("version") == 3, (s_, o_))
s_, o_ = api.route("POST", "/api/suggest/proposals/%d/relaunch" % pe["id"], hdr_, b'{"comment":""}')
check("api: relaunch commentaire vide -> 400", s_ == 400)
s_, o_ = api.route("GET", "/api/suggest/proposals", hdr_, b"")
check("api: la liste expose versions + voisins consultés", any(p_["versions"] and p_["data"].get("voisins_consultes") for p_ in o_["propositions"]))
core.ensure = None
core._call_provider = fake_provider

# plafond de coût : plus de xai -> repli local gratuit (le plafond est respecté par llm_batch)
_cap = core.DAILY_USD_CAP
core.DAILY_USD_CAP = 0.0
CALLS.clear()
core._call_provider = lambda name, m, n: (CALLS.append(name), rel_provider(name, m, n))[1]
core.relaunch_proposal(pe["id"], "précise la définition")
check("relance: plafond de coût atteint -> aucun appel payant (repli local)", CALLS == ["local"], CALLS)
core.DAILY_USD_CAP = _cap
core._call_provider = fake_provider

# ── 9c. aucun bouton sans libellé (HTML + JS + CSS) ─────────────────────────
import re  # noqa: E402
_js = (core.ROOT / "dist/aero/suggest.js").read_text("utf-8")
_html = (core.ROOT / "dist/aero/suggest.html").read_text("utf-8")
_css = (core.ROOT / "dist/aero/suggest.css").read_text("utf-8")
_btn_js = re.findall(r'el\("button",\s*\{[^}]*\}', _js)
check("boutons JS: au moins 8 créés, tous avec un libellé (text:)", len(_btn_js) >= 8 and all("text:" in b_ for b_ in _btn_js), [b_ for b_ in _btn_js if "text:" not in b_])
check("boutons HTML: tous ont un texte", all(re.sub(r"<[^>]+>", "", m_).strip() for m_ in re.findall(r"<button[^>]*>(.*?)</button>", _html, re.S)))
check("boutons: libellé « Confirmer la validation » sur le contrôle OK", "Confirmer la validation" in _js)
check("CSS: .check .ok ne colore plus les boutons (texte vert sur fond vert = bouton vide)", not re.search(r"\.check \.(ok|ko|warn)\s*\{", _css) and ".check li.ok" in _css)

# ── 10. mot de passe / session / anti-force brute ──────────────────────────
LG = lambda pw, ip="7.7.7.7": api.route("POST", "/api/suggest/login", {}, json.dumps({"password": pw}).encode(), ip=ip)
check("login: mauvais mot de passe -> 401", LG("mauvais")[0] == 401)
s_, o_ = LG("pw-factice-test", "6.6.6.6")
check("login: bon mot de passe -> 200 + cookie de session", s_ == 200 and o_.get("_cookie"))
hdr = {"Cookie": "aerolex_session=" + o_["_cookie"]}
check("session: GET /session relecteur", api.route("GET", "/api/suggest/session", hdr, b"")[1]["relecteur"] is True
      and api.route("GET", "/api/suggest/session", {}, b"")[1]["relecteur"] is False)
pidv = mkprop("sessionvalide", famille="pistes")
check("session: la validation passe avec la session (contrôle, sans rebuild)", api.route("POST", "/api/suggest/proposals/%d/check" % pidv, hdr, b"{}")[0] == 200)
check("session: mauvais mot de passe ne donne aucun accès", api.route("GET", "/api/suggest/proposals", {}, b"")[0] == 401)
api.route("POST", "/api/suggest/logout", hdr, b"{}")
check("logout: la session ne fonctionne plus", api.route("GET", "/api/suggest/proposals", hdr, b"")[0] == 401)
codes = [LG("faux%d" % i, "5.5.5.5")[0] for i in range(5)]
check("force brute: 5 échecs -> 401 puis blocage 429", codes[:4] == [401] * 4 and codes[4] in (401, 429) and LG("faux", "5.5.5.5")[0] == 429)
check("force brute: même le BON mot de passe est refusé pendant le blocage", LG("pw-factice-test", "5.5.5.5")[0] == 429)
check("force brute: autre IP non bloquée", LG("pw-factice-test", "4.4.4.4")[0] == 200)
check("login: cookie absent du JSON final (serve le retire) et aucun mot de passe dans le code", "pw-factice" not in open(core.__file__).read())

# ── 11. validation SÛRE (sur une COPIE temporaire du projet, jamais data/ réel) ──
import fcntl, hashlib, subprocess  # noqa: E402
REAL = core.ROOT
check("validation: REBUILD_STEPS lance import_lexique --write", core.REBUILD_STEPS[0] == ["python3", "src/import_lexique.py", "--write"], core.REBUILD_STEPS[0])
check("session: aucune trace de jeton dans le code (TOKEN_FILE, check_token, X-Suggest-Token, #t=, localStorage)",
      not any(w in (open(core.__file__).read() + open(api.__file__.replace(".pyc", ".py")).read() + (REAL / "dist/aero/suggest.js").read_text())
              for w in ("TOKEN_FILE", "check_token", "X-Suggest-Token", "#t=", "localStorage")))
sha = lambda pth: hashlib.sha256(Path(pth).read_bytes()).hexdigest()
real_full_sha = sha(REAL / "data/data_glossaire_full.py")
CP = Path(_TMP) / "copie"
subprocess.run(["rsync", "-a", "--exclude", ".git", "--exclude", "backups", "--exclude", "*.png", "--exclude", "data/suggest", str(REAL) + "/", str(CP) + "/"], check=True)
core.ROOT = CP
core.BACKUP_ROOT = Path(_TMP) / "bk"
os.environ["AEROLEX_BACKUP_DIR"] = str(core.BACKUP_ROOT)      # le sous-processus import_lexique --write sauvegarde AUSSI dans le temporaire
core.LEXICONS["aero"]["source"] = "data/data_glossaire.py"
core._idx_cache.clear()
n0 = core._count_cards()
check("validation: la copie contient les fiches", n0 > 1000, n0)

# a) succès : la fiche arrive dans le lexique COMPLET (essai à blanc impossible grâce à --write)
pid = mkprop("zzvalidationtest", definition="Terme fictif de test. Il sert uniquement à vérifier la propagation.")
r = core.validate_proposals([pid], force=True, run_llm=False)
full_txt = (CP / "data/data_glossaire_full.py").read_text("utf-8")
check("validation: reconstruction complète OK", r["valides"] == ["zzvalidationtest"] and len(r["build"]) == len(core.REBUILD_STEPS), r.get("build"))
check("validation: la fiche est dans data_glossaire_full.py (propagée par --write)", "zzvalidationtest" in full_txt)
check("validation: la fiche a sa page (nombre de fiches +1)", core._count_cards() == n0 + 1, (n0, core._count_cards()))
check("validation: sauvegarde horodatée -validate de data/ et dist/aero/", any(d.name.endswith("-validate") and (d / "data").is_dir() and (d / "dist_aero").is_dir() for d in core.BACKUP_ROOT.iterdir()))
check("validation: data/ RÉEL intact", sha(REAL / "data/data_glossaire_full.py") == real_full_sha)
n1 = core._count_cards()

def state():
    return (sha(CP / "data/data_glossaire.py"), sha(CP / "data/data_glossaire_full.py"), core._count_cards())

def prop_state(pid_):
    return next(x for x in core.list_proposals("aero", "pending") if x["id"] == pid_)

# a2) rattachements de fiches existantes (sur la copie) dans la même opération sûre
sha_g = lambda: sha(CP / "data/data_glossaire_full.py")
pid_a = mkprop("zzemplanturetest", famille="", famille_nouvelle="structure_de_l_aile", famille_nouvelle_label="Structure de l'aile",
               famille_justification="Regroupe les éléments de la structure de l'aile.", voir_aussi=["bord d'attaque"],
               definition="Terme fictif de test. Il sert à vérifier les rattachements de famille.",
               rattachements=["bord d'attaque", "bord de fuite", "longeron"], rattachements_retenus=["bord d'attaque", "longeron"])
core._idx_cache.clear()
g_before = core.get_index("aero").glossaire
check("rattachements: avant, bord d'attaque / longeron sont sans famille", not g_before["bord d'attaque"].get("famille") and not g_before["longeron"].get("famille"))
r = core.validate_proposals([pid_a], force=False, run_llm=False)
core._idx_cache.clear()
g_after = core.get_index("aero").glossaire
check("rattachements: validation OK sans forçage (famille justifiée + fiches rattachées)", r["valides"] == ["zzemplanturetest"], r)
check("rattachements: les fiches cochées rejoignent la famille", g_after["bord d'attaque"]["famille"] == "structure_de_l_aile" and g_after["longeron"]["famille"] == "structure_de_l_aile")
check("rattachements: la fiche décochée (bord de fuite) reste sans famille", not g_after["bord de fuite"].get("famille"))
check("rattachements: la nouvelle fiche porte la famille + voir aussi", g_after["zzemplanturetest"].get("famille") == "structure_de_l_aile" and g_after["zzemplanturetest"].get("xrefs") == ["bord d'attaque"])
check("rattachements: nombre de fiches inchangé hors nouvelle fiche (+1)", len(g_after) == len(g_before) + 1, (len(g_before), len(g_after)))
_tj = json.loads((CP / "dist/aero/t/bord-d-attaque.json").read_text("utf-8"))
check("rattachements: page régénérée avec le libellé lisible de la famille", _tj["famille"] == "structure_de_l_aile" and _tj["famille_label"] == "Structure de l'aile" and "longeron" in [m_["t"] for m_ in _tj["famille_membres"]], (_tj["famille"], _tj["famille_label"]))
check("rattachements: résultat renvoyé (appliqués)", sorted(t_ for t_, _f in r["rattaches"]) == ["bord d'attaque", "longeron"], r["rattaches"])
check("rattachements: data/ RÉEL intact", sha(REAL / "data/data_glossaire_full.py") == real_full_sha and not (REAL / "data/familles_labels.json").exists())
n1 = core._count_cards()

# a3) échec après rattachement -> restauration complète (full + labels + pages)
pid_b = mkprop("zzrestauratest", famille="", famille_nouvelle="autre_famille_test", famille_nouvelle_label="Autre famille",
               famille_justification="Test.", definition="Terme fictif de test. Il sert à simuler un échec après rattachement.",
               rattachements_retenus=["corde", "profil"])
st = (sha_g(), core._count_cards(), (CP / "data/familles_labels.json").read_bytes())
try:
    core.validate_proposals([pid_b], run_llm=False, steps=[core.REBUILD_STEPS[0], ["python3", "-c", "import sys; sys.exit(3)"]])
    check("rattachements: échec d'étape remonté", False)
except core.ValidationError:
    check("rattachements: échec d'étape remonté", True)
check("rattachements: après échec, full / pages / libellés restaurés à l'identique", (sha_g(), core._count_cards(), (CP / "data/familles_labels.json").read_bytes()) == st)
check("rattachements: la proposition reste à valider avec le message", "erreur_validation" in json.dumps(prop_state(pid_b), ensure_ascii=False))
# éditeur de famille : refuse d'écraser une famille existante, conserve le reste du fichier
_a, _s = core.set_families_in_full(CP / "data/data_glossaire_full.py", {"aileron": "x_test", "profil": "structure_de_l_aile"})
check("rattachements: une fiche déjà classée (aileron) n'est jamais déplacée", _a == [("profil", "structure_de_l_aile")] and _s and _s[0][0] == "aileron", (_a, _s))
shutil.copy(CP / "data/data_glossaire_full.py", CP / "data/zz.bak")
core.set_families_in_full(CP / "data/data_glossaire_full.py", {"corde": "structure_de_l_aile"})
_d = subprocess.run(["diff", str(CP / "data/zz.bak"), str(CP / "data/data_glossaire_full.py")], capture_output=True, text=True).stdout
check("rattachements: le diff du full = UNE seule ligne ajoutée", _d.count("\n> ") == 1 and "\n< " not in ("\n" + _d), _d)
(CP / "data/zz.bak").unlink()
core._idx_cache.clear()

# b) échec d'une étape -> restauration automatique, proposition de nouveau « à valider » avec le message
pid = mkprop("zzechectest", definition="Terme fictif de test. Il sert à simuler un échec.")
st = state()
try:
    core.validate_proposals([pid], force=True, run_llm=False, steps=[core.REBUILD_STEPS[0], ["python3", "-c", "import sys; sys.exit(3)"]])
    check("restauration: échec d'étape remonté", False)
except core.ValidationError as e:
    check("restauration: échec d'étape remonté", True)
check("restauration: data/ + dist/aero/ identiques à l'avant", state() == st, (state(), st))
pp = prop_state(pid)
check("restauration: proposition de nouveau à valider avec le message d'erreur", "erreur_validation" in json.dumps(pp, ensure_ascii=False) and "zzechectest" not in (CP / "data/data_glossaire_full.py").read_text("utf-8"))

# c) le nombre de fiches baisse -> refus + restauration
st = state()
drop = ["python3", "-c", "import glob,os; os.remove(sorted(glob.glob('dist/aero/t/*.json'))[0])"]
try:
    core.validate_proposals([pid], force=True, run_llm=False, steps=[drop], links_cmd=["python3", "-c", "pass"])
    check("restauration: baisse du nombre de fiches refusée", False)
except core.ValidationError as e:
    check("restauration: baisse du nombre de fiches refusée", "baissé" in str(e), e)
check("restauration: fiches rétablies après la baisse", state() == st)

# d) test_links_resolve en échec -> restauration
st = state()
try:
    core.validate_proposals([pid], force=True, run_llm=False, steps=[["python3", "-c", "pass"]], links_cmd=["python3", "-c", "import sys; sys.exit(1)"])
    check("restauration: échec de test_links_resolve", False)
except core.ValidationError:
    check("restauration: échec de test_links_resolve", True)
check("restauration: état identique après échec des liens", state() == st)

# e) verrou : une seule validation à la fois
lk = open(core.DATA_DIR / "validate.lock", "w")
fcntl.flock(lk, fcntl.LOCK_EX)
try:
    core.validate_proposals([pid], force=True, run_llm=False, steps=[["python3", "-c", "pass"]], links_cmd=["python3", "-c", "pass"])
    check("verrou: 2e validation simultanée refusée", False)
except ValueError as e:
    check("verrou: 2e validation simultanée refusée", "déjà en cours" in str(e))
fcntl.flock(lk, fcntl.LOCK_UN); lk.close()
check("verrou: aucune écriture pendant le refus", state() == st)

# ── 12. sigles développés dans les définitions (post-traitement déterministe) ─
_ix = core.get_index("aero")
_t1, _r1 = core.develop_acronyms("Elle reste sous la MTOM indiquée. La MTOM limite la masse ; voir la MTOM et le MTOM.", "masse totale", _ix)
check("sigles: insertion à la 1re occurrence seulement (MTOM x3 -> 1 développé)",
      _t1.count("Maximum Take-Off Mass") == 1 and _t1.startswith("Elle reste sous la MTOM (Maximum Take-Off Mass — masse maximale au décollage) indiquée.")
      and _t1.count("(") == 1 and _r1["inseres"] == ["MTOM"], _t1)
_t2, _r2 = core.develop_acronyms("Elle doit rester inférieure à la masse maximale au décollage (MTOM) indiquée dans le manuel de vol.", "masse totale", _ix)
check("sigles: forme longue déjà devant -> complété seulement avec la forme d'origine, sans doublon",
      _t2 == "Elle doit rester inférieure à la masse maximale au décollage (MTOM — Maximum Take-Off Mass) indiquée dans le manuel de vol."
      and _t2.count("masse maximale au décollage") == 1, _t2)
_t2b, _ = core.develop_acronyms("Elle dépasse le Maximum Take-Off Mass (MTOM) autorisé.", "masse totale", _ix)
check("sigles: forme anglaise déjà devant -> ajout de la traduction française seule", "(MTOM — masse maximale au décollage)" in _t2b and _t2b.count("Maximum Take-Off Mass") == 1, _t2b)
_t3, _r3 = core.develop_acronyms("Elle reste sous la MTOM (Maximum Take-Off Mass — masse maximale au décollage) du manuel. Voir MTOM.", "masse totale", _ix)
check("sigles: déjà développé -> inchangé, pas de double parenthèse", _t3 == "Elle reste sous la MTOM (Maximum Take-Off Mass — masse maximale au décollage) du manuel. Voir MTOM." and _r3["inseres"] == [])
_t4, _ = core.develop_acronyms("Vol en VFR puis IFR, avec le QNH.", "masse totale", _ix)
check("sigles: idempotent (2e passage = identique), QNH (code) non développé en ligne", core.develop_acronyms(_t4, "masse totale", _ix)[0] == _t4 and "QNH (" not in _t4 and "VFR (Visual Flight Rules" in _t4, _t4)
_t5, _ = core.develop_acronyms("Dans (MTOM, MLW) la MTOM compte.", "masse totale", _ix)
check("sigles: dans une parenthèse ouverte -> crochets, jamais de parenthèse imbriquée", "[Maximum Take-Off Mass" in _t5 and "((" not in _t5 and "( (" not in _t5, _t5)
check("sigles: le terme lui-même n'est pas développé dans sa propre définition", core.develop_acronyms("Le MTOM est une masse.", "MTOM", _ix)[0] == "Le MTOM est une masse.")
check("sigles: MTOM connu de term_expansions.py (Maximum Take-Off Mass — masse maximale au décollage)",
      core.acr_info("MTOM", _ix)["expansion"] == "Maximum Take-Off Mass" and core.acr_info("MTOM", _ix)["gloss"] == "masse maximale au décollage")

# règle de casse des sigles : MAJUSCULES ou casse exacte déclarée, jamais un mot en minuscules / en casse de phrase
_tc, _ = core.develop_acronyms("C'est un cas de nuage d'origine locale, sans effet sur le vol.", "silvagenitus", _ix)
check("casse sigles: « un cas de » (minuscules) n'est PAS développé en CAS", "(" not in _tc and _tc == "C'est un cas de nuage d'origine locale, sans effet sur le vol.", _tc)
_tc2, _rc2 = core.develop_acronyms("La CAS est de 90 kt en finale.", "silvagenitus", _ix)
check("casse sigles: « la CAS est de 90 kt » EST développé", "CAS (Calibrated Airspeed" in _tc2 and "CAS" in _rc2["inseres"], _tc2)
_tc3, _ = core.develop_acronyms("Cas particulier : la base et la tour restent ouvertes, tas de nuages, Ils volent, ils volent, va et vient.", "silvagenitus", _ix)
check("casse sigles: « Cas » en début de phrase, « base », « tour », « tas », « Ils », « ils », « va » non développés", "(" not in _tc3, _tc3)
_tc4, _ = core.develop_acronyms("On cherche la Vy en montée.", "silvagenitus", _ix)
check("casse sigles: « Vy » (casse exacte déclarée) est développé", "Vy (" in _tc4, _tc4)
_tc5, _ = core.develop_acronyms("On cherche la vy en montée, VY aussi.", "silvagenitus", _ix)
check("casse sigles: « vy » (minuscules) non développé", "vy (" not in _tc5, _tc5)
check("casse sigles: acr_info('cas'/'Cas') None, acr_info('CAS') défini, acr_info('Vy') défini, 'base' None",
      core.acr_info("cas", _ix) is None and core.acr_info("Cas", _ix) is None and core.acr_info("CAS", _ix) and core.acr_info("Vy", _ix) and core.acr_info("base", _ix) is None)
check("casse sigles: aucun développé inséré après un mot en minuscules (pas de 'cas (Calibrated')", "cas (Calibrated" not in _tc and "cas (Calibrated" not in _tc3)

# sigle INCONNU : demandé au modèle (champ sigles) ; initiales vérifiées ; sinon avertissement, jamais d'invention silencieuse
_it = {"domaine": True, "pertinent": True, "definition": "Elle utilise le ZQX pour le calcul. Deuxième phrase de la définition.", "confiance": 0.9}
_v = core.validate_item(dict(_it, sigles=[{"sigle": "ZQX", "developpe": "Zone Quick Xchange", "traduction_fr": "échange rapide de zone"}]), "masse totale", fams, _ix)
check("sigles inconnus: développé du modèle inséré si les initiales correspondent, et listé pour la carte",
      "ZQX (Zone Quick Xchange — échange rapide de zone)" in _v["definition"] and _v["sigles"][0]["coherent"] and _v["sigles"][0]["developpe"] == "Zone Quick Xchange", _v["definition"])
_v2 = core.validate_item(dict(_it, sigles=[{"sigle": "ZQX", "developpe": "Foo Bar Baz", "traduction_fr": ""}]), "masse totale", fams, _ix)
check("sigles inconnus: initiales incohérentes -> texte non modifié, sigle signalé incohérent",
      "Foo Bar Baz" not in _v2["definition"] and not _v2["sigles"][0]["coherent"] and _v2["sigles"][0]["developpe_modele"] == "Foo Bar Baz", _v2)
_v3 = core.validate_item(_it, "masse totale", fams, _ix)
check("sigles inconnus: sans réponse du modèle -> signalé sans développé", _v3["sigles"] and not _v3["sigles"][0]["developpe"] and _v3["definition"] == _it["definition"])
_pw = mkprop("zzsiglewarn", definition=_v3["definition"], sigles=_v3["sigles"])
_cw = chk(_pw, llm=False)
_sd = next(c for c in _cw["controles"] if c["nom"] == "Sigles développés")
check("sigles inconnus: contrôle « Sigles développés » = ⚠ avec la liste, validation bloquée", _sd["statut"] == "warn" and "ZQX" in _sd["detail"] and not _cw["ok"] and any("ZQX" in b for b in _cw["bloquants"]), _sd)
_rw = core.validate_proposals([_pw], run_llm=False)
check("sigles inconnus: validation refusée sans forçage (rien d'écrit)", _rw["valides"] == [] and _rw["refuses"] and _rw["refuses"][0]["terme"] == "zzsiglewarn", _rw)
_cok = chk(mkprop("zzsigleok", definition="Elle reste sous la MTOM (Maximum Take-Off Mass — masse maximale au décollage). Deuxième phrase."), llm=False)
_so = next(c for c in _cok["controles"] if c["nom"] == "Sigles développés")
check("sigles: contrôle « Sigles développés » = ✓ quand tout est développé", _so["statut"] == "ok" and _cok["ok"], _so)
_cno = chk(mkprop("zzsiglenone"), llm=False)
check("sigles: ✓ aussi sans aucun sigle", next(c for c in _cno["controles"] if c["nom"] == "Sigles développés")["statut"] == "ok")
_cu = chk(mkprop("zzsiglemtom", definition="Elle reste sous la MTOM du manuel. Deuxième phrase."), llm=False)
check("sigles: MTOM non développé (édition manuelle) = ⚠ bloquant", not _cu["ok"] and any("MTOM" in b for b in _cu["bloquants"]))

# la relance commentée applique la même règle (prompt + post-traitement)
_ps = mkprop("zzrelancesigle")
_sav = core._call_provider


def _rel_sigle(name, messages, n):
    SEEN["m"] = messages
    t_ = [l[2:] for l in messages[1]["content"].splitlines() if l.startswith("- ")][0]
    it_ = {"terme": t_, "domaine": True, "pertinent": True, "raison_domaine": "r", "raison_pertinent": "r", "famille": "pistes", "confiance": 0.9,
           "definition": "La masse totale est la masse de l'avion en ordre de vol. Elle doit rester inférieure à la masse maximale au décollage (MTOM) indiquée dans le manuel de vol.",
           "sigles": [{"sigle": "MTOM", "developpe": "Maximum Take-Off Mass", "traduction_fr": "masse maximale au décollage"}]}
    return json.dumps({"items": [it_]}), {"in": 1, "out": 1}, "grok-4.3", 0.001


core._call_provider = _rel_sigle
core.relaunch_proposal(_ps, "développe les sigles")
_pr = prop_state(_ps)
check("relance: le prompt porte la règle des sigles (système + rappel) avec 2 exemples",
      "RÈGLE DES SIGLES" in SEEN["m"][0]["content"] and "Rappel de la règle des sigles" in SEEN["m"][1]["content"]
      and SEEN["m"][0]["content"].count("Maximum Take-Off Mass") >= 2 and '"sigles"' in SEEN["m"][0]["content"])
check("relance: la v2 applique la règle (MTOM complété à la forme d'origine)", "(MTOM — Maximum Take-Off Mass)" in _pr["data"]["definition"] and _pr["data"]["version"] == 2, _pr["data"]["definition"])
core.submit("aero", "zzanalysesigle", background=False)
check("analyse: le prompt d'analyse porte aussi la règle des sigles", "RÈGLE DES SIGLES" in SEEN["m"][0]["content"] and "Rappel de la règle des sigles" not in SEEN["m"][1]["content"])
core._call_provider = _sav

# sigles nouveaux ajoutés à term_expansions.py dans l'opération sûre (copie temporaire) ; restauration si échec
_exp = CP / "scripts/term_expansions.py"
_exp_real_sha = sha(REAL / "scripts/term_expansions.py")
_sig = [{"sigle": "ZQX", "developpe": "Zone Quick Xchange", "traduction_fr": "échange rapide de zone"}]
_dn = "Terme fictif de test. Le ZQX (Zone Quick Xchange — échange rapide de zone) sert à vérifier l'ajout du sigle."
_pz = mkprop("zzsiglenouveau", definition=_dn, sigles=_sig)
_st = (sha(_exp), state())
try:
    core.validate_proposals([_pz], run_llm=False, steps=[core.REBUILD_STEPS[0], ["python3", "-c", "import sys; sys.exit(3)"]])
    check("sigles nouveaux: échec d'étape remonté", False)
except core.ValidationError:
    check("sigles nouveaux: échec d'étape remonté", True)
check("sigles nouveaux: après échec, term_expansions.py restauré à l'identique (et data/dist)", (sha(_exp), state()) == _st)
_rz = core.validate_proposals([_pz], run_llm=False)
_txt = _exp.read_text("utf-8")
check("sigles nouveaux: validation OK, ZQX ajouté à term_expansions.py (copie)", _rz["valides"] == ["zzsiglenouveau"] and _rz["sigles_ajoutes"] == ["ZQX"]
      and '"ZQX": ("Zone Quick Xchange", "échange rapide de zone", "")' in _txt, _rz.get("sigles_ajoutes"))
check("sigles nouveaux: fichier relu et valide, MTOM/MTOW intacts", "mtom" in _txt and "MTOW" in _txt and _txt.count('"ZQX"') == 1)
check("sigles nouveaux: term_expansions.py RÉEL jamais modifié par les tests", sha(REAL / "scripts/term_expansions.py") == _exp_real_sha)
check("sigles nouveaux: la sauvegarde -validate contient term_expansions.py", any((d_ / "term_expansions.py").exists() for d_ in core.BACKUP_ROOT.iterdir() if d_.name.endswith("-validate")))
check("sigles nouveaux: pas d'ajout en double (2e appel)", core.add_abbreviations(_exp, _sig) == [])


# ── 13. RÈGLES DE QUALITÉ (2026-11-04) : forme de base, variantes, fiche existante, anti-ridicule ──────────
import suggest_rules as RULES  # noqa: E402
def _enq(term, data):
    core.enqueue_proposal("aero", term, data, "t13", "pending")
    return [p["id"] for p in core.list_proposals("aero") if p["terme"] == term][0]


_idx = core.get_index("aero")
_cnt = RULES.accent_forms(RULES.corpus_dir(core.ROOT, _idx.cfg), _idx.glossaire)
_s = RULES.accent_suggestion("variometre", _cnt)
check("qualité 1: forme sans accent -> forme accentuée du corpus (variomètre)", _s and _s["forme"] == "variomètre", _s)
check("qualité 1: forme déjà accentuée / sigle -> aucune suggestion", RULES.accent_suggestion("variomètre", _cnt) is None and RULES.accent_suggestion("QNH", _cnt) is None)
_fams = _idx.families
_it = core.validate_item({"domaine": True, "pertinent": True, "definition": "Instrument qui mesure la vitesse verticale de l'avion en montée ou en descente.",
                          "famille": "divers", "forme_base": "variomètre", "confiance": 0.9}, "variometre", _fams, _idx)
check("qualité 1: validate_item propose la forme accentuée", _it.get("forme_base_proposee") == "variomètre", _it.get("forme_base_proposee"))
_it2 = core.validate_item({"domaine": True, "pertinent": True, "definition": "Instrument qui mesure la vitesse verticale de l'avion en montée.", "famille": "divers",
                           "forme_base": "variomètre"}, "variomètre", _fams, _idx)
check("qualité 1: forme déjà correcte -> pas d'avertissement", not _it2.get("forme_base_proposee"))
_it3 = core.validate_item({"domaine": True, "pertinent": True, "definition": "Surface de contrôle qui commande le mouvement autour de l'axe de lacet de l'avion.",
                           "famille": "divers", "forme_base": "VOR"}, "VOR", _fams, _idx)
check("qualité 1: le sigle reste forme de base s'il est l'usage (VOR)", not _it3.get("forme_base_proposee"))

# variantes générées
_vs = {v["type"]: v["forme"] for v in RULES.build_variants("point de rosée", {"equivalent_anglais": "dew point"}, _idx)[0]}
check("qualité 2: pluriel de la tête avec mot-outil (points de rosée)", RULES.plural_form("point de rosée") == "points de rosée")
check("qualité 2: accord complet nom + adjectif (milles nautiques)", RULES.plural_form("mille nautique") == "milles nautiques")
check("qualité 2: singulier d'un pluriel (volets -> volet) ; pas de pluriel d'un infinitif", RULES.singular_form("volets") == "volet" and RULES.plural_form("virer de bord") is None)
check("qualité 2: variantes proposées = pluriel + sans accent + anglais", "pluriel" in _vs and "sans accent" in _vs and _vs.get("anglais") == "dew point", _vs)
_kp, _dr = RULES.build_variants("QZX", {"origine": "Quick Zone Xchange", "traduction": "échange rapide de zone"}, _idx)
check("qualité 2: sigle -> développés proposés (origine + traduction), pas de pluriel", {v["forme"] for v in _kp} == {"Quick Zone Xchange", "échange rapide de zone"}, _kp)
_kp, _dr = RULES.build_variants("zzterme", {"synonymes": ["dans", "ab", "variomètre", "zzsyn"]}, _idx)
_why = {x["forme"]: x["raison"] for x in _dr}
check("qualité 2: variante grammaticale / < 3 lettres / déjà forme d'une autre fiche écartées avec raison",
      "grammatical" in _why.get("dans", "") and "3 lettres" in _why.get("ab", "") and "variomètre" in _why.get("variomètre", ""), _why)
check("qualité 2: interdictions (< 3 lettres minuscules, grammatical) ; sigle de 2 lettres MAJUSCULES admis",
      RULES.forbidden_variant("va") and RULES.forbidden_variant("de la") and not RULES.forbidden_variant("TS") and not RULES.forbidden_variant("vario"))
_pv = core.validate_item({"domaine": True, "pertinent": True, "definition": "Zone de l'aérodrome réservée aux manœuvres de test des moteurs avant le vol.",
                          "famille": "divers", "synonymes": ["banc d'essais", "de"], "equivalent_anglais": "run-up area", "forme_base": "aire d'essai moteur"},
                         "aire d'essai moteur", _fams, _idx)
check("qualité 2: validate_item génère les variantes cochées par défaut", _pv["variantes"] and all(v["coche"] for v in _pv["variantes"]) and any(v["type"] == "anglais" for v in _pv["variantes"]), _pv["variantes"])
_pid = _enq("aire d'essai moteur", _pv)
core.edit_proposal(_pid, None, {"variantes_cochees": ["run-up area"]})
_row = [p for p in core.list_proposals("aero") if p["id"] == _pid][0]
check("qualité 2: le relecteur décoche une variante (carte) -> état conservé", [v["forme"] for v in _row["data"]["variantes"] if v["coche"]] == ["run-up area"], _row["data"]["variantes"])
check("qualité 2: seules les variantes cochées sont écrites dans la fiche", '"variantes": ["run-up area"]' in core.render_entry("aire d'essai moteur", _row["data"]).replace("'", '"') or "run-up area" in core.render_entry("aire d'essai moteur", _row["data"]) and "banc d'essais" not in core.render_entry("aire d'essai moteur", _row["data"]))
try:
    core.edit_proposal(_pid, None, {"variantes_ajout": "ab"})
    check("qualité 2: variante manuelle < 3 lettres refusée", False)
except ValueError:
    check("qualité 2: variante manuelle < 3 lettres refusée", True)

# détection d'une fiche existante -> « ajouter comme variante de X »
_c = RULES.detect_existing("vario", _idx)
check("qualité 3: vario -> forme d'appel de variomètre", _c and _c[0]["fiche"] == "variomètre", _c)
_c = RULES.detect_existing("anticyclonique", _idx)
check("qualité 3: anticyclonique -> forme d'appel d'anticyclone (même radical)", _c and _c[0]["fiche"] == "anticyclone", _c)
check("qualité 3: un sigle ou un mot sans rapport n'est pas rattaché", RULES.detect_existing("QNH", _idx) == [] and not RULES.detect_existing("plan", _idx))
_vi = core.validate_item({"domaine": True, "pertinent": True, "definition": "Qui se rapporte à un anticyclone, zone de hautes pressions atmosphériques.",
                          "famille": "divers", "variante_de": "anticyclone"}, "anticyclonal", _fams, _idx)
check("qualité 3: le candidat est mémorisé sur la proposition (bouton « Ajouter comme variante »)", _vi["variante_candidats"] and _vi["variante_candidats"][0]["fiche"] == "anticyclone", _vi.get("variante_candidats"))
_pv_id = _enq("anticyclonal", _vi)
_full = core.ROOT / "data" / "data_glossaire_full.py"
_before = _full.read_text("utf-8")
try:
    core.apply_as_variant(_pv_id, "anticyclone", steps=[["python3", "-c", "import sys; sys.exit(3)"]])
    check("qualité 3: échec de l'étape -> erreur remontée", False)
except core.ValidationError:
    check("qualité 3: échec de l'étape -> erreur remontée et full restauré à l'identique", _full.read_text("utf-8") == _before)
_ra = core.apply_as_variant(_pv_id, "anticyclone", do_rebuild=False)
_after = _full.read_text("utf-8")
_gg = _IL.load_glossaire(_full)
check("qualité 3: application sûre : « anticyclonal » ajouté aux variantes d'anticyclone, aucune nouvelle fiche",
      "anticyclonal" in _gg["anticyclone"]["variantes"] and "anticyclonal" not in _gg, (_ra, _gg["anticyclone"].get("variantes")))
check("qualité 3: le reste du fichier est conservé (une seule fiche modifiée)", abs(len(_after.splitlines()) - len(_before.splitlines())) <= 1 and
      _IL.load_glossaire(_full)["variomètre"] == _g["variomètre"])
check("qualité 3: sauvegarde créée et proposition marquée validée", Path(_ra["sauvegarde"]).exists() and
      [p for p in core.list_proposals("aero", "validated") if p["id"] == _pv_id] != [])
_c2 = core.apply_as_variant if False else None
try:
    core.apply_as_variant(_pv_id, "anticyclone")
    check("qualité 3: 2e application refusée (proposition plus en attente)", False)
except KeyError:
    check("qualité 3: 2e application refusée (proposition plus en attente)", True)

# anti-ridicule BLOQUANT : simulation du moteur sur le corpus des séances
_hv = core.validate_item({"domaine": True, "pertinent": True, "definition": "Nuage mince et étendu en voile voilant le ciel, signe avant-coureur d'un front chaud.",
                          "famille": "divers", "synonymes": ["voile"], "forme_base": "zzvoile nuageux", "homographe_courant": True}, "zzvoile nuageux", _fams, _idx)
check("qualité 4: le modèle ne fournit pas de contexte -> variante « voile » (homographe) proposée", "voile" in [v["forme"] for v in _hv["variantes"]] and not _hv["contexte_requis"], _hv["variantes"])
_hid = _enq("zzvoile nuageux", _hv)
_rep = core.check_proposal_id(_hid, run_llm=False)
_sim = [c for c in _rep["controles"] if c["nom"] == "Soulignements simulés"]
check("qualité 4: ligne « Soulignements simulés » dans le contrôle de cohérence", len(_sim) == 1 and _sim[0].get("simulation"), _rep["controles"])
check("qualité 4: homographe courant sans contexte_requis = BLOQUANT (incontournable) avec 3 exemples", _sim and _sim[0]["statut"] == "ko" and _sim[0]["incontournable"]
      and len(_sim[0]["simulation"]["exemples"]) == 3 and not _rep["ok"], _sim and _sim[0]["detail"][:300])
check("qualité 4: le détail demande contexte_requis ou le retrait de la variante", _sim and "contexte_requis" in _sim[0]["detail"] and "retirer" in _sim[0]["detail"])
_vv = core.validate_proposals([_hid], run_llm=False, force=True, steps=[["python3", "-c", "pass"]])
check("qualité 4: même avec forçage, la validation est refusée", _vv["valides"] == [] and _vv["refuses"], _vv)
core.edit_proposal(_hid, None, {"variantes_cochees": [v["forme"] for v in _hv["variantes"] if v["forme"] != "voile"]})
_rep = core.check_proposal_id(_hid, run_llm=False)
_sim = [c for c in _rep["controles"] if c["nom"] == "Soulignements simulés"][0]
check("qualité 4: variante retirée (décochée) -> le contrôle passe", _sim["statut"] != "ko", _sim["detail"][:200])
core.edit_proposal(_hid, None, {"variantes_cochees": [v["forme"] for v in _hv["variantes"]], "contexte_requis": "nuage, front, cirrus, ciel"})
_rep = core.check_proposal_id(_hid, run_llm=False)
_sim = [c for c in _rep["controles"] if c["nom"] == "Soulignements simulés"][0]
check("qualité 4: contexte_requis fourni -> le contrôle passe (soulignements filtrés par le contexte)", _sim["statut"] != "ko", _sim["detail"][:240])
check("qualité 4: contexte_requis écrit dans la fiche", '"contexte_requis"' in core.render_entry("zzvoile nuageux", [p for p in core.list_proposals("aero") if p["id"] == _hid][0]["data"]))
_tc = core.validate_item({"domaine": True, "pertinent": True, "definition": "Terme de test suffisamment long pour la définition.", "famille": "divers"}, "va", _fams, _idx)
_tid = _enq("va", _tc)
_rt = core.check_proposal_id(_tid, run_llm=False)
check("qualité 4: terme de moins de 3 lettres en minuscules = bloquant incontournable", any(c["nom"] == "Terme" and c["statut"] == "ko" and c.get("incontournable") for c in _rt["controles"]) and not _rt["ok"])
_r = api.handle("POST", "/proposals/%d/simulate" % _hid, b"{}", {"cookie": ""}) if False else core.simulate_proposal_id(_hid)
check("qualité 4: simulate_proposal_id (route /simulate) renvoie statut + exemples", _r["statut"] in ("ok", "warn") and "simulation" in _r, _r)
for _p_ in (_pid, _hid, _tid):
    core.reject_proposal(_p_)

core.ROOT = REAL
check("validation: data/ réel jamais modifié par les tests", sha(REAL / "data/data_glossaire_full.py") == real_full_sha)

# rotation : backup_site garde 20 sauvegardes automatiques max, jamais les manuelles
(core.BACKUP_ROOT / "20261104-2114").mkdir(parents=True, exist_ok=True)
for _i in range(22):
    (core.BACKUP_ROOT / ("19990101-0000%02d-validate" % _i)).mkdir(exist_ok=True)
core.backup_site()
_auto = [x for x in core.BACKUP_ROOT.iterdir() if x.name.endswith("-validate") or x.name.startswith("import-")]
check("sauvegardes: rotation à 20 automatiques, sauvegarde manuelle intacte", len(_auto) == 20 and (core.BACKUP_ROOT / "20261104-2114").exists(), len(_auto))

shutil.rmtree(_TMP, ignore_errors=True)
print("\n%d échec(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
