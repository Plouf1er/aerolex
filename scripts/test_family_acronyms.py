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
from term_display import build_display_table, dev_label, expr_sigles, expr_text  # noqa: E402
from term_payload import PayloadContext     # noqa: E402

DIST = os.path.join(_ROOT, "dist", os.environ.get("AEROLEX_LEXICON") or "aero")


def main():
    disp = build_display_table(GLOSSAIRE)
    sigles = {k for k, d in disp.items() if d["expansion"]}
    assert len(sigles) > 100 or (os.environ.get("AEROLEX_LEXICON") or "aero") != "aero", "détection des sigles anormalement basse"
    ctx = PayloadContext(GLOSSAIRE)
    bad, checked = [], 0
    n_expr = [0]
    # Détection indépendante : tout libellé multi-mots contenant un token
    # MAJUSCULES (>=2 lettres) résolu par la table doit avoir un développé.
    import re as _re
    upper_index = {k.upper(): k for k, v in disp.items() if v["expansion"]}
    for k, v in disp.items():
        if v["expansion"] or " " not in k.strip():
            continue
        for tok in _re.findall(r"[A-Za-z0-9]+", v["titre"]):
            if tok.isupper() and len(tok) >= 2 and tok in upper_index and tok not in {"GO", "NO", "UP", "PAN", "STOP"}:
                if not any(s == tok for s, _d in v["sigles_expr"]) and \
                        dev_label(disp[upper_index[tok]]).lower() not in v["titre"].lower():
                    bad.append((k, f"sigle {tok} dans l'expression sans développé"))
    for terme in ctx.termes_tries:
        slug = ctx.slug(terme)
        if slug == "index":
            # COLLISION connue : le terme « index » (masse et centrage) a pour slug « index »,
            # donc sa fiche est écrasée par la page d'index (dist/aero/index.html), qui n'est
            # pas une fiche et n'a pas de listes famille/voir aussi. À régler côté slugs.
            print("WARN slug 'index' : fiche du terme 'index' écrasée par index.html (non vérifiée ici)")
            continue
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
                    # expression contenant un sigle : texte développé du sigle
                    ex = disp[m["t"]]["expr"]
                    if ex:
                        n_expr[0] += 1
                        if m.get("expr") != ex:
                            bad.append((terme, f"payload {name}: expression '{m['t']}' sans développé du sigle"))
                        if f'<span class="dev">({escape(ex)})</span>' not in html:
                            bad.append((terme, f"html {name}: expression '{m['t']}' sans développé du sigle"))
                    continue
                checked += 1
                want = dev_label(disp[m["t"]])
                if m.get("dev") != want:
                    bad.append((terme, f"payload {name}: {m['t']} sans développé"))
                if f'<span class="dev">— {escape(want)}</span>' not in html:
                    bad.append((terme, f"html {name}: {m['t']} sans développé"))
    for b in bad[:40]:
        print("KO", *b)
    n_expr_total = sum(1 for v in disp.values() if v["sigles_expr"])
    unres = ctx.unresolved_sigles
    print(f"{checked} sigles en liste, {n_expr[0]} expressions en liste vérifiés, "
          f"{n_expr_total} expressions traitées, {len(unres)} sigles non résolus {sorted(unres)}, {len(bad)} KO")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
