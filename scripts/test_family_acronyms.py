#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_family_acronyms.py — ÉCHOUE si un sigle cité dans une liste d'une fiche
(famille, voir aussi) n'a pas son développé, dans le payload (dist/aero/t/<slug>.json,
lu par la popup) ET dans le HTML statique (dist/aero/<slug>.html).
Prérequis : build fait (build_pages.py + build_terms_json.py).
Lancer : python3 scripts/test_family_acronyms.py
"""
import json
import os
import sys
from html import escape

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(_ROOT, "data"), os.path.join(_ROOT, "scripts")]

from data_glossaire_full import GLOSSAIRE   # noqa: E402
from term_display import build_display_table, dev_label  # noqa: E402
from term_payload import PayloadContext     # noqa: E402

DIST = os.path.join(_ROOT, "dist", "aero")


def main():
    disp = build_display_table(GLOSSAIRE)
    sigles = {k for k, d in disp.items() if d["expansion"]}
    assert len(sigles) > 100, "détection des sigles anormalement basse"
    ctx = PayloadContext(GLOSSAIRE)
    bad, checked = [], 0
    for terme in ctx.termes_tries:
        slug = ctx.slug(terme)
        try:
            payload = json.load(open(os.path.join(DIST, "t", f"{slug}.json"), encoding="utf-8"))
            html = open(os.path.join(DIST, f"{slug}.html"), encoding="utf-8").read()
        except FileNotFoundError:
            bad.append((terme, "fichier de build manquant"))
            continue
        lists = [("famille", payload.get("famille_membres") or []),
                 ("voir aussi", payload.get("xrefs") or [])]
        for name, items in lists:
            for m in items:
                if m["t"] not in sigles:
                    continue
                checked += 1
                want = dev_label(disp[m["t"]])
                if m.get("dev") != want:
                    bad.append((terme, f"payload {name}: {m['t']} sans développé"))
                if f'<span class="dev">— {escape(want)}</span>' not in html:
                    bad.append((terme, f"html {name}: {m['t']} sans développé"))
    for b in bad[:40]:
        print("KO", *b)
    print(f"{checked} sigles en liste vérifiés, {len(bad)} KO")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
