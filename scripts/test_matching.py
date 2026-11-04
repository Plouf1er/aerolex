#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_matching.py — tests du MOTEUR de reconnaissance (dist/aerolex.js, exécuté dans Node via
window.AeroLexCore.findMatches) sur l'index publié (dist/aerolex-index.json). Lot « reconnaissance »
du 2026-11-04 (S1 à S6). Lancer : python3 scripts/test_matching.py
Nécessite node. Aucune écriture, aucun réseau.
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "dist", "aerolex.js")
INDEX = os.path.join(ROOT, "dist", "aerolex-index.json")

DRIVER = r"""
const fs=require('fs'), vm=require('vm');
const [, enginePath, indexPath]=process.argv;
const cases=JSON.parse(fs.readFileSync(0,'utf8'));
const win={}, doc={readyState:'loading',addEventListener(){},querySelector(){return null;}};
const ctx=vm.createContext({window:win,document:doc,console,performance:{now:()=>0}});
vm.runInContext(fs.readFileSync(enginePath,'utf8'),ctx);
const core=win.AeroLexCore, idx=JSON.parse(fs.readFileSync(indexPath,'utf8')).terms;
const maps=core.buildMaps(idx), rx=core.buildRegex(maps.ciMap,maps.csMap);
const out=cases.map(t=>core.findMatches(t,rx,maps).map(m=>[m.raw,m.canon]));
console.log(JSON.stringify({version:win.AeroLex&&win.AeroLex.version,res:out}));
"""

# (libellé, texte, attendus [(raw, canon)], interdits [raw])
CASES = [
    # ── S1 : frontières Unicode / trait d'union
    ("S1 écarte ne souligne pas carte", "Il écarte la manette.", [], ["carte"]),
    ("S1 carte seule reste reconnue", "Sur la carte de navigation.", [("carte", "carte")], []),
    ("S1 accélérer ne souligne pas acc", "Pour accélérer au décollage.", [], ["acc", "Acc"]),
    ("S1 posé ne souligne pas pos", "le devoir posé", [], ["pos"]),
    ("S1 stressé ne souligne pas stress", "un élève stressé", [], ["stress"]),
    ("S1 -SHRA (METAR) reconnu", "METAR LFPN 09007KT 9999 -SHRA SCT025", [("SHRA", "shra")], []),
    ("S1 trait d'union derrière une lettre bloque", "un anti-carte magique", [], ["carte"]),
    ("S1 × n'est pas une lettre", "t = NM/TAS×60", [("TAS", "TAS")], []),
    # ── S2 : sigles de 2 lettres
    ("S2 Vy souligné", "Vy = 65 KIAS", [("Vy", "Vy")], []),
    ("S2 VX majuscules", "montée VX/VY selon situation", [("VX", "Vx"), ("VY", "Vy")], []),
    ("S2 FL souligné", "Un niveau de vol (FL) n'existe que sur le calage standard.", [("FL", "niveau de vol")], []),
    ("S2 CG souligné", "le CG avant demande plus de trim", [("CG", "cg")], []),
    ("S2 minuscules refusées", "le cg et la vy et le fl du cl", [], ["cg", "vy", "fl", "cl"]),
    ("S2 CL = 7 (code OMM) refusé", "Atlas OMM, CL = 7 : stratus fractus", [], ["CL"]),
    ("S2 Cl coefficient de portance accepté", "le coefficient de portance (ou CL) du profil", [("CL", "Cl")], []),
    ("S2 Cc = cap compas", "Cm = 100° et Cc = Cm + d", [("Cc", "cap compas"), ("Cm", "cap magnétique")], []),
    ("S2 GS² refusé", "avec GS² dans la formule", [], ["GS"]),
    ("S2 SS PLUS30 refusé", "horaires quotidiens « SS PLUS30 – SR MIN »", [], ["SS"]),
    ("S2 GS souligné", "GS = TAS = 110 kt", [("GS", "GS")], []),
    ("S2 1 lettre refusée sans nombre", "le L et le m de la liste", [], ["L", "m"]),
    ("S2 nombre à gauche accepté", "emporte 50 l de carburant", [("l", "litre")], []),
    ("S2 élision après un nombre refusée (l')", "Si T = 10 et Td = 5, l'humidité relative est forte.", [], ["l"]),
    ("S2 élision après un nombre refusée (L')", "alors que tu es à 2700. L'altimètre est faux", [], ["L"]),
    ("S2 élision après un nombre refusée (s')", "Le facteur 1,3 s'applique ensuite.", [], ["s"]),
    ("S2 unité après nombre : m, s, lb, °F", "à 50 m, pendant 5 s, 800 lb et 70 °F", [("m", "mètre"), ("s", "seconde"), ("lb", "livre"), ("°F", "Fahrenheit")], []),
    ("S2 unité sans nombre refusée : m, s, lb", "le m et le s puis lb", [], ["m", "s", "lb"]),
    ("S2 Va (VA) souligné en casse exacte", "Va = 112 KIAS, sous Va en turbulence", [("Va", "VA")], []),
    ("S2 va (verbe) jamais souligné", "il va chercher et on va voir", [], ["va"]),
    # ── S3 : pluriels / singuliers automatiques
    ("S3 milles nautiques", "Dix milles nautiques au départ.", [("milles nautiques", "mille nautique")], []),
    ("S3 calages altimétriques", "des calages altimétriques différents", [("calages altimétriques", "calage altimétrique")], []),
    ("S3 flap singulier", "flap extended speed", [("flap", "flaps")], []),
    ("S3 amer singulier", "un amer visuel", [("amer", "amers")], []),
    ("S3 volet aéro (contexte)", "asymétrie de volet à l'atterrissage", [("volet", "volets")], []),
    ("S3 volet radio refusé", "volet radio / ATC / squawk", [], ["volet"]),
    ("S3 volets pluriel inchangé", "il bloque les volets", [("volets", "volets")], []),
    ("S3 index n'attire pas indice", "un indice de risque", [], ["indice"]),
    ("S3 pas de pluriel sur mot-outil", "points de rosée", [("points de rosée", "point de rosée")], []),
    # ── S4 : titres accentués
    ("S4 variomètre", "Le variomètre indique la vitesse verticale.", [("variomètre", "variomètre")], []),
    ("S4 ancienne graphie en variante", "le variometre", [("variometre", "variomètre")], []),
    ("S4 réserve finale", "Tu penses atterrir sous ta réserve finale.", [("réserve finale", "réserve finale")], []),
    ("S4 limite arrière", "à la limite arrière.", [("limite arrière", "limite arrière")], []),
    ("S4 masse à vide", "la masse à vide de l'avion", [("masse à vide", "masse à vide")], []),
    ("S4 pas de repli d'accents global", "il est estimé fatigué", [], ["estimé", "estime", "fatigue", "fatigué"]),
    # ── S5 : aérodrome
    ("S5 aérodrome", "Sur un aérodrome non contrôlé.", [("aérodrome non contrôlé", "aérodrome non contrôlé")], []),
    ("S5 aérodrome seul", "le tour de l'aérodrome", [("aérodrome", "aérodrome")], []),
    ("S5 aérodromes", "plusieurs aérodromes", [("aérodromes", "aérodrome")], []),
    ("S5 Aerodrome anglais", "Terminal Aerodrome Forecast", [("Aerodrome", "aérodrome")], []),
    # ── S6 : AD selon le contexte
    ("S6 AD navigabilité", "Une consigne de navigabilité (AD) non appliquée", [("AD", "consignes de navigabilité")], []),
    ("S6 AD visites CRS", "Visites, CRS, AD, libération", [("AD", "consignes de navigabilité")], []),
    ("S6 AD entretien", "L'entretien courant (50 h, 100 h, AD) maintient l'état", [("AD", "consignes de navigabilité")], []),
    ("S6 AD aérodrome (AIP)", "tu confirmes avec l'AIP AD 2 LFPN, la VAC en vigueur", [("AD", "AD")], []),
    ("S6 ALT AD", "VAC LFPN, case ALT AD : 538 ft", [("AD", "AD")], []),
    # ── homonyme / contexte déjà déclarés (réparation de la chaîne)
    ("S6 vent arrière -> composante arrière", "composante de vent arrière de 10 kt", [("vent arrière", "composante arrière")], []),
    ("S6 casse sensible TORA", "la tora disponible", [], ["tora"]),
    ("S6 contexte requis : base sans circuit", "la base des cumulus est à 1 600 ft", [], ["base"]),
]


