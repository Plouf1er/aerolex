# -*- coding: utf-8 -*-
"""lexicon_env.py — quel lexique construit-on ? (rien de codé en dur « aero » dans la chaîne de build)

  AEROLEX_LEXICON  identifiant (slug) du lexique ; défaut « aero » (le lexique historique)
  AEROLEX_LEXROOT  racine du lexique (data/, dist/<slug>/) ; défaut : racine du projet (dossier parent de scripts/)

Un lexique créé par scripts/new_lexicon.py a sa propre racine (lexicons/<slug>/ : data/, dist/<slug>/, scripts liés),
donc tous les chemins relatifs de la chaîne (data/..., dist/...) restent valables ; seuls le NOM du dossier de fiches
et les noms des fichiers d'index partagés (aerolex-index.json…) dépendent du slug. Pour « aero » : noms historiques inchangés.
"""
import os

LEX_ID = os.environ.get("AEROLEX_LEXICON") or "aero"


def lex_root(default: str) -> str:
    return os.environ.get("AEROLEX_LEXROOT") or default


def dist_dir(root: str) -> str:
    return os.path.join(root, "dist", LEX_ID)


def index_name() -> str:
    return "aerolex-index.json" if LEX_ID == "aero" else "aerolex-%s-index.json" % LEX_ID


def search_name() -> str:
    return "aerolex-search.json" if LEX_ID == "aero" else "aerolex-%s-search.json" % LEX_ID


def meta(root: str) -> dict:
    """data/lexicon.json (écrit par new_lexicon.py) : {id, label, base_url, ...} ; {} pour le lexique historique."""
    import json
    try:
        with open(os.path.join(root, "data", "lexicon.json"), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}
