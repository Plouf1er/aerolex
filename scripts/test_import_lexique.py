#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_import_lexique.py — non-régression de src/import_lexique.py.
Rejoue le script dans un dossier TEMPORAIRE et vérifie : diff = 0 contre le full réel
(mêmes termes, définitions, variantes, tous champs), essai à blanc sans écriture,
ajouts de la source / du full préservés, idempotence, jamais d'écriture du full réel.
Lancer : python3 scripts/test_import_lexique.py
"""
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import import_lexique as I  # noqa: E402

REAL_FULL = ROOT / "data" / "data_glossaire_full.py"
SCRIPT = ROOT / "src" / "import_lexique.py"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def clone(tmp: Path) -> Path:
    (tmp / "data").mkdir(parents=True)
    for f in ("data_glossaire.py", "data_glossaire_full.py", "lexique-filtre.txt"):
        shutil.copy(ROOT / "data" / f, tmp / "data" / f)
    return tmp


def cli(root, *args):
    return subprocess.run([sys.executable, str(SCRIPT), "--root", str(root), "--backup-dir", str(root.parent / "bk"), *args],
                          capture_output=True, text=True, timeout=120)


def compare(a: dict, b: dict):
    probs = []
    for k in sorted(set(a) | set(b)):
        if k not in a:
            probs.append("en trop: %r" % k)
        elif k not in b:
            probs.append("manquant: %r" % k)
        elif a[k] != b[k]:
            probs.append("différent: %r" % k)
    return probs


def main():
    real_hash = sha(REAL_FULL)
    real = I.load_glossaire(REAL_FULL)
    n_before = len(real)
    ko = []

    with tempfile.TemporaryDirectory() as t:
        tmp = clone(Path(t) / "p")
        full_tmp = tmp / "data" / "data_glossaire_full.py"
        h0 = sha(full_tmp)

        # 1. essai à blanc par défaut : diff = 0, rien écrit
        r = cli(tmp)
        assert r.returncode == 0, r.stderr
        if "DIFF = 0" not in r.stdout:
            ko.append("dry-run: diff non nul\n" + r.stdout)
        if sha(full_tmp) != h0:
            ko.append("dry-run a modifié le full")

        # 2. --write : sortie identique (termes, définitions, variantes, tous champs) au full réel
        r = cli(tmp, "--write")
        assert r.returncode == 0, r.stderr
        probs = compare(real, I.load_glossaire(full_tmp))
        if probs:
            ko.append("diff != 0 après --write: %s" % probs[:10])
        if len(I.load_glossaire(full_tmp)) != n_before:
            ko.append("nombre de fiches changé")
        if sha(full_tmp) != h0:
            ko.append("octets du full changés alors qu'il n'y a rien à fusionner")

        # 3. ajout dans la source (suggest) + ajout direct dans le full : tous deux préservés
        src_tmp = tmp / "data" / "data_glossaire.py"
        txt = src_tmp.read_text(encoding="utf-8")
        i = txt.index("GLOSSAIRE = {")
        j = txt.index("\n}", i)
        txt = txt[:j] + "\n    'zz terme suggest': {'definition': 'def suggest', 'categorie': 'X', 'origine': 'suggest'},\n" + txt[j + 1:]
        src_tmp.write_text(txt, encoding="utf-8")
        ft = full_tmp.read_text(encoding="utf-8")
        ft = ft[:ft.rindex("}")] + "    'zz ajout direct': {\n        'definition': 'def directe',\n        'categorie': 'X',\n        'statut': 'redigee',\n    },\n}\n"
        full_tmp.write_text(ft, encoding="utf-8")
        r = cli(tmp)
        if "zz terme suggest" not in r.stdout:
            ko.append("dry-run n'annonce pas l'ajout suggest")
        cli(tmp, "--write")
        g = I.load_glossaire(full_tmp)
        if g.get("zz terme suggest", {}).get("definition") != "def suggest" or g["zz terme suggest"].get("statut") != "redigee":
            ko.append("ajout suggest perdu ou sans statut")
        if g.get("zz ajout direct", {}).get("definition") != "def directe":
            ko.append("ajout direct dans le full perdu")
        if compare(real, {k: v for k, v in g.items() if not k.startswith("zz ")}):
            ko.append("fiches existantes altérées par la fusion")
        # 4. idempotence
        h1 = sha(full_tmp)
        cli(tmp, "--write")
        if sha(full_tmp) != h1:
            ko.append("non idempotent")

        # 4b. --write a créé une sauvegarde horodatée (data/ + dist/) dans le dossier temporaire
        bks = list((Path(t) / "p" / ".." / "bk").resolve().glob("import-*"))
        if not bks or not (bks[0] / "data" / "data_glossaire_full.py").exists():
            ko.append("pas de sauvegarde créée par --write")

        # 4c. garde anti-réduction : refus si le nombre de fiches baisse, sauf --allow-shrink
        orig_merge = I.merge
        def shrinking(full, src, lex=None):
            m, rep = orig_merge(full, src, lex)
            m.pop(next(iter(m)))
            return m, rep
        I.merge = shrinking
        tmp3 = clone(Path(t) / "p3")
        h3 = sha(tmp3 / "data" / "data_glossaire_full.py")
        try:
            I.run(tmp3, write=True, backup_dir=Path(t) / "bk3", out=lambda *_: None)
            ko.append("écriture réduisant le nombre de fiches non refusée")
        except SystemExit:
            if sha(tmp3 / "data" / "data_glossaire_full.py") != h3:
                ko.append("full modifié malgré le refus")
        I.merge = orig_merge

        # 5. --check : code 1 s'il reste un diff
        tmp2 = clone(Path(t) / "p2")
        s2 = tmp2 / "data" / "data_glossaire.py"
        s2.write_text(src_tmp.read_text(encoding="utf-8"), encoding="utf-8")
        if cli(tmp2, "--check").returncode != 1:
            ko.append("--check devrait retourner 1")

    if sha(REAL_FULL) != real_hash:
        ko.append("LE FULL RÉEL A ÉTÉ MODIFIÉ")

    if ko:
        print("ECHEC test_import_lexique:")
        for k in ko:
            print(" -", k)
        return 1
    print("OK test_import_lexique : diff = 0 sur %d fiches, dry-run sans écriture, ajouts préservés, idempotent" % n_before)
    return 0


if __name__ == "__main__":
    sys.exit(main())
