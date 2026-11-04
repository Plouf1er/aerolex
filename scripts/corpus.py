# -*- coding: utf-8 -*-
"""
corpus.py — corpus de texte du contrôle « anti-ridicule » (simulation des soulignements, suggestion d'accents). FACULTATIF et CONFIGURABLE.

Le corpus est déclaré PAR LEXIQUE, dans la clé « corpus » de <racine>/data/lexicon.json (jamais publiée) :

    "corpus": {"type": "dir",     "path": "../mon-site/pages", "unit": "page"}         dossier local (.html .htm .txt .md), relatif à la racine du lexique
    "corpus": {"type": "sitemap", "url": "https://site.exemple/sitemap.xml", "max_pages": 40}   sitemap.xml du site hôte (index de sitemaps accepté)
    "corpus": {"type": "urls",    "urls": ["https://site.exemple/a", "https://site.exemple/b"]}
    "corpus": {"type": "upload"}                                                        échantillon de textes téléversé depuis la page « Suggérer »
    "corpus": {"type": "none"}                                                          aucun corpus (valeur par défaut)
    "corpus": "dossier"                                                                 raccourci de {"type": "dir", "path": "dossier"}

Sans corpus exploitable, la simulation passe en MODE GÉNÉRIQUE (suggest_rules.simulate) : définitions du lexique lui-même, liste d'homographes
français embarquée (scripts/resources/fr_homographes.json), règles de casse et d'unités du moteur. Ce n'est jamais une erreur : le cartouche
affiche « simulation générique (aucun corpus configuré) ».

Sitemap / URL : récupérés (http/https seulement, taille et durée bornées, même hôte que le sitemap) puis MIS EN CACHE
(<dossier suggest>/corpus-cache/<empreinte>/, 24 h par défaut ; en cas d'échec réseau le cache périmé sert). Téléversement : textes enregistrés
dans <dossier suggest>/corpus-upload/<lexique>/ (plafonds : 40 textes, 200 Ko chacun, 2 Mo en tout).

    python3 scripts/corpus.py <lexique> [--refresh] [--base DOSSIER]
"""
from __future__ import annotations

import hashlib
import html as _html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

DIR_EXT = (".html", ".htm", ".txt", ".md")
UPLOAD_MAX_FILES, UPLOAD_MAX_BYTES, UPLOAD_MAX_TOTAL = 40, 200_000, 2_000_000
FETCH_TIMEOUT, FETCH_BUDGET, FETCH_MAX_BYTES, DEFAULT_MAX_PAGES, DEFAULT_TTL_H = 8, 40, 2_000_000, 40, 24
USER_AGENT = "AeroLex-corpus/1.0 (simulation des soulignements)"

_TAGS = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")


def html_text(raw: str) -> str:
    raw = _TAGS.sub(" ", raw)
    raw = re.sub(r"</(p|div|li|h\d|tr|section|summary|details|ul|ol|table)\s*>|<br\s*/?>", "\n", raw, flags=re.I)
    return re.sub(r"[ \t\r\f\v]+", " ", _html.unescape(_TAG.sub(" ", raw)))


def _plain(name: str, raw: str) -> str:
    head = raw[:2000].lower()
    return html_text(raw) if name.lower().endswith((".html", ".htm")) or "<html" in head or "<body" in head else raw


def suggest_dir(root: Path) -> Path:
    return Path(os.environ.get("AEROLEX_SUGGEST_DIR") or (Path(root) / "data" / "suggest"))


