#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_new_lexicon.py — scripts/new_lexicon.py + scripts/check_lexicon.py de bout en bout, sur une COPIE du projet dans /tmp.
Lancer : python3 scripts/test_new_lexicon.py   (aucun appel réseau ; ni data/ ni dist/ réels touchés ; base SQLite temporaire)"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL = HERE.parent
TMP = Path(tempfile.mkdtemp(prefix="newlex-test-"))
BASE = TMP / "base"
os.environ["AEROLEX_SUGGEST_DIR"] = str(TMP / "db")
os.environ["AEROLEX_BACKUP_DIR"] = str(TMP / "bk")
os.environ["AEROLEX_ROOT"] = str(BASE)
FAILS = []


def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + (" " + str(extra)[:300] if (extra and not cond) else ""))
    if not cond:
        FAILS.append(name)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


real_full, real_exp = sha(REAL / "data" / "data_glossaire_full.py"), sha(REAL / "scripts" / "term_expansions.py")

# ── copie minimale du projet : chaîne de build + moteur + modèles de pages (pas les 1300 fiches) ──
(BASE / "dist" / "aero").mkdir(parents=True)
(BASE / "data").mkdir()
subprocess.run(["cp", str(REAL / "data" / "lexicon.json"), str(BASE / "data" / "lexicon.json")], check=True)   # configuration du lexique principal (son id est réservé)
subprocess.run(["rsync", "-a", "--exclude", "__pycache__", "--exclude", "fixtures", str(REAL / "scripts"), str(REAL / "src"), str(REAL / "build_index_js.py"), str(BASE) + "/"], check=True)
for f in ("aerolex.js", "aerolex.css", "aerolex-page.css", "aerolex-svg.js", "aerolex-indexpage.css", "aerolex-indexpage.js", "aerolex-searchbox.js"):
    subprocess.run(["cp", str(REAL / "dist" / f), str(BASE / "dist" / f)], check=True)
for f in ("suggest.html", "suggest.js", "suggest.css"):
    subprocess.run(["cp", str(REAL / "dist" / "aero" / f), str(BASE / "dist" / "aero" / f)], check=True)
sys.path.insert(0, str(BASE / "scripts"))
import new_lexicon as NL  # noqa: E402  (celui de la copie)

# ── 1. slug : refus ──
for bad in ("Voile", "aero", "a", "voile_x", "voilé", "-voile", "api", "x" * 41):
    try:
        NL.check_slug(bad)
        check("slug refusé : %r" % bad, False)
    except SystemExit:
        check("slug refusé : %r" % bad, True)
NL.check_slug("demo-voile")

# ── 2. création ──
FAM = {"greement": "Gréement et voiles", "manoeuvres": "Manœuvres", "coque": "Coque et appendices", "reglementation": "Règlement et navigation"}
out = []
# corpus du lexique de démonstration : celui que déclare la configuration du lexique principal (si présent sur cette machine) ;
# sinon aucun (les assertions qui en dépendent sont alors sautées).
_cj = (json.loads((REAL / "data" / "lexicon.json").read_text("utf-8")).get("corpus") or {})
_cdir = (REAL / str(_cj.get("path", "-absent-"))).resolve()
if not _cdir.is_dir() and os.environ.get("AEROLEX_CORPUS_DIR"):
    _cdir = Path(os.environ["AEROLEX_CORPUS_DIR"]).resolve()
HAS_CORPUS = _cdir.is_dir()
root = NL.create_lexicon("demo-voile", "Voile (démonstration)", BASE, familles=FAM, out=out.append,
                         corpus=NL.corpus_spec(str(_cdir)) if HAS_CORPUS else NL.corpus_spec())
dd = root / "dist" / "demo-voile"
check("création: structure data/ (glossaire, full, familles, méta, extra_content)", all((root / "data" / f).exists() for f in (
    "data_glossaire.py", "data_glossaire_full.py", "familles_labels.json", "lexicon.json", "extra_content.py", "lexique-filtre.txt")))
check("création: catalogue de familles de départ écrit", json.loads((root / "data" / "familles_labels.json").read_text("utf-8")) == FAM)
check("création: moteur v1.4.0 + feuilles copiés", all((root / "dist" / f).exists() for f in ("aerolex.js", "aerolex-indexpage.js", "aerolex-searchbox.js")) and
      "AeroLex Runtime v1.4.0" in (root / "dist" / "aerolex.js").read_text("utf-8"))
