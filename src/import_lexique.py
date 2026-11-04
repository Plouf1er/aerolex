#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_lexique.py — SYNCHRONISE data_glossaire_full.py (fiche complète servie par le
site) avec les sources éditables. Remise à niveau 2026-11 (ancienne version : elle
reconstruisait le full depuis zéro dans un format périmé et supprimait ~200 fiches v2).

Modèle de données actuel
------------------------
  data/data_glossaire_full.py   STOCK CANONIQUE des fiches (1 300+ termes : v1, lots v2,
                                ajouts manuels, séances). Les fiches existantes n'y sont
                                JAMAIS écrasées ni supprimées par ce script.
  data/data_glossaire.py        source d'entrée : fiches validées par « Suggérer des termes »
                                (scripts/suggest_core.py y insère les entrées, origine="suggest").
  data/lexique-filtre.txt       lexique brut du corpus. N'est plus une source de fiches :
                                les monomots ont été purgés exprès (284 termes) ; il ne sert
                                qu'avec --with-stubs.

Opération (fusion additive, idempotente)
  1. full existant  -> conservé tel quel (ordre, champs, ajouts faits directement dans le full).
  2. fiche de data_glossaire.py absente du full (clé exacte) -> ajoutée en fin de fichier
     (statut="redigee" par défaut, origine conservée). Alerte si sa forme normalisée est déjà
     couverte par une autre fiche (clés U variantes U synonymes) : doublon probable.
  3. --with-stubs (jamais par défaut) : termes de lexique-filtre.txt non couverts -> stubs
     « Fiche en construction. ».

Sécurité : SANS --write c'est un essai à blanc (aucune écriture) qui affiche le diff.
Avec --write l'écriture est atomique et n'a lieu que s'il y a un changement.
--check : essai à blanc + code retour 1 s'il y a un diff.
Le préambule (docstring) du full est conservé tel quel.

