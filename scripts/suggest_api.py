#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suggest_api.py — routes HTTP de « Suggérer des termes », montées par serve_cors.py
sous /api/suggest/ (le site est statique, servi par serve_cors.py derrière le tunnel
cloudflared : c'est le seul processus HTTP ; pas de second service ni de second port).

Accès :
  PUBLIC (sans jeton) : lexicons, parse, submit, job. Garde-fous de coût côté serveur : quota LLM par IP
  (30 termes/h, 300/j ; le cache et l'entonnoir gratuit sont illimités), plafond global 2 $/24 h (puis
  Qwopus local, puis refus poli), fichier <= 5 Mo, 300 termes/soumission, 20 analyses de fichier/h/IP.
  SESSION RELECTEUR (POST /login {password}, cookie HttpOnly/Secure/SameSite=Strict 30 j ; mot de passe hors dépôt ~/.aerolex-suggest-password ; 5 échecs/IP -> blocage 15 min) : revue (proposals, écartés, repêchage), validation
  (écriture dans le lexique + rebuild du site), stats.

  GET  /api/suggest/lexicons                    lexiques + familles (public)
  POST /api/suggest/parse?filename=x.pdf        corps = fichier brut -> termes extraits
  POST /api/suggest/submit   {domain,text|terms}  unitaire (réponse directe) ou lot (job)
  GET  /api/suggest/job/<id>                    progression / résultats
  GET  /api/suggest/proposals?status=pending|discarded&domain=aero
  POST /api/suggest/proposals/<id>/check        contrôle de cohérence (sans écrire)
  POST /api/suggest/proposals/<id>/rescue       repêche un terme écarté automatiquement
  POST /api/suggest/proposals/<id>/edit  {term?,data}
  POST /api/suggest/proposals/<id>/reject
  POST /api/suggest/validate {ids:[...],force?}  contrôle puis ajout à la source + rebuild
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


def route(method: str, path: str, headers, body: bytes, ip: str | None = None):
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
        authed = core.check_session(headers)
        if method == "GET" and p == "/session":
            return 200, {"relecteur": authed}
        if method == "POST" and p == "/login":
            d = json.loads(body.decode("utf-8") or "{}")
            ok, sid, wait = core.login(str(d.get("password", "")), ip or "?")
            if ok:
                return 200, {"ok": True, "_cookie": sid}
            if wait:
                return 429, {"error": "trop d'essais : réessayez dans %d min" % (-(-wait // 60)), "retry_after": wait}
            return 401, {"error": "mot de passe incorrect"}
        if method == "POST" and p == "/logout":
            core.logout(headers)
            return 200, {"ok": True, "_cookie": ""}
        # ── public (sans jeton) ──
        if method == "POST" and p == "/parse":
            if len(body) > core.MAX_UPLOAD_BYTES:
                return 413, {"error": "fichier trop gros (max 5 Mo)"}
            if ip and not authed:
                if core.rate_used(ip, "parse", 3600) >= core.PARSE_PER_IP_HOUR:
                    return 429, {"error": "trop de fichiers envoyés depuis cette connexion : réessayez plus tard"}
                core.rate_record(ip, "parse")
            return 200, core.parse_upload(q.get("filename", "x.txt"), body)
        if method == "POST" and p == "/submit":
            d = json.loads(body.decode("utf-8") or "{}")
            # le relecteur authentifié n'est pas soumis au quota par IP
            return 200, core.submit(d.get("domain", "aero"), text=d.get("text", ""), terms=d.get("terms"),
                                    ip=None if authed else (ip or "?"), full=authed)
        m = re.fullmatch(r"/job/([0-9a-f]{16})", p)
        if method == "GET" and m:
            v = core.job_view(m.group(1), full=authed)
            return (200, v) if v else (404, {"error": "job inconnu"})
        # ── protégé : revue / validation (écriture en production) ──
        if not authed:
            return 401, {"error": "connexion relecteur requise"}
        if method == "GET" and p == "/proposals":
            return 200, {"propositions": core.list_proposals(q.get("domain"), q.get("status", "pending"))}
        m = re.fullmatch(r"/proposals/(\d+)/(edit|reject|check|rescue)", p)
        if method == "POST" and m:
            pid = int(m.group(1))
            if m.group(2) == "check":
                return 200, core.check_proposal_id(pid)
            if m.group(2) == "rescue":
                return 200, core.rescue_proposal(pid)
            if m.group(2) == "reject":
                return 200, core.reject_proposal(pid)
            d = json.loads(body.decode("utf-8") or "{}")
            return 200, core.edit_proposal(pid, d.get("term"), d.get("data") or {})
        if method == "POST" and p == "/validate":
            d = json.loads(body.decode("utf-8") or "{}")
            ids = [int(i) for i in d.get("ids", [])]
            return 200, core.validate_proposals(ids, force=bool(d.get("force")))
        if method == "GET" and p == "/stats":
            return 200, core.stats()
        return 404, {"error": "route inconnue"}
    except core.ValidationError as e:
        return 409, {"error": str(e)}
    except KeyError as e:
        return 404, {"error": str(e).strip("'\"")}
    except (ValueError, json.JSONDecodeError) as e:
        return 400, {"error": str(e)}
    except Exception as e:  # ne jamais faire tomber le serveur statique
        sys.stderr.write("suggest_api erreur: %r\n" % (e,))
        return 500, {"error": "erreur interne : " + str(e)[:200]}


def client_ip(handler) -> str:
    """IP réelle du visiteur : derrière cloudflared (connexion locale), en-tête CF-Connecting-IP / X-Forwarded-For."""
    remote = handler.client_address[0]
    if remote in ("127.0.0.1", "::1", "::ffff:127.0.0.1"):
        h = handler.headers.get("CF-Connecting-IP") or (handler.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
        if h:
            return h
    return remote


def serve(handler) -> None:
    """Adaptateur BaseHTTPRequestHandler -> route()."""
    n = int(handler.headers.get("Content-Length") or 0)
    if n > core.MAX_UPLOAD_BYTES + 1024:
        status, out = 413, {"error": "corps trop gros"}
    else:
        body = handler.rfile.read(n) if n else b""
        status, out = route(handler.command, handler.path, handler.headers, body, client_ip(handler))
    ck = out.pop("_cookie", None) if isinstance(out, dict) else None
    data = json.dumps(out, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store")
    if ck is not None:
        base = "%s=%s; Path=/; HttpOnly; Secure; SameSite=Strict" % (core.COOKIE_NAME, ck)
        handler.send_header("Set-Cookie", base + ("; Max-Age=%d" % (core.SESSION_DAYS * 86400) if ck else "; Max-Age=0"))
    handler.send_header("Content-Length", str(len(data)))
    handler._cors_done = True       # l'API est same-origin : pas d'en-têtes CORS
    handler.end_headers()
    if handler.command != "HEAD":
        handler.wfile.write(data)
