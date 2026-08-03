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

## 4. PROCÉDURE D'AJOUT DE TERMES (à écrire quand on aura bien avancé)
Demandé par Louis le 03/08/2026 20h33.

Besoin : pouvoir ajouter plus tard une LISTE de mots oubliés et les intégrer
PARTOUT où ils doivent apparaître, **sans reconsommer d'immenses ressources**.

Ce que la procédure devra couvrir (chaque endroit à toucher) :
1. `data/data_glossaire_full.py` — la fiche elle-même (definition, categorie,
   famille, variantes, synonymes, xrefs, statut)
2. `membres_famille` de TOUS les membres de la famille du nouveau terme
   (réciprocité : si on ajoute `cirrus` à `nuages_genres`, les 12 autres
   doivent le voir apparaître dans leur tableau)
3. `xrefs` réciproques éventuelles
4. `colonnes_tableau` + `schema` héritées de la famille
5. rebuild `dist/aerolex-index.json` (build_index_js.py)
6. rebuild `assets/glossaire-data.js` (src/build_glossaire.py)
7. compteurs en dur de `dist/index.html` (termes / rédigées / familles / liens)
8. commit + push

Contrainte d'économie (le point important pour Louis) :
- **NE PAS refaire tourner un agent sur les 769 fiches.** L'ajout doit être
  INCRÉMENTAL : seuls les N nouveaux termes passent à la rédaction, et seule
  leur famille est recalculée (pas le corpus entier).
- Un script `scripts/ajouter_termes.py` prenant en entrée un simple
  `nouveaux.json` : `[{"terme":"cirrus","famille":"nuages_genres"}, ...]`
  → rédaction Gemini du seul lot des nouveaux → merge → recalcul de la
  réciprocité SUR LES FAMILLES TOUCHÉES UNIQUEMENT → rebuild → rapport.
- Coût cible : proportionnel au nombre de mots ajoutés, pas à la taille du brain.

Leçons à intégrer dans la procédure (vécues le 03/08) :
- vérifier chaque rendu d'agent SUR DISQUE, ne jamais croire son rapport
- interdire les valeurs chiffrées propres à un avion (incident Aquila AT01)
- ne jamais laisser un agent "consolider" globalement : il supprime des familles
  entières en croyant nettoyer (incident assemblage : 64 familles -> 5)
- écrire le .py avec repr(), pas json.dumps (sinon `false` au lieu de `False`)

## 5. 🎯 INDEX PERSONNALISÉS PAR N'IMPORTE QUI (feature produit majeure)
Demandé par Louis le 03/08/2026 20h40.

Vision : AeroLex n'est pas qu'un lexique aéro — c'est un **moteur de lexique**.
N'importe qui doit pouvoir créer SON propre index de vocabulaire métier et le
poser sur n'importe quel site avec la même ligne de `<script>`.

### Les 3 voies de création (cumulables)
1. **Import** — l'utilisateur fournit un fichier existant : CSV, JSON, XLSX,
   glossaire Markdown, export Notion/Airtable. Mapping des colonnes
   (terme / définition / catégorie / variantes) puis validation.
2. **Manuel** — éditeur web : ajouter/modifier/supprimer une fiche, gérer
   variantes, synonymes, familles, xrefs. Pour l'artisan qui a 40 termes.
3. **IA** — deux entrées possibles, combinables :
   a. **À partir d'un domaine décrit** : « je suis charpentier couvreur en
      France » → l'IA propose la liste des termes du métier, l'utilisateur
      coche/décoche, puis l'IA rédige les définitions.
   b. **À partir de documents** : l'utilisateur dépose ses PDF/DOCX/pages web
      (manuel interne, cours, doc technique) → extraction du vocabulaire
      spécifique (fréquence + saillance), dédup contre un index générique,
      puis rédaction.
   c. **Les deux** : documents pour le vocabulaire réel + domaine décrit pour
      combler les trous (exactement le pipeline qu'on vient de faire sur le PPL).

### Ce que ça implique techniquement
- **Multi-index** : le runtime `aerolex.js` doit charger un index par ID
  (`aerolex.js?index=charpente` ou attribut `data-index`), plus un index par défaut.
- **Stockage** : un index = 1 JSON (clés + variantes) + 1 JS de définitions.
  L'index PPL fait 30 Ko / 7,8 Ko gzip pour 769 termes → très supportable.
- **Namespace / propriété** : qui possède l'index, public ou privé, licence.
- **Coût IA maîtrisé** : réutiliser la logique incrémentale du point 4
  (ne rédiger que les nouveaux termes, jamais tout le corpus).
- **Garde-fous héritant des leçons PPL** : interdiction des valeurs chiffrées
  propres à un modèle/machine, format 20-45 mots, pas de HTML dans les défs,
  familles ≤ 13 membres, `famille: null` autorisé.
- **Modération** : un index public créé par IA doit pouvoir être signalé/relu.

### Pourquoi c'est fort
Le même moteur sert le PPL, la charpente, le droit notarial, la viticulture,
la plomberie, un jargon d'entreprise interne. La valeur n'est pas le contenu
aéro : c'est la **mécanique de lexique posable partout**.

---

## 6. 📌 RÈGLE DE TRAVAIL — un TODO-FEATURES.md par projet
Demandé par Louis le 03/08/2026 20h40.

**Sur CHAQUE projet** : créer un `TODO-FEATURES.md` à la racine et le
**maintenir au fur et à mesure du développement** — pas en fin de chantier.

Contenu attendu : features souhaitées, chantiers en cours, dettes techniques
identifiées, leçons vécues sur le projet, et ce qui reste à faire avec assez
de contexte pour être repris à froid après un restart.

Règle : dès qu'une idée de feature ou un manque est évoqué en conversation,
il atterrit dans le TODO-FEATURES.md du projet concerné DANS LA MÊME SESSION.
