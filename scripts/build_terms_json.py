#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_terms_json.py — Génère dist/aero/t/<slug>.json (un fichier par mot)
                      + dist/aero/lexicon.json (config du lexique).

Idée Louis (2026-08-04) : le clic charge UN fichier statique par mot contenant
TOUT ce qui a servi à bâtir la page HTML. Conséquences :
  - cacheable par le navigateur/CDN, mot par mot (immutable en pratique) ;
  - la popup n'a plus rien à lire dans l'index → l'index redevient un pur
    index de SURLIGNAGE (léger, chargé par tous les sites hôtes) ;
  - un mot lourd (gros SVG) ne pénalise plus les 1295 autres.

Le contenu vient de scripts/term_payload.py, la MÊME fonction que celle qui
alimente le générateur HTML : aucune divergence possible entre la fiche en
ligne et ce que montre la popup.

Usage :
    python3 scripts/build_terms_json.py
"""
from __future__ import annotations

import json
import os
import sys
import gzip

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)
for _p in (os.path.join(_ROOT, "data"), _DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from data_glossaire_full import GLOSSAIRE      # noqa: E402
from term_payload import build_all_payloads, PAYLOAD_VERSION  # noqa: E402

OUT_DIR = os.path.join(_ROOT, "dist", "aero", "t")
LEXICON_PATH = os.path.join(_ROOT, "dist", "aero", "lexicon.json")

# ── Config du lexique ────────────────────────────────────────────────────────
# HIÉRARCHIE D'AFFICHAGE (décision Louis, 2026-08-04) :
#
#   1. PUBLICATION (ce fichier)  — autorité du créateur du lexique.
#   2. PRÉFÉRENCE CSS (--alx-pop-show-*) — confort du site hôte / du lecteur.
#
# La règle : le CSS ne peut que MASQUER un contenu déjà autorisé, il ne peut
# JAMAIS en créer un. Concrètement, si html_published vaut false, le JS n'émet
# pas le lien « voir la fiche complète » du tout — aucune règle CSS, aucune
# surcharge côté hôte ne peut le faire réapparaître, parce que l'élément
# n'existe pas dans le DOM. À l'inverse, si html_published vaut true, le lien
# est émis mais un hôte reste libre de le cacher via
# `:root { --alx-pop-show-link: none }`.
# Autrement dit : publication = condition nécessaire, CSS = filtre facultatif.
LEXICON = {
    "id": "aero",
    "titre": "Glossaire Aéronautique",
    # true  = les pages HTML par mot sont publiées et référençables → le JS
    #         PEUT émettre le lien « voir la fiche complète ».
    # false = lexique non publié → le JS n'émet AUCUN lien (le CSS n'y peut rien).
    "html_published": True,
    "visibility": "public",
    "base_url": "https://aerolex.prunel.net/aero/",
    "payload_version": PAYLOAD_VERSION,
    # Valeurs par défaut des interrupteurs d'affichage de la popup.
    # Pour `aero` : TOUT ACTIVÉ (demande explicite de Louis).
    "popup": {
        "def": True,
        "schema": True,     # images / SVG
        "variants": True,   # variantes du mot
        "family": True,
        "xrefs": True,
        "link": True,       # soumis à html_published ci-dessus
    },
}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    ctx, payloads = build_all_payloads(GLOSSAIRE)
    if ctx.collisions:
        print(f"⚠️  collisions de slug : {ctx.collisions}", file=sys.stderr)

    # Purge des .json orphelins (un terme renommé ne doit pas laisser de fichier
    # fantôme que la popup servirait encore depuis le cache CDN).
    attendus = {f"{p['slug']}.json" for p in payloads.values() if p.get("slug")}
    supprimes = 0
    if os.path.isdir(OUT_DIR):
        for existing in os.listdir(OUT_DIR):
            if existing.endswith(".json") and existing not in attendus:
                os.remove(os.path.join(OUT_DIR, existing))
                supprimes += 1

    tailles = []
    plus_gros = ("", 0)
    n_svg = 0
    for terme, p in payloads.items():
        slug = p.get("slug")
        if not slug:
            print(f"⚠️  pas de slug pour {terme!r}, ignoré", file=sys.stderr)
            continue
        s = json.dumps(p, ensure_ascii=False, separators=(",", ":"))
        b = s.encode("utf-8")
        with open(os.path.join(OUT_DIR, f"{slug}.json"), "wb") as f:
            f.write(b)
        tailles.append(len(b))
        if len(b) > plus_gros[1]:
            plus_gros = (slug, len(b))
        if p.get("schema_svg"):
            n_svg += 1

    with open(LEXICON_PATH, "w", encoding="utf-8") as f:
        json.dump(LEXICON, f, ensure_ascii=False, indent=2)

    total = sum(tailles)
    n = len(tailles)
    print(f"✅ {OUT_DIR}")
    print(f"   Fichiers écrits : {n} (orphelins supprimés : {supprimes})")
    print(f"   Avec SVG inline : {n_svg}")
    print(f"   Poids total     : {total:,} o ({total/1024:.1f} Ko)")
    print(f"   Poids moyen     : {total/n:.0f} o" if n else "   (aucun)")
    print(f"   Plus gros       : {plus_gros[0]}.json = {plus_gros[1]:,} o")
    print(f"✅ {LEXICON_PATH} (html_published={LEXICON['html_published']})")


if __name__ == "__main__":
    main()
