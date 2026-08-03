# AeroLex — Chantiers qualité (demandés par Louis, 03/08/2026 20h26)

## 1. Relecture des 124 fiches d'origine — EN COURS
Les 124 fiches `redigee` du corpus initial n'avaient JAMAIS été relues :
elles cohabitaient avec 645 fiches récentes d'un autre style.

Diagnostic mesuré :
- longueur 20 → **92 mots** (médiane 36) vs 21-45 pour les nouvelles
- **37 fiches sur 124 (30 %) hors cible 20-45 mots**
- **79 fiches sur 124 (64 %) contiennent du HTML** (`<em>`, `<strong>`)
- 1 « POH » + 1 « poids » à corriger
- pires cas : vent arrière 92 mots, courte finale 81, vent traversier 79,
  roulement 79, dernier virage 78, piste 76, verticale terrain 74, décollage 74

→ Lots `RELECTURE-in-1/2.json` envoyés en relecture (62 + 62).
   Consigne : condenser, retirer le HTML, ajouter les `xrefs`,
   NE PAS réécrire ce qui est déjà bon (`modifie: false` attendu et valide).

## 2. Fiche de référence = « niveau de vol »
Citée par Louis comme le bon standard. À utiliser comme mètre-étalon du rendu final.
Ce qui la rend bonne, et qu'il faut généraliser :
1. un **exemple chiffré concret** (FL45 = 4500 ft)
2. le **contexte d'usage réel** (« en croisière au-dessus de l'altitude de transition »)
3. des **`xrefs`** vers les 2-4 notions prérequises
4. dense, 25-40 mots
⚠️ Les 645 nouvelles fiches ont `famille`/`membres_famille` mais **PAS de `xrefs`** → manque à combler.

## 3. ⚠️ EXHAUSTIVITÉ PAR CATÉGORIE vs programme PPL — PAS FAIT
**À RAPPELER À LOUIS TANT QUE CE N'EST PAS FAIT.**

Le corpus vient d'un **scraping**, pas du programme officiel PPL → il a des trous.
Il faut reprendre les cours PPL catégorie par catégorie et lister les termes manquants.

Exemple donné par Louis : **les nuages**.
On a 24 termes en famille `nuages`, mais la classification OACI compte
**10 genres** : cirrus, cirrocumulus, cirrostratus, altocumulus, altostratus,
nimbostratus, stratocumulus, stratus, cumulus, cumulonimbus
+ les espèces et variétés au programme (castellanus, lenticularis, congestus,
humilis, mediocris, fractus, calvus, capillatus…).

Autres catégories à auditer de la même façon :
- espaces aériens (classes A à G, TMA/CTR/CTA/AWY, zones P/R/D)
- vitesses caractéristiques (VS0/VS1/VA/VNO/VNE/VFE/VLE/VX/VY/VBG/VRA)
- feux de balisage (seuil, extrémité, axe, PAPI/VASIS, taxiway)
- messages météo (METAR/TAF/SIGMET/AIRMET/GAMET/ATIS/VOLMET)
- documents de bord, marquages de piste, signaux visuels

Méthode proposée : 1 sous-agent par catégorie, en s'appuyant sur le programme
théorique PPL FR (annexe des matières examen) → liste des termes attendus
→ diff avec le lexique → rédaction des manquants.
