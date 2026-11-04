#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_enqueue_proposals.py — le script de mise en file n'appelle jamais le modèle, ne valide rien, et reste fidèle au tri.
Usage : python3 scripts/test_enqueue_proposals.py"""
import json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT / "data")]
import enqueue_proposals as ep

FAILS = []
def ok(c, msg):
    print(("OK   " if c else "FAIL ") + msg)
    if not c: FAILS.append(msg)

ok(ep.expansion("NCO — Non-Commercial Operations with other-than-complex motor-powered aircraft").startswith("Non-Commercial"), "expansion : le sigle est retiré du développé")
ok(ep.expansion("") == "" and ep.expansion("vilebrequin") == "vilebrequin", "expansion : vide / sans tiret")

tri = {
  "alpha": {"categorie": 2, "decision": "propose_avec_contexte", "contexte_requis": ["moteur"], "risque_faux_positifs": {"niveau": "moyen"},
            "fiche": {"forme_base": "alpha", "developpe": "", "famille": "divers", "definition": "Définition alpha.", "variantes": ["alphas"], "synonymes": [], "voir_aussi": []}},
  "beta": {"categorie": 2, "decision": "propose", "contexte_requis": ["x"], "fiche": {"forme_base": "beta", "famille": "divers", "definition": "Définition beta.", "variantes": []}},
  "bêta": {"categorie": 1, "slug_cible": "beta (nouvelle fiche proposée)", "variantes_a_ajouter": ["bêta test"]},
  "gamma": {"categorie": 1, "slug_cible": "variometre", "variantes_a_ajouter": ["vario"]},
}
an, ex, pend = ep.build_items(tri, "tri-test")
ok(set(an) == {"alpha", "beta"}, "seules les fiches de catégorie 2 sont mises en file")
ok(an["alpha"]["contexte_requis"] == ["moteur"] and an["beta"]["contexte_requis"] == [], "contexte_requis : seulement pour la décision « avec contexte »")
ok("bêta test" in ex["beta"]["variantes"] and "vario" not in ex["beta"]["variantes"], "variantes de catégorie 1 visant une nouvelle fiche : rejoignent cette fiche seulement")
ok(ex["alpha"]["tri"]["origine_tri"] == "tri-test" and ex["alpha"]["tri"]["risque"] == "moyen", "origine du tri et risque conservés")
ok(all(v["domaine"] is True and v["pertinent"] is True for v in an.values()), "fiches préparées : domaine/pertinence posés sans modèle")

# intégration : base TEMPORAIRE, aucun appel modèle (llm=False), rien de validé
import suggest_core as sc
sc.DATA_DIR = Path(tempfile.mkdtemp(prefix="test-enqueue-"))
calls = []
orig = sc.llm_batch
sc.llm_batch = lambda *a, **k: calls.append(a) or ({}, [], 0.0)
sc.free_discard = lambda *a, **k: None          # même contournement que le script (entonnoir « faute de frappe »)
res = sc.seed_terms("aero", ["vilebrequin"], analysis={"vilebrequin": {"domaine": True, "pertinent": True, "definition": "Arbre coudé du moteur qui transforme le mouvement alternatif des pistons en rotation (fiche de test, base temporaire).", "famille": "divers", "confiance": 0.9}},
                    llm=False, adopt_base=False, job="tri-test")
sc.llm_batch = orig
ok(not calls, "aucun appel au modèle")
with sc.db() as con:
    st = [r["status"] for r in con.execute("SELECT status FROM proposals")]
ok(st == ["pending"], "la proposition est en attente (rien de validé) : %s" % st)
print("\nÉCHECS : %d" % len(FAILS))
sys.exit(1 if FAILS else 0)
