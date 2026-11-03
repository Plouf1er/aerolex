#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_schemas_json.py — Génère dist/aero/schemas.json

{ "<nom_generateur>": "<svg ...>...</svg>", ... }

POURQUOI un fichier séparé et pas dans aerolex-index.json :
l'index est chargé par TOUS les sites hôtes à chaque page ; les 9 SVG le
gonfleraient pour 18 termes sur 1296. schemas.json est fetché une seule fois,
à la demande, au premier clic sur un terme qui porte un schéma (clé "g"),
puis mémoïsé côté client.

Le mapping terme -> générateur vit dans scripts/schema_map.py (source unique).
"""
from __future__ import annotations

import json
import os
import sys
import gzip

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
sys.path.insert(0, os.path.join(_ROOT, "src"))
sys.path.insert(0, _DIR)

from svg_glossaire import SCHEMAS, get_schema  # noqa: E402
from schema_map import TERM_TO_SCHEMA  # noqa: E402

OUT = os.path.join(_ROOT, "dist", "aero", "schemas.json")


def main():
    # On ne sort que les schémas réellement atteignables depuis un terme.
    utilises = sorted(set(TERM_TO_SCHEMA.values()))
    out = {}
    for name in utilises:
        if name not in SCHEMAS:
            print(f"⚠️  schéma inconnu dans SCHEMAS : {name}", file=sys.stderr)
            continue
        svg = get_schema(name)
        if svg:
            out[name] = svg

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    js = json.dumps(out, ensure_ascii=False, separators=(",", ":"))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(js)

    raw = len(js.encode("utf-8"))
    gz = len(gzip.compress(js.encode("utf-8")))
    print(f"✅ {OUT}")
    print(f"   Schémas : {len(out)} ({', '.join(out.keys())})")
    print(f"   Brut    : {raw:,} o ({raw/1024:.1f} Ko) | gzip : {gz:,} o ({gz/1024:.1f} Ko)")


if __name__ == "__main__":
    main()
