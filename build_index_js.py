#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index_js.py — Génère aerolex/dist/aerolex-index.json

Lit data/data_glossaire_full.py (dict GLOSSAIRE, 1101 entrées) et produit
un index JSON minimaliste : uniquement ce qu'il faut pour SURLIGNER.

Structure de sortie :
  {
    "terms": {
      "TERME": {
        "s": 1,           // statut: 1=rédigée, 0=a_rediger
        "v": [...],       // variantes + synonymes (optionnel, absent si vide)
        "cs": true,       // casse_sensible (optionnel)
        "ctx": [...]      // contexte_requis (optionnel)
      }, ...
    }
  }

Usage :
    python3 build_index_js.py
    python3 build_index_js.py --output /chemin/vers/index.json
"""
from __future__ import annotations

import json
import os
import sys
import gzip

# Ajoute le dossier data/ au path
_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_DIR, "data"))
from data_glossaire_full import GLOSSAIRE  # noqa: E402

DEFAULT_OUT = os.path.join(_DIR, "dist", "aerolex-index.json")


def build_index(glossaire: dict) -> dict:
    """Construit le dict index à partir du GLOSSAIRE complet."""
    terms = {}
    for canon, meta in glossaire.items():
        if not isinstance(meta, dict):
            meta = {}
        statut = meta.get("statut", "a_rediger")
        s = 1 if statut == "redigee" else 0

        entry: dict = {"s": s}

        # Variantes + synonymes
        variantes = list(meta.get("variantes") or [])
        synonymes = list(meta.get("synonymes") or [])
        all_v = variantes + [x for x in synonymes if x not in variantes]
        if all_v:
            entry["v"] = all_v

        # Casse sensible
        if meta.get("casse_sensible"):
            entry["cs"] = True

        # Contexte requis (désambiguïsation)
        ctx = meta.get("contexte_requis") or []
        if ctx:
            entry["ctx"] = list(ctx)

        # Homonyme (aiguillage)
        hom = meta.get("homonyme")
        if isinstance(hom, dict) and hom.get("cible") and hom.get("contexte"):
            entry["hom"] = {"c": hom["cible"], "ctx": list(hom["contexte"])}

        # Origine (corpus vs metier) — utile pour filtrer ultérieurement
        # On l'exclut pour garder l'index léger (non nécessaire au surlignage)
        # Si besoin futur : entry["o"] = meta.get("origine", "corpus")

        terms[canon] = entry

    return {"terms": terms}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Génère aerolex-index.json")
    parser.add_argument("--output", default=DEFAULT_OUT, help="Chemin de sortie JSON")
    args = parser.parse_args()

    out_path = args.output
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    index = build_index(GLOSSAIRE)

    json_str = json.dumps(index, ensure_ascii=False, separators=(",", ":"))
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    # Stats
    raw_size = len(json_str.encode("utf-8"))
    gz_data = gzip.compress(json_str.encode("utf-8"))
    gz_size = len(gz_data)
    n_terms = len(index["terms"])
    n_redigees = sum(1 for v in index["terms"].values() if v["s"] == 1)

    print(f"✅ {out_path}")
    print(f"   Entrées       : {n_terms}")
    print(f"   Rédigées      : {n_redigees} ({n_terms - n_redigees} à rédiger)")
    print(f"   Taille brute  : {raw_size:,} octets ({raw_size/1024:.1f} Ko)")
    print(f"   Taille gzip   : {gz_size:,} octets ({gz_size/1024:.1f} Ko)")


if __name__ == "__main__":
    main()