Usage : python3 src/import_lexique.py [--write] [--check] [--with-stubs] [--root DIR]
"""

import argparse
import difflib
import importlib.util
import os
import re
import sys
import tempfile
import types
import unicodedata
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PLACEHOLDER = "Fiche en construction."
START_MARK = "GLOSSAIRE = {\n"


# --------------------------------------------------------------------------
# Normalisation — identique à scripts/suggest_core.norm et au moteur de rendu
# --------------------------------------------------------------------------
def norm(s: str) -> str:
    """Minuscules, accents retirés, ponctuation neutralisée, espaces tassés."""
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^\w\s/+-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def read_lexique(path: Path):
    """Retourne [(terme, occurrences, nb_seances, origine)] (corpus | metier)."""
    entries, bloc = [], None
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
        if line.startswith("#") or bloc is None:
            continue
        parts = line.split("\t")
        terme = parts[0].strip()
        if not terme:
            continue
        occ = int(parts[1]) if len(parts) > 1 and parts[1].strip().isdigit() else 0
        nbs = int(parts[2]) if len(parts) > 2 and parts[2].strip().isdigit() else 0
        entries.append((terme, occ, nbs, bloc))
    return entries


def load_glossaire(path: Path):
    """Charge un data_glossaire*.py (stub de glos_utils injecté si besoin). -> (GLOSSAIRE dict, source texte)."""
    if "glos_utils" not in sys.modules:
        stub = types.ModuleType("glos_utils")
        stub.dev_mode = lambda *a, **k: False  # noqa: E731
        sys.modules["glos_utils"] = stub
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location("dg_" + path.stem, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.path.pop(0)
    return dict(getattr(mod, "GLOSSAIRE", {}))


def covered_forms(gloss: dict) -> set:
    """clés U variantes U synonymes, en forme normalisée."""
    forms = set()
    for k, v in gloss.items():
        forms.add(norm(k))
        for champ in ("variantes", "synonymes"):
            for x in v.get(champ, []) or []:
                forms.add(norm(x))
    forms.discard("")
    return forms


# --------------------------------------------------------------------------
# Sérialisation — format du full committé (repr Python, 4 espaces)
# --------------------------------------------------------------------------
def dump_entry(key: str, val: dict) -> str:
    lines = ["    %r: {" % key]
    for champ, v in val.items():
        lines.append("        %r: %r," % (champ, v))
    lines.append("    },")
    return "\n".join(lines) + "\n"


def split_preamble(text: str):
    i = text.index(START_MARK) + len(START_MARK)
    return text[:i]


def merge(full: dict, src: dict, lex=None):
    """Retourne (résultat dict ordonné, rapport dict). Ne modifie ni full ni src."""
    out = dict(full)  # ordre conservé
    rep = {"ajoutes_src": [], "doublons_probables": [], "src_divergents": [], "stubs": []}
    covered = covered_forms(out)
    for k, v in src.items():
        if k in out:
            if {c: x for c, x in v.items()} != {c: out[k].get(c) for c in v} and any(
                    out[k].get(c) != x for c, x in v.items() if c in out[k]):
                rep["src_divergents"].append(k)
            continue
        entry = dict(v)
        entry.setdefault("statut", "redigee")
        entry.setdefault("origine", "suggest")
        if norm(k) in covered:
            rep["doublons_probables"].append(k)
        out[k] = entry
        covered |= {norm(k)} | {norm(x) for c in ("variantes", "synonymes") for x in entry.get(c, []) or []}
        rep["ajoutes_src"].append(k)
    for terme, occ, nbs, origine in (lex or []):
        n = norm(terme)
        if not n or n in covered:
            continue
        out[terme] = {"definition": PLACEHOLDER, "categorie": "divers", "origine": origine,
                      "statut": "a_rediger", "occurrences": occ, "nb_seances": nbs}
        covered.add(n)
        rep["stubs"].append(terme)
    return out, rep


def render(preamble: str, gloss: dict) -> str:
    return preamble + "".join(dump_entry(k, v) for k, v in gloss.items()) + "}\n"


def atomic_write(path: Path, text: str):
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def run(root: Path, write=False, with_stubs=False, out=print):
    """Cœur testable. Retourne (changed: bool, rapport dict)."""
    data = root / "data"
    full_p, src_p, lex_p = data / "data_glossaire_full.py", data / "data_glossaire.py", data / "lexique-filtre.txt"
    for p in (full_p, src_p):
        if not p.exists():
            raise SystemExit("ERREUR: introuvable: %s" % p)
    old_text = full_p.read_text(encoding="utf-8")
    full, src = load_glossaire(full_p), load_glossaire(src_p)
    lex = read_lexique(lex_p) if with_stubs else None
    merged, rep = merge(full, src, lex)
    new_text = render(split_preamble(old_text), merged)
    changed = new_text != old_text
    out("IMPORT LEXIQUE -> data_glossaire_full.py  (%s)" % ("ECRITURE" if write else "essai à blanc"))
    out("  full existant ............ %d fiches (conservées telles quelles)" % len(full))
    out("  source data_glossaire.py . %d fiches" % len(src))
    out("  ajoutées depuis la source  %d %s" % (len(rep["ajoutes_src"]), rep["ajoutes_src"][:15]))
    if rep["doublons_probables"]:
        out("  ATTENTION doublons probables (forme normalisée déjà couverte): %s" % rep["doublons_probables"])
    if rep["src_divergents"]:
        out("  info: %d fiches de la source diffèrent du full (le full fait foi, non écrasé)" % len(rep["src_divergents"]))
    if with_stubs:
        out("  stubs lexique ajoutés .... %d" % len(rep["stubs"]))
    out("  total après fusion ....... %d" % len(merged))
    if changed:
        diff = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(),
                                         "full (actuel)", "full (après import)", lineterm="", n=1))
        out("  DIFF: %d lignes" % len(diff))
        for l in diff[:80]:
            out("    " + l[:160])
        if len(diff) > 80:
            out("    ... (%d lignes de plus)" % (len(diff) - 80))
    else:
        out("  DIFF = 0 : le full est déjà à jour.")
    if write and changed:
        atomic_write(full_p, new_text)
        out("  Écrit -> %s" % full_p)
    elif changed:
        out("  (rien écrit : relancer avec --write pour appliquer)")
    return changed, rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="écrit réellement data_glossaire_full.py")
    ap.add_argument("--check", action="store_true", help="essai à blanc, code retour 1 s'il y a un diff")
    ap.add_argument("--with-stubs", action="store_true", help="ajoute aussi les stubs du lexique brut (déconseillé)")
    ap.add_argument("--root", default=str(BASE), help="racine du projet (tests : dossier temporaire)")
    a = ap.parse_args(argv)
    changed, _ = run(Path(a.root), write=a.write and not a.check, with_stubs=a.with_stubs)
    return 1 if (a.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
