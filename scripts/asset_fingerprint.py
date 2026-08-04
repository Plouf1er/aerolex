#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asset_fingerprint.py — Empreinte CALCULÉE des assets client (cache-busting).

Pourquoi
────────
Avant (2026-08-04) `ASSET_V` était une constante écrite à la main dans
build_pages.py. Conséquence observée DEUX fois le 3-4/08 : Cloudflare a servi un
vieux aerolex.css (cf-cache-status: HIT) parce que la constante n'avait pas été
incrémentée après une modif de code. Un cache-buster qu'un humain doit penser à
bumper n'est pas un cache-buster, c'est un piège.

Désormais l'empreinte est DÉRIVÉE du contenu réel des fichiers servis au
navigateur. Toute modification d'une ligne de JS, de CSS, ou d'un réglage client
(lexicon.json) change l'empreinte automatiquement — et donc l'URL — donc le CDN
et le navigateur sont obligés de retélécharger. Aucune discipline humaine requise.

Fichiers couverts (tout ce qui est exécuté/interprété côté client) :
    dist/aerolex.js        moteur de surlignage + popup
    dist/aerolex.css       styles du surlignage et de la popup
    dist/aerolex-page.css  habillage des pages de fiche (dist/aero/*.html)
    dist/aerolex-svg.js    libellés SVG cliquables
    dist/aero/lexicon.json réglages client (popup.*, html_published)

lexicon.json EST inclus volontairement : il pilote l'affichage (quels blocs la
popup montre). Un changement de réglage sans changement de code doit tout de
même invalider les pages, sinon un lecteur garde l'ancien comportement 4 h.

Usage :
    from asset_fingerprint import asset_fingerprint, write_build_info
    v = asset_fingerprint()          # -> '3f9a1c07' (8 hex)
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_DIR)

# Ordre FIGÉ : le hash doit être reproductible d'un build à l'autre.
ASSET_FILES = (
    os.path.join(_ROOT, "dist", "aerolex.js"),
    os.path.join(_ROOT, "dist", "aerolex.css"),
    # Ajouté le 04/08/2026 avec la feuille de mise en page des fiches. Un asset
    # servi au navigateur mais ABSENT de cette liste est un piège à cache : on
    # pourrait modifier tout l'habillage sans que l'URL ?v= change, et
    # Cloudflare servirait l'ancienne feuille 4 h (exactement le bug d'origine).
    os.path.join(_ROOT, "dist", "aerolex-page.css"),
    os.path.join(_ROOT, "dist", "aerolex-svg.js"),
    os.path.join(_ROOT, "dist", "aero", "lexicon.json"),
)

BUILD_INFO_PATH = os.path.join(_ROOT, "dist", "aero", "build-info.json")

FINGERPRINT_LEN = 8


def asset_fingerprint(files=ASSET_FILES) -> str:
    """sha256 tronqué (8 hex) du contenu concaténé des assets client.

    Un fichier absent est hashé comme son nom + marqueur MISSING : l'apparition
    ou la disparition d'un asset change donc aussi l'empreinte, au lieu d'être
    silencieuse.
    """
    h = hashlib.sha256()
    for path in files:
        name = os.path.basename(path)
        h.update(name.encode("utf-8"))
        h.update(b"\x00")
        try:
            with open(path, "rb") as f:
                h.update(f.read())
        except OSError:
            h.update(b"MISSING")
        h.update(b"\x1e")
    return h.hexdigest()[:FINGERPRINT_LEN]


def asset_details(files=ASSET_FILES):
    """[{fichier, octets, sha256_court}] — pour l'audit dans build-info.json."""
    out = []
    for path in files:
        try:
            with open(path, "rb") as f:
                b = f.read()
            out.append({
                "fichier": os.path.basename(path),
                "octets": len(b),
                "sha256": hashlib.sha256(b).hexdigest()[:FINGERPRINT_LEN],
            })
        except OSError:
            out.append({"fichier": os.path.basename(path), "octets": None, "sha256": None})
    return out


def write_build_info(nb_termes: int, extra: dict | None = None) -> dict:
    """Écrit dist/aero/build-info.json et retourne le dict écrit.

    Ce fichier est le point de vérité consultable en public : il permet de
    vérifier d'un `curl` quelle empreinte est censée être servie, et donc de
    diagnostiquer un cache CDN périmé sans deviner.
    """
    v = asset_fingerprint()
    info = {
        "empreinte": v,
        "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "nb_termes": nb_termes,
        "assets": asset_details(),
    }
    if extra:
        info.update(extra)
    os.makedirs(os.path.dirname(BUILD_INFO_PATH), exist_ok=True)
    with open(BUILD_INFO_PATH, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)
    return info


if __name__ == "__main__":
    print(asset_fingerprint())
