#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_familles.py — règle « famille obligatoire » : chaque terme de TOUT lexique AeroLex a une famille
(« divers » si aucune ne convient).

Vérifie :
  1. 0 NOUVEAU terme sans famille, dans le full ou en attente d'import (les fiches orphelines historiques sont listées dans
     data/familles_orphelines_baseline.txt ; toute orpheline hors de cette liste = ÉCHEC) ;
  2. la famille « Divers » existe dans chaque lexique (index de suggest, libellé, tri en dernier) ;
  3. suggest BLOQUE une validation sans famille (même avec forçage) — base SQLite temporaire, rien n'est écrit ;
  4. import_lexique --write REFUSE un ajout sans famille (sur une COPIE temporaire) ; --default-famille-divers l'accepte.

Les fiches orphelines historiques (77 au 04/11/2026) sont signalées en AVERTISSEMENT sans échec.
--strict : échoue s'il reste la moindre fiche sans famille (à activer une fois le classement appliqué,
puis supprimer le fichier baseline).

Lancer : python3 scripts/test_familles.py [--strict]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STRICT = "--strict" in sys.argv
_TMP = tempfile.mkdtemp(prefix="familles-test-")
os.environ["AEROLEX_SUGGEST_DIR"] = _TMP                       # base SQLite temporaire (jamais data/suggest réel)
_PWF = os.path.join(_TMP, "pw-factice")
Path(_PWF).write_text("pw-factice-test\n")
os.environ["AEROLEX_SUGGEST_PASSWORD_FILE"] = _PWF
os.environ["AEROLEX_BACKUP_DIR"] = os.path.join(_TMP, "bk")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import import_lexique as I  # noqa: E402
import suggest_core as core  # noqa: E402
import term_display as TD    # noqa: E402

FAILS, WARNS = [], []
BASELINE = ROOT / "data" / "familles_orphelines_baseline.txt"


def check(name, cond, extra=""):
    print(("OK   " if cond else "FAIL ") + name + (" " + str(extra)[:300] if (extra and not cond) else ""))
    if not cond:
        FAILS.append(name)


def orphans(gloss):
    return sorted(k for k, v in gloss.items() if not str(v.get("famille") or "").strip())


# ── 1. aucun nouveau terme sans famille ────────────────────────────────
full = I.load_glossaire(ROOT / "data" / "data_glossaire_full.py")
src = I.load_glossaire(ROOT / "data" / "data_glossaire.py")
orph = orphans(full)
base = set(l.strip() for l in BASELINE.read_text("utf-8").splitlines() if l.strip() and not l.startswith("#")) if BASELINE.exists() else set()
new_orph = [t for t in orph if t not in base]
check("0 nouveau terme sans famille (full)", not new_orph, new_orph)
_pending = [t for t in orphans(src) if t not in full]          # fiches de la source que l'import ajouterait au full
check("0 terme sans famille parmi les fiches de la source pas encore importées", not _pending, _pending)
check("la famille de chaque fiche est connue du catalogue (slug existant ou divers)",
      all((v.get("famille") or "divers") in core.get_index("aero").families for v in full.values() if v.get("famille")),
      sorted({v["famille"] for v in full.values() if v.get("famille") and v["famille"] not in core.get_index("aero").families}))
if orph:
    msg = "%d fiche(s) existante(s) sans famille (héritage, non bloquant)%s" % (len(orph), " — --strict : ÉCHEC" if STRICT else "")
    print("WARN " + msg)
    WARNS.append(msg)
if STRICT:
    check("--strict : aucune fiche sans famille", not orph, "%d orphelines" % len(orph))

# ── 2. « Divers » dans chaque lexique ──────────────────────────────────
for lex_id in core.LEXICONS:
    idx = core.get_index(lex_id)
    fams = list(idx.families)
    check("[%s] famille « divers » présente dans le catalogue" % lex_id, "divers" in idx.families)
    check("[%s] « Divers » est affichée en dernier" % lex_id, fams[-1] == "divers", fams[-3:])
    check("[%s] libellé « Divers »" % lex_id, idx.family_labels.get("divers") == "Divers" and core.family_label("divers", ROOT) == "Divers")
    check("[%s] Divers dans family_info (prompt du modèle)" % lex_id, any(f["slug"] == "divers" for f in idx.family_info()))
