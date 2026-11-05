#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prevalidate.py — pré-valide la file « À valider » d'un lexique (même logique que le bouton « Pré-valider en lot »).

  python3 scripts/prevalidate.py <lexique> [--ids 12,13,14] [--model xai/grok-4.3] [--second-model local | --no-second]
                                 [--effort low] [--json rapport.json] [--apply-ready] [--reject-flagged]

Sans option d'écriture, RIEN n'est publié : seules la file (corrections, enregistrées avec l'état d'origine) et le journal de coût sont touchés.
  --apply-ready     après le tri, valide EN UNE OPÉRATION toutes les « prêtes » et « corrigées-prêtes » (verrou, une sauvegarde, une
                    reconstruction, tests, restauration automatique si un test échoue). ÉCRIT dans le lexique de l'installation.
  --reject-flagged  rejette les propositions classées « à rejeter » (écriture dans la file seulement).
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suggest_core as sc  # noqa: E402
import suggest_prevalidate as pv  # noqa: E402

ORDER = [("douteuse", "DOUTEUSES — une question pour vous"), ("a_rejeter", "À REJETER"), ("corrigee_prete", "CORRIGÉES-PRÊTES"), ("prete", "PRÊTES")]


def show(v, n=170):
    s = v if isinstance(v, str) else ", ".join(map(str, v)) if isinstance(v, list) else str(v)
    return s if len(s) <= n else s[:n - 1] + "…"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("lexique", nargs="?", default=sc.DEFAULT_LEX)
    ap.add_argument("--ids", default="all", help="ids séparés par des virgules (défaut : toute la file)")
    ap.add_argument("--model", default=None, help="premier passage, ex. xai/grok-4.3 ou local")
    ap.add_argument("--second-model", default=None, help="deuxième avis (modèle différent), ex. local")
    ap.add_argument("--no-second", action="store_true", help="pas de deuxième avis : les cas douteux restent douteux")
    ap.add_argument("--effort", default=None, help="reasoning_effort xAI (défaut : low)")
    ap.add_argument("--json", default="", help="écrit le rapport complet en JSON")
    ap.add_argument("--apply-ready", action="store_true")
    ap.add_argument("--reject-flagged", action="store_true")
    a = ap.parse_args(argv)
    ids = "all" if a.ids == "all" else [int(x) for x in a.ids.split(",") if x.strip()]
    cfg = pv.config(model=a.model, second="none" if a.no_second else a.second_model, effort=a.effort)
    n = len(pv.select_ids(a.lexique, ids))
    print("Lexique %s : %d proposition(s) à pré-valider. Modèles : %s | 2e avis : %s | repli : %s" % (
        a.lexique, n, pv.label(cfg["first"]), pv.label(cfg["second"]) or "aucun", pv.label(cfg["fallback"]) or "aucun"))
    if not n:
        return 0
    last = [""]

    def prog(done, total, etape):
        etape = re.sub(r"\s*\(\d+/\d+\)$", "", etape)
        if etape != last[0]:
            print("  … %s" % etape, flush=True)
            last[0] = etape

    rep = pv.prevalidate(a.lexique, ids, cfg=cfg, progress=prog)
    c = rep["comptes"]
    print("\n%d prêtes · %d corrigées · %d douteuses · %d à rejeter   —   %s s, %.4f $ (%d appel(s) modèle, %d deuxième(s) avis)" % (
        c["prete"], c["corrigee_prete"], c["douteuse"], c["a_rejeter"], rep["secs"], rep["usd"], rep["appels"], rep["deuxieme_avis"]))
    if rep["douteux_sans_second_avis"]:
        print("  (%d cas douteux sans deuxième avis : aucun second modèle configuré)" % rep["douteux_sans_second_avis"])
    for st, titre in ORDER:
        items = rep["groupes"][st]
        if not items:
            continue
        print("\n== %s (%d) ==" % (titre, len(items)))
        for it in items:
            conf = (" [conf. %s]" % str(it["confiance"]).replace(".", ",")) if it["confiance"] is not None else ""
            print("#%d %s%s — %s" % (it["id"], it["terme"], conf, show(it["raison"])))
            if it["question"]:
                print("     ? %s" % show(it["question"], 220))
            for f in it["corrections"]:
                print("     ~ %s (%s) : %s  →  %s" % (f["champ"], f["origine"], show(f["avant"], 90), show(f["apres"], 90)))
    if a.json:
        with open(a.json, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, ensure_ascii=False, indent=1)
        print("\nrapport : " + a.json)
    rc = 0
    if a.reject_flagged:
        ids_r = [it["id"] for it in rep["groupes"]["a_rejeter"]]
        r = pv.reject_flagged(a.lexique, ids_r) if ids_r else {"rejetes": []}
        print("\nRejetées : %d" % len(r["rejetes"]))
    if a.apply_ready:
        ready = [it["id"] for k in pv.READY for it in rep["groupes"][k]]
        print("\nValidation des %d prêtes en une opération (sauvegarde, reconstruction, tests)…" % len(ready))
        t0 = time.time()
        r = pv.apply_ready(a.lexique, ready) if ready else {"ok": True, "valides": []}
        if r.get("ok"):
            print("OK : %d fiche(s) ajoutée(s)%s en %.0f s ; sauvegarde %s" % (len(r["valides"]), (" (fiches %s -> %s)" % tuple(r["fiches"])) if r.get("fiches") else "",
                                                                       time.time() - t0, r.get("sauvegarde", "—")))
        else:
            print("ÉCHEC, site restauré : %s" % r.get("erreur"))
            rc = 1
    elif rep["groupes"]["prete"] or rep["groupes"]["corrigee_prete"]:
        print("\nRien n'est publié. Pour valider les prêtes : relancer avec --apply-ready (ou bouton « Valider les N prêtes »).")
    return rc


if __name__ == "__main__":
    sys.exit(main())
