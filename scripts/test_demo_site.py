#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_demo_site.py — PREUVE D'INDÉPENDANCE : AeroLex installé ailleurs, sur un site sans rapport avec l'aéronautique, SANS corpus.

Construit dans un dossier temporaire (ou $AEROLEX_DEMO_DIR, conservé) :
  1. une installation vierge (chaîne de build + moteur ; ni data/lexicon.json du lexique d'origine, ni aerolex.config.json de notre site) ;
  2. le lexique de démonstration « demo-voile » (scripts/new_lexicon.py, SANS corpus), 12 fiches publiées + 3 laissées « À valider » ;
  3. un mini-site de club de voile : UNE balise script (data-lexicon + data-src + data-skip-selectors), aucune dépendance à notre site.
Puis, dans Chrome headless : soulignements corrects (casse, sigles, contexte_requis, zones ignorées par défaut et par option) ; la page « Suggérer » du
lexique (espace relecteur) affiche « simulation générique (aucun corpus configuré) » sans erreur. Sauté (code 0) si Chrome ou node est absent.

    python3 scripts/test_demo_site.py
"""
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REAL = HERE.parent
KEEP = os.environ.get("AEROLEX_DEMO_DIR")
TMP = Path(KEEP) if KEEP else Path(tempfile.mkdtemp(prefix="aerolex-demo-"))
TMP.mkdir(parents=True, exist_ok=True)
INSTALL = TMP / "install"
SITE = TMP / "site"
FAILS = []
PASSWORD = "demo-relecteur-" + str(os.getpid())


def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + ("" if cond else " " + str(extra)[:700]))
    if not cond:
        FAILS.append(name)


def find_chrome():
    for c in (os.environ.get("AEROLEX_CHROME"), "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing", shutil.which("google-chrome"), shutil.which("chromium")):
        if c and os.path.exists(c):
            return c
    return None


chrome, node = find_chrome(), shutil.which("node") or "/opt/homebrew/bin/node"
if not chrome or not os.path.exists(node):
    print("SKIP Chrome ou node introuvable : preuve navigateur non exécutée")
    sys.exit(0)

# ── 1. installation vierge ─────────────────────────────────────────────────
shutil.rmtree(INSTALL, ignore_errors=True)
(INSTALL / "dist" / "_template").mkdir(parents=True)
(INSTALL / "data").mkdir()
subprocess.run(["rsync", "-a", "--exclude", "__pycache__", str(REAL / "scripts"), str(REAL / "src"), str(REAL / "build_index_js.py"), str(REAL / "serve_cors.py"), str(INSTALL) + "/"], check=True)
for f in ("aerolex.js", "aerolex.css", "aerolex-page.css", "aerolex-svg.js", "aerolex-indexpage.css", "aerolex-indexpage.js", "aerolex-searchbox.js"):
    shutil.copy2(REAL / "dist" / f, INSTALL / "dist" / f)
tpl = REAL / "dist" / next(p.parent.name for p in sorted((REAL / "dist").glob("*/suggest.html")))
for f in ("suggest.html", "suggest.js", "suggest.css"):
    shutil.copy2(tpl / f, INSTALL / "dist" / "_template" / f)
check("installation vierge : ni configuration de notre site ni lexique d'origine",
      not (INSTALL / "aerolex.config.json").exists() and not (INSTALL / "data" / "lexicon.json").exists())

for k in list(os.environ):
    if k.startswith("AEROLEX_"):
        del os.environ[k]
pwf = TMP / "pw"
pwf.write_text(PASSWORD)
os.environ.update({"AEROLEX_ROOT": str(INSTALL), "AEROLEX_SUGGEST_DIR": str(TMP / "db"), "AEROLEX_BACKUP_DIR": str(TMP / "bk"),
                   "AEROLEX_SUGGEST_PASSWORD_FILE": str(pwf)})
sys.path.insert(0, str(INSTALL / "scripts"))
import new_lexicon as NL  # noqa: E402

FAM = {"greement": "Gréement et voiles", "manoeuvres": "Manœuvres", "coque": "Coque et appendices", "reglementation": "Règlement et navigation"}
root = NL.create_lexicon("demo-voile", "Voile (démonstration)", INSTALL, familles=FAM, out=lambda *_: None, skip_selectors=".cookie-banner")
# règle de reconnaissance DU LEXIQUE, déclarée dans sa configuration et publiée avec l'index : « ais » (la planche) n'est jamais souligné
lj0 = json.loads((root / "data" / "lexicon.json").read_text("utf-8"))
lj0["rules"] = {"exact_case": ["ais"]}
(root / "data" / "lexicon.json").write_text(json.dumps(lj0, ensure_ascii=False, indent=1) + "\n", "utf-8")
fixture = HERE / "fixtures" / "demo-voile-items.json"
items = json.loads(fixture.read_text("utf-8"))
NL.seed("demo-voile", INSTALL, [i["terme"] for i in items], str(fixture), llm=False, out=lambda *_: None)
import suggest_core as core  # noqa: E402

lj = json.loads((root / "data" / "lexicon.json").read_text("utf-8"))
check("lexique créé SANS corpus (configuration data/lexicon.json)", (lj.get("corpus") or {}).get("type") == "none", lj.get("corpus"))
props = core.list_proposals("demo-voile")
publish = [p["id"] for p in props if p["terme"] not in ("bôme", "virement de bord", "quille")]
r = core.validate_proposals(publish, run_llm=False)
check("12 fiches publiées dans le lexique de démonstration (sans corpus)", len(r["valides"]) == len(publish) == 12, r)
left = [p["terme"] for p in core.list_proposals("demo-voile")]
check("3 propositions restent « À valider » pour la page Suggérer", sorted(left) == ["bôme", "quille", "virement de bord"], left)
idxf = root / "dist" / "aerolex-demo-voile-index.json"
meta = json.loads(idxf.read_text("utf-8")).get("meta", {})
check("index publié : meta.lexicon / terms_base relatif / aucune règle de notre site", meta.get("lexicon") == "demo-voile" and meta.get("terms_base") == "demo-voile/t/" and
      (meta.get("display") or {}).get("skip_selectors") == [".cookie-banner"], meta)

# ── 2. mini-site sans rapport avec l'aéronautique ──────────────────────────
shutil.rmtree(SITE, ignore_errors=True)
SITE.mkdir()
(SITE / "lexique").symlink_to(root / "dist")
(SITE / "index.html").write_text('''<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Club nautique de la baie — journal de bord</title>
<link rel="stylesheet" href="lexique/aerolex.css">
<style>body{font:16px/1.5 sans-serif;max-width:46rem;margin:2rem auto}.cookie-banner{background:#eee;padding:.5rem}</style>
<script src="lexique/aerolex.js" defer data-lexicon="demo-voile" data-src="lexique/aerolex-demo-voile-index.json" data-skip-selectors=".cookie-banner"></script>
</head><body>
<nav><a href="#">Foc et génois</a> <button type="button">Réserver un spinnaker</button></nav>
<div class="cookie-banner" id="cb">Ce site range les cookies comme un foc dans la quille.</div>
<h1>Safran et génois : le journal du week-end</h1>
<main>
<p id="p1">Samedi, nous avons réglé la grand-voile avant de border les écoutes pour remonter au près.</p>
<p id="p2">Le skipper a hissé le génois puis le spinnaker au portant ; un empannage raté a failli casser la bôme.</p>
<p id="p3">Le voile de la mariée claquait dans le vent, et la voile du voisin aussi.</p>
<p id="p4">Sur le bateau, la voile se hisse le long du mât.</p>
<p id="p5">Avec l'AIS et l'EPIRB à bord, nous tenions une VMG correcte.</p>
<p id="p6">L'ais de la planche est en bois ; AIS écrit en capitales est le système radio.</p>
<p id="p7">La dérive des continents ne se mesure pas en nœuds.</p>
<p id="p7b">La dérive du bateau se règle sous la coque.</p>
<p id="p8" data-aerolex-skip>Ici le safran et le génois sont ignorés par data-aerolex-skip.</p>
<p id="p9">Dans le code, <code>foc = génois</code> reste intact, comme <a href="#">le safran dans un lien</a>.</p>
<p id="p10"><button type="button">Le foc</button> est un bouton ; un SAFRAN en capitales reste souligné.</p>
</main></body></html>''', "utf-8")

# ── 3. serveur (même service que l'installation de référence : site statique + API de suggestion) ──
def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


port = free_port()
srv = subprocess.Popen([sys.executable, str(INSTALL / "serve_cors.py"), str(port), "--dir", str(SITE)], env=os.environ.copy(),
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
try:
    for _ in range(60):
        try:
            urllib.request.urlopen("http://127.0.0.1:%d/index.html" % port, timeout=2)
            break
        except Exception:
            time.sleep(0.3)
    p = subprocess.run([node, str(HERE / "demo_chrome.js"), "http://127.0.0.1:%d" % port, PASSWORD, chrome, "demo-voile"], capture_output=True, text=True, timeout=180)
    try:
        out = json.loads([l for l in p.stdout.splitlines() if l.startswith("{")][-1])
    except Exception:
        out = {"fatal": (p.stdout + p.stderr)[-800:]}
finally:
    srv.terminate()

check("Chrome : pilotage sans erreur", "fatal" not in out, out.get("fatal"))
site = out.get("site") or {}
sp = site.get("spans") or []
texts = lambda pid: [s["text"] for s in sp if s["in"] == pid]  # noqa: E731
check("moteur chargé par UNE balise (data-lexicon + data-src) : version et configuration exposées", out.get("site_ready") and site.get("version") == "1.4.0" and
      site.get("config", {}).get("lexicon") == "demo-voile" and ".cookie-banner" in site.get("config", {}).get("skipSelectors", ""), site.get("config"))
check("fiche au clic : base des fiches déduite de l'index (relative), sans domaine codé", (site.get("termUrl") or "").endswith("/lexique/demo-voile/t/safran.json"), site.get("termUrl"))
check("soulignés : grand-voile, écoutes (p1)", {"grand-voile", "écoutes"} <= set(t.lower() for t in texts("p1")), texts("p1"))
check("soulignés : génois, spinnaker, empannage ; bôme (non publiée) jamais (p2)", {"génois", "spinnaker", "empannage"} <= set(t.lower() for t in texts("p2")) and "bôme" not in [t.lower() for t in texts("p2")], texts("p2"))
check("contexte_requis : « voile » homographe SANS contexte = pas souligné (p3)", not any(t.lower() == "voile" for t in texts("p3")), texts("p3"))
check("contexte_requis : « voile » avec contexte (bateau, mât) = souligné (p4)", any(t.lower() == "voile" for t in texts("p4")), texts("p4"))
check("sigles en MAJUSCULES soulignés (AIS, EPIRB, VMG)", {"AIS", "EPIRB", "VMG"} <= set(texts("p5")), texts("p5"))
check("casse exacte (meta.rules.exact_case de l'index) : « ais » (la planche) jamais souligné, « AIS » souligné (p6)", texts("p6") == ["AIS"], texts("p6"))
check("contexte_requis : « dérive des continents » non souligné (p7), « dérive du bateau » souligné (p7b)", not texts("p7") and [t.lower() for t in texts("p7b")] == ["dérive"], (texts("p7"), texts("p7b")))
check("zones ignorées par DÉFAUT : titres, liens, boutons, code", all(not texts(i) for i in ()) and not any(s["zone"] in ("h1", "a", "button", "code") for s in sp), [s for s in sp if s["zone"] in ("h1", "a", "button", "code")])
check("zone ignorée par OPTION (data-skip-selectors=.cookie-banner)", not texts("cb"), texts("cb"))
check("zone ignorée par ATTRIBUT (data-aerolex-skip)", not texts("p8"), texts("p8"))
check("aucun soulignement dans les zones ignorées (comptage DOM)", site.get("skippedCount") == 0, site.get("skippedCount"))
check("casse : « SAFRAN » en capitales souligné hors bouton (p10)", [t for t in texts("p10")] == ["SAFRAN"], texts("p10"))
check("le moteur ne lit que l'index (aucune requête serveur hors feuilles et scripts)", sorted(site.get("serverCalls") or []) == ["/lexique/aerolex-demo-voile-index.json"], site.get("serverCalls"))
rv = out.get("review") or {}
check("page Suggérer : espace relecteur ouvert, file « À valider » affichée", out.get("review_open") and rv.get("n_proposals") == 3, rv)
check("page Suggérer : le corpus du lexique est annoncé comme générique, téléversement proposé", "simulation générique (aucun corpus configuré)" in (rv.get("corpus_msg") or "") and rv.get("corpus_box_visible") and rv.get("upload_visible"), rv)
check("page Suggérer : cartouche « simulation générique (aucun corpus configuré) » sur chaque proposition", out.get("sims_done") and rv.get("n_proposals") == 3 and
      all("simulation générique (aucun corpus configuré)" in s for s in rv.get("sims", [])) and rv.get("pills") == 3, rv.get("sims"))
check("page Suggérer : aucune erreur (cartouche ni console)", not any("indisponible" in s for s in rv.get("sims", [])) and not out.get("errors"), out.get("errors"))

if not KEEP:
    shutil.rmtree(TMP, ignore_errors=True)
else:
    print("démonstration conservée dans", TMP)
print("\n%d échec(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
