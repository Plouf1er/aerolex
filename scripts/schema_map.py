#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
schema_map.py — SOURCE UNIQUE du mapping terme -> générateur de schéma SVG.

Extrait de scripts/build_pages.py (2026-08-04) pour être partagé par :
  - scripts/build_pages.py   (pages statiques dist/aero/*.html)
  - build_index_js.py        (clé "g" de dist/aerolex-index.json)
  - scripts/build_schemas_json.py (dist/aero/schemas.json pour la popup)

Les noms de valeurs doivent exister dans src/svg_glossaire.py::SCHEMAS.
Ne pas dupliquer cette règle ailleurs : importer d'ici.
"""

TERM_TO_SCHEMA = {
    "TORA": "distances_piste",
    "TODA": "distances_piste",
    "ASDA": "distances_piste",
    "LDA": "distances_piste",
    "seuil de piste": "piste_seuils_qfu",
    "manche à air": "manche_a_air",
    "composante de travers": "composantes_face_travers",
    "décrabage": "decrabage",
    "déclinaison magnétique": "azimut_vrai_magnetique",
    "rose des vents": "rose_des_vents",
    "tour de piste": "tour_de_piste",
    "vent arrière": "tour_de_piste",
    "étape de base": "tour_de_piste",
    "longue finale": "tour_de_piste",
    "vent traversier": "tour_de_piste",
    "montée initiale": "tour_de_piste",
    "arrondi": "tour_de_piste",
    "remise des gaz": "remise_des_gaz",
}


def schema_for(terme: str):
    """Retourne le nom du générateur de schéma pour un terme, ou None."""
    return TERM_TO_SCHEMA.get(terme)
