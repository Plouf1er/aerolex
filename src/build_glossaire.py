# -*- coding: utf-8 -*-
"""Génère le glossaire (plan §5.2 / F6) :

1. sessions/glossaire.html — index alphabétique consultable (ancres par lettre
   et par terme, lié depuis le sommaire de chaque séance et depuis index.html).
2. assets/glossaire-data.js — window.GLOSSAIRE_TERMS, dictionnaire consommé
   par l'overlay glossaire d'aero.js (clic sur un span .glos).

Usage : python3 build_glossaire.py
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import unicodedata

from data_familles import FAMILLES, rendu_famille, texte_famille
from data_glossaire import GLOSSAIRE
from data_metar_codes import METAR_FICHES
from glos_utils import wrap_glossaire
from svg_glossaire import get_schema

HERE = os.path.dirname(os.path.abspath(__file__))


def _asset_version() -> str:
    hsh = hashlib.sha256()
    for rel in ("assets/aero.css", "assets/aero.js", "assets/glossaire-data.js"):
        p = os.path.join(HERE, rel)
        try:
            with open(p, "rb") as f:
                hsh.update(f.read())
        except OSError:
            pass  # glossaire-data.js n'existe pas encore au premier run
    return hsh.hexdigest()[:10]


# Symboles qui n'ont AUCUN équivalent ASCII : sans translittération explicite,
# `_anchor` les efface et plusieurs fiches distinctes se retrouvent avec la
# même ancre (bug observé le 02/08/2026 : « ° » et « θ » produisaient tous deux
# l'ancre de repli "terme", donc un lien croisé vers θ atterrissait sur °).
# On les nomme au lieu de les supprimer. Toute nouvelle clé symbolique doit
# être ajoutée ici — `tests/test_collisions.py` échoue sinon.
_SYMBOLES_ASCII = {
    "°": "degre",
    "θ": "theta",
    "ρ": "rho",
    "Δ": "delta",
    "α": "alpha",
    "β": "beta",
    "%": "pourcent",
    "/": "-",
    "+": "plus",
    "≤": "inf-egal",
    "≥": "sup-egal",
}


def _anchor(terme: str) -> str:
    """Ancre HTML : ascii, minuscules, non-alnum -> tiret.

    Les symboles de `_SYMBOLES_ASCII` sont translittérés AVANT le décapage,
    sans quoi une clé purement symbolique s'effondre sur l'ancre de repli.
    """
    s = "".join(_SYMBOLES_ASCII.get(c, c) for c in terme)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "terme"


def _lettre(terme: str) -> str:
    c = unicodedata.normalize("NFKD", terme)[0].upper()
    return c if "A" <= c <= "Z" else "#"


# ============================================================
# Garde-fou §9ter.6 — tout sigle doit porter son développé
# ============================================================

def _est_sigle(terme: str) -> bool:
    """True si le terme est une suite d'initiales (QNH, METAR, GO/NO GO…).

    Critère : au moins 2 lettres, et TOUTES les lettres sont en majuscules.
    Les chiffres et séparateurs (PROB30, GO/NO GO) sont ignorés.
    """
    lettres = [c for c in terme if c.isalpha()]
    return len(lettres) >= 2 and all(c.isupper() for c in lettres)


_DEV_RE = re.compile(r"<em>.+?</em>", re.DOTALL)


def assert_sigles_developpes(glossaire: dict) -> None:
    """Build rouge si un sigle n'a pas son développé (plan §9ter.6).

    Convention retenue : le développé d'origine ouvre la définition, en
    <em>…</em>, suivi de la traduction française entre guillemets.
    Ex. : <em>METeorological Aerodrome Report</em> — « message d'observation… »
    """
    manquants = []
    for terme, v in glossaire.items():
        if not _est_sigle(terme):
            continue
        if v.get("a_rediger"):
            continue          # mode dev : le stub n'a par définition pas de def
        d = v.get("definition", "")
        if not _DEV_RE.search(d[:220]):
            manquants.append(terme)
    if manquants:
        raise SystemExit(
            "\n" + "=" * 64
            + "\n[BUILD ÉCHOUÉ] Sigles sans développé (plan §9ter.6)\n"
            + "=" * 64 + "\n"
            + "\n".join(f"  · {t}" for t in sorted(manquants))
            + "\n\nChaque entrée en initiales doit ouvrir sur son développé "
              "d'origine en <em>…</em> suivi de la traduction française.\n"
              "Ex. : \"<em>Terminal Aerodrome Forecast</em> — « prévision "
              "d'aérodrome ». …\"\n" + "=" * 64 + "\n"
        )


# ============================================================
# Liens croisés §9ter.7 — les termes cités dans une définition
# deviennent des liens vers leur propre fiche.
# ============================================================

def _liens_croises(terme_courant: str, definition: str, termes) -> str:
    """Wrappe dans la définition les autres termes du glossaire.

    Réutilise la mécanique éprouvée de glos_utils (nœuds texte uniquement,
    zones <em>/<code>/<a> préservées), puis convertit les spans .glos en
    <a class="glos-xref"> pointant sur l'ancre de la fiche.
    """
    if not definition:
        return ""          # mode dev : stub sans définition, rien à lier
    autres = [t for t in termes if t != terme_courant]
    wrapped = wrap_glossaire(definition, autres, once_per_term=True, park_em=True)

    def _to_link(m):
        cible = m.group(1)
        texte = m.group(2)
        return (
            f'<a class="glos-xref" href="#t-{_anchor(cible)}" '
            f'data-term="{html.escape(cible, quote=True)}">{texte}</a>'
        )

    return re.sub(
        r'<span class="glos"[^>]*data-term="([^"]+)"[^>]*>(.*?)</span>',
        _to_link,
        wrapped,
        flags=re.DOTALL,
    )


def assert_familles_connues(glossaire: dict) -> None:
    """Build rouge si une fiche déclare une famille qui n'existe pas.

    Sans ce garde-fou, une faute de frappe dans `"famille": "vitessse"`
    ferait disparaître silencieusement le tableau — exactement le genre de
    panne muette qui a coûté cher avec les variantes mortes.
    """
    inconnues = {
        (t, v["famille"])
        for t, v in glossaire.items()
        if v.get("famille") and v["famille"] not in FAMILLES
    }
    if inconnues:
        raise SystemExit(
            "\n" + "=" * 64
            + "\n[BUILD ÉCHOUÉ] Familles inconnues déclarées\n" + "=" * 64 + "\n"
            + "\n".join(f"  · {t} → famille {f!r}" for t, f in sorted(inconnues))
            + f"\n\nFamilles connues : {', '.join(sorted(FAMILLES))}\n"
            + "=" * 64 + "\n"
        )


def main() -> None:
    assert_sigles_developpes(GLOSSAIRE)
    assert_familles_connues(GLOSSAIRE)

    termes = sorted(GLOSSAIRE.items(), key=lambda kv: _anchor(kv[0]))
    toutes_cles = list(GLOSSAIRE.keys())

    # Liens croisés : calculés une fois, partagés page + overlay (§9ter.7)
    xrefs = {t: _liens_croises(t, v["definition"], toutes_cles) for t, v in termes}

    # ---------- 1. assets/glossaire-data.js ----------
    # "d"  : texte nu (repli / accessibilité)
    # "h"  : définition HTML avec liens croisés cliquables dans l'overlay
    # « Famille » (02/08/2026) : tableau partagé par toutes les fiches d'un même
    # système (les vitesses, les nuages, les composantes de vent…), rendu sur
    # CHAQUE fiche avec la ligne du terme courant en surbrillance. L'élève voit
    # le système, pas le mot isolé. Cf. data_familles.py.
    fam_html = {
        t: rendu_famille(v["famille"], t) if v.get("famille") else ""
        for t, v in termes
    }

    # "todo": 1 — mode dev, fiche non rédigée. aero.js s'en sert pour afficher
    # le badge « ⚠️ FICHE À RÉDIGER » et la carte au style d'alerte. Absent en
    # production (les stubs ne sont même pas injectés dans GLOSSAIRE).
    data_js = {
        t: {
            "d": re.sub(r"<[^>]+>", "", v["definition"]),  # texte nu pour l'overlay
            "h": xrefs[t] + fam_html[t],
            "c": v["categorie"],
            "a": _anchor(t),
            **({"s": get_schema(v["schema"], t)} if v.get("schema") and get_schema(v["schema"], t) else {}),
            **({"f": v["famille"]} if v.get("famille") else {}),
            **({"todo": 1} if v.get("a_rediger") else {}),
        }
        for t, v in termes
    }
    # §9quater.10 — fiches METAR/TAF (groupes cliquables du message brut).
    # N'écrase pas une entrée déjà présente dans GLOSSAIRE (ex. METAR, CAVOK) :
    # on enrichit la définition existante avec le tableau de catégorie.
    for t, v in METAR_FICHES.items():
        table_html = ""
        # La définition METAR_FICHES embarque déjà le tableau ; on l'utilise tel quel.
        def_html = v["definition"]
        if t in data_js:
            # Garde la def pédagogique + ajoute le tableau s'il n'y est pas
            if 'class="glos-metar-table"' not in data_js[t]["h"]:
                # extrait le tableau de la fiche METAR
                m = re.search(
                    r'(<table class="glos-metar-table">.*?</table>)',
                    def_html,
                    re.DOTALL,
                )
                if m:
                    data_js[t]["h"] = data_js[t]["h"] + m.group(1)
            continue
        data_js[t] = {
            "d": re.sub(r"<[^>]+>", "", def_html),
            "h": def_html,
            "c": v.get("categorie", "METAR"),
            "a": _anchor(t),
        }
    js_path = os.path.join(HERE, "assets", "glossaire-data.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* Généré par build_glossaire.py — ne pas éditer à la main */\n")
        f.write("window.GLOSSAIRE_TERMS = ")
        f.write(json.dumps(data_js, ensure_ascii=False, indent=1))
        f.write(";\n")
    ver = _asset_version()

    # ---------- 2. sessions/glossaire.html ----------
    lettres = sorted({_lettre(t) for t, _ in termes})
    cats = sorted({v["categorie"] for _, v in termes})

    doc = []
    doc.append("<!DOCTYPE html>")
    doc.append('<html lang="fr">')
    doc.append("<head>")
    doc.append('<meta charset="utf-8">')
    doc.append('<meta name="viewport" content="width=device-width, initial-scale=1">')
    doc.append("<title>Glossaire — Aero Coach PPL</title>")
    doc.append(f'<link rel="stylesheet" href="../assets/aero.css?v={ver}">')
    doc.append("</head>")
    doc.append('<body data-seance="aero-glossaire">')
    doc.append('<div class="dossier">')
    n_todo = sum(1 for _, v in termes if v.get("a_rediger"))
    _redigees = len(termes) - n_todo
    doc.append(
        '<div class="entete-seance"><h1>📖 Glossaire aéronautique</h1>'
        f"<p>{_redigees} termes · cliquables dans toutes les séances "
        "(soulignés en pointillés)</p>"
        + (
            f'<p class="glos-badge-todo">MODE DEV — {n_todo} fiche(s) à rédiger '
            "affichées en rouge</p>"
            if n_todo
            else ""
        )
        + "</div>"
    )

    doc.append('<nav class="sommaire"><h3>Index</h3><ul>')
    doc.append('<li><a href="index.html">← Séances</a></li>')
    for c in lettres:
        doc.append(f'<li><a href="#lettre-{c}">{c}</a></li>')
    doc.append("</ul></nav>")

    # Filtre par catégorie (pure ancre visuelle, pas de JS)
    doc.append(
        '<p style="margin:0 0 14px;color:#64748b;font-size:0.9rem">'
        "Catégories : " + " · ".join(cats) + "</p>"
    )

    courante = None
    for terme, v in termes:
        L = _lettre(terme)
        if L != courante:
            if courante is not None:
                doc.append("</section>")
            courante = L
            doc.append(f'<section class="bloc" id="lettre-{L}">')
            doc.append(f"<h2>{L}</h2>")
        todo = bool(v.get("a_rediger"))
        cls = "glos-entree glos-todo" if todo else "glos-entree"
        doc.append(f'<div class="{cls}" id="t-{_anchor(terme)}">')
        doc.append(
            f'<h3>{html.escape(terme)} '
            f'<span class="badge-rappel">{html.escape(v["categorie"])}</span></h3>'
        )
        if todo:
            # Mode dev uniquement : la fiche n'existe pas encore, on le dit.
            doc.append('<p class="glos-badge-todo">⚠️ FICHE À RÉDIGER</p>')
            doc.append(
                '<p>Terme repéré dans le lexique, définition pas encore écrite.</p>'
            )
        else:
            # définition : HTML inline autorisé (<strong>/<em>) — jamais ré-échappée.
            # Liens croisés §9ter.7 : les autres termes cités pointent sur leur fiche.
            doc.append(f"<p>{xrefs[terme]}</p>")
        # Tableau de famille : le système complet, ligne courante surlignée.
        if fam_html[terme]:
            doc.append(fam_html[terme])
        # §9quater lot 2B — schéma illustratif inline si le terme en déclare un
        _sch = v.get("schema")
        if _sch:
            _svg = get_schema(_sch, terme)
            if _svg:
                doc.append(f'<figure class="glos-schema">{_svg}</figure>')
        doc.append("</div>")
    doc.append("</section>")

    doc.append(
        '<p style="margin:24px 0;color:#64748b;font-size:0.9rem">'
        "Ce glossaire s'enrichit à chaque séance. Un terme manquant ? "
        "Signale-le à Arthur à la fin de la séance.</p>"
    )
    doc.append("</div>")  # dossier
    doc.append("</body>")
    doc.append("</html>")

    out = os.path.join(HERE, "sessions", "glossaire.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(doc))

    print(f"Écrit : {out} ({os.path.getsize(out)//1024} ko)")
    print(f"Écrit : {js_path} ({os.path.getsize(js_path)//1024} ko)")
    n_fam = sum(1 for _, v in termes if v.get("famille"))
    print(f"Termes : {len(termes)} · lettres : {len(lettres)} · catégories : {len(cats)}")
    if n_todo:
        print(
            f"⚠️  MODE DEV ACTIF (AERO_GLOS_DEV) — {n_todo} fiche(s) à rédiger "
            "injectée(s). NE PAS PUBLIER CE BUILD."
        )
    print(f"Familles : {len(FAMILLES)} · fiches rattachées à une famille : {n_fam}")


if __name__ == "__main__":
    main()
