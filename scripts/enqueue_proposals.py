#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enqueue_proposals.py — met les fiches PRÉPARÉES du tri (catégorie 2) dans la file « À valider » de Suggérer,
SANS appel au modèle et SANS rien publier. Réutilise suggest_core.seed_terms (analysis = fiches injectées) :
même pipeline que Suggérer (entonnoir gratuit, forme de base, variantes, sigles développés, anti-ridicule).
Aucune validation : le relecteur valide à la main.

Usage : python3 scripts/enqueue_proposals.py [--triage FICHIER.json] [--job tri-2026-11-04] [--dry-run] [--report OUT.json]
  --dry-run : écrit dans une base SQLite TEMPORAIRE (la vraie file n'est pas touchée).
"""
import argparse, json, os, re, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src"), str(ROOT / "data")]
DEFAULT_TRIAGE = Path(os.environ.get("AEROLEX_TRIAGE_FILE") or "aerolex-triage-termes.json")


def expansion(developpe: str) -> str:
    """'NCO — Non-Commercial Operations …' -> 'Non-Commercial Operations …' (le développé seul, sans le sigle)."""
    return re.split(r"\s+[—–-]\s+", developpe, maxsplit=1)[-1].strip() if developpe else ""


def build_items(tri: dict, job: str) -> tuple:
    """-> (analysis {terme: item}, extras {terme: {variantes, contexte, meta}}, nouvelle_fiche_variantes)."""
    analysis, extras = {}, {}
    cat2 = {k: v for k, v in tri.items() if v.get("categorie") == 2 and v.get("fiche")}
    # variantes de catégorie 1 qui visent une fiche NOUVELLE (« nouvelle fiche proposée ») : elles rejoignent cette fiche
    pending_var = {}
    for t, e in tri.items():
        if e.get("categorie") == 1 and "(nouvelle fiche" in (e.get("slug_cible") or ""):
            cible = e["slug_cible"].split(" (nouvelle")[0].strip()
            pending_var.setdefault(cible.lower(), []).extend(e.get("variantes_a_ajouter", []))
    for k, e in cat2.items():
        f = e["fiche"]
        term = f["forme_base"]
        ctx = list(e.get("contexte_requis") or []) if e.get("decision") == "propose_avec_contexte" else []
        risque = (e.get("risque_faux_positifs") or {}).get("niveau") or ""
        analysis[term] = {
            "terme": term, "domaine": True, "pertinent": True,
            "raison_domaine": "fiche préparée et validée au tri du 2026-11-04", "raison_pertinent": e.get("raison", "")[:300],
            "definition": f["definition"], "famille": f["famille"],
            "famille_justification": "Famille retenue au tri validé du 2026-11-04 (famille existante).",
            "voir_aussi": f.get("voir_aussi") or [], "synonymes": f.get("synonymes") or [],
            "origine": expansion(f.get("developpe") or ""), "confiance": 0.9,
            "contexte_requis": ctx, "homographe_courant": bool(ctx),
        }
        vs = list(f.get("variantes") or []) + pending_var.get(term.lower(), [])
        extras[term] = {"variantes": list(dict.fromkeys(vs)), "ctx": ctx, "tri": {
            "origine_tri": job, "risque": risque, "priorite": e.get("priorite"), "occurrences": e.get("occurrences"),
            "nb_seances": e.get("nb_seances"), "developpe_tri": f.get("developpe") or "", "decision": e.get("decision")}}
    return analysis, extras, pending_var


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--triage", default=str(DEFAULT_TRIAGE))
    ap.add_argument("--job", default="tri-2026-11-04")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--report", default=None)
    ap.add_argument("--skip-seed", action="store_true", help="reprise : ne ré-enregistre pas, applique seulement variantes préparées + métadonnées aux propositions déjà en file")
    ap.add_argument("--only", default=None, help="liste de termes séparés par | (essais)")
    ap.add_argument("--no-bypass", action="store_true", help="garder l'entonnoir « faute de frappe / fragment » (par défaut contourné : le tri a déjà validé ces termes)")
    a = ap.parse_args(argv)
    import suggest_core as sc
    if a.dry_run:
        sc.DATA_DIR = Path(tempfile.mkdtemp(prefix="enqueue-dry-"))
    tri = json.load(open(a.triage, encoding="utf-8"))
    analysis, extras, pend = build_items(tri, a.job)
    if a.only:
        keep = set(a.only.split("|"))
        analysis = {k: v for k, v in analysis.items() if k in keep}
        extras = {k: v for k, v in extras.items() if k in keep}
    if not a.no_bypass:
        # l'entonnoir gratuit prend « culasse » pour une faute de « classe », « dérapage » pour « décrabage »… : le tri a déjà tranché.
        # Seuls les statuts « présent » / « alias » (le terme existe déjà au lexique) restent exclus.
        sc.free_discard = lambda *args, **kw: None
    if a.skip_seed:
        res = {"en_file": 0, "reprise": True}
    else:
        res = sc.seed_terms(sc.DEFAULT_LEX, list(analysis), analysis=analysis, llm=False, adopt_base=False, job=a.job)
    # compléments : métadonnées du tri, variantes préparées (mêmes interdictions que les variantes générées)
    rep = {"demandees": len(analysis), "seed": {k: v for k, v in res.items() if k != "corriges"}, "corriges": res.get("corriges"),
           "variantes_refusees": {}, "variantes_ajoutees": {}, "ids": {}}
    with sc._db_lock, sc.db() as con:
        rows = {r["term"]: r["id"] for r in con.execute("SELECT id,term FROM proposals WHERE domain=? AND status='pending' AND job=?", (sc.DEFAULT_LEX, a.job))}
    for term, ex in extras.items():
        pid = rows.get(term)
        if not pid:
            continue
        rep["ids"][term] = pid
        ok, bad = [], []
        for v in ex["variantes"]:
            try:
                sc.edit_proposal(pid, None, {"variantes_ajout": [v]})
                ok.append(v)
            except ValueError as e:
                bad.append("%s : %s" % (v, str(e)[:90]))
        rep["variantes_ajoutees"][term], rep["variantes_refusees"][term] = ok, bad
        with sc._db_lock, sc.db() as con:                # métadonnées du tri (origine, risque, développé) dans la proposition
            r = con.execute("SELECT data FROM proposals WHERE id=?", (pid,)).fetchone()
            d = json.loads(r["data"])
            d.update(ex["tri"])
            if ex["ctx"]:
                d["contexte_requis"] = ex["ctx"]
            con.execute("UPDATE proposals SET data=? WHERE id=?", (json.dumps(d, ensure_ascii=False), pid))
    rep["en_file"] = len(rep["ids"])
    rep["absents"] = [t for t in analysis if t not in rep["ids"]]
    if a.report:
        Path(a.report).write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("demandées %d | en file %d | absentes %d%s" % (rep["demandees"], rep["en_file"], len(rep["absents"]), " (DRY-RUN base temporaire)" if a.dry_run else ""))
    if rep["absents"]:
        print("absentes :", rep["absents"][:20])
    return 0


if __name__ == "__main__":
    sys.exit(main())
