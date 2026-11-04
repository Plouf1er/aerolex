#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
term_display.py — règles d'AFFICHAGE d'un terme (sigles, alias, famille, titre).

Source unique, consommée par term_payload.py (donc HTML + popup).
Aucune donnée inventée : tout vient des champs existants de GLOSSAIRE
(definition, variantes, synonymes). Un sigle sans développement dans ces
données reste sans développement (listé par audit_sigles()).

Règle de Louis (2026-11-03) : partout où un acronyme apparaît, il est défini
juste à côté ou en dessous.
"""
from __future__ import annotations

import re

from term_expansions import EXPANSIONS, GLOSS_FIX, NOT_ACRONYMS, lookup  # noqa: F401

STOP = {"of", "and", "the", "de", "des", "du", "la", "le", "les", "et", "d", "l",
        "à", "a", "in", "for", "to", "or", "ou", "en", "au", "aux", "un", "une"}


def _words(phrase: str):
    ws = [w for w in re.split(r"[\s'’\-/]+", phrase) if w]
    return [w for w in ws if w.lower() not in STOP] or ws


def initials_match(key: str, phrase: str, skip: bool = False) -> bool:
    """Strict : chaque mot (hors mots vides) fournit sa 1re lettre puis, au
    plus, des lettres suivantes dans l'ordre ; toutes les lettres du sigle
    sont consommées. 'KTAS' <- Knots True Airspeed ; 'EAS' <- Equivalent
    Airspeed ; 'cap' !<- 'Cap magnétique'."""
    k = re.sub(r"[^a-z0-9]", "", key.lower())
    ws = [re.sub(r"[^a-z0-9]", "", w.lower()) for w in _words(phrase)]
    ws = [w for w in ws if w]
    if not k or len(ws) < 1:
        return False

    def rec(ki, wi):
        if wi == len(ws):
            return ki == len(k)
        w = ws[wi]
        if skip and wi > 0 and ki < len(k) and rec(ki, wi + 1):
            return True   # mot omis dans le sigle (ex. EASA : Union)
        if ki >= len(k) or w[0] != k[ki]:
            return False
        ki += 1
        # prend 0..n lettres supplémentaires du mot (sous-suite)
        pos = 1
        if rec(ki, wi + 1):
            return True
        while pos < len(w) and ki < len(k):
            j = w.find(k[ki], pos)
            if j < 0:
                break
            ki += 1
            pos = j + 1
            if rec(ki, wi + 1):
                return True
        return False

    return rec(0, 0)


_KEY_OK = re.compile(r"^[A-Za-z][A-Za-z0-9]{1,7}$")


def _norm_alias(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def _prefix_expansion(definition: str):
    """'Calibrated Air Speed: vitesse ...' -> ('Calibrated Air Speed', reste)."""
    m = re.match(r"^([^:]{2,70}):\s+(.*)$", definition or "", re.S)
    if not m:
        return None, definition
    pre = m.group(1).strip()
    if len(pre.split()) > 8 or "." in pre or "," in pre.replace(", ", ", ") and len(pre) > 50:
        return None, definition
    return pre, m.group(2).strip()


def compute_entry(key: str, meta: dict):
    """Pour un terme : (titre, expansion|None, gloss|None, definition_sans_prefixe).

    Priorité : développé curaté (term_expansions.EXPANSIONS / code OACI) >
    développé calculé depuis les données. Voir _compute_auto() pour le calcul.
    """
    return compute_entry_full(key, meta)[:4]


def compute_entry_full(key: str, meta: dict):
    """(titre, expansion, gloss, definition_base, inline)."""
    if key in NOT_ACRONYMS:
        return key, None, None, ((meta or {}).get("definition") or "").strip(), False
    titre, exp, gloss, rest = _compute_auto(key, meta)
    cur = lookup(key, meta)
    if cur:
        exp, gloss, upper, inline = cur
        if upper:
            titre = key.upper()
        return titre, exp, gloss, rest, inline
    if exp and key in GLOSS_FIX:
        fe, fg = GLOSS_FIX[key]
        if fe:
            exp = fe
        if fg:
            gloss = fg
    return titre, exp, gloss, rest, True


def _compute_auto(key: str, meta: dict):
    """Calcul automatique (préfixe de définition / variantes à initiales).

    Un terme est un SIGLE si sa clé est courte alphanumérique ET qu'on trouve
    un développement dans les données (préfixe de définition ou variante dont
    les initiales correspondent), OU si la clé est déjà en majuscules.
    """
    definition = (meta.get("definition") or "").strip()
    variantes = [_norm_alias(x) for x in (meta.get("variantes") or [])]
    synonymes = [_norm_alias(x) for x in (meta.get("synonymes") or [])]
    aliases = [a for a in variantes + synonymes if a]

    if not _KEY_OK.match(key):
        return key, None, None, definition

    expansion = None
    rest = definition
    pre, reste = _prefix_expansion(definition)
    if pre and (initials_match(key, pre) or (key.isupper() and len(key) >= 2)
                or (key.islower() and len(key) >= 3 and len(_words(pre)) >= 3
                    and initials_match(key, pre, skip=True))):
        expansion, rest = pre, reste
        if rest:
            rest = rest[0].upper() + rest[1:]
    if expansion is None:
        for a in aliases:
            if " " in a and initials_match(key, a):
                expansion = a
                break

    titre = key
    if key.islower() and expansion is not None and expansion[0].isupper() \
            and len(_words(expansion)) >= 2 \
            and initials_match(key, expansion, skip=True):
        titre = key.upper()   # casse cohérente : un sigle s'affiche en majuscules
    if expansion is None:
        return titre, None, None, definition

    # Traduction/équivalent français : 1re variante qui n'est ni le sigle ni
    # le développement ni un autre sigle, et qui ne contient pas le sigle.
    gloss = None
    for a in aliases:
        al = a.lower()
        if al == key.lower() or al == expansion.lower():
            continue
        if re.fullmatch(r"[A-Za-z0-9]{2,8}", a) and (a.isupper() or len(a) <= 5 and " " not in a):
            continue   # autre sigle (KIAS, kias…)
        if key.lower() in re.split(r"\W+", al):
            continue
        if initials_match(key, a):
            continue
        if re.sub(r"\W", "", al) == re.sub(r"\W", "", expansion.lower()):
            continue
        gloss = a
        break
    return titre, expansion, gloss, rest


def dev_label(info):
    """Développé affichable d'un terme pour les listes (famille, voir aussi) :
    'Area Control Centre (centre de contrôle régional)' ou None si ce n'est pas
    un sigle. Source unique HTML + popup (transite par le payload)."""
    exp = (info or {}).get("expansion")
    if not exp:
        return None
    gl = info.get("gloss")
    return f"{exp} ({gl})" if gl else exp


def build_display_table(glossaire: dict):
    """{terme: {titre, expansion, gloss, definition_base}} pour tout le lexique."""
    out = {}
    for k, meta in glossaire.items():
        if not isinstance(meta, dict):
            meta = {}
        t, e, g, d, inl = compute_entry_full(k, meta)
        out[k] = {"titre": t, "expansion": e, "gloss": g, "definition_base": d,
                  "inline": inl}
    return out


# ── Alias propres ────────────────────────────────────────────────────────────
def clean_aliases(titre: str, key: str, aliases, expansion=None, gloss=None):
    """Dédoublonne (insensible à la casse/espaces), retire le titre, la clé,
    le développement et l'équivalent déjà affichés ailleurs dans la fiche."""
    seen = {titre.lower(), key.lower()}
    if expansion:
        seen.add(expansion.lower())
    if gloss:
        seen.add(gloss.lower())
    out = []
    for a in aliases:
        a = _norm_alias(a)
        if not a:
            continue
        k = a.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(a)
    return out


