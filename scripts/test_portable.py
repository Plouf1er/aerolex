# -*- coding: utf-8 -*-
"""
test_portable.py — le CODE DISTRIBUABLE ne doit contenir aucun chemin, domaine, port ni classe CSS propres à une installation.

AeroLex est installable ailleurs : tout ce qui est propre au site de Louis (dossier du corpus, domaines, port, fichiers .env, classes CSS de son
site hôte) vit dans la CONFIGURATION de l'installation :
  data/lexicon.json        (par lexique : corpus, zones à ignorer, règles)    aerolex.config.json   (par installation : .env, modèle local, port, CORS)
  deploy/                  (service launchd d'exemple)                         dist/<lexique>/…, data/…  (contenu publié du lexique)
Ce test échoue dès qu'un motif propre à notre installation réapparaît dans le code (scripts/, src/, build_*.py, serve_cors.py, dist/*.js|css, gabarit de la
page Suggérer), ou qu'un nom de lexique « aero » y est codé en dur, ou que le moteur appelle autre chose que l'index statique.

    python3 scripts/test_portable.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FAILS = []


def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + ("" if cond else " " + str(extra)[:600]))
    if not cond:
        FAILS.append(name)


# Motifs propres à une installation (construits par morceaux pour que ce fichier ne se détecte pas lui-même)
J = "".join
FORBIDDEN = {
    "chemin du corpus de notre site": J(["aero", "-coach"]),
    "domaine de notre site": J(["prun", "el\\."]),
    "chemin absolu d'un compte": J(["/Us", "ers/"]),
    "dossier de configuration de l'assistant": J(["\\.open", "claw"]),
    "port de notre service": J([r"\b41", "40", r"\b"]),
    "classe CSS de notre site hôte": J(["barre", "-score"]) + "|" + J(["qcm", "-options"]),
    "hôte mDNS du modèle local": J(["OMEN", "-INFERENCE"]),
    "adresse tailscale": J([r"100\.9", r"6\."]),
    "autre domaine de notre site": J(["at", "cf-ppl"]),
}
# Nom de lexique « aero » en dur (littéral entre guillemets) : interdit dans le code (les TESTS peuvent nommer le lexique livré)
SLUG_LITERAL = re.compile("[\"']" + "ae" + "ro" + "[\"']")

SCAN_DIRS = ["scripts", "src"]
SCAN_ROOT_PATTERNS = ["*.py"]
SCAN_DIST = ["dist/*.js", "dist/*.css"]
TEMPLATE = ["dist/aero/suggest.html", "dist/aero/suggest.js", "dist/aero/suggest.css"]   # gabarit copié dans chaque nouveau lexique
EXT = {".py", ".js", ".css", ".html", ".json", ".mjs"}
SKIP_PARTS = {"__pycache__", "node_modules", ".git", "backups", "legacy-data"}
SELF = Path(__file__).resolve()


def files():
    out = []
    for d in SCAN_DIRS:
        for p in (ROOT / d).rglob("*"):
            if p.is_file() and p.suffix in EXT and not (set(p.parts) & SKIP_PARTS) and "BAK" not in p.name.upper():
                out.append(p)
    for pat in SCAN_ROOT_PATTERNS + SCAN_DIST:
        out += [p for p in ROOT.glob(pat) if p.is_file()]
    out += [ROOT / t for t in TEMPLATE if (ROOT / t).exists()]
    return sorted({p.resolve() for p in out} - {SELF})


def is_test(p):
    return p.name.startswith("test_") or "fixtures" in p.parts


scan = files()
check("fichiers du code distribuable trouvés", len(scan) > 30, len(scan))
for label, pat in FORBIDDEN.items():
    rx = re.compile(pat)
    hits = []
    for p in scan:
        for n, line in enumerate(p.read_text("utf-8", "ignore").splitlines(), 1):
            if rx.search(line):
                hits.append("%s:%d %s" % (p.relative_to(ROOT), n, line.strip()[:90]))
    check("code distribuable : aucun %s" % label, not hits, " | ".join(hits[:6]))

slug_hits = []
for p in scan:
    if is_test(p):
        continue
    for n, line in enumerate(p.read_text("utf-8", "ignore").splitlines(), 1):
        if SLUG_LITERAL.search(line):
            slug_hits.append("%s:%d %s" % (p.relative_to(ROOT), n, line.strip()[:90]))
check("code distribuable : aucun nom de lexique codé en dur (hors tests)", not slug_hits, " | ".join(slug_hits[:8]))

# ── moteur : tout est embarqué, rien n'est demandé au serveur pour décider d'un soulignement ──
eng = (ROOT / "dist" / "aerolex.js").read_text("utf-8")
code = re.sub(r"/\*.*?\*/", "", eng, flags=re.S)
code = re.sub(r"(^|\s)//[^\n]*", " ", code)
check("moteur : une seule lecture réseau (l'index statique)", len(re.findall(r"\bfetch\s*\(", code)) == 1 and not re.search(r"XMLHttpRequest|WebSocket|sendBeacon|EventSource", code))
check("moteur : aucune URL absolue codée en dur", not re.search(r"https?://", code))
for opt in ("skipSelectors", "data-aerolex-skip", "skipTags", "data-lexicon", "data-src", "meta.rules", "terms_base"):
    check("moteur : option / règle embarquée « %s »" % opt, opt in eng)
check("moteur : « glos » seulement par jetons de classe (pas de sous-chaîne qui avalerait une classe du site hôte)", "indexOf('glos')" not in eng and "indexOf(\"glos\")" not in eng)

# ── configuration : l'installation déclare ses propres valeurs hors du code ──
import json  # noqa: E402

lex = json.loads((ROOT / "data" / "lexicon.json").read_text("utf-8")) if (ROOT / "data" / "lexicon.json").exists() else {}
check("data/lexicon.json : le lexique d'origine déclare son corpus dans sa configuration", isinstance(lex.get("corpus"), dict) and lex["corpus"].get("type") in ("dir", "sitemap", "urls", "upload", "none"), lex.get("corpus"))
check("data/lexicon.json : zones à ignorer de l'hôte déclarées dans la configuration (publiées avec l'index)", bool((lex.get("display") or {}).get("skip_selectors")))
idxp = ROOT / "dist" / ("aerolex-index.json" if lex.get("legacy_names") else "aerolex-%s-index.json" % lex.get("id"))
if idxp.exists():
    meta = json.loads(idxp.read_text("utf-8")).get("meta") or {}
    check("index publié : bloc meta (lexique, terms_base, display, rules) présent", meta.get("format") == 2 and meta.get("lexicon") == lex.get("id") and meta.get("terms_base"), meta)
    check("index publié : les zones à ignorer de l'hôte voyagent avec l'index", (meta.get("display") or {}).get("skip_selectors") == lex["display"]["skip_selectors"])
    check("index publié : aucun chemin local (le corpus n'est jamais publié)", "corpus" not in json.dumps(meta) and "/" not in json.dumps(meta.get("display", {}).get("skip_selectors", [])) )

print("\n%d échec(s)" % len(FAILS))
sys.exit(1 if FAILS else 0)
