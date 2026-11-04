#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_lexicon.py <slug> — enchaîne TOUS les contrôles de qualité d'un lexique et rend un verdict clair.

    python3 scripts/check_lexicon.py aero
    python3 scripts/check_lexicon.py demo-voile [--base DOSSIER] [--json] [--only a,b]

Contrôles : acronyms · family_acronyms · links_resolve · slugs · familles (--strict) · matching · import (diff = 0) · titres accentués ·
variantes < 3 lettres en minuscules (exceptions : unités après nombre, sigles en casse exacte, vérifiées dans le moteur) · mots grammaticaux · aller-retour du moteur · empreinte de cache · index (lettres vides masquées).
Code retour : 0 = lexique propre, 1 = au moins un contrôle en échec. N'écrit rien dans data/ ni dist/.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "src"))
import suggest_rules as RULES  # noqa: E402

def _node_bin():
    """Chemin absolu de node : le service launchd n'a pas /opt/homebrew/bin dans son PATH."""
    import os, shutil
    for c in (os.environ.get("AEROLEX_NODE"), shutil.which("node"), "/opt/homebrew/bin/node", "/usr/local/bin/node", "/usr/bin/node"):
        if c and os.path.exists(c):
            return c
    return "node"



def lexroot(slug: str, base: Path) -> Path:
    if slug == "aero":
        return base
    p = base / "lexicons" / slug
    if not (p / "data").is_dir():
        raise SystemExit("lexique introuvable : %s (attendu : %s)" % (slug, p))
    return p


class Report:
    def __init__(self):
        self.rows = []

    def add(self, name, ok, detail="", warn=False):
        self.rows.append({"controle": name, "ok": bool(ok), "detail": detail, "avert": bool(warn) and bool(ok)})
        print(("  ✓ " if ok and not warn else "  ⚠ " if ok else "  ✗ ") + name + (" — " + detail if detail else ""), flush=True)


def run(cmd, root: Path, slug: str, timeout=900):
    env = dict(os.environ, AEROLEX_LEXICON=slug, AEROLEX_LEXROOT=str(root))
    p = subprocess.run(cmd, cwd=str(root), env=env, capture_output=True, text=True, timeout=timeout)
    out = (p.stdout + p.stderr).strip()
    last = [l for l in out.splitlines() if l.strip()][-3:]
    return p.returncode, " | ".join(x.strip()[:200] for x in last)


def load_gloss(root: Path, name="data_glossaire_full.py") -> dict:
    import import_lexique as IL
    return IL.load_glossaire(root / "data" / name)


NODE_ROUNDTRIP = r"""
const fs=require('fs'), vm=require('vm');
const inp=JSON.parse(fs.readFileSync(0,'utf8'));
const win={}, doc={readyState:'loading',addEventListener(){},querySelector(){return null;}};
const ctx=vm.createContext({window:win,document:doc,console,performance:{now:()=>0}});
vm.runInContext(fs.readFileSync(inp.engine,'utf8'),ctx);
const core=win.AeroLexCore, idx=JSON.parse(fs.readFileSync(inp.index,'utf8')).terms;
const maps=core.buildMaps(idx), rx=core.buildRegex(maps.ciMap,maps.csMap);
const bad=[];
for(const c of inp.cases){
  const texts=c.texts||[c.text]; let ok=false, coll=false, got=[];
  for(const t of texts){const ms=core.findMatches(t,rx,maps); if(ms.some(m=>m.canon===c.canon)) ok=true;
    if(ms.some(m=>m.raw.toLowerCase()===c.form.toLowerCase()||m.raw.toLowerCase()===c.form.toUpperCase().toLowerCase())) coll=true;
    got=got.concat(ms.map(m=>m.raw+'>'+m.canon));}
  if(!ok) bad.push([c.form,c.canon,got.join(','),coll?'collision':'non reconnue']);
}
console.log(JSON.stringify({version:win.AeroLex&&win.AeroLex.version,bad}));
"""

