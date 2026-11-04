#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measure_underlines.py — mesure les soulignements posés par le moteur (dist/aerolex.js) dans Chrome headless, page par page.

Sert à PROUVER qu'un changement du moteur / de l'index / de la configuration ne déplace aucun soulignement (écart = 0), ou à expliquer chaque écart.

  mesurer :   python3 scripts/measure_underlines.py measure --root DOSSIER_SITE --pages SOUS_DOSSIER --dist-link NOM --dist DIST --out mesure.json [--glob '*.html']
      DOSSIER_SITE   site hôte (ses pages référencent le moteur par le lien NOM, ex. ./aerolex-dist/aerolex.js)
      SOUS_DOSSIER   dossier des pages dans le site (ex. sessions)
      --dist         dossier dist/ à tester : le lien NOM est remplacé, dans une COPIE LÉGÈRE du site (liens symboliques), par ce dossier
  comparer :  python3 scripts/measure_underlines.py compare avant.json apres.json

Sortie de mesure : {page: [[classe, attributs data-*, texte], ...]} dans l'ordre du document. Aucun fichier du site n'est modifié.
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CHROMES = [os.environ.get("AEROLEX_CHROME") or "", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
           "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing", "google-chrome", "chromium", "chrome"]
SPAN = re.compile(r'<span class="(glos[^"]*)"([^>]*)>(.*?)</span>', re.S)


def chrome_bin() -> str:
    for c in CHROMES:
        if c and (os.path.exists(c) or shutil.which(c)):
            return c
    raise SystemExit("Chrome introuvable (variable AEROLEX_CHROME)")


def shadow_site(root: Path, pages: str, link: str, dist: Path, glob: str, tmp: Path) -> Path:
    site = tmp / "site"
    site.mkdir()
    for e in root.iterdir():
        if e.name != pages and not e.name.startswith("."):
            (site / e.name).symlink_to(e)
    pd = site / pages
    pd.mkdir()
    for f in sorted((root / pages).glob(glob)):
        if f.is_file():
            (pd / f.name).symlink_to(f)
    (pd / link).symlink_to(dist.resolve())
    return site


def dump(url: str, budget_ms: int) -> str:
    prof = tempfile.mkdtemp(prefix="alx-chrome-")
    try:
        p = subprocess.run([chrome_bin(), "--headless=new", "--disable-gpu", "--no-sandbox", "--no-first-run", "--user-data-dir=" + prof,
                            "--virtual-time-budget=%d" % budget_ms, "--dump-dom", url], capture_output=True, text=True, timeout=90)
        return p.stdout
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def spans(dom: str) -> list:
    return [[c, re.sub(r"\s+", " ", a).strip(), re.sub(r"<[^>]+>", "", t)] for c, a, t in SPAN.findall(dom)]


def measure(root, pages, link, dist, glob, out, jobs=4, budget=8000):
    tmp = Path(tempfile.mkdtemp(prefix="alx-measure-"))
    try:
        site = shadow_site(Path(root), pages, link, Path(dist), glob, tmp)
        h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site))
        h.log_message = lambda *a, **k: None
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        names = sorted(p.name for p in (site / pages).glob(glob) if p.is_file())
        base = "http://127.0.0.1:%d/%s/" % (srv.server_port, pages)

        def one(n):
            return n, spans(dump(base + n, budget))

        with ThreadPoolExecutor(jobs) as ex:
            res = dict(ex.map(one, names))
        srv.shutdown()
        Path(out).write_text(json.dumps(res, ensure_ascii=False), "utf-8")
        tot = sum(len(v) for v in res.values())
        print("%d page(s), %d soulignement(s) -> %s" % (len(res), tot, out))
        return res
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def compare(a_path, b_path) -> int:
    a, b = json.loads(Path(a_path).read_text("utf-8")), json.loads(Path(b_path).read_text("utf-8"))
    diffs = 0
    for page in sorted(set(a) | set(b)):
        x, y = a.get(page), b.get(page)
        if x != y:
            diffs += 1
            xs, ys = {json.dumps(i, ensure_ascii=False) for i in x or []}, {json.dumps(i, ensure_ascii=False) for i in y or []}
            print("ÉCART %s : %d -> %d  (-%d +%d)" % (page, len(x or []), len(y or []), len(xs - ys), len(ys - xs)))
            for i in list(xs - ys)[:5]:
                print("   - " + i)
            for i in list(ys - xs)[:5]:
                print("   + " + i)
    na, nb = sum(len(v) for v in a.values()), sum(len(v) for v in b.values())
    empty = [p for p, v in a.items() if not v]
    print("pages : %d | soulignements : %d -> %d | pages en écart : %d%s" % (len(a), na, nb, diffs, " | pages sans soulignement : %d" % len(empty) if empty else ""))
    return 1 if diffs else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure")
    m.add_argument("--root", required=True)
    m.add_argument("--pages", required=True)
    m.add_argument("--dist-link", required=True)
    m.add_argument("--dist", required=True)
    m.add_argument("--out", required=True)
    m.add_argument("--glob", default="*.html")
    m.add_argument("--jobs", type=int, default=4)
    c = sub.add_parser("compare")
    c.add_argument("avant")
    c.add_argument("apres")
    a = ap.parse_args()
    if a.cmd == "compare":
        sys.exit(compare(a.avant, a.apres))
    measure(a.root, a.pages, a.dist_link, a.dist, a.glob, a.out, a.jobs)


if __name__ == "__main__":
    main()
