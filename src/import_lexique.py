#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_lexique.py — Fusionne lexique-filtre.txt (1092 termes) avec les fiches
deja redigees de data_glossaire.py, et produit data_glossaire_full.py.

Chaque terme sans fiche recoit un stub `fiche en construction` :
    - definition = placeholder
    - statut     = "a_rediger"
    - origine    = "corpus" | "metier"

Regles appliquees :
  1. ANTI-DOUBLON par forme normalisee (minuscules, accents retires,
     ponctuation neutralisee) contre l'ensemble cles U variantes U synonymes.
     Un terme deja couvert n'ouvre PAS de seconde entree.
  2. COLLISIONS DE CASSE (VA/Va, VNE/Vne, ...) : la cle MAJUSCULE gagne,
     l'autre casse bascule en `variantes`. Rapport imprime.
  3. Les fiches deja redigees ne sont JAMAIS ecrasees.
  4. `origine` reporte sur chaque entree (corpus => lien actif ;
     metier => fiche sans lien actif).
"""

import re
import sys
import unicodedata
import importlib.util
from pathlib import Path
from collections import OrderedDict, defaultdict

BASE = Path(__file__).resolve().parent.parent
LEXIQUE = BASE / "data" / "lexique-filtre.txt"
GLOSSAIRE_SRC = BASE / "data" / "data_glossaire.py"
OUT = BASE / "data" / "data_glossaire_full.py"

PLACEHOLDER = "Fiche en construction."


# --------------------------------------------------------------------------
# Normalisation — doit rester IDENTIQUE a celle du moteur de rendu
# --------------------------------------------------------------------------
def norm(s: str) -> str:
    """Minuscules, accents retires, ponctuation neutralisee, espaces tasses."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^\w\s/+-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# --------------------------------------------------------------------------
# 1. Lecture du lexique filtre
# --------------------------------------------------------------------------
def read_lexique(path: Path):
    """Retourne [(terme, occurrences, nb_seances, origine)]."""
    entries = []
    bloc = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("### DANS LE CORPUS"):
            bloc = "corpus"
            continue
        if line.startswith("### METIER"):
            bloc = "metier"
            continue
        if line.startswith("#"):
            continue
        if bloc is None:
            continue
        parts = line.split("\t")
        terme = parts[0].strip()
        if not terme:
            continue
        occ = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 0
        nbs = int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0
        entries.append((terme, occ, nbs, bloc))
    return entries


# --------------------------------------------------------------------------
# 2. Chargement du glossaire redige
# --------------------------------------------------------------------------
def load_glossaire(path: Path):
    """Charge data_glossaire.py en neutralisant sa dependance a glos_utils.

    Le fichier source appelle `from glos_utils import dev_mode` dans une
    fonction d'injection propre au build Aero Coach. Le projet glossaire est
    autonome : on injecte un stub avant l'import plutot que de patcher la
    source (qui reste la propriete du projet cours).
    """
    import types

    if "glos_utils" not in sys.modules:
        stub = types.ModuleType("glos_utils")
        stub.dev_mode = lambda *a, **k: False  # noqa: E731
        sys.modules["glos_utils"] = stub

    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location("dg_src", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)

    return (
        dict(getattr(mod, "GLOSSAIRE", {})),
        dict(getattr(mod, "FICHES_A_REDIGER", {})),
    )


# --------------------------------------------------------------------------
# 3. Resolution des collisions de casse
# --------------------------------------------------------------------------
def resolve_case_collisions(gloss: dict):
    """VA/Va, VNE/Vne... -> garde la cle MAJUSCULE, l'autre passe en variante."""
    by_norm = defaultdict(list)
    for k in gloss:
        by_norm[norm(k)].append(k)

    report = []
    for n, keys in by_norm.items():
        if len(keys) < 2 or not n:
            continue
        # Collision de pure casse uniquement (memes lettres)
        if len({k.lower() for k in keys}) != 1:
            continue  # recouvrement semantique -> a arbitrer a la main
        winner = max(keys, key=lambda k: (sum(c.isupper() for c in k), k))
        for k in keys:
            if k == winner:
                continue
            entry = gloss[winner]
            variantes = list(entry.get("variantes", []))
            if k not in variantes:
                variantes.append(k)
            entry["variantes"] = variantes
            del gloss[k]
            report.append((k, winner))
    return report


# --------------------------------------------------------------------------
# 4. Index de couverture
# --------------------------------------------------------------------------
def covered_forms(gloss: dict) -> set:
    """cles U variantes U synonymes, en forme normalisee."""
    forms = set()
    for k, v in gloss.items():
        forms.add(norm(k))
        for champ in ("variantes", "synonymes"):
            for x in v.get(champ, []) or []:
                forms.add(norm(x))
    forms.discard("")
    return forms