check("term_display : libellé Divers non surchargeable", TD.family_label("divers") == "Divers")
check("term_display : tri des familles, Divers en dernier",
      sorted(["divers", "zzz", "aaa", "masses"], key=TD.family_sort_key)[-1] == "divers", sorted(["divers", "zzz", "aaa", "masses"], key=TD.family_sort_key))
bp = (ROOT / "scripts" / "build_pages.py").read_text("utf-8")
check("index (build_pages) : liste des familles triée avec Divers en dernier", "key=family_sort_key" in bp)
js = (ROOT / "dist" / "aero" / "suggest.js").read_text("utf-8")
check("suggest.js : menu Famille (existantes + Divers + nouvelle…) sur la carte", 'data-card-fam' in js and '"__new__"' in js and 'push("divers")' in js)


# ── 3. suggest bloque une validation sans famille ──────────────────────
def mkprop(term, **kw):
    d = {"definition": "Zone de jonction entre deux éléments structuraux de la cellule. Elle transmet les efforts du fuselage vers la voilure.",
         "famille": "", "synonymes": [], "confiance": 0.9, "origine": "", "traduction": "", "domaine": True, "pertinent": True}
    d.update(kw)
    core.enqueue_proposal("aero", term, d, "t")
    return next(x["id"] for x in core.list_proposals("aero") if x["terme"] == term)


pid = mkprop("zzsansfamilletest")
rep = core.check_proposal_id(pid, False)
fam_ctl = [c for c in rep["controles"] if c["nom"] == "Famille"]
check("suggest : contrôle « Famille » KO si famille vide", rep["ok"] is False and fam_ctl and fam_ctl[0]["statut"] == "ko", rep)
check("suggest : blocage marqué incontournable (pas de forçage)", rep.get("incontournable") is True)
for force in (False, True):
    r = core.validate_proposals([pid], do_rebuild=False, run_llm=False, force=force)
    check("suggest : validation refusée sans famille (force=%s) — rien n'est écrit" % force, r["valides"] == [] and len(r["refuses"]) == 1, r)
core.edit_proposal(pid, None, {"famille": "divers"})
rep = core.check_proposal_id(pid, False)
check("suggest : après choix de « Divers » sur la carte, le contrôle Famille passe", any(c["nom"] == "Famille" and c["statut"] == "ok" for c in rep["controles"]), rep["controles"])
core.edit_proposal(pid, None, {"famille": ""})
check("suggest : famille de nouveau vide -> bloqué", core.check_proposal_id(pid, False)["ok"] is False)
try:
    core.edit_proposal(pid, None, {"famille": "famille_inventee_xyz"})
    check("suggest : famille inconnue refusée à l'édition", False)
except ValueError:
    check("suggest : famille inconnue refusée à l'édition", True)
pid2 = mkprop("zznouvellefamilletest")
core.edit_proposal(pid2, None, {"famille_nouvelle": "Famille d'essai", "famille_nouvelle_label": "Famille d'essai"})
rep = core.check_proposal_id(pid2, False)
check("suggest : nouvelle famille sans justification = bloquant non forçable", rep["ok"] is False and rep["incontournable"] is True, rep["controles"])
core.edit_proposal(pid2, None, {"famille_justification": "Aucune famille existante ne couvre ce sujet."})
rep = core.check_proposal_id(pid2, False)
check("suggest : nouvelle famille justifiée mais 0 rattachement = bloquant (forçable), sans accord", rep["ok"] is False and not rep["incontournable"])
core.edit_proposal(pid2, None, {"famille_accord": True})
rep = core.check_proposal_id(pid2, False)
check("suggest : accord explicite du relecteur -> Famille OK", any(c["nom"] == "Famille" and c["statut"] == "ok" for c in rep["controles"]), rep["controles"])
pr = core.build_prompt("aero", ["zzterme"], core.get_index("aero").families)
sysm = pr[0]["content"] if isinstance(pr, (list, tuple)) and isinstance(pr[0], dict) else (pr[0] if isinstance(pr, (list, tuple)) else pr)
check("suggest : le prompt impose famille existante / divers / nouvelle justifiée", "divers" in sysm and "JAMAIS vide" in sysm and "au moins 2" in sysm)
check("suggest : « divers » est dans le catalogue du prompt", "divers — Divers" in sysm)