# Sonde des variantes courtes : cases {text, raw, canon, expect:'match'|'nomatch'}
NODE_PROBE = r"""
const fs=require('fs'), vm=require('vm');
const inp=JSON.parse(fs.readFileSync(0,'utf8'));
const win={}, doc={readyState:'loading',addEventListener(){},querySelector(){return null;}};
const ctx=vm.createContext({window:win,document:doc,console,performance:{now:()=>0}});
vm.runInContext(fs.readFileSync(inp.engine,'utf8'),ctx);
const core=win.AeroLexCore, idx=JSON.parse(fs.readFileSync(inp.index,'utf8')).terms;
const maps=core.buildMaps(idx), rx=core.buildRegex(maps.ciMap,maps.csMap);
const bad=[];
for(const c of inp.cases){
  const ms=core.findMatches(c.text,rx,maps);
  const ok = c.expect==='match' ? ms.some(m=>m.raw===c.raw && m.canon===c.canon) : !ms.some(m=>m.raw===c.raw);
  if(!ok) bad.push([c.label,c.expect,ms.map(m=>m.raw+'>'+m.canon).join(',')]);
}
console.log(JSON.stringify({bad}));
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("slug")
    ap.add_argument("--base", default=str(HERE.parent))
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args(argv)
    base = Path(a.base).resolve()
    slug = a.slug
    root = lexroot(slug, base)
    only = set(x for x in a.only.split(",") if x)
    want = lambda n: not only or n in only  # noqa: E731
    R = Report()
    t0 = time.time()
    print("Contrôle du lexique « %s » (%s)" % (slug, root))
    G = load_gloss(root)
    print("  %d fiche(s)" % len(G))
    py = ["python3"]
    # 1-4 : tests de chaîne (les mêmes scripts, rendus indépendants du lexique par AEROLEX_LEXICON)
    for name, script in (("acronyms", "test_acronyms.py"), ("family_acronyms", "test_family_acronyms.py"),
                         ("links_resolve", "test_links_resolve.py"), ("slugs", "test_slugs.py")):
        if want(name):
            rc, tail = run(py + ["scripts/" + script], root, slug)
            R.add(name, rc == 0, tail)
    # 5 : familles
    if want("familles"):
        if slug == "aero":
            rc, tail = run(py + ["scripts/test_familles.py", "--strict"], root, slug)
            R.add("familles --strict", rc == 0, tail)
        else:
            orph = [k for k, v in G.items() if not v.get("famille")]
            cat = json.loads((root / "data" / "familles_labels.json").read_text("utf-8")) if (root / "data" / "familles_labels.json").exists() else {}
            unknown = sorted({v["famille"] for v in G.values() if v.get("famille") and v["famille"] != "divers" and v["famille"] not in cat})
            R.add("familles --strict", not orph and not unknown,
                  ("%d fiche(s) sans famille : %s" % (len(orph), ", ".join(orph[:8]))) if orph else
                  ("famille(s) hors catalogue : %s" % ", ".join(unknown)) if unknown else "tout terme a une famille (Divers d'office)")
    # 6 : moteur
    eng, idxp = RULES.engine_paths(root, slug)
    if want("matching"):
        if slug == "aero":
            rc, tail = run(py + ["scripts/test_matching.py"], root, slug)
            R.add("matching (moteur v1.3.0)", rc == 0, tail)
        else:
            txt = eng.read_text("utf-8") if eng.exists() else ""
            m = re.search(r"AeroLex Runtime v(\d+\.\d+\.\d+)", txt)
            ok = bool(m) and tuple(int(x) for x in m.group(1).split(".")) >= (1, 3, 0) and "contexte" in txt.lower() or bool(m) and "ctx" in txt
            R.add("matching (moteur v1.3.0)", bool(m) and tuple(int(x) for x in m.group(1).split(".")) >= (1, 3, 0), "moteur " + (m.group(1) if m else "introuvable"))
    # 7 : import diff = 0
    if want("import"):
        rc, tail = run(py + ["src/import_lexique.py", "--check", "--root", str(root)], root, slug)
        R.add("import (diff = 0)", rc == 0, "aucun écart data_glossaire.py → full" if rc == 0 else tail)
    # 8 : titres accentués (le corpus et les définitions accentuent un mot dont le titre est sans accent)
    cdir = RULES.corpus_dir(base, json.loads((base / "lexicons" / "registry.json").read_text("utf-8")).get("lexicons", {}).get(slug) if (base / "lexicons" / "registry.json").exists() else None)
    if want("titres"):
        defs_only = {str(i): {"definition": v.get("definition", "")} for i, v in enumerate(G.values())}
        cnt = RULES.accent_forms(cdir, defs_only)
        bad = []
        for t in G:
            if G[t].get("titre_sans_accent"):      # graphie sans accent voulue et justifiée (champ de la fiche : la raison)
                continue
            s = RULES.accent_suggestion(t, cnt)
            if s:
                bad.append("%s → %s" % (t, s["forme"]))
        R.add("titres accentués", not bad, ("%d titre(s) sans accent alors que le corpus l'accentue : %s" % (len(bad), " ; ".join(bad[:8]))) if bad
              else "tous les titres suivent l'accentuation du corpus" + ("" if cdir else " (corpus introuvable : non comparé)"), warn=not cdir)
    # 9-10 : variantes interdites
    if want("variantes"):
        short, gram, units, exact = [], [], [], []
        for t, m in G.items():
            declared = set(m.get("unites_apres_nombre") or [])
            for v in list(m.get("variantes") or []) + list(m.get("synonymes") or []):
                if not isinstance(v, str):
                    continue
                if RULES.too_short(v):
                    if v in declared:
                        units.append((t, v))
                    else:
                        short.append("%s ⊃ %r" % (t, v))
                elif RULES.forbidden_variant(v, t) == "mot grammatical":
                    gram.append("%s ⊃ %r" % (t, v))
                elif RULES.is_exact_case_sigle(v, t):
                    exact.append((t, v))
        # exceptions documentées, vérifiées DANS LE MOTEUR : unité = reconnue après un nombre et jamais seule ; « Va » = reconnue en
        # casse exacte, jamais en minuscules (le verbe « va »).
        probes = []
        for t, v in units:
            probes.append({"label": "unité %r (%s) après un nombre" % (v, t), "expect": "match", "raw": v, "canon": t, "text": "Il y a 12 %s au total." % v})
            if "°" not in v and " " not in v:
                probes.append({"label": "unité %r (%s) sans nombre" % (v, t), "expect": "nomatch", "raw": v, "canon": t, "text": "le %s, le %s et puis %s." % (v, v, v)})
        for t, v in exact:
            probes.append({"label": "casse exacte %r (%s)" % (v, t), "expect": "match", "raw": v, "canon": t, "text": "%s = 112 KIAS" % v})
            probes.append({"label": "minuscules %r (%s) jamais liées" % (v.lower(), t), "expect": "nomatch", "raw": v.lower(), "canon": t,
                           "text": "il %s chercher, on %s voir et elle %s bien." % (v.lower(), v.lower(), v.lower())})
        if probes:
            if eng.exists() and idxp.exists():
                p = subprocess.run([_node_bin(), "-e", NODE_PROBE], input=json.dumps({"engine": str(eng), "index": str(idxp), "cases": probes}),
                                   capture_output=True, text=True, timeout=120)
                try:
                    for b_ in json.loads(p.stdout)["bad"]:
                        short.append("moteur : %s → attendu %s, obtenu %s" % (b_[0], b_[1], b_[2] or "rien"))
                except Exception:
                    short.append("sonde du moteur illisible : " + (p.stderr or p.stdout)[-120:])
            else:
                short.append("moteur introuvable : exceptions (unités, casse exacte) non vérifiables")
        extra = (" ; exceptions vérifiées dans le moteur : %d unité(s) après nombre (%s), %d sigle(s) en casse exacte (%s)" % (
            len(units), ", ".join(v for _, v in units[:8]), len(exact), ", ".join(v for _, v in exact[:6]))) if (units or exact) else ""
        R.add("aucune variante < 3 lettres en minuscules", not short,
              ("%d : %s" % (len(short), " ; ".join(short[:8]))) if short else "aucune forme interdite" + extra)
        R.add("aucun mot grammatical en variante", not gram, ("%d : %s" % (len(gram), " ; ".join(gram[:8]))) if gram else "")
    # 11 : aller-retour du moteur (chaque titre / variante est reconnu et mène à sa fiche)
    #      non reconnue = aucune souligné ; collision = la forme est liée mais à UNE AUTRE fiche (forme déclarée dans deux fiches)
    if want("aller_retour") and eng.exists() and idxp.exists():
        cases = []
        for t, m in G.items():
            ctxw = " ".join(m.get("contexte_requis") or [])
            if m.get("contexte_sigle"):
                ctxw += " " + " ".join(m["contexte_sigle"])
            for f in [t] + [v for v in (m.get("variantes") or []) if isinstance(v, str) and not RULES.too_short(v)]:
                if len(re.sub(r"[^A-Za-zÀ-ÿ]", "", f)) < 2 or m.get("casse_sensible") and f != t:
                    continue
                texts = ["Voici %s, %s utilisé ici." % (f, ctxw or "terme")]
                alnum = re.sub(r"[^0-9A-Za-zÀ-ÿ]", "", f)
                if f == f.lower() and (len(alnum) <= 2 or m.get("casse_sensible") or " " not in f):
                    # sigle/unité écrit en minuscules dans le titre : le moteur ne le lie qu'en capitales (« CG ») ou après un nombre (« 12 kt »)
                    texts = ["Voici %s, %s utilisé ici." % (f.upper(), ctxw or "terme"), "Il y a 12 %s, %s utilisé ici." % (f, ctxw or "terme")]
                cases.append({"form": f, "canon": t, "texts": texts})
        inp = {"engine": str(eng), "index": str(idxp), "cases": cases}
        p = subprocess.run([_node_bin(), "-e", NODE_ROUNDTRIP], input=json.dumps(inp), capture_output=True, text=True, timeout=300)
        if p.returncode == 0:
            res = json.loads(p.stdout)
            unrec = [b for b in res["bad"] if b[3] == "non reconnue"]
            coll = [b for b in res["bad"] if b[3] == "collision"]
            parts = []
            if unrec:
                parts.append("%d non reconnue(s) : %s" % (len(unrec), " ; ".join("%s→%s" % (b[0], b[1]) for b in unrec[:6])))
            if coll:
                parts.append("%d forme(s) liée(s) à une autre fiche (déclarée dans deux fiches) : %s" % (coll.__len__(), " ; ".join("%s→%s (lié : %s)" % (b[0], b[1], b[2].split(",")[0]) for b in coll[:5])))
            ok = not unrec and (not coll or slug == "aero")
            R.add("aller-retour du moteur", ok, ("; ".join(parts) + " — sur %d formes" % len(cases)) if parts else "%d forme(s) reconnue(s)" % len(cases),
                  warn=bool(coll) and ok)
        else:
            R.add("aller-retour du moteur", False, (p.stderr or p.stdout)[-200:])
    # 12 : empreinte de cache
    if want("empreinte"):
        bi = root / "dist" / slug / "build-info.json"
        try:
            env = dict(os.environ, AEROLEX_LEXICON=slug, AEROLEX_LEXROOT=str(root))
            cur = subprocess.run(["python3", "scripts/asset_fingerprint.py"], cwd=str(root), env=env, capture_output=True, text=True).stdout.strip()
            have = json.loads(bi.read_text("utf-8")).get("empreinte")
            html = (root / "dist" / slug / "index.html").read_text("utf-8")
            R.add("empreinte de cache à jour", have == cur and ("?v=" + cur) in html, "build-info %s, calculée %s" % (have, cur))
        except Exception as e:
            R.add("empreinte de cache à jour", False, str(e)[:160])
    # 13 : index (lettres vides masquées, autocomplétion)
    if want("index"):
        try:
            h = (root / "dist" / slug / "index.html").read_text("utf-8")
            links = set(re.findall(r'<a href="#(\w+)" data-l=', h))
            groups = set(re.findall(r'<section class="ix-group" id="(\w+)"', h))
            ok = links == groups and "aerolex-searchbox.js" in h and 'id="ix-sug"' in h
            R.add("index (lettres vides masquées, autocomplétion)", ok, "%d lettre(s) affichée(s), %d groupe(s)" % (len(links), len(groups)))
        except OSError as e:
            R.add("index (lettres vides masquées, autocomplétion)", False, str(e)[:120])
    fails = [r for r in R.rows if not r["ok"]]
    warns = [r for r in R.rows if r["avert"]]
    print("\n%s  (%d contrôle(s), %d échec(s), %d avertissement(s), %.0f s)" % (
        "VERDICT : LEXIQUE PROPRE ✓" if not fails else "VERDICT : NON CONFORME ✗ — " + ", ".join(r["controle"] for r in fails),
        len(R.rows), len(fails), len(warns), time.time() - t0))
    if a.json:
        print(json.dumps({"slug": slug, "propre": not fails, "controles": R.rows}, ensure_ascii=False))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