# --------------------------------------------------------------------------
# 5. Serialisation
# --------------------------------------------------------------------------
def dump_entry(key: str, val: dict) -> str:
    def esc(s):
        return (
            str(s)
            .replace("\\", "\\\\")
            .replace('"', '\\"')
            .replace("\n", "\\n")
        )

    lines = [f'    "{esc(key)}": {{']
    for champ in (
        "definition", "categorie", "origine", "statut",
        "occurrences", "nb_seances",
        "variantes", "synonymes", "xrefs",
        "contexte_requis", "schema", "lien",
    ):
        if champ not in val:
            continue
        v = val[champ]
        if isinstance(v, (list, tuple)):
            if not v:
                continue
            items = ", ".join(f'"{esc(x)}"' for x in v)
            lines.append(f'        "{champ}": [{items}],')
        elif isinstance(v, bool):
            lines.append(f'        "{champ}": {v},')
        elif isinstance(v, (int, float)):
            lines.append(f'        "{champ}": {v},')
        else:
            lines.append(f'        "{champ}": "{esc(v)}",')
    lines.append("    },")
    return "\n".join(lines)


def main():
    if not LEXIQUE.exists():
        sys.exit(f"ERREUR: lexique introuvable: {LEXIQUE}")
    if not GLOSSAIRE_SRC.exists():
        sys.exit(f"ERREUR: glossaire introuvable: {GLOSSAIRE_SRC}")

    lex = read_lexique(LEXIQUE)
    gloss, fiches_a_rediger = load_glossaire(GLOSSAIRE_SRC)
    n_redigees = len(gloss)

    # -- collisions de casse
    collisions = resolve_case_collisions(gloss)

    # -- marquer les fiches deja redigees
    for k, v in gloss.items():
        v.setdefault("statut", "redigee")
        v.setdefault("origine", "corpus")

    # -- injecter FICHES_A_REDIGER (17 termes deja identifies)
    covered = covered_forms(gloss)
    n_from_far = 0
    for k, v in fiches_a_rediger.items():
        if norm(k) in covered:
            continue
        entry = dict(v) if isinstance(v, dict) else {}
        entry.setdefault("definition", PLACEHOLDER)
        entry.setdefault("categorie", "divers")
        entry["statut"] = "a_rediger"
        entry.setdefault("origine", "corpus")
        gloss[k] = entry
        covered.add(norm(k))
        n_from_far += 1

    # -- injecter le lexique
    added, skipped = 0, 0
    stats = defaultdict(int)
    for terme, occ, nbs, origine in lex:
        n = norm(terme)
        if not n or n in covered:
            skipped += 1
            continue
        gloss[terme] = {
            "definition": PLACEHOLDER,
            "categorie": "divers",
            "origine": origine,
            "statut": "a_rediger",
            "occurrences": occ,
            "nb_seances": nbs,
        }
        covered.add(n)
        added += 1
        stats[origine] += 1

    # -- tri : alphabetique sur forme normalisee
    ordered = OrderedDict(sorted(gloss.items(), key=lambda kv: (norm(kv[0]), kv[0])))

    total = len(ordered)
    n_red = sum(1 for v in ordered.values() if v.get("statut") == "redigee")
    n_att = total - n_red

    header = f'''# -*- coding: utf-8 -*-
"""
data_glossaire_full.py — GENERE par src/import_lexique.py. NE PAS EDITER A LA MAIN.

Fusion du lexique aero filtre ({len(lex)} termes) et des fiches redigees.

  Total entrees ............ {total}
  Fiches redigees .......... {n_red}
  Fiches en construction ... {n_att}

  origine="corpus" -> le terme apparait dans le corpus => LIEN ACTIF
  origine="metier" -> vocabulaire aero standard absent du corpus
                      => fiche consultable, PAS de lien actif

  statut="redigee"    -> definition reelle
  statut="a_rediger"  -> affiche "Fiche en construction."

Pour rediger une fiche : l'ecrire dans data_glossaire.py (source manuelle),
puis relancer src/import_lexique.py. Ce fichier est ecrase a chaque run.
"""

PLACEHOLDER = "{PLACEHOLDER}"

GLOSSAIRE = {{
'''

    body = "\n".join(dump_entry(k, v) for k, v in ordered.items())
    footer = "\n}\n"

    OUT.write_text(header + body + footer, encoding="utf-8")

    # -- rapport
    print("=" * 62)
    print("IMPORT LEXIQUE -> GLOSSAIRE")
    print("=" * 62)
    print(f"  Lexique lu ................. {len(lex)} termes")
    print(f"    - corpus ................. {sum(1 for e in lex if e[3]=='corpus')}")
    print(f"    - metier ................. {sum(1 for e in lex if e[3]=='metier')}")
    print(f"  Fiches redigees (source) ... {n_redigees}")
    if collisions:
        print(f"  Collisions de casse fusionnees ... {len(collisions)}")
        for loser, winner in collisions:
            print(f"      {loser!r} -> variante de {winner!r}")
    print(f"  Ajoutes depuis FICHES_A_REDIGER .. {n_from_far}")
    print(f"  Ajoutes depuis le lexique ........ {added}")
    print(f"    - corpus ....................... {stats['corpus']}")
    print(f"    - metier ....................... {stats['metier']}")
    print(f"  Deja couverts (ignores) .......... {skipped}")
    print("-" * 62)
    print(f"  TOTAL ENTREES .................... {total}")
    print(f"    redigees ....................... {n_red}")
    print(f"    en construction ................ {n_att}")
    print(f"  Ecrit -> {OUT}")
    print("=" * 62)


if __name__ == "__main__":
    main()
