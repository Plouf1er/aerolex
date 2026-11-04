#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_links_resolve.py — ÉCHOUE si un lien/mot souligné de l'index ou d'une fiche
ne mène à aucune fiche (symptôme : clic = curseur « ? » sans effet).
Vérifie : (1) chaque href *.html de l'index et des fiches -> page existante ;
(2) chaque terme de aerolex-index.json (= futur data-term) -> slugmap.json ->
fiche HTML + aero/t/<slug>.json existants ; (3) l'index définit CURRENT_SLUG
(sinon ReferenceError au clic) et n'a aucun {ASSET_V} littéral.
Lancer : python3 scripts/test_links_resolve.py  (après build_pages.py)
"""
import glob, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import lexicon_env  # noqa: E402
LEX = os.environ.get("AEROLEX_LEXICON") or lexicon_env.default_id(ROOT)
D = os.path.join(ROOT, "dist", LEX)
errs = []

smap = json.load(open(os.path.join(D, "slugmap.json"), encoding="utf-8"))
idx = json.load(open(os.path.join(ROOT, "dist", lexicon_env.index_file(LEX, ROOT)), encoding="utf-8"))
terms = idx.get("terms", idx)

for t, v in terms.items():
    sl = smap.get(t)
    if not sl:
        errs.append("terme sans slugmap: %r" % t); continue
    if not os.path.exists(os.path.join(D, sl + ".html")):
        errs.append("fiche HTML absente: %s" % sl)
    if not os.path.exists(os.path.join(D, "t", sl + ".json")):
        errs.append("JSON de fiche absent: t/%s.json" % sl)
    if v.get("sl") and v["sl"] != sl:
        errs.append("slug index/slugmap divergent: %r %s != %s" % (t, v["sl"], sl))

href_re = re.compile(r'href="([^"#?:]+\.html)')
for f in glob.glob(os.path.join(D, "*.html")):
    h = open(f, encoding="utf-8").read()
    for target in href_re.findall(h):
        if target.startswith("../") or target.startswith("http"):
            continue
        if not os.path.exists(os.path.join(D, target)):
            errs.append("%s -> lien mort %s" % (os.path.basename(f), target))

index_html = open(os.path.join(D, "index.html"), encoding="utf-8").read()
if "{ASSET_V}" in index_html:
    errs.append("index.html: {ASSET_V} littéral (f-string oubliée)")
if "CURRENT_SLUG" in index_html and not re.search(r"var\s+CURRENT_SLUG\s*=", index_html):
    errs.append("index.html: CURRENT_SLUG utilisé mais non défini (ReferenceError au clic)")
for f in glob.glob(os.path.join(D, "*.html")):
    h = open(f, encoding="utf-8").read()
    if "CURRENT_SLUG" in h and not re.search(r"var\s+CURRENT_SLUG\s*=", h):
        errs.append("%s: CURRENT_SLUG non défini" % os.path.basename(f))

if errs:
    print("ÉCHEC (%d)" % len(errs)); print("\n".join(errs[:40])); sys.exit(1)
print("OK : %d termes résolus (slugmap + fiche + JSON), liens et JS d'index valides" % len(terms))
