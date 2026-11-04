#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serve_cors.py — Serveur statique d'un site AeroLex (dist/) avec CORS en liste FERMÉE, et API de suggestion (/api/suggest/).

POURQUOI (décision 2026-08-04)
──────────────────────────────
Les fichiers par mot (<lexique>/t/<slug>.json) vivent à UN SEUL endroit, le site qui publie le lexique ; les sites clients les appellent
en CROSS-ORIGIN (si le client héberge lui-même dist/, tout est same-origin : aucun CORS à configurer). Sans en-tête CORS,
\`python3 -m http.server\` fait échouer tout fetch cross-origin côté navigateur.

Pourquoi ici et pas dans un _headers statique ou un Worker : Access-Control-Allow-Origin n'accepte qu'UNE origine ou « * » ; avec une liste
il faut comparer l'Origin entrante et la renvoyer en ÉCHO — c'est dynamique. \`Vary: Origin\` est OBLIGATOIRE (sinon un cache resservirait la
réponse d'une origine autorisée à une autre). Un refus est un 403 JSON LISIBLE, pas une erreur CORS opaque.

Origines autorisées : $AEROLEX_CORS_ORIGINS (séparées par des virgules) ou aerolex.config.json -> serve.cors_origins ; AUCUNE par défaut
(comparaison EXACTE sur l'origine, jamais de motif ni de préfixe). Port : argument, sinon serve.port, sinon 8000. Dossier : --dir, sinon
serve.dir, sinon <projet>/dist. Chemins exposés en cross-origin : l'index de chaque lexique, <lexique>/t/*, <lexique>/lexicon.json.

Usage :
    python3 serve_cors.py [PORT] [--dir CHEMIN]
"""
from __future__ import annotations

import functools
import json
import os
import re
import sys

# API « Suggérer des termes » (scripts/suggest_api.py), montée sous /api/suggest/.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts"))
try:
    import suggest_api
except Exception as _e:                       # le site statique doit survivre à un bug de l'API
    suggest_api = None
    sys.stderr.write("suggest_api indisponible: %r\n" % (_e,))
import lexicon_env  # noqa: E402  (scripts/ est dans sys.path)
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

_HERE = os.path.dirname(os.path.abspath(__file__))
_SERVE = lexicon_env.install_config(_HERE).get("serve") or {}

# ── Liste FERMÉE d'origines autorisées ───────────────────────────────────────
# Comparaison EXACTE de l'origine (schéma + hôte + port) : pas de motif, pas de préfixe (« https://site.exemple.evil.com » ne matche rien).
ALLOWED_ORIGINS = frozenset(o.strip() for o in (os.environ.get("AEROLEX_CORS_ORIGINS", "").split(",") if os.environ.get("AEROLEX_CORS_ORIGINS")
                                                else _SERVE.get("cors_origins") or []) if o.strip())

# Seuls ces chemins sont exposés en cross-origin (le reste du site, pages HTML comprises, reste same-origin) :
# index du moteur de chaque lexique, fiches par mot, réglages du lexique.
CORS_PATH_RE = re.compile(r"^/(?:aerolex-(?:[a-z0-9-]+-)?index\.json|[a-z0-9-]+/t/.*|[a-z0-9-]+/lexicon\.json)$")

DEFAULT_PORT = int(_SERVE.get("port") or 8000)
DEFAULT_DIR = os.path.expanduser(_SERVE.get("dir") or os.path.join(_HERE, "dist"))


def _cors_eligible(path: str) -> bool:
    clean = path.split("?", 1)[0].split("#", 1)[0]
    return bool(CORS_PATH_RE.match(clean))


class CorsHandler(SimpleHTTPRequestHandler):
    server_version = "AeroLexStatic/1.0"

    # ── Écho conditionnel de l'origine ───────────────────────────────────────
    def _apply_cors(self) -> str:
        """Pose les en-têtes CORS si l'origine est autorisée.
        Retourne 'ok' | 'refuse' | 'same-origin'."""
        origin = self.headers.get("Origin")
        if not origin:
            return "same-origin"          # requête classique, rien à faire
        if not _cors_eligible(self.path):
            return "same-origin"          # chemin non exposé en cross-origin
        # Vary AVANT tout : la réponse dépend de l'Origin même en cas de refus.
        self.send_header("Vary", "Origin")
        if origin in ALLOWED_ORIGINS:
            # UNE seule origine renvoyée : celle qui a demandé.
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
            self.send_header("Access-Control-Max-Age", "86400")
            return "ok"
        return "refuse"

    def end_headers(self) -> None:
        # SimpleHTTPRequestHandler appelle end_headers() après ses send_header().
        if getattr(self, "_cors_done", False) is False:
            self._apply_cors()
            self._cors_done = True
        super().end_headers()

    def _refuse(self) -> None:
        """403 LISIBLE plutôt qu'une erreur CORS opaque."""
        origin = self.headers.get("Origin", "")
        body = json.dumps({
            "error": "origin_not_allowed",
            "message": "Cette origine n'est pas autorisee a lire le lexique AeroLex.",
            "origin": origin,
            "allowed": sorted(ALLOWED_ORIGINS),
        }, ensure_ascii=True).encode("utf-8")
        self.send_response(403)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Vary", "Origin")
        self._cors_done = True            # ne pas re-poser les en-têtes CORS
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _origin_refused(self) -> bool:
        origin = self.headers.get("Origin")
        return bool(origin) and _cors_eligible(self.path) and origin not in ALLOWED_ORIGINS

    def _api(self) -> bool:
        if suggest_api is not None and suggest_api.handles(self.path):
            suggest_api.serve(self)
            return True
        return False

    def do_POST(self) -> None:
        if not self._api():
            self.send_error(405, "POST non supporte ici")

    def do_GET(self) -> None:
        if self._api():
            return
        if self._origin_refused():
            self._refuse()
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        if self._origin_refused():
            self._refuse()
            return
        super().do_HEAD()

    def do_OPTIONS(self) -> None:
        """Préflight. Un GET simple n'en déclenche pas, mais on répond
        correctement pour ne pas dépendre de ce détail."""
        if self._origin_refused():
            self._refuse()
            return
        self.send_response(204)
        self.send_header("Content-Length", "0")
        allowed = self.headers.get("Access-Control-Request-Headers")
        if allowed:
            self.send_header("Access-Control-Allow-Headers", allowed)
        self.end_headers()               # end_headers() pose le CORS

    def log_message(self, fmt: str, *args) -> None:
        # Journal compact : le KeepAlive launchd tourne en continu.
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


def main() -> int:
    port = DEFAULT_PORT
    directory = DEFAULT_DIR
    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        if argv[i] == "--dir" and i + 1 < len(argv):
            directory = argv[i + 1]; i += 2; continue
        if argv[i].isdigit():
            port = int(argv[i]); i += 1; continue
        i += 1

    if not os.path.isdir(directory):
        sys.stderr.write("ERREUR: repertoire introuvable: %s\n" % directory)
        return 2

    handler = functools.partial(CorsHandler, directory=directory)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
    sys.stderr.write(
        "AeroLex static+CORS sur 127.0.0.1:%d  dir=%s\n  origines: %s\n  chemins CORS: %s\n"
        % (port, directory, ", ".join(sorted(ALLOWED_ORIGINS)) or "(aucune)", CORS_PATH_RE.pattern)
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
