#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""test_lot3_recognition.py — garde-fous du lot 3a (variantes du tri validé, contextes élargis, anti-ridicule).
Le moteur (dist/aerolex.js) est exécuté sous Node sur dist/aerolex-index.json. Usage : python3 scripts/test_lot3_recognition.py"""
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CASES = [  # (phrase, forme attendue soulignée | None si RIEN ne doit être souligné sur cette forme, forme testée)
 ("Le vario indique une montée de 500 ft/min.", "variomètre", "vario"),
 ("Subsidence anticyclonique sur le nord du pays.", "anticyclone", "anticyclonique"),
 ("Le compte-tours affiche 5 000 tr/min.", "tachymètre", "compte-tours"),
 ("Le collationnement correct est ton filet.", "collationnement clairance", "collationnement"),
 ("NOTE : tachometer indicates propeller speed.", "hélice", "propeller"),
 ("Le PIC décide de la poursuite du vol.", "commandant de bord", "PIC"),
 ("Au pic de la journée, le vent forcit.", None, "pic"),                       # casse exacte : « pic » n'est pas le sigle PIC
 ("La déviation du flux autour du relief est forte.", None, "déviation"),       # « déviations » retiré (singulier auto)
 ("Le sandwich d'espaces aériens est complexe.", None, "sandwich"),
 ("La ligne rouge basse de l'huile est à 50 °C.", None, "ligne rouge"),
 ("Le drainage d'air froid dans la vallée.", None, "drainage"),
 ("Un tour de piste à gauche, puis finale.", "tour de piste", "tour de piste"),  # contexte retiré : clé non ambiguë
 ("Tu es en finale, prêt à remettre les gaz si besoin.", "finale", "finale"),     # contexte élargi (remise des gaz)
 ("Tu vires en base puis en finale, avec le trafic en vent arrière.", "finale", "finale"),
 ("La base des cumulus est estimée à 4 500 ft.", None, "base"),
 ("Un seuil de 5000 ft est retenu pour le plafond.", None, "seuil"),
 ("Une bande nuageuse arrive par l'ouest.", None, "bande"),
 ("La séparation verticale minimale est de 1 000 ft.", None, "verticale"),
 ("La décision finale appartient au commandant.", None, "finale"),
]
DRIVER = r'''
const fs=require('fs'), vm=require('vm');
const [, , eng, idxp, casesp]=process.argv;
const win={}, doc={readyState:'loading',addEventListener(){},querySelector(){return null;}};
const ctx=vm.createContext({window:win,document:doc,console,performance:{now:()=>0}});
vm.runInContext(fs.readFileSync(eng,'utf8'),ctx);
const core=win.AeroLexCore, idxFull=JSON.parse(fs.readFileSync(idxp,'utf8')), idx=idxFull.terms;
const maps=core.buildMaps(idx, idxFull.meta&&idxFull.meta.rules), rx=core.buildRegex(maps.ciMap,maps.csMap);
const cases=JSON.parse(fs.readFileSync(casesp,'utf8'));
console.log(JSON.stringify(cases.map(c=>core.findMatches(c[0],rx,maps).map(m=>[m.raw,m.canon]))));
'''
def main():
    import tempfile
    d = Path(tempfile.mkdtemp())
    (d / "d.js").write_text(DRIVER); (d / "c.json").write_text(json.dumps(CASES, ensure_ascii=False))
    out = subprocess.check_output(["node", str(d / "d.js"), str(ROOT / "dist/aerolex.js"), str(ROOT / "dist/aerolex-index.json"), str(d / "c.json")], text=True)
    res = json.loads(out); fails = 0
    for (phrase, want, form), got in zip(CASES, res):
        hit = [g for g in got if g[0].lower() == form.lower() or (want and g[1] == want and g[0] == form)]
        good = bool(hit) and hit[0][1] == want if want else not any(g[0].lower() == form.lower() for g in got)
        print(("OK   " if good else "FAIL ") + "%-62s -> %s" % (phrase[:62], got))
        fails += 0 if good else 1
    print("\nÉCHECS : %d / %d" % (fails, len(CASES)))
    return 1 if fails else 0
if __name__ == "__main__":
    sys.exit(main())