class Corpus:
    """Source de texte d'un lexique. .texts() -> [(nom, texte)] ; .available = au moins un texte ; .describe() pour l'interface."""

    def __init__(self, kind: str = "none", label: str = "", unit: str = "document", spec: dict | None = None, root: Path | None = None,
                 lex_id: str = "", note: str = ""):
        self.kind, self.unit, self.spec, self.root, self.lex_id, self.note = kind, unit or "document", spec or {}, Path(root or "."), lex_id, note
        self.label = label or {"dir": "dossier local", "sitemap": "sitemap du site", "urls": "liste d'URL", "upload": "échantillon téléversé", "none": ""}.get(kind, kind)
        self.errors: list = []
        self._cache = None

    # ── identité (clé de cache des simulations) ──
    def key(self) -> tuple:
        if self.kind == "dir":
            d = self._dir()
            files = self._files(d) if d else []
            return ("dir", str(d), len(files), max((f.stat().st_mtime for f in files), default=0))
        if self.kind in ("sitemap", "urls"):
            m = self._cache_meta()
            return (self.kind, self._fp(), (m or {}).get("fetched_at", 0))
        if self.kind == "upload":
            d = self._upload_dir()
            files = sorted(d.glob("*.txt")) if d.is_dir() else []
            return ("upload", str(d), len(files), max((f.stat().st_mtime for f in files), default=0))
        return ("none",)

    def __str__(self) -> str:
        return "%s:%s" % (self.kind, self.key()[1:2])

    @property
    def available(self) -> bool:
        return bool(self.texts())

    @property
    def generic(self) -> bool:
        return not self.available

    # ── lecture ──
    def texts(self) -> list:
        key = self.key()
        if self._cache and self._cache[0] == key:
            return self._cache[1]
        out: list = []
        try:
            if self.kind == "dir":
                d = self._dir()
                for f in (self._files(d) if d else []):
                    try:
                        out.append((f.name, _plain(f.name, f.read_text("utf-8", "ignore"))))
                    except OSError:
                        continue
            elif self.kind in ("sitemap", "urls"):
                out = self._load_remote()
                key = self.key()
            elif self.kind == "upload":
                d = self._upload_dir()
                for f in (sorted(d.glob("*.txt")) if d.is_dir() else []):
                    try:
                        out.append((f.stem, f.read_text("utf-8", "ignore")))
                    except OSError:
                        continue
        except Exception as e:  # une source cassée ne casse jamais la simulation : mode générique
            self.errors.append(str(e)[:200])
            out = []
        self._cache = (key, out)
        return out

    def describe(self) -> dict:
        t = self.texts()
        d = {"type": self.kind, "label": self.label, "unit": self.unit, "documents": len(t), "generique": not t}
        notes = ([self.note] if self.note else []) + self.errors[:3]
        if self.kind == "dir" and not t and not self._dir():
            notes.append("dossier introuvable : %s" % self.spec.get("path"))
        if notes:
            d["notes"] = notes
        return d

    # ── dossier local ──
    def _dir(self) -> Path | None:
        p = self.spec.get("path")
        if not p:
            return None
        p = Path(os.path.expanduser(str(p)))
        p = p if p.is_absolute() else (self.root / p)
        return p if p.is_dir() else None

    @staticmethod
    def _files(d: Path) -> list:
        return sorted(f for f in d.iterdir() if f.is_file() and f.suffix.lower() in DIR_EXT)

    # ── téléversement ──
    def _upload_dir(self) -> Path:
        return suggest_dir(self.root) / "corpus-upload" / (self.lex_id or "main")

    # ── sitemap / URL : récupération + cache ──
    def _fp(self) -> str:
        return hashlib.sha1(json.dumps([self.kind, self.spec.get("url"), self.spec.get("urls"), self.spec.get("max_pages")], sort_keys=True).encode()).hexdigest()[:12]

    def _cache_dir(self) -> Path:
        return suggest_dir(self.root) / "corpus-cache" / self._fp()

    def _cache_meta(self) -> dict | None:
        try:
            return json.loads((self._cache_dir() / "meta.json").read_text("utf-8"))
        except (OSError, ValueError):
            return None

    def _load_remote(self) -> list:
        ttl = float(self.spec.get("cache_hours", DEFAULT_TTL_H)) * 3600
        meta = self._cache_meta()
        if not (meta and (time.time() - meta.get("fetched_at", 0)) < ttl):
            try:
                self._refresh()
            except Exception as e:
                self.errors.append("récupération impossible (%s)%s" % (str(e)[:120], " : cache périmé utilisé" if meta else ""))
        d = self._cache_dir()
        return [(f.stem, f.read_text("utf-8", "ignore")) for f in sorted(d.glob("*.txt"))] if d.is_dir() else []

    def refresh(self) -> dict:
        """Récupère de nouveau les pages (sitemap / URL) et réécrit le cache. -> {pages, erreurs}."""
        self.errors = []
        try:
            self._refresh()
        except Exception as e:
            self.errors.append("récupération impossible (%s)" % str(e)[:160])
        self._cache = None
        return {"pages": len(self.texts()), "erreurs": self.errors}

    def _refresh(self) -> None:
        urls = self._urls()
        if not urls:
            raise RuntimeError("aucune URL à récupérer")
        d = self._cache_dir()
        d.mkdir(parents=True, exist_ok=True)
        t0, ok, errs, keep = time.time(), 0, [], set()
        for i, u in enumerate(urls):
            if time.time() - t0 > FETCH_BUDGET:
                errs.append("durée maximale atteinte (%d pages sur %d)" % (ok, len(urls)))
                break
            try:
                raw = _fetch(u)
            except Exception as e:
                errs.append("%s : %s" % (u, str(e)[:80]))
                continue
            txt = _plain(u if re.search(r"\.(txt|md)$", u) else "x.html", raw)
            if len(txt.strip()) < 40:
                continue
            (d / ("%03d.txt" % i)).write_text(txt[:UPLOAD_MAX_BYTES], "utf-8")
            keep.add("%03d.txt" % i)
            ok += 1
        if ok == 0:
            raise RuntimeError("aucune page récupérée" + (" (%s)" % errs[0] if errs else ""))
        for f in d.glob("*.txt"):
            if f.name not in keep:
                f.unlink()
        (d / "meta.json").write_text(json.dumps({"fetched_at": time.time(), "pages": ok, "erreurs": errs[:10], "source": self.spec.get("url") or "urls"}), "utf-8")
        self.errors.extend(errs[:3])

    def _urls(self) -> list:
        mx = int(self.spec.get("max_pages") or DEFAULT_MAX_PAGES)
        if self.kind == "urls":
            urls = [str(u) for u in (self.spec.get("urls") or []) if str(u).startswith(("http://", "https://"))]
        else:
            urls = _sitemap_urls(str(self.spec.get("url") or ""), mx)
        return list(dict.fromkeys(urls))[:mx]