# ── 4. import_lexique --write refuse un ajout sans famille (copie) ─────
def clone(tmp):
    (tmp / "data").mkdir(parents=True)
    for f in ("data_glossaire.py", "data_glossaire_full.py", "lexique-filtre.txt"):
        shutil.copy(ROOT / "data" / f, tmp / "data" / f)
    return tmp


def cli(root, *args):
    return subprocess.run([sys.executable, str(ROOT / "src" / "import_lexique.py"), "--root", str(root), "--backup-dir", str(root.parent / "bk"), *args],
                          capture_output=True, text=True, timeout=120)


def add_src(root, entry):
    p = root / "data" / "data_glossaire.py"
    t = p.read_text("utf-8")
    i = t.index("GLOSSAIRE = {")
    j = t.index("\n}", i)
    p.write_text(t[:j] + "\n" + entry + t[j + 1:], "utf-8")


with tempfile.TemporaryDirectory() as t:
    tmp = clone(Path(t) / "p")
    fp = tmp / "data" / "data_glossaire_full.py"
    h0 = fp.read_bytes()
    add_src(tmp, "    'zz sans famille': {'definition': 'def', 'categorie': 'X', 'origine': 'suggest'},\n    'zz autre orphelin': {'definition': 'def', 'categorie': 'X', 'origine': 'suggest'},")
    r = cli(tmp)
    check("import dry-run : annonce les ajouts sans famille, ne bloque pas", r.returncode == 0 and "zz sans famille" in r.stdout and "SANS FAMILLE" in r.stdout, r.stdout[-400:] + r.stderr[-200:])
    r = cli(tmp, "--write")
    check("import --write REFUSE un ajout sans famille (code != 0, termes listés)", r.returncode != 0 and "zz sans famille" in (r.stdout + r.stderr) and "zz autre orphelin" in (r.stdout + r.stderr) and "sans famille" in (r.stdout + r.stderr), r.stdout[-300:] + r.stderr[-300:])
    check("import --write refusé : full intact (rien écrit)", fp.read_bytes() == h0)
    check("import : avertissement avec le compte des orphelines existantes", "fiche(s) existante(s) sans famille" in r.stdout or not orph)
    r = cli(tmp, "--write", "--default-famille-divers")
    g = I.load_glossaire(fp)
    check("import --default-famille-divers : écrit, orphelins ajoutés = divers", r.returncode == 0 and g.get("zz sans famille", {}).get("famille") == "divers" and g.get("zz autre orphelin", {}).get("famille") == "divers", r.stdout[-300:] + r.stderr[-300:])
    check("import --default-famille-divers : le vrai full n'est pas touché (copie)", I.load_glossaire(ROOT / "data" / "data_glossaire_full.py") == full)
    tmp2 = clone(Path(t) / "q")
    add_src(tmp2, "    'zz avec famille': {'definition': 'def', 'categorie': 'X', 'famille': 'masses', 'origine': 'suggest'},")
    r = cli(tmp2, "--write")
    check("import --write accepte un ajout AVEC famille", r.returncode == 0 and I.load_glossaire(tmp2 / "data" / "data_glossaire_full.py").get("zz avec famille", {}).get("famille") == "masses", r.stdout[-300:] + r.stderr[-300:])

print()
for w in WARNS:
    print("AVERTISSEMENT :", w)
shutil.rmtree(_TMP, ignore_errors=True)
if FAILS:
    print("%d échec(s)" % len(FAILS))
    sys.exit(1)
print("OK test_familles%s" % (" (--strict)" if STRICT else ""))

