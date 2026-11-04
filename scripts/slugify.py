"""Regle d'URL AeroLex — source unique de verite.
Le slug est calcule UNIQUEMENT ici (Python) ; le JS lit les slugs deja calcules
(champ "sl" de aerolex-index.json, slugmap.json) : aucune re-implementation cote JS.

Regles (04/11/2026) :
  - translitteration des symboles (° -> degre, °C -> degre-celsius, % -> pourcent, θ -> theta...) ;
  - jamais de slug vide, d'une seule lettre, ni "terme"/"terme-N" : derive du premier
    developpe / de la premiere variante lisible ;
  - slugs RESERVES (index, suggest, search, slugmap, build-info, lexicon, schemas, t + tout
    fichier statique de dist/aero) : la fiche recoit le suffixe "-terme" (index -> index-terme) ;
  - l'ancien slug (legacy_slugify) est conserve en redirection (page HTML + _redirects du slugmap).
"""
import os
import re
import unicodedata

RESERVED_BASE = frozenset({"index", "suggest", "search", "slugmap", "build-info", "lexicon", "schemas", "t"})
RESERVED_SUFFIX = "terme"          # index -> index-terme
DEFAULT_DIST = os.path.join(os.environ.get("AEROLEX_LEXROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist", os.environ.get("AEROLEX_LEXICON") or __import__("lexicon_env").default_id())
GENERIC_RE = re.compile(r"^terme(-\d+)?$")

# Symboles -> mots (ordre : motifs longs d'abord)
_SYMBOLS = [
    ("°c", " degre celsius "), ("° c", " degre celsius "), ("°f", " degre fahrenheit "), ("° f", " degre fahrenheit "),
    ("°", " degre "), ("º", " degre "), ("%", " pourcent "), ("‰", " pour mille "),
    ("&", " et "), ("+", " plus "), ("±", " plus ou moins "), ("≥", " sup egal "), ("≤", " inf egal "),
    ("≈", " environ "), ("×", " fois "), ("÷", " sur "), ("√", " racine "), ("∆", " delta "), ("Δ", " delta "),
    ("θ", " theta "), ("α", " alpha "), ("β", " beta "), ("γ", " gamma "), ("δ", " delta "), ("λ", " lambda "),
    ("μ", " micro "), ("µ", " micro "), ("π", " pi "), ("ρ", " rho "), ("σ", " sigma "), ("φ", " phi "),
    ("ω", " omega "), ("Ω", " ohm "), ("œ", "oe"), ("æ", "ae"), ("ø", "o"), ("ß", "ss"),
    ("<", " inferieur "), (">", " superieur "), ("=", " egal "), ("€", " euro "), ("$", " dollar "),
]


def _translit(s: str) -> str:
    s = s.lower()
    for a, b in _SYMBOLS:
        s = s.replace(a, b)
    return s


def _ascii_slug(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")   # accents
    s = s.lower().replace("'", "-").replace("’", "-").replace("/", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def legacy_slugify(terme: str) -> str:
    """ANCIENNE regle (avant le 04/11/2026) : sert uniquement a calculer les redirections."""
    s = unicodedata.normalize("NFD", terme)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = s.replace("'", "-").replace("’", "-").replace("/", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "terme"


def slugify(terme: str) -> str:
    """Slug brut translittere ('' si rien d'exploitable ; voir slug_ok / build_slug_map)."""
    return _ascii_slug(_translit(terme))


def static_reserved(dist_dir=None) -> set:
    """Reserves : liste fixe + noms (sans extension) de tout fichier statique de dist/aero
    (hors fiches generees : le .html d'un terme n'est pas statique)."""
    res = set(RESERVED_BASE)
    if dist_dir and os.path.isdir(dist_dir):
        for f in os.listdir(dist_dir):
            stem, ext = os.path.splitext(f)
            if ext and ext != ".html":
                res.add(stem)
            elif not ext:
                res.add(f)
    return res


def slug_ok(slug: str) -> bool:
    return len(slug) >= 2 and not GENERIC_RE.match(slug) and bool(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug))


def _derive(terme: str, meta) -> str:
    """Slug de repli : premier developpe / premiere variante lisible."""
    meta = meta if isinstance(meta, dict) else {}
    cands = []
    try:
        from term_display import compute_entry
        cands.append(compute_entry(terme, meta)[1])        # developpe
    except Exception:
        pass
    cands += list(meta.get("variantes") or []) + list(meta.get("synonymes") or [])
    d = (meta.get("definition") or "").split(":", 1)
    if len(d) == 2 and len(d[0]) < 60:
        cands.append(d[0])
    for c in cands:
        s = slugify(c or "")
        if slug_ok(s):
            return s
    return "fiche-" + (_ascii_slug(terme) or "x")


def build_slug_map(termes, glossaire=None, dist_dir=None):
    """Retourne (map terme->slug, collisions). Desambiguise par suffixe -2, -3 (jamais 'terme-N')."""
    reserved = static_reserved(dist_dir or DEFAULT_DIST)
    used, m, coll = {}, {}, []
    for t in sorted(termes):
        base = slugify(t)
        if not slug_ok(base):
            base = _derive(t, (glossaire or {}).get(t))
        if base in reserved:
            base = base + "-" + RESERVED_SUFFIX
        if base in used:
            coll.append((t, used[base], base))
            n = 2
            while f"{base}-{n}" in used or f"{base}-{n}" in reserved:
                n += 1
            base = f"{base}-{n}"
        used[base] = t
        m[t] = base
    return m, coll


def build_redirects(terme_to_slug: dict, dist_dir=None) -> dict:
    """{ancien slug: nouveau slug} pour les fiches dont le slug a change avec la nouvelle regle.
    Pas de redirection si l'ancien slug est un fichier reserve (ex. index = la page d'index) ou le slug
    actuel d'une AUTRE fiche."""
    reserved = static_reserved(dist_dir or DEFAULT_DIST)
    current = set(terme_to_slug.values())
    legacy, used = {}, {}
    for t in sorted(terme_to_slug):                      # meme desambiguation qu'avant (suffixe -2, -3)
        b = legacy_slugify(t)
        if b in used:
            n = 2
            while f"{b}-{n}" in used:
                n += 1
            b = f"{b}-{n}"
        used[b] = t
        legacy[t] = b
    out = {}
    for t, old in legacy.items():
        new = terme_to_slug[t]
        if old != new and old not in reserved and old not in current:
            out[old] = new
    return dict(sorted(out.items()))