def _fetch(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        raise ValueError("schéma non autorisé")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml,text/plain;q=0.8"})
    with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as r:
        data = r.read(FETCH_MAX_BYTES + 1)
        if len(data) > FETCH_MAX_BYTES:
            raise ValueError("page trop grosse")
        cs = r.headers.get_content_charset() or "utf-8"
    return data.decode(cs, "ignore")


def _sitemap_urls(url: str, limit: int, depth: int = 0) -> list:
    """URL des pages d'un sitemap.xml (index de sitemaps : un niveau, même hôte)."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL de sitemap invalide")
    xml = _fetch(url)
    host = urllib.parse.urlparse(url).netloc
    locs = [_html.unescape(u) for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", xml, flags=re.S | re.I)]
    locs = [u for u in locs if urllib.parse.urlparse(u).netloc == host]
    if "<sitemapindex" in xml.lower() and depth < 1:
        out: list = []
        for sm in locs[:10]:
            try:
                out += _sitemap_urls(sm, limit, depth + 1)
            except Exception:
                continue
            if len(out) >= limit:
                break
        return out
    return [u for u in locs if not re.search(r"\.(jpg|jpeg|png|gif|svg|pdf|zip|xml|css|js)(\?|$)", u, re.I)]


# ── téléversement (échantillon de textes) ───────────────────────────────────
def save_upload(root: Path, lex_id: str, items: list, replace: bool = False) -> dict:
    """items = [{name, text}]. Plafonds : 40 textes, 200 Ko chacun, 2 Mo en tout. -> {documents, octets, ignores}."""
    d = suggest_dir(root) / "corpus-upload" / (lex_id or "main")
    d.mkdir(parents=True, exist_ok=True)
    if replace:
        for f in d.glob("*.txt"):
            f.unlink()
    have = sorted(d.glob("*.txt"))
    total = sum(f.stat().st_size for f in have)
    ignored = 0
    for it in items:
        name = re.sub(r"[^A-Za-z0-9._-]+", "-", str((it or {}).get("name") or "texte"))[:60].strip("-.") or "texte"
        text = str((it or {}).get("text") or "")
        if name.lower().endswith((".html", ".htm")) or "<body" in text[:2000].lower():
            text = html_text(text)
        text = text.strip()[:UPLOAD_MAX_BYTES]
        if len(text) < 20 or len(have) >= UPLOAD_MAX_FILES or total + len(text.encode()) > UPLOAD_MAX_TOTAL:
            ignored += 1
            continue
        stem = re.sub(r"\.(txt|md|html?)$", "", name, flags=re.I) or "texte"
        p, n = d / (stem + ".txt"), 1
        while p.exists():
            n += 1
            p = d / ("%s-%d.txt" % (stem, n))
        p.write_text(text, "utf-8")
        have.append(p)
        total += len(text.encode())
    return {"documents": len(have), "octets": total, "ignores": ignored}


def clear_upload(root: Path, lex_id: str) -> int:
    d = suggest_dir(root) / "corpus-upload" / (lex_id or "main")
    n = 0
    for f in (d.glob("*.txt") if d.is_dir() else []):
        f.unlink()
        n += 1
    return n


# ── résolution depuis la configuration d'un lexique ─────────────────────────
def resolve(root: Path, cfg: dict | None, lex_id: str = "") -> Corpus:
    """Corpus d'un lexique : $AEROLEX_CORPUS_DIR (surcharge explicite, dossier) > cfg['corpus'] (data/lexicon.json) > aucun. Jamais d'exception."""
    root = Path(root or ".")
    spec = (cfg or {}).get("corpus")
    if os.environ.get("AEROLEX_CORPUS_DIR"):       # surcharge explicite (tests, CI, copie de travail hors de l'arborescence de l'installation)
        spec = {"type": "dir", "path": os.environ["AEROLEX_CORPUS_DIR"], "unit": (spec.get("unit") if isinstance(spec, dict) else None) or "document",
                "label": (spec.get("label") if isinstance(spec, dict) else None) or ""}
    if isinstance(spec, str):
        spec = {"type": "dir", "path": spec}
    if not isinstance(spec, dict):
        spec = {}
    kind = str(spec.get("type") or ("dir" if spec.get("path") else "sitemap" if spec.get("url") else "urls" if spec.get("urls") else "")).lower()
    if kind not in ("dir", "sitemap", "urls", "upload", "none"):
        kind = "none"
    c = Corpus(kind, str(spec.get("label") or ""), str(spec.get("unit") or "document"), spec, root, lex_id)
    if kind in ("none", "upload"):                 # un échantillon téléversé sert dès qu'il existe
        up = Corpus("upload", "", str(spec.get("unit") or "document"), spec, root, lex_id)
        if up.texts():
            return up
    return c


def main(argv=None) -> int:
    import argparse
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import lexicon_env
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("lexique")
    ap.add_argument("--base", default=str(Path(__file__).resolve().parent.parent))
    ap.add_argument("--refresh", action="store_true", help="récupère de nouveau les pages (sitemap / URL)")
    a = ap.parse_args(argv)
    base = Path(a.base).resolve()
    root = base if lexicon_env.meta(str(base)).get("id") == a.lexique else base / "lexicons" / a.lexique
    c = resolve(root, lexicon_env.meta(str(root)), a.lexique)
    if a.refresh and c.kind in ("sitemap", "urls"):
        print(json.dumps(c.refresh(), ensure_ascii=False))
    print(json.dumps(c.describe(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
