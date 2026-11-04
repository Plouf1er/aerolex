#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_search_json.py — dist/aerolex-search.json : index de RECHERCHE (autocomplétion).

Lignes [titre, slug, clé, développement, "alias1|alias2"]. Chargé au 1er focus du
champ de recherche uniquement (pas au chargement de page).
"""
import json, os, sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(_ROOT, "data"), os.path.join(_ROOT, "scripts")]
from data_glossaire_full import GLOSSAIRE
from term_payload import PayloadContext, build_payload

ctx = PayloadContext(GLOSSAIRE)
rows = []
for t in ctx.termes_tries:
    p = build_payload(t, ctx)
    sg = p["sigle"] or {}
    al = list(p["variantes"])
    if sg.get("equivalent"):
        al.append(sg["equivalent"])
    rows.append([p["titre"], p["slug"], t, sg.get("developpement") or ctx.display[t].get("expr") or "", "|".join(al)])
out = os.path.join(_ROOT, "dist", "aerolex-search.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump({"v": 1, "d": rows}, f, ensure_ascii=False, separators=(",", ":"))
import gzip
raw = os.path.getsize(out)
print("aerolex-search.json : %d o brut, %d o gzip, %d entrées" % (raw, len(gzip.compress(open(out, 'rb').read())), len(rows)))