check("création: page index (autocomplétion) + slugmap + lexicon.json + build-info + suggest", all((dd / f).exists() for f in (
    "index.html", "slugmap.json", "lexicon.json", "build-info.json", "suggest.html", "suggest.js", "suggest.css")))
_ix = (dd / "index.html").read_text("utf-8")
check("création: index = bonne page (id du lexique, autocomplétion, JSON de recherche du lexique)", 'data-lexicon="demo-voile"' in _ix or "ix-head" in _ix and "aerolex-demo-voile-search.json" in _ix, _ix[:300])
check("création: suggest.html pointe le lexique", 'data-lexicon="demo-voile"' in (dd / "suggest.html").read_text("utf-8"))
check("création: servi par le service (dist/<slug> et JSON partagés reliés dans dist/)", (BASE / "dist" / "demo-voile").is_symlink() and
      (BASE / "dist" / "demo-voile" / "index.html").exists() and (BASE / "dist" / "aerolex-demo-voile-index.json").exists() and (BASE / "dist" / "aerolex-demo-voile-search.json").exists())
check("création: scripts/src/build_index_js.py liés à la chaîne du projet", all((root / n).is_symlink() for n in ("scripts", "src", "build_index_js.py")))
reg = json.loads((BASE / "lexicons" / "registry.json").read_text("utf-8"))["lexicons"]["demo-voile"]
check("création: déclaré au registre (racine, catalogue de familles)", reg["root"] == "lexicons/demo-voile" and reg["catalog_seed"] is True and reg["full"] == "data/data_glossaire_full.py", reg)
try:
    NL.create_lexicon("demo-voile", "x", BASE, out=lambda *_: None)
    check("création: lexique existant refusé", False)
except SystemExit:
    check("création: lexique existant refusé", True)
import suggest_core as core  # noqa: E402
idx = core.get_index("demo-voile")
check("suggest: lexique reconnu, famille Divers d'office + catalogue", "divers" in idx.families and set(FAM) <= set(idx.families), idx.families)
check("suggest: lexique créé déclaré (racine propre, corpus de sa configuration)", core.LEXICONS["demo-voile"]["root"] == "lexicons/demo-voile" and
      (core.LEXICONS["demo-voile"].get("corpus", {}).get("type") == ("dir" if HAS_CORPUS else "none")), core.LEXICONS["demo-voile"])

# ── 3. lot de termes source -> file « À valider » (même pipeline que Suggérer) ──
items = json.loads((HERE / "fixtures" / "demo-voile-items.json").read_text("utf-8"))
terms = [i["terme"] for i in items]
rep = NL.seed("demo-voile", BASE, terms, str(HERE / "fixtures" / "demo-voile-items.json"), llm=False, out=lambda *_: None)
pend = {p["terme"]: p for p in core.list_proposals("demo-voile")}
check("lot: 15 termes déposés en file « À valider », rien de publié", len(pend) == 15 and rep["en_file"] == 15 and not core.get_index("demo-voile").glossaire, len(pend))
check("lot: forme de base corrigée (derive -> dérive, écoutes -> écoute)", "dérive" in pend and "écoute" in pend and "derive" not in pend and "écoutes" not in pend, sorted(pend))
check("lot: variante sans accent générée (derive) et pluriel conservé (écoutes)", "derive" in [v["forme"] for v in pend["dérive"]["data"]["variantes"] if v["coche"]] or "dérives" in [v["forme"] for v in pend["dérive"]["data"]["variantes"]]
      and "écoutes" in [v["forme"] for v in pend["écoute"]["data"]["variantes"]])
check("lot: variantes générées (pluriel, anglais) pour foc", [v["type"] for v in pend["foc"]["data"]["variantes"]] == ["pluriel", "anglais"], pend["foc"]["data"]["variantes"])
check("lot: sigles (AIS, VMG, EPIRB) : développés proposés en variantes", {v["forme"] for v in pend["AIS"]["data"]["variantes"]} >= {"Automatic Identification System"})
check("lot: famille obligatoire (tous classés, Divers autorisé)", all(p["data"].get("famille") for p in pend.values()) and pend["VMG"]["data"]["famille"] == "divers")
check("lot: homographe courant « voile » : contexte_requis du modèle conservé", pend["voile"]["data"]["contexte_requis"] and pend["voile"]["data"]["homographe_courant"])
check("lot: variante anglaise « rudder » (homographe des séances) décochée automatiquement", not HAS_CORPUS or "rudder" not in [v["forme"] for v in pend["safran"]["data"]["variantes"] if v["coche"]] and
      any("rudder" in n for n in rep["corriges"].get(pend["safran"]["id"], [])), rep["corriges"])