def main():
    idx = json.load(open(INDEX, encoding="utf-8"))["terms"]
    fails = []

    def check(label, ok, detail=""):
        print(("ok   " if ok else "FAIL ") + label + ("" if ok else "  -> " + detail))
        if not ok:
            fails.append(label)

    # ── données exportées par la chaîne (le diagnostic en trouvait 0)
    n_ctx = sum(1 for e in idx.values() if e.get("ctx"))
    n_cs = sum(1 for e in idx.values() if e.get("cs"))
    n_hom = sum(1 for e in idx.values() if e.get("hom"))
    check("index : >= 11 champs ctx exportés", n_ctx >= 11, str(n_ctx))
    check("index : >= 4 champs cs exportés", n_cs >= 4, str(n_cs))
    check("index : AD a un homonyme -> consignes de navigabilité",
          (idx.get("AD", {}).get("hom") or {}).get("c") == "consignes de navigabilité", str(idx.get("AD")))
    check("index : vent arrière a un homonyme", "hom" in idx.get("vent arrière", {}), "")
    check("index : Cc n'est plus variante de cirrocumulus", "Cc" not in idx["cirrocumulus"].get("v", []), "")
    check("index : Cc est variante de cap compas", "Cc" in idx["cap compas"].get("v", []), "")
    check("index : AD n'est plus variante de consignes de navigabilité",
          "AD" not in idx["consignes de navigabilité"].get("v", []), "")
    check("index : fiche aérodrome", "aérodrome" in idx and idx["aérodrome"].get("sl") == "aerodrome", "")
    check("index : titres accentués (10 fiches)", all(k in idx for k in (
        "variomètre", "tachymètre", "troposphère", "réserve finale", "limite arrière", "point de décision",
        "marge de décrochage", "aérofrein", "temps de réaction", "masse à vide")), "")
    check("index : anciens titres sans accent retirés comme clés",
          not any(k in idx for k in ("variometre", "tachymetre", "reserve finale", "limite arriere")), "")
    check("index : slug conservé (variomètre -> variometre, redirection inutile)", idx["variomètre"].get("sl") == "variometre", "")

    res = subprocess.run(["node", "-e", DRIVER, ENGINE, INDEX], input=json.dumps([c[1] for c in CASES]),
                         capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr)
        sys.exit("node a échoué")
    out = json.loads(res.stdout)
    check("moteur v1.3.0", out["version"] == "1.3.0", str(out["version"]))
    for (label, text, want, forbid), got in zip(CASES, out["res"]):
        gotset = {tuple(g) for g in got}
        miss = [w for w in want if tuple(w) not in gotset]
        bad = [raw for raw, _ in got if raw in forbid]
        check(label, not miss and not bad, "attendus manquants %s ; interdits trouvés %s ; obtenu %s" % (miss, bad, got))
    print("\n%d échec(s)" % len(fails))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

