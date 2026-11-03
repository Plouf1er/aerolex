#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_index_js.py — Génère aerolex/dist/aerolex-index.json

Lit data/data_glossaire_full.py (dict GLOSSAIRE) et produit un index JSON
STRICTEMENT limité au SURLIGNAGE.

RÈGLE (décision Louis, 2026-08-04) : cet index est chargé par TOUS les sites
hôtes, à chaque page. Il ne doit donc contenir QUE ce qui sert à détecter et
matcher un terme dans du texte. Tout le contenu affiché (définition, catégorie,
famille + membres, xrefs, SVG) vit désormais dans dist/aero/t/<slug>.json,
fetché au clic, mot par mot.

RETIRÉ de l'index (déplacé dans les fichiers par mot) :
  "d"        définitions            — le gros du poids
  "c"        catégorie
  "f"        famille
  "x"        xrefs
  "g"        nom du schéma SVG
  "families" bloc des familles pré-calculé

Structure de sortie (le strict minimum pour détecter + matcher + router) :
  {
    "terms": {
      "TERME": {
        "s": 1,           // 1=définition non vide, 0=vide (DÉDUIT) → style gris/rouge
        "v": [...],       // variantes + synonymes : ce qu'il faut MATCHER aussi
        "cs": true,       // casse_sensible (optionnel) : pilote le matching
        "ctx": [...],     // contexte_requis (optionnel) : désambiguïsation
        "hom": {...},     // homonyme (optionnel) : aiguillage au matching
        "sl": "..."       // slug → URL du fichier par mot ET de la fiche HTML
      }, ...
    }
  }

  "sl" reste indispensable : c'est la clé qui permet au clic de construire
  't/<slug>.json'. "s" reste indispensable : le surlignage colore différemment
  un terme sans définition, avant tout clic.

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
sys.path.insert(0, os.path.join(_DIR, "scripts"))
from data_glossaire_full import GLOSSAIRE  # noqa: E402
from slugify import build_slug_map  # noqa: E402

DEFAULT_OUT = os.path.join(_DIR, "dist", "aerolex-index.json")


def build_index(glossaire: dict) -> dict:
    """Construit le dict index à partir du GLOSSAIRE complet."""
    terms = {}

    # Slugs : MÊME fonction que build_pages.py (scripts/slugify.py), donc les
    # liens "sl" de la popup pointent exactement sur les fichiers générés.
    terme_to_slug, collisions = build_slug_map(list(glossaire.keys()))
    if collisions:
        print(f"⚠️  collisions de slug : {collisions}", file=sys.stderr)

    # (Le pré-calcul des familles a été retiré : il vit maintenant dans
    #  scripts/term_payload.py, qui alimente les fichiers par mot.)

    for canon, meta in glossaire.items():
        if not isinstance(meta, dict):
            meta = {}
        # SOURCE DE VÉRITÉ UNIQUE = LA DÉFINITION (décision Louis, 2026-08-03).
        #
        # Avant : s était calculé depuis meta["statut"] ("redigee"/"redige" -> 1).
        # Ce flag est un second état, qui peut désynchroniser de la réalité :
        # une fiche pouvait porter statut="redigee" sans définition, ou l'inverse.
        # Désormais l'état « défini / à rédiger » est DÉDUIT : une fiche est
        # rédigée si et seulement si sa définition n'est pas vide.
        # meta["statut"] ne pilote plus AUCUN affichage.
        definition = (meta.get("definition") or "").strip()
        s = 1 if definition else 0

        entry: dict = {"s": s}

        # PAS de "d" ici : la définition est dans dist/aero/t/<slug>.json,
        # fetché au clic (aero.js). Elle pesait ~85 % de l'index.
        # PAS de "c" (catégorie) : affichage seul, donc fichier par mot.

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

        # Slug : SEUL champ de routage conservé. Il sert à deux choses :
        #   - construire l'URL du fichier par mot ('t/<slug>.json') au clic ;
        #   - construire l'URL de la fiche HTML publiée.
        # Ni famille, ni catégorie, ni xrefs, ni nom de schéma ici : rien de
        # tout cela n'intervient dans la DÉTECTION d'un terme dans du texte.
        slug = terme_to_slug.get(canon)
        if slug:
            entry["sl"] = slug

        terms[canon] = entry

    # Plus de bloc "families" : la popup reçoit les membres de sa famille,
    # déjà triés et résolus en slugs, dans son fichier par mot.
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
    n_slug = sum(1 for v in index["terms"].values() if v.get("sl"))
    n_var = sum(1 for v in index["terms"].values() if v.get("v"))

    print(f"✅ {out_path}  [INDEX DE SURLIGNAGE SEUL]")
    print(f"   Entrées       : {n_terms}")
    print(f"   Avec slug     : {n_slug}")
    print(f"   Avec variantes: {n_var}")
    print(f"   Rédigées      : {n_redigees} ({n_terms - n_redigees} à rédiger)")
    print("   Retiré        : d, c, f, x, g, families -> dist/aero/t/<slug>.json")
    print(f"   Taille brute  : {raw_size:,} octets ({raw_size/1024:.1f} Ko)")
    print(f"   Taille gzip   : {gz_size:,} octets ({gz_size/1024:.1f} Ko)")


if __name__ == "__main__":
    main()
