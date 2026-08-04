#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serve_cors.py — Serveur statique de aerolex.prunel.net avec CORS en liste FERMÉE.

POURQUOI CE FICHIER EXISTE (décision Louis, 2026-08-04 02h10)
─────────────────────────────────────────────────────────────
Les fichiers par mot (aero/t/<slug>.json) vivent à UN SEUL endroit :
aerolex.prunel.net. Les sites clients (atcf-ppl.prunel.net…) les appellent en
CROSS-ORIGIN. On ne duplique plus le lexique chez les clients — on s'est fait
piéger par deux copies divergentes de aero.js.

Sans en-tête CORS, `python3 -m http.server` (ce qui tournait avant) fait
échouer tout fetch cross-origin côté navigateur. D'où ce remplaçant minimal.

POURQUOI PAS UN _headers CLOUDFLARE PAGES NI UN WORKER
──────────────────────────────────────────────────────
1. `Access-Control-Allow-Origin` n'accepte qu'UNE origine ou `*`. Il ne prend
   PAS de liste. Avec 2 domaines autorisés il faut donc comparer l'`Origin`
   entrante et la renvoyer en ÉCHO si elle matche : c'est dynamique, un
   `_headers` statique ne peut pas le faire.
2. Mais aerolex.prunel.net n'est PAS servi par Cloudflare Pages : c'est un
   tunnel cloudflared vers ce serveur local (127.0.0.1:4140, cf.
   ~/.cloudflared/config.yml). Il n'y a donc pas de Pages où poser un
   `_headers`, et une Function/Worker serait une couche de plus à déployer
   pour un besoin que l'origine sait déjà satisfaire.
   → Le choix le plus simple qui marche pour 2 domaines : le faire ICI.

`Vary: Origin` est OBLIGATOIRE : sans lui, le cache (Cloudflare ou navigateur)
peut resservir la réponse d'un domaine autorisé à un autre domaine, avec la
mauvaise en-tête — donc soit une fuite, soit une panne aléatoire.

Un refus est un 403 JSON LISIBLE (pas une erreur CORS opaque) : quand ça
casse, on veut lire la cause, pas deviner.

Motifs génériques (*.exemple.com) : PAS maintenant, c'est spécifié dans
TODO-FEATURES.md §4quater. Aujourd'hui : 2 domaines en dur, propre et testé.

Usage :
    python3 serve_cors.py [PORT] [--dir CHEMIN]
"""
from __future__ import annotations

import functools
import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# ── Liste FERMÉE d'origines autorisées ───────────────────────────────────────
# Comparaison EXACTE sur le tuple (schéma, hôte). Pas de motif, pas de
# préfixe : 'https://atcf-ppl.prunel.net.evil.com' ne matche donc rien.
ALLOWED_ORIGINS = frozenset({
    "https://atcf-ppl.prunel.net",
    "https://aerolex.prunel.net",
})

# Seul ce préfixe est exposé en cross-origin. Le reste du site (pages HTML,
# index) reste same-origin : on n'ouvre que ce qui doit l'être.
CORS_PATH_PREFIXES = ("/aero/t/", "/aerolex-index.json", "/aero/lexicon.json")

DEFAULT_PORT = 4140
DEFAULT_DIR = "/Users/aprunel/.openclaw/workspace/projects/aerolex/dist"


def _cors_eligible(path: str) -> bool:
    clean = path.split("?", 1)[0].split("#", 1)[0]
    return any(clean.startswith(p) for p in CORS_PATH_PREFIXES)


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

    def do_GET(self) -> None:
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
        % (port, directory, ", ".join(sorted(ALLOWED_ORIGINS)), ", ".join(CORS_PATH_PREFIXES))
    )
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
