#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_slugs.py — slugs sûrs : aucun vide / d'une lettre / générique (terme, terme-N) / réservé ;
aucune collision entre deux fiches ni avec un fichier statique de dist/aero ; chaque ancien slug
redirige vers la bonne fiche ; règle de translittération (°, °C, %, θ) ; la fiche « index » existe.
Lancer : python3 scripts/test_slugs.py   (après build_pages.py)"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts")); sys.path.insert(0, os.path.join(ROOT, "data"))
import slugify as S
from data_glossaire_full import GLOSSAIRE as G

LEX = os.environ.get("AEROLEX_LEXICON") or "aero"       # un lexique créé par new_lexicon.py : AEROLEX_LEXICON=<slug>, cwd = sa racine
D = os.path.join(ROOT, "dist", LEX)
MARK = "Index du Glossaire" if LEX == "aero" else "ix-head"
FAILS = []
def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + ("" if cond else " " + str(extra)[:300]))
    if not cond: FAILS.append(name)

# 1. règle pure
for t, exp in [("°", "degre"), ("°C", "degre-celsius"), ("°F", "degre-fahrenheit"), ("%", "pourcent"), ("θ", "theta"),
               ("manœuvre", "manoeuvre"), ("Tour de piste", "tour-de-piste")]:
    check("slugify(%r) == %r" % (t, exp), S.slugify(t) == exp, S.slugify(t))
m, coll = S.build_slug_map(list(G), G)
if "index" in G:
    check("build_slug_map : 'index' -> slug réservé évité", m["index"] == "index-terme", m["index"])
check("slug dérivé jamais générique pour un terme vide de sens", all(S.slug_ok(S.build_slug_map([x], {x: {"variantes": ["degré"]}})[0][x]) for x in ["", "?", "x", "°°"]))
check("réservés (index, suggest, search, slugmap, build-info) -> suffixe", all(S.build_slug_map([r])[0][r] == r + "-terme" for r in ["index", "suggest", "search", "slugmap", "build-info"]))

# 2. slugmap réel
sm = json.load(open(os.path.join(D, "slugmap.json"), encoding="utf-8"))
red = sm.get("_redirects", {})
terms = {k: v for k, v in sm.items() if k != "_redirects"}
check("slugmap = calcul courant", terms == m)
check("%d fiches dans slugmap = glossaire" % len(G), set(terms) == set(G))
bad = {t: s for t, s in terms.items() if not S.slug_ok(s)}
check("aucun slug vide / 1 lettre / générique / hors [a-z0-9-]", not bad, bad)
reserved = S.static_reserved(D)
check("aucun slug réservé", not [s for s in terms.values() if s in reserved], [s for s in terms.values() if s in reserved])
dup = [s for s in set(terms.values()) if list(terms.values()).count(s) > 1]
check("aucune collision entre fiches", not dup, dup)
static_files = {f for f in os.listdir(D) if not os.path.isdir(os.path.join(D, f))}
gen = {s + ".html" for s in terms.values()}
check("aucune fiche ne masque un fichier statique", not (gen & {f for f in static_files if f in ("index.html", "suggest.html") or not f.endswith(".html")}))
check("chaque fiche a son HTML et son JSON", all(os.path.exists(os.path.join(D, s + ".html")) and os.path.exists(os.path.join(D, "t", s + ".json")) for s in terms.values()))
_ix = os.path.join(D, "index-terme.html")
if "index" in G:
    check("la fiche « index » existe (index-terme.html) et n'est pas la page d'index",
          terms["index"] == "index-terme" and os.path.exists(_ix) and MARK not in open(_ix, encoding="utf-8").read()[:1500])
check("index.html reste la page d'index", MARK in open(os.path.join(D, "index.html"), encoding="utf-8").read())

# 3. redirections
want = S.build_redirects(terms)
check("redirections = calcul courant", red == want)
if LEX == "aero":
    check("°, °C, θ : anciens slugs redirigés", red.get("terme") == "degre" and red.get("c") == "degre-celsius" and red.get("terme-2") == "theta", red)
errs = []
for old, new in red.items():
    p = os.path.join(D, old + ".html")
    if not os.path.exists(p): errs.append("page absente " + old); continue
    h = open(p, encoding="utf-8").read()
    if "aerolex-redirect" not in h or ('url=%s.html' % new) not in h: errs.append("mauvaise cible " + old)
    if new not in terms.values(): errs.append("cible inconnue " + new)
    if old in terms.values(): errs.append("ancien slug = fiche vivante " + old)
check("chaque ancien slug redirige vers la bonne fiche", not errs, errs)
check("pas de page de renvoi orpheline", all(
    (f[:-5] in red) for f in os.listdir(D) if f.endswith(".html") and "aerolex-redirect" in open(os.path.join(D, f), encoding="utf-8").read(400)))
print()
if FAILS:
    print("ECHEC test_slugs :", FAILS); sys.exit(1)
print("OK test_slugs")
