#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_acronyms.py — ÉCHOUE si une entrée sigle/abréviation du lexique n'a pas de
développé affiché (règle de Louis : tout acronyme est développé sous le titre
de la fiche et dans l'index). Lancer : python3 scripts/test_acronyms.py
"""
import os
import re
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(_ROOT, "data"), os.path.join(_ROOT, "scripts")]

from data_glossaire_full import GLOSSAIRE            # noqa: E402
from term_display import build_display_table         # noqa: E402
from term_expansions import UNRESOLVED, CODEWORDS, NOT_ACRONYMS  # noqa: E402

_ABBR_DEF = re.compile(
    r"^(abréviation|abreviation|sigle|symbole|code |terme abrégé|diminutif|"
    r"kilo|mètres|litres|pieds|knot|foot|take-off|degré|indicateur de prob|"
    r"terme radio|maximum take-off|coordinated)", re.I)
_SHAPE = re.compile(r"^[A-Za-z0-9°/\-]{1,8}$")


def is_abbreviation(key, meta):
    """Heuristique de détection (indépendante du moteur d'affichage)."""
    if key in CODEWORDS or key in NOT_ACRONYMS:
        return False
    d = ((meta or {}).get("definition") or "").strip()
    if re.fullmatch(r"lf[a-z]{2}", key, re.I):
        return True                                   # codes OACI d'aérodrome
    if key.isupper() and len(key) >= 2 and not key.isdigit():
        return True
    if _SHAPE.match(key) and any(c.isupper() for c in key[1:]):
        return True                                   # Vref, inHg, Cd, T-VASIS…
    if (("/" in key and " " not in key and len(key) <= 9) or key == "°C"):
        return True                                   # unités ft/min, km/h, metar/taf
    if key.islower() and len(key) <= 4 and _ABBR_DEF.match(d):
        return True
    return False


def test_case_rule():
    """Règle de casse : un sigle n'est détecté/développé qu'en MAJUSCULES ou en casse exacte déclarée."""
    import suggest_core as core
    from term_display import expr_sigles
    ix = core.get_index("aero")
    errs = []
    t, _ = core.develop_acronyms("C'est un cas de nuage.", "silvagenitus", ix)
    if "(" in t:
        errs.append("« un cas de » développé : %s" % t)
    t, _ = core.develop_acronyms("La CAS est de 90 kt.", "silvagenitus", ix)
    if "CAS (Calibrated Airspeed" not in t:
        errs.append("« la CAS » non développé : %s" % t)
    t, _ = core.develop_acronyms("Cas particulier : la base est ouverte.", "silvagenitus", ix)
    if "(" in t:
        errs.append("« Cas »/« base » développés : %s" % t)
    t, _ = core.develop_acronyms("La Vy est de 70 kt.", "silvagenitus", ix)
    if "Vy (" not in t:
        errs.append("« Vy » non développé : %s" % t)
    table = build_display_table(GLOSSAIRE)
    ui = {}
    for k, v in table.items():
        if v["expansion"]:
            ui.setdefault(k.upper(), k)
    for lab in ("Ac cas", "cas d'urgence", "un cas de vol"):
        r_lab, items, _u = expr_sigles(lab, table, ui)
        if items or r_lab != lab:
            errs.append("libellé « %s » recasé/développé : %s %s" % (lab, r_lab, items))
    r_lab, items, _u = expr_sigles("carte vac", table, ui)
    if r_lab != "carte VAC" or not items:
        errs.append("libellé déclaré « carte vac » perdu : %s %s" % (r_lab, items))
    return errs


def main():
    table = build_display_table(GLOSSAIRE)
    missing = []
    nb = 0
    for k, meta in GLOSSAIRE.items():
        if not is_abbreviation(k, meta):
            continue
        nb += 1
        if k in UNRESOLVED:
            continue                                   # sens douteux, listé
        if not (table[k]["expansion"] or "").strip():
            missing.append(k)
    bad_title = [k for k, v in table.items()
                 if v["expansion"] and v["expansion"].strip().lower() == v["titre"].strip().lower()
                 and k not in ("CB", "hPa", "few")]
    ok = True
    for e in test_case_rule():
        ok = False
        print("❌ casse des sigles : %s" % e)
    if missing:
        ok = False
        print("❌ sigles sans développé (%d) : %s" % (len(missing), ", ".join(missing)))
    if bad_title:
        ok = False
        print("❌ développé identique au titre : %s" % ", ".join(bad_title))
    # Aucun développé ne doit être un fragment de définition tronqué/vide.
    print("%s %d abréviations détectées, %d sans développé, %d douteuses listées"
          % ("✅" if ok else "❌", nb, len(missing), len(UNRESOLVED)))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
