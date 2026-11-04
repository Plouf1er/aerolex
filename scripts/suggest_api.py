#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suggest_api.py — routes HTTP de « Suggérer des termes », montées par serve_cors.py
sous /api/suggest/ (le site est statique, servi par serve_cors.py derrière le tunnel
cloudflared : c'est le seul processus HTTP ; pas de second service ni de second port).

Protection : jeton (en-tête X-Suggest-Token) sur TOUT sauf GET /api/suggest/lexicons.
Le jeton vit hors dépôt (~/.aerolex-suggest-token, 0600) ; soumission, revue et
validation exigent le même jeton -> pas d'abus de coût LLM sur le site public.

  GET  /api/suggest/lexicons                    lexiques + familles (public)
  POST /api/suggest/parse?filename=x.pdf        corps = fichier brut -> termes extraits
  POST /api/suggest/submit   {domain,text|terms}  unitaire (réponse directe) ou lot (job)
  GET  /api/suggest/job/<id>                    progression / résultats
  GET  /api/suggest/proposals?status=pending&domain=aero
  POST /api/suggest/proposals/<id>/edit  {term?,data}
  POST /api/suggest/proposals/<id>/reject
  POST /api/suggest/validate {ids:[...]}        ajout à la source + rebuild
  GET  /api/suggest/stats
"""
from __future__ import annotations

import json
import re
import sys
from urllib.parse import urlparse, parse_qs

import suggest_core as core

PREFIX = "/api/suggest"


def handles(path: str) -> bool:
    return path.split("?", 1)[0].startswith(PREFIX + "/") or path.split("?", 1)[0] == PREFIX


def route(method: str, path: str, headers, body: bytes):
    """-> (status, dict). Pure (testable sans socket)."""
    u = urlparse(path)
    p = u.path[len(PREFIX):].rstrip("/") or "/"
    q = {k: v[0] for k, v in parse_qs(u.query).items()}
    try:
        if method == "GET" and p == "/lexicons":
            out = []
            for k, cfg in core.LEXICONS.items():
                idx = core.get_index(k)
                out.append({"id": k, "label": cfg["label"], "familles": idx.families, "termes": len(idx.glossaire)})
            return 200, {"lexiques": out, "max_termes": core.MAX_TERMS_PER_SUBMISSION}
        if not core.check_token(headers.get("X-Suggest-Token")):
            return 401, {"error": "jeton manquant ou invalide"}
        if method == "POST" and p == "/parse":
            if len(body) > core.MAX_UPLOAD_BYTES:
                return 413, {"error": "fichier trop gros"}
            r = core.parse_upload(q.get("filename", "x.txt"), body)
            return 200, r
        if method == "POST" and p == "/submit":
            d = json.loads(body.decode("utf-8") or "{}")
            return 200, core.submit(d.get("domain", "aero"), text=d.get("text", ""), terms=d.get("terms"))
        m = re.fullmatch(r"/job/([0-9a-f]{16})", p)
        if method == "GET" and m:
            v = core.job_view(m.group(1))
            return (200, v) if v else (404, {"error": "job inconnu"})
        if method == "GET" and p == "/proposals":
            return 200, {"propositions": core.list_proposals(q.get("domain"), q.get("status", "pending"))}
        m = re.fullmatch(r"/proposals/(\d+)/(edit|reject)", p)
        if method == "POST" and m:
            pid = int(m.group(1))
            if m.group(2) == "reject":
                return 200, core.reject_proposal(pid)
            d = json.loads(body.decode("utf-8") or "{}")
            return 200, core.edit_proposal(pid, d.get("term"), d.get("data") or {})
        if method == "POST" and p == "/validate":
            d = json.loads(body.decode("utf-8") or "{}")
            ids = [int(i) for i in d.get("ids", [])]
            return 200, core.validate_proposals(ids)
        if method == "GET" and p == "/stats":
            return 200, core.stats()
        return 404, {"error": "route inconnue"}
    except KeyError as e:
        return 404, {"error": str(e).strip("'\"")}
    except (ValueError, json.JSONDecodeError) as e:
        return 400, {"error": str(e)}
    except Exception as e:  # ne jamais faire tomber le serveur statique
        sys.stderr.write("suggest_api erreur: %r\n" % (e,))
        return 500, {"error": "erreur interne : " + str(e)[:200]}


def serve(handler) -> None:
    """Adaptateur BaseHTTPRequestHandler -> route()."""
    n = int(handler.headers.get("Content-Length") or 0)
    if n > core.MAX_UPLOAD_BYTES + 1024:
        status, out = 413, {"error": "corps trop gros"}
    else:
        body = handler.rfile.read(n) if n else b""
        status, out = route(handler.command, handler.path, handler.headers, body)
    data = json.dumps(out, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    handler.send_header("Content-Length", str(len(data)))
    handler._cors_done = True       # l'API est same-origin : pas d'en-têtes CORS
    handler.end_headers()
    if handler.command != "HEAD":
        handler.wfile.write(data)