# ── Libellé de famille ───────────────────────────────────────────────────────
_FAM_WORDS = {
    "aerodromes": "aérodromes", "phraseologie": "phraséologie", "regles": "règles",
    "controles": "contrôlés", "parametres": "paramètres", "unites": "unités",
    "stabilite": "stabilité", "atmospherique": "atmosphérique", "atmospheriques": "atmosphériques", "trainee": "traînée",
    "meteo": "météo", "etat": "état", "helice": "hélice", "aeronautiques": "aéronautiques",
    "anemobarometriques": "anémobarométriques", "decrochages": "décrochages",
    "modeles": "modèles", "procedures": "procédures", "mesurees": "mesurées",
    "references": "références", "magnetiques": "magnétiques", "temperatures": "températures",
    "operationnelles": "opérationnelles", "visibilite": "visibilité", "verification": "vérification",
    "especes": "espèces", "magnetos": "magnétos", "meteorologiques": "météorologiques",
    "altimetriques": "altimétriques", "reglementes": "réglementés", "evolutions": "évolutions",
    "gyroscopiques": "gyroscopiques", "oaci": "OACI", "decision": "décision",
    "radionavigation": "radionavigation", "anemometre": "anémomètre",
}


_FAM_SPECIAL = {
    "facteurs_humains_physiologie": "Facteurs humains : physiologie",
    "codes_meteo_etat": "Codes météo : état",
}


def family_label(fam: str) -> str:
    if not fam:
        return ""
    if fam in _FAM_SPECIAL:
        return _FAM_SPECIAL[fam]
    toks = fam.split("_")
    pre = ""
    if toks[0] == "fh":
        pre = "Facteurs humains : "
        toks = toks[1:]
    words = [_FAM_WORDS.get(t, t) for t in toks]
    s = " ".join(words)
    if pre:
        return pre + s
    return s[:1].upper() + s[1:]


# ── Sigles dans le texte des définitions ─────────────────────────────────────
_TOKEN = re.compile(r"(?<![\w(])([A-Z][A-Z0-9]{1,6})(?![\w])")


def expand_acronyms(text: str, own_key: str, table: dict, upper_index: dict):
    """Ajoute « (Développement) » après la 1re occurrence de chaque sigle connu
    (développement présent dans les données) qui apparaît sans développement
    dans le texte. Retourne (texte, inconnus) ; inconnus = sigles du texte
    sans développement dans les données."""
    unknown = []
    done = set()
    own = own_key.lower()

    def rep(m):
        tok = m.group(1)
        k = tok.lower()
        if k == own or tok in done:
            return tok
        key = upper_index.get(tok)
        info = table.get(key) if key else None
        exp = info and info["expansion"]
        if exp and (info.get("inline") is False or exp.lower() == tok.lower()):
            done.add(tok)
            return tok
        if not exp:
            if tok not in unknown:
                unknown.append(tok)
            done.add(tok)
            return tok
        done.add(tok)
        if exp.lower() in text.lower():
            return tok
        # déjà suivi d'une parenthèse explicative ?
        tail = text[m.end():m.end() + 3]
        if tail.startswith(" ("):
            return tok
        return f"{tok} ({exp})"

    return _TOKEN.sub(rep, text), unknown

