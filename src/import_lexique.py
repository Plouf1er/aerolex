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
Avec --write : (1) sauvegarde horodatée de data/ et dist/ dans ~/Backups/aerolex/<date>/
(--backup-dir pour changer), (2) refus d'écrire si le nombre de fiches baisse (sauf
--allow-shrink), (3) écriture atomique seulement s'il y a un changement, (4) vérification
après écriture (aucune fiche perdue, nombre >= avant) sinon restauration automatique.
--check : essai à blanc + code retour 1 s'il y a un diff.
Le préambule (docstring) du full est conservé tel quel.

Règle « famille obligatoire » : chaque terme de tout lexique AeroLex a une famille (slug « divers » si
aucune ne convient). Avec --write, un terme AJOUTÉ sans famille est REFUSÉ (message listant les termes ;
rien n'est écrit). --default-famille-divers met explicitement dans « divers » les termes sans famille
(à ne PAS utiliser sur le vrai lexique tant que le classement des fiches orphelines n'est pas validé).
Les fiches existantes sans famille (héritage) ne bloquent pas : simple avertissement avec leur nombre.

Usage : python3 src/import_lexique.py [--write] [--check] [--with-stubs] [--default-famille-divers] [--root DIR]
"""

import argparse
import datetime
import difflib
import importlib.util
import os
import re
import shutil
import sys
import tempfile
import types
import unicodedata
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PLACEHOLDER = "Fiche en construction."
START_MARK = "GLOSSAIRE = {\n"

# Règles de RECONNAISSANCE portées par la source (data_glossaire.py) pour des fiches DÉJÀ présentes dans le
# full : contexte_requis, casse_sensible, homonyme. Avant le 2026-11-04 elles n'étaient jamais copiées (la
# fusion ignorait toute fiche existante) : l'index publié n'avait donc aucun champ ctx / cs / hom et le
# moteur n'appliquait aucune désambiguïsation. Copie ADDITIVE : jamais d'écrasement d'un champ déjà présent.
REGLES_RECONNAISSANCE = ("contexte_requis", "casse_sensible", "homonyme")


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
    rep = {"ajoutes_src": [], "doublons_probables": [], "src_divergents": [], "stubs": [], "regles_propagees": []}
    covered = covered_forms(out)
    for k, v in src.items():
        if k in out:
            for champ in REGLES_RECONNAISSANCE:
                if champ in v and champ not in out[k]:
                    out[k] = dict(out[k], **{champ: v[champ]})
                    rep["regles_propagees"].append((k, champ))
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


DIVERS = "divers"      # famille de repli (scripts/term_display.DIVERS_SLUG)


def sans_famille(gloss: dict) -> list:
    """Termes sans famille (absente, vide ou blanche)."""
    return [k for k, v in gloss.items() if not str(v.get("famille") or "").strip()]


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


DEFAULT_BACKUP_DIR = Path(os.environ.get("AEROLEX_BACKUP_DIR") or Path.home() / "Backups" / "aerolex")


def backup_project(root: Path, backup_dir: Path) -> Path:
    """Copie horodatée de data/ et dist/ (et src/) -> backup_dir/<AAAAmmjj-HHMMSS>/. Retourne le dossier."""
    dest = Path(backup_dir) / ("import-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    n = 1
    while dest.exists():
        n += 1
        dest = Path(backup_dir) / ("import-%s-%d" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"), n))
    dest.mkdir(parents=True)
    for sub in ("data", "dist", "src"):
        if (root / sub).is_dir():
            shutil.copytree(root / sub, dest / sub, symlinks=True)
    return dest


KEEP_BACKUPS = 20


def prune_backups(backup_dir: Path, keep: int = KEEP_BACKUPS, prefixes=("import-", "validate-")) -> list:
    """Ne garde que les <keep> plus récentes sauvegardes AUTOMATIQUES (dossiers import-*/validate-*).
    Les sauvegardes manuelles (autre nom) ne sont jamais touchées."""
    d = Path(backup_dir)
    if not d.is_dir():
        return []
    def is_auto(name):                     # import-AAAAmmjj-… ou <horodatage>-validate (créé par suggest_core)
        return name.startswith(prefixes) or re.search(r"-validate$", name)
    auto = sorted((x for x in d.iterdir() if x.is_dir() and is_auto(x.name)), key=lambda x: re.sub(r"^(import|validate)-", "", x.name))
    gone = auto[:-keep] if keep > 0 else auto
    for x in gone:
        shutil.rmtree(x, ignore_errors=True)
    return [x.name for x in gone]


def run(root: Path, write=False, with_stubs=False, out=print, backup_dir=None, allow_shrink=False, default_divers=False):
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
    old_orph = set(sans_famille(full))
    if default_divers:                     # explicite : les orphelins (ajoutés ou hérités) vont dans « divers »
        for k in sans_famille(merged):
            merged[k] = dict(merged[k], famille=DIVERS)
    new_orph = [k for k in sans_famille(merged) if k not in old_orph]      # ajoutés par cette fusion, sans famille
    rep["sans_famille_ajoutes"] = new_orph
    rep["sans_famille_existants"] = sorted(old_orph & set(sans_famille(merged)))
    new_text = render(split_preamble(old_text), merged)
    changed = new_text != old_text
    out("IMPORT LEXIQUE -> data_glossaire_full.py  (%s)" % ("ECRITURE" if write else "essai à blanc"))
    out("  full existant ............ %d fiches (conservées telles quelles)" % len(full))
    out("  source data_glossaire.py . %d fiches" % len(src))
    out("  ajoutées depuis la source  %d %s" % (len(rep["ajoutes_src"]), rep["ajoutes_src"][:15]))
    if rep["regles_propagees"]:
        out("  règles de reconnaissance copiées (contexte_requis / casse_sensible / homonyme) : %d champ(s) sur %d fiche(s)"
            % (len(rep["regles_propagees"]), len({k for k, _ in rep["regles_propagees"]})))
    if rep["doublons_probables"]:
        out("  ATTENTION doublons probables (forme normalisée déjà couverte): %s" % rep["doublons_probables"])
    if rep["src_divergents"]:
        out("  info: %d fiches de la source diffèrent du full (le full fait foi, non écrasé)" % len(rep["src_divergents"]))
    if with_stubs:
        out("  stubs lexique ajoutés .... %d" % len(rep["stubs"]))
    out("  total après fusion ....... %d" % len(merged))
    if default_divers:
        n_div = sum(1 for k, v in merged.items() if v.get("famille") == DIVERS and full.get(k, {}).get("famille") != DIVERS)
        out("  --default-famille-divers : %d fiche(s) mise(s) dans la famille « divers »" % n_div)
    if rep["sans_famille_existants"]:
        out("  AVERTISSEMENT : %d fiche(s) existante(s) sans famille (héritage, non bloquant ; classement en attente de validation)" % len(rep["sans_famille_existants"]))
    if new_orph:
        out("  %s %d terme(s) ajouté(s) SANS FAMILLE : %s" % ("ERREUR (bloquant en --write) :" if write else "ATTENTION (--write refusera) :", len(new_orph), ", ".join(new_orph)))
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
    if write and new_orph:
        raise SystemExit("REFUS: %d terme(s) à ajouter sans famille : %s. Règle AeroLex : chaque terme a une famille "
                         "(« divers » si aucune ne convient). Renseigner 'famille' dans data_glossaire.py, ou relancer avec "
                         "--default-famille-divers pour les mettre explicitement dans Divers. Rien écrit."
                         % (len(new_orph), ", ".join(new_orph)))
    if write and changed:
        if len(merged) < len(full) and not allow_shrink:
            raise SystemExit("REFUS: le nombre de fiches baisserait (%d -> %d). Rien écrit. --allow-shrink pour forcer."
                             % (len(full), len(merged)))
        bk = backup_project(root, Path(backup_dir) if backup_dir else DEFAULT_BACKUP_DIR)
        out("  Sauvegarde -> %s" % bk)
        prune_backups(Path(backup_dir) if backup_dir else DEFAULT_BACKUP_DIR)
        atomic_write(full_p, new_text)
        after = load_glossaire(full_p)
        lost = [k for k in full if k not in after]
        if (lost or len(after) < len(full)) and not allow_shrink:
            shutil.copy2(bk / "data" / full_p.name, full_p)
            raise SystemExit("ECHEC vérification (%d fiche(s) manquante(s): %s) : full restauré depuis %s"
                             % (len(lost), lost[:5], bk))
        out("  Écrit -> %s (vérifié : %d fiches, aucune perdue)" % (full_p, len(after)))
    elif changed:
        out("  (rien écrit : relancer avec --write pour appliquer)")
    return changed, rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--write", action="store_true", help="écrit réellement data_glossaire_full.py")
    ap.add_argument("--check", action="store_true", help="essai à blanc, code retour 1 s'il y a un diff")
    ap.add_argument("--with-stubs", action="store_true", help="ajoute aussi les stubs du lexique brut (déconseillé)")
    ap.add_argument("--default-famille-divers", action="store_true",
                    help="met explicitement dans la famille « divers » les termes sans famille (NE PAS utiliser sur le vrai lexique)")
    ap.add_argument("--allow-shrink", action="store_true", help="autorise une baisse du nombre de fiches")
    ap.add_argument("--backup-dir", default=None, help="dossier des sauvegardes (défaut ~/Backups/aerolex)")
    ap.add_argument("--root", default=str(BASE), help="racine du projet (tests : dossier temporaire)")
    a = ap.parse_args(argv)
    changed, _ = run(Path(a.root), write=a.write and not a.check, with_stubs=a.with_stubs,
                      backup_dir=a.backup_dir, allow_shrink=a.allow_shrink, default_divers=a.default_famille_divers)
    return 1 if (a.check and changed) else 0


if __name__ == "__main__":
    sys.exit(main())
