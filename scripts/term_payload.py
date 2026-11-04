#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
term_payload.py — SOURCE DE VÉRITÉ UNIQUE du contenu d'un terme.

Pourquoi ce module existe
─────────────────────────
Avant (2026-08-04, matin) il y avait DEUX logiques parallèles qui décidaient
« que contient une fiche » :
  - scripts/build_pages.py  construisait le HTML (définition, variantes, SVG,
    tableau de famille, xrefs) directement dans sa f-string ;
  - build_index_js.py       reconstruisait les mêmes champs, en clés courtes,
    pour l'index chargé par la popup.
Deux implémentations du même contrat = divergence garantie à la première
évolution (un filtre de xref changé d'un côté et pas de l'autre, un tri de
famille différent, etc.).

Désormais : `build_payload(terme, ctx)` est la SEULE fonction qui décide du
contenu d'un terme. Elle est consommée par :
  - scripts/build_pages.py  → rend le HTML depuis le payload ;
  - scripts/build_terms_json.py → sérialise le payload en dist/aero/t/<slug>.json.
Un seul endroit à modifier pour changer le contrat de contenu.

Le payload est volontairement « prêt à afficher » : les xrefs et les membres de
famille arrivent déjà filtrés (existence réelle) et résolus (slug), et le SVG
est inline. Objectif Louis : la popup n'a besoin de RIEN d'autre que ce fichier.
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
for _p in (os.path.join(_ROOT, "data"), _DIR, os.path.join(_ROOT, "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from slugify import build_slug_map            # noqa: E402  (ne pas réécrire)
from schema_map import TERM_TO_SCHEMA         # noqa: E402
from svg_glossaire import SCHEMAS, get_schema  # noqa: E402
from term_display import (build_display_table, clean_aliases, family_label,  # noqa: E402
                          expand_acronyms, dev_label)

# Version du schéma de payload. Incrémenter si la forme change de façon
# incompatible : le JS peut alors refuser un cache périmé.
PAYLOAD_VERSION = 2   # champ "dev" ajouté (additif, compatible)


class PayloadContext:
    """Contexte de build partagé : slugs, familles, ordre alphabétique.

    Calculé UNE fois puis passé à chaque appel de build_payload : les 1296
    payloads se partagent les mêmes tables, aucun recalcul par terme.
    """

    def __init__(self, glossaire: dict):
        self.glossaire = glossaire
        self.termes_tries = sorted(glossaire.keys(), key=lambda x: x.lower())

        # Slugs : MÊME fonction que partout ailleurs (scripts/slugify.py).
        self.terme_to_slug, self.collisions = build_slug_map(list(glossaire.keys()))

        # Familles, triées insensible à la casse (ordre unique, HTML == JSON).
        fam = defaultdict(list)
        for t, meta in glossaire.items():
            if not isinstance(meta, dict):
                continue
            f = (meta.get("famille") or "").strip()
            if f:
                fam[f].append(t)
        for f in fam:
            fam[f].sort(key=lambda t: t.lower())
        self.families = dict(fam)

        # Affichage : titre (casse des sigles), développement, équivalent FR.
        self.display = build_display_table(glossaire)
        self.upper_index = {}
        for k, d in self.display.items():
            self.upper_index.setdefault(k.upper(), k)
        self.unknown_acronyms = {}   # sigle -> [termes où il apparaît sans développement]

        # Cache des SVG : get_schema() est appelé une fois par (schéma, terme).
        self._svg_cache: dict = {}

    def slug(self, terme: str):
        return self.terme_to_slug.get(terme)

    def svg(self, schema_name: str, terme: str):
        key = (schema_name, terme)
        if key not in self._svg_cache:
            self._svg_cache[key] = get_schema(schema_name, terme=terme)
        return self._svg_cache[key]


def build_payload(terme: str, ctx: PayloadContext) -> dict:
    """Construit le payload complet d'un terme. SEULE définition du contrat.

    Retourne un dict sérialisable JSON contenant TOUT ce qui sert à bâtir la
    fiche : définition, catégorie, famille (+ membres avec slugs), variantes,
    xrefs (+ slugs), statut, schéma (nom + SVG inline), voisins de navigation.
    """
    meta = ctx.glossaire.get(terme)
    if not isinstance(meta, dict):
        meta = {}

    g = ctx.glossaire
    disp = ctx.display.get(terme) or {"titre": terme, "expansion": None, "gloss": None, "definition_base": ""}
    definition = (meta.get("definition") or "").strip()
    if definition:
        definition, _unk = expand_acronyms(disp["definition_base"], terme, ctx.display, ctx.upper_index)
        for _u in _unk:
            ctx.unknown_acronyms.setdefault(_u, []).append(terme)
    categorie = (meta.get("categorie") or "").strip()
    famille = (meta.get("famille") or "").strip()
    slug = ctx.slug(terme)

    # Variantes + synonymes dédoublonnés, ordre stable (variantes d'abord).
    variantes = list(meta.get("variantes") or [])
    synonymes = list(meta.get("synonymes") or [])
    all_variantes = clean_aliases(disp["titre"], terme, variantes + synonymes,
                                  disp["expansion"], disp["gloss"])

    # Alias qui sont eux-mêmes des sigles connus : {alias: développé}.
    variantes_dev = {}
    for a in all_variantes:
        ak = ctx.upper_index.get(a.upper())
        dv = dev_label(ctx.display[ak]) if ak and ak != terme else None
        if dv:
            variantes_dev[a] = dv

    # Xrefs : filtrées sur l'existence réelle dans le glossaire → aucun lien
    # mort possible, ni en HTML ni dans la popup. Résolues en slug ici.
    xrefs = []
    for xr in (meta.get("xrefs") or []):
        if xr in g and xr != terme:
            xrefs.append({"t": xr, "titre": ctx.display[xr]["titre"], "sl": ctx.slug(xr),
                          "dev": dev_label(ctx.display[xr])})

    # Membres de la famille (>= 2 pour valoir un tableau), avec slug + marqueur
    # du terme courant (jamais de lien d'un terme vers lui-même).
    famille_membres = []
    if famille:
        membres = ctx.families.get(famille, [])
        if len(membres) >= 2:
            for m in membres:
                famille_membres.append({
                    "t": m,
                    "titre": ctx.display[m]["titre"],
                    "sl": ctx.slug(m),
                    "courant": (m == terme),
                    "dev": dev_label(ctx.display[m]),
                })

    # Schéma : nom + SVG inline (c'est le point clé — la popup n'a plus besoin
    # de fetcher schemas.json en plus du fichier du mot).
    schema_name = TERM_TO_SCHEMA.get(terme)
    schema_svg = None
    if schema_name and schema_name in SCHEMAS:
        schema_svg = ctx.svg(schema_name, terme)
    else:
        schema_name = None

    # Voisins alphabétiques (navigation « précédent / suivant » du HTML).
    try:
        idx = ctx.termes_tries.index(terme)
    except ValueError:
        idx = -1
    prev_t = ctx.termes_tries[idx - 1] if idx > 0 else None
    next_t = ctx.termes_tries[idx + 1] if 0 <= idx < len(ctx.termes_tries) - 1 else None

    return {
        "v": PAYLOAD_VERSION,
        "terme": terme,
        "titre": disp["titre"],
        "sigle": ({"developpement": disp["expansion"], "equivalent": disp["gloss"]}
                  if disp["expansion"] else None),
        "slug": slug,
        "definition": definition,
        # ÉTAT DÉDUIT de la définition, jamais d'un flag (décision Louis
        # 2026-08-03) : redigee <=> definition non vide.
        "redigee": bool(definition),
        # statut brut conservé pour information/audit, ne pilote AUCUN affichage.
        "statut": (meta.get("statut") or "").strip(),
        "categorie": categorie,
        "famille": famille,
        "famille_label": family_label(famille),
        "famille_membres": famille_membres,
        "variantes": all_variantes,
        "variantes_dev": variantes_dev,
        "xrefs": xrefs,
        "schema": schema_name,
        "schema_svg": schema_svg,
        "prev": ({"t": prev_t, "titre": ctx.display[prev_t]["titre"], "sl": ctx.slug(prev_t)} if prev_t else None),
        "next": ({"t": next_t, "titre": ctx.display[next_t]["titre"], "sl": ctx.slug(next_t)} if next_t else None),
    }


def build_all_payloads(glossaire: dict):
    """(ctx, {terme: payload}) pour tout le glossaire."""
    ctx = PayloadContext(glossaire)
    return ctx, {t: build_payload(t, ctx) for t in ctx.termes_tries}
