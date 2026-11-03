"""Regle d'URL AeroLex — source unique de verite.
Doit rester STRICTEMENT identique a slugify() cote JS (dist/aerolex.js).
"""
import unicodedata, re

def slugify(terme: str) -> str:
    s = unicodedata.normalize('NFD', terme)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')  # accents
    s = s.lower()
    s = s.replace("'", '-').replace("'", '-').replace('/', '-')
    s = re.sub(r'[^a-z0-9]+', '-', s)   # virgules, espaces, points -> tiret
    s = re.sub(r'-+', '-', s).strip('-')
    return s or 'terme'

def build_slug_map(termes):
    """Retourne (map terme->slug, collisions). Desambiguise par suffixe -2, -3."""
    used, m, coll = {}, {}, []
    for t in sorted(termes):
        base = slugify(t)
        if base in used:
            coll.append((t, used[base], base))
            n = 2
            while f'{base}-{n}' in used: n += 1
            base = f'{base}-{n}'
        used[base] = t
        m[t] = base
    return m, coll