check("lot: « écoute » (108 passages hors sujet) : contexte_requis proposé d'après la définition", not HAS_CORPUS or pend["écoute"]["data"]["contexte_requis"] and
      any("contexte_requis proposé" in n for n in rep["corriges"].get(pend["écoute"]["id"], [])))
bad = []
for p in pend.values():
    c = core.check_proposal_id(p["id"], run_llm=False)
    if not c["ok"]:
        bad.append((p["terme"], c["bloquants"]))
check("lot: aucune proposition bloquée (anti-ridicule, sigles, variantes, famille)", not bad, bad)

# ── 4. hors ligne : pas de modèle -> à rédiger, bloqué tant que la définition est vide ──
NL.create_lexicon("demo-offline", "Hors ligne", BASE, out=lambda *_: None)
rep2 = NL.seed("demo-offline", BASE, ["bout", "taquet"], "", llm=False, out=lambda *_: None)
po = core.list_proposals("demo-offline")
check("hors ligne: termes en file, définition à rédiger, famille Divers", len(po) == 2 and all(p["data"].get("a_rediger") and p["data"]["famille"] == "divers" for p in po))
c = core.check_proposal_id(po[0]["id"], run_llm=False)
check("hors ligne: validation bloquée tant que la définition est vide", not c["ok"], c["bloquants"])
_sl = [x for x in c["controles"] if x["nom"] == "Soulignements simulés"]
check("sans corpus: simulation GÉNÉRIQUE signalée dans le cartouche, sans erreur", len(_sl) == 1 and _sl[0]["simulation"]["generique"] and
      "simulation générique (aucun corpus configuré)" in _sl[0]["detail"] and _sl[0]["simulation"]["disponible"], _sl)

# ── 5. validation (dans la COPIE) puis verdict check_lexicon ──
r = core.validate_proposals([p["id"] for p in core.list_proposals("demo-voile")], run_llm=False)
check("validation: 15 fiches publiées dans le lexique de démonstration", len(r["valides"]) == 15 and r["fiches"] == [0, 15], r)
p = subprocess.run([sys.executable, "scripts/check_lexicon.py", "demo-voile", "--base", str(BASE)], cwd=str(BASE), capture_output=True, text=True)
check("check_lexicon: passe du premier coup après le pipeline", p.returncode == 0 and "LEXIQUE PROPRE" in p.stdout, "\n".join(l for l in p.stdout.splitlines() if not l.strip().startswith("✓"))[-1500:])
check("check_lexicon: enchaîne tous les contrôles du jour", all(k in p.stdout for k in (
    "acronyms", "family_acronyms", "links_resolve", "slugs", "familles --strict", "matching", "import (diff = 0)", "titres accentués",
    "variante < 3 lettres", "mot grammatical", "aller-retour", "empreinte", "index")), p.stdout)

# ── 6. cas négatifs : le verdict doit échouer ──
full = root / "data" / "data_glossaire_full.py"
orig = full.read_text("utf-8")
_j = orig.index("'variantes': [", orig.index("'bôme': {")) + len("'variantes': [")
full.write_text(orig[:_j] + "'bm', 'de la', " + orig[_j:], "utf-8")
p = subprocess.run([sys.executable, "scripts/check_lexicon.py", "demo-voile", "--base", str(BASE), "--only", "variantes"], cwd=str(BASE), capture_output=True, text=True)
check("check_lexicon: variante de 2 lettres / mot grammatical -> NON CONFORME (code 1)", p.returncode == 1 and "✗ aucune variante < 3 lettres" in p.stdout and "✗ aucun mot grammatical" in p.stdout, p.stdout)
full.write_text(orig, "utf-8")
full.write_text(orig.replace("'dérive': {", "'derive': {"), "utf-8")
p = subprocess.run([sys.executable, "scripts/check_lexicon.py", "demo-voile", "--base", str(BASE), "--only", "titres"], cwd=str(BASE), capture_output=True, text=True)
check("check_lexicon: titre sans accent alors que le corpus l'accentue -> NON CONFORME", p.returncode == 1 and "derive → dérive" in p.stdout, p.stdout)
full.write_text(orig, "utf-8")

check("data/ et term_expansions.py RÉELS jamais modifiés par ces tests", sha(REAL / "data" / "data_glossaire_full.py") == real_full and sha(REAL / "scripts" / "term_expansions.py") == real_exp)
import shutil  # noqa: E402
shutil.rmtree(TMP, ignore_errors=True)
print("\n%d échec(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
