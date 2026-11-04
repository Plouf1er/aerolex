# -*- coding: utf-8 -*-
"""lexicon_env.py — quel lexique construit-on ? Configuration PAR LEXIQUE, aucun identifiant codé en dur.

  AEROLEX_LEXICON  identifiant (slug) du lexique ; défaut : l'« id » de <racine>/data/lexicon.json (« main » si absent)
  AEROLEX_LEXROOT  racine du lexique (data/, dist/<slug>/) ; défaut : racine du projet (dossier parent de scripts/)

Un lexique créé par scripts/new_lexicon.py a sa propre racine (lexicons/<slug>/ : data/, dist/<slug>/, scripts liés),
donc tous les chemins relatifs de la chaîne (data/..., dist/...) restent valables ; seuls le NOM du dossier de fiches
et les noms des fichiers d'index partagés (aerolex-<slug>-index.json…) dépendent du slug.

Configuration d'un lexique : <racine>/data/lexicon.json (voir README « Configurer un lexique »). Clés reconnues :

  id, label, audience, scope, base_url, index_title     identité et textes
  legacy_names (bool)      noms de fichiers historiques SANS slug (aerolex-index.json, aerolex-search.json) — lexique d'origine seulement
  corpus                   source de texte du contrôle anti-ridicule : dossier local / sitemap / liste d'URL / échantillon téléversé / aucun
                           (voir scripts/corpus.py ; jamais publié)
  display                  options d'affichage PUBLIÉES dans l'index du moteur (meta.display) : skip_selectors, metar
  rules                    règles de reconnaissance PUBLIÉES dans l'index (meta.rules) : exact_case, singular_exclude
"""
import json
import os

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.environ.get("AEROLEX_LEXROOT") or os.path.dirname(_HERE)


def meta(root: str) -> dict:
    """data/lexicon.json du lexique : configuration complète ({} si absent ou illisible)."""
    try:
        with open(os.path.join(root, "data", "lexicon.json"), encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def default_id(root: str = "") -> str:
    return os.environ.get("AEROLEX_LEXICON") or meta(root or _ROOT).get("id") or "main"


LEX_ID = default_id()


def lex_root(default: str) -> str:
    return os.environ.get("AEROLEX_LEXROOT") or default


def dist_dir(root: str) -> str:
    return os.path.join(root, "dist", LEX_ID)


def legacy(root: str = "", lex_id: str = "") -> bool:
    """Vrai si ce lexique garde les noms de fichiers sans slug (declaré dans sa configuration)."""
    m = meta(root or _ROOT)
    return bool(m.get("legacy_names")) and (not lex_id or m.get("id") == lex_id)


def index_file(lex_id: str, root: str = "") -> str:
    return "aerolex-index.json" if legacy(root, lex_id) else "aerolex-%s-index.json" % lex_id


def search_file(lex_id: str, root: str = "") -> str:
    return "aerolex-search.json" if legacy(root, lex_id) else "aerolex-%s-search.json" % lex_id


def index_name() -> str:
    return index_file(LEX_ID)


def search_name() -> str:
    return search_file(LEX_ID)


def node_bin() -> str:
    """Chemin absolu de node : $AEROLEX_NODE, puis le PATH, puis les emplacements d'installation usuels (un service lancé hors terminal
    n'a pas le PATH de l'utilisateur)."""
    import shutil
    for c in (os.environ.get("AEROLEX_NODE"), shutil.which("node"), "/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"):
        if c and os.path.exists(c):
            return c
    return "node"


def install_config(root: str = "") -> dict:
    """Configuration de l'INSTALLATION (≠ du lexique) : $AEROLEX_CONFIG ou <racine>/aerolex.config.json ({} si absent). Clés :
         env_files        fichiers .env (KEY=valeur) où chercher XAI_API_KEY (~ accepté)
         password_file    fichier du mot de passe relecteur (défaut ~/.aerolex-suggest-password)
         llm              {local_url, local_model} : modèle local de secours (aucun par défaut)
         serve            {port, dir, cors_origins:[...]} : serveur statique serve_cors.py
       Ne contient jamais de secret : seulement des chemins et des adresses."""
    p = os.environ.get("AEROLEX_CONFIG") or os.path.join(root or _ROOT, "aerolex.config.json")
    try:
        with open(p, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}
