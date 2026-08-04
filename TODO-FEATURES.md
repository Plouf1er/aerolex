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

## 4quater. 🔒 DOMAINES AUTORISÉS PAR LEXIQUE (CORS) — Louis 04/08 02h10

**Décision Louis** : les `t/<slug>.json` vivent à UN SEUL endroit
(`aerolex.prunel.net`), les sites clients (ATCF et autres) les appellent en
cross-origin. On ne duplique PAS les fichiers chez chaque client — sinon on
recrée le problème des deux copies divergentes (vécu le 04/08 avec deux `aero.js`).

**Origine fermée à des domaines déclarés dans un premier temps** (pas `*`).
Plus facile d'élargir que de restreindre, et c'est le prérequis de la
facturation au trafic (§4bis) : `*` = service gratuit pour tout le monde.

### À prévoir dans le modèle de données (demande explicite de Louis)
Chaque lexique porte sa **liste de domaines autorisés à la consommation**.
Le champ doit accepter plusieurs granularités de motif :

| Motif | Sens |
|---|---|
| `atcf-ppl.prunel.net` | un hôte exact |
| `*.xyz.com` | tous les sous-domaines d'un domaine |
| `*.*.*` / `*` | tout ouvert (lexique public, à assumer) |

Implications à spécifier :
- Le champ appartient au **lexique** (un index = un jeu de domaines), pas au terme.
- CORS ne se négocie pas par wildcard côté navigateur : `Access-Control-Allow-Origin`
  ne peut renvoyer qu'UNE origine (ou `*`). Donc pour une liste/motif, il faut
  **comparer l'`Origin` de la requête au motif et répondre en écho** l'origine
  si elle matche → un `_headers` statique de Cloudflare Pages NE SUFFIT PAS dès
  qu'il y a plusieurs domaines ou un wildcard. Il faut une Cloudflare Function /
  Worker devant `/aero/t/*`. ⚠️ À acter avant de promettre la feature.
- Prévoir `Vary: Origin` sinon le cache CF sert la mauvaise en-tête au domaine suivant.
- Un refus doit être lisible côté client (403 explicite plutôt qu'une erreur CORS
  opaque, qui est indébuggable dans la console).
- Lien §4bis : c'est le même Worker qui peut compter les appels par `Origin`
  → CORS et facturation partagent le point de passage.

⚠️ **Dépendance externe acceptée** : si `aerolex.prunel.net` tombe, les popups
des sites clients meurent (avec des fichiers locaux, non). Prix normal d'un
service centralisé, Louis en est informé (04/08 02h04).

## 4bis. 📊 STATS D'APPEL PAR FICHIER → FACTURATION AU TRAFIC (Louis 04/08 02h03)

Bénéfice secondaire de l'architecture « fichier par mot », relevé par Louis :
en plus d'alléger les pages client (index 370 Ko → 90 Ko), **chaque définition
est désormais une requête HTTP distincte** (`t/<slug>.json`) — donc mesurable
individuellement, sans aucun code de tracking à écrire.

Ce que ça débloque :
- **Facturation à l'usage / au trafic** pour les index tiers (voir §5 : moteur
  de lexique multi-clients). Le volume d'appels = la valeur consommée.
- **Analytics de contenu gratuits** : quels termes sont réellement cliqués,
  lesquels ne le sont jamais (candidats à la suppression), quels termes sont
  cherchés mais absents (404 sur `t/`).
- **Priorisation éditoriale par la donnée** : rédiger/enrichir d'abord les
  termes les plus consultés au lieu de deviner.

Implémentation pressentie (à spécifier, RIEN de fait) :
- Les logs Cloudflare portent déjà l'info (chemin + référent + horodatage) →
  pas besoin d'un backend au départ. Vérifier ce que le plan CF actuel expose
  (Analytics GraphQL vs Logpush) avant de construire quoi que ce soit.
- Agrégation par `index_id` + `slug` + jour. Le `slug` est dans l'URL, donc
  aucune instrumentation côté JS n'est nécessaire.
- ⚠️ Le **cache** fausse le comptage : un terme mis en cache navigateur/CF ne
  génère plus de hit. Pour de la facturation, compter au niveau CF (avant le
  cache navigateur) et assumer le biais, ou définir l'unité facturable comme
  « appel origine » plutôt que « consultation ». À trancher AVANT de vendre.
- ⚠️ RGPD : agréger, ne pas conserver d'IP. Des compteurs par slug suffisent.

Lien avec §5 : c'est le compteur qui rend le plan pro « schémas » et l'usage
en mode `open` facturables — deux arbitrages déjà ouverts dans TODO-ETAT §4.

## 4ter. 🔤 SÉPARATION MOT / DÉFINITIONS (Louis 04/08 01h43) — HAUT DE PILE

**Décision Louis** : un mot peut porter **N définitions**. On sépare la notion
de *mot* (la forme, le slug, le matching) de celle de *définition* (le contenu).

Ce que ça résout d'un coup — deux arbitrages du modèle v4 en une idée :
- **Homonymes (9)** : plus besoin d'élire un « sens par défaut ». `dérive` = UNE
  page, deux définitions listées (Navigation / Empennage), chacune avec sa
  famille et ses xrefs. Le lecteur voit l'ambiguïté → supérieur pédagogiquement
  à un choix arbitraire qui cache l'autre sens. `context_reroute` devient un
  confort, plus une nécessité.
- **Fusions (11)** : plus rien à détruire. Sur MTOW (3 fiches, 3 définitions
  rédigées et correctes), les 3 cohabitent ; `MTOW`/`MTOM` deviennent des formes
  de surface. Aucune définition ne meurt → l'arbitrage « laquelle survit »
  disparaît.

**Format rétro-compatible (proposé par Louis, retenu)** :
- `definition` reste une **chaîne** quand il n'y a qu'un sens ;
- un tableau `definitions[]` apparaît **seulement** s'il y en a plusieurs ;
- le JS teste le type et gère les deux.
→ Conséquence : **1 299 payloads inchangés**, seul `dérive` prend la forme
  enrichie. Ce n'est PAS une migration des 1 300 fichiers (ma première
  estimation était fausse) — c'est un ajout sur un fichier + du code défensif.

À faire :
1. Fable met à jour le modèle de données v4 avec cette forme (EN COURS).
2. `aero.js` / `aerolex.js` : gérer chaîne ET tableau (déjà dans le brief du
   chantier popup en cours, en défensif).
3. Popup avec 2+ définitions : empiler quand il y en a 2, replier au-delà
   (« + 1 autre sens »). Cas rare : 1 seul homonyme identifié sur 1 300 termes.
4. Le `v` (payload_version) doit protéger ce changement de forme — c'est
   exactement le rôle du contrat versionné (leçon du bug popup du 04/08 :
   une clé qui change de sens entre deux formats casse le consommateur).

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

### 5bis. 🧩 EMBED DU LEXIQUE HTML CHEZ UN TIERS (Louis 04/08 02h50)

Verbatim Louis : « Note aussi dans la ToDo features qu'on pourrait faire en sorte
de permettre l'embed de toute la partie HTML du lexique si quelqu'un veut mettre
ça sur son site. »

Même logique de plateforme que le §5 (index personnalisés) : aujourd'hui on pose
une ligne de `<script>` qui **surligne les mots d'une page existante**. L'embed,
c'est l'autre moitié du produit : poser **le lexique lui-même** (les pages fiches
+ l'index A-Z) à l'intérieur d'un site tiers, comme une section de leur site.

Ce qui serait intégrable :
- l'**index A-Z** complet (liens seulement, cf. décision SEO en TODO-ETAT §3)
- les **pages fiches** `<slug>.html` (définition, famille, tableau, xrefs, SVG)
- la **recherche** dans le lexique

Trois techniques possibles, à trancher (aucune retenue) :

| Voie | Avantage | Coût |
|---|---|---|
| `<iframe>` | isolation CSS totale, zéro conflit | pas de SEO pour l'hôte, hauteur à gérer, style « encart étranger » |
| Web component (`<aerolex-lexique>`) | Shadow DOM = isolation propre, s'intègre au flux de la page | rendu client → SEO faible sans SSR |
| Snippet JS qui injecte dans le DOM hôte | CSS de l'hôte hérité (look natif), indexable si rendu tôt | collisions de styles, le risque réel |

→ Dépend directement du **§7bis (thème CSS des pages HTML)** : un embed sans thème
  personnalisable rend un bloc qui jure avec le site hôte. Les deux features vont
  ensemble.

Questions ouvertes à noter :
- **Isolation du style** : Shadow DOM ou préfixe `--aerolex-*` sur tout ? On a déjà
  23 variables CSS (§P4 de TODO-ETAT) → base saine, mais insuffisante si l'hôte a
  un reset agressif.
- **CORS** : mêmes contraintes qu'en §4quater (domaines déclarés, `Vary: Origin`,
  Worker devant `/aero/t/*`). L'embed multiplie les origines appelantes → la liste
  de domaines autorisés devient le point de contrôle central.
- **Attribution / branding** : « propulsé par AeroLex » obligatoire en gratuit,
  retirable en payant ? À décider AVANT d'ouvrir la feature.
- **Comptage d'usage** : un embed génère beaucoup plus d'appels qu'une pose de
  surlignage → l'unité facturable du §4bis doit être revue pour ce mode.
- **URL canonique / SEO** : si le lexique est embarqué sur 10 sites, qui porte la
  canonique ? (`rel=canonical` vers `aerolex.prunel.net` par défaut.)

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

---

## 7. 🧹 NETTOYAGE DES DONNÉES — CAS D'ÉCOLE (Louis 04/08 : « ajoute ce cas à notre sujet nettoyage dans le fichier des features »)

> **La méthode elle-même est dans `TODO-ETAT.md` §6** (cas réels mesurés + les
> 6 contrôles à automatiser). Cette section garde les **spécimens de référence** :
> les cas concrets qui servent de test de non-régression au futur pipeline de
> nettoyage vendu avec la plateforme (§5).

### 7.1 Spécimen n°1 — `MTOW` en TRIPLE (contrôle n°3 de la méthode)

Mesuré le 04/08 sur `dist/aero/t/`. Ce n'est pas un doublon, c'est un **triplon** :

| Slug | Terme affiché | Famille déclarée | Problème |
|---|---|---|---|
| `mtow` | `MTOW` | `documents_bord` | ❌ **FAUSSE famille** — c'est une masse, pas un document de bord |
| `masse-maximale-au-decollage` | `masse maximale au décollage` | `masses` | ✅ la bonne fiche — porte **déjà `MTOW` en variante** |
| `mtom` | `mtom` | — | ❌ 3e fiche, même notion (*Maximum Take-Off Mass*), casse minuscule |

**Les TROIS ont une définition rédigée et correcte** (96 à 311 caractères). Il n'y
a donc rien à jeter : le nettoyage ne peut pas être « supprimer les 2 mauvaises ».

**Conséquence constatée par Louis en usage réel** : `MTOW` est à la fois un terme
autonome ET une variante d'un autre terme → conflit de résolution dans le moteur
→ **`MTOW` ne se surligne pas dans les cours**.
C'est une **fonctionnalité cassée**, pas une coquetterie de données. C'est
l'argument qui justifie que le nettoyage soit une étape du produit et pas une
option de confort.

**Pourquoi c'est LE spécimen de référence du contrôle n°3** (« sigle présent à la
fois comme terme ET comme variante d'un autre terme ») : il cumule les 4 pathologies
que le contrôle doit attraper d'un coup —
1. sigle = terme autonome **et** variante ailleurs (le conflit) ;
2. famille manifestement fausse (`documents_bord` pour une masse) ;
3. variante de casse traitée comme un terme distinct (`mtom`) ;
4. contenu rédigé des deux côtés → interdit de résoudre par suppression sèche.

→ Tout pipeline de nettoyage doit être testé sur ce cas avant d'être considéré
  comme fonctionnel. Correction opérationnelle détaillée : `TODO-ETAT.md` §0.1.

---

## 7bis. 🎨 PERSONNALISATION DU CSS DES PAGES HTML (Louis 04/08 02h50)

Verbatim Louis : « là aussi on pourrait permettre dans le modèle de données de
personnaliser le CSS de la partie HTML »

État : le modèle prévoit **déjà** un thème CSS pour l'**overlay / popup** (décision
actée, TODO-ETAT §3 : « Thème CSS : appartient au lexique, choisi par pose ;
override 3 crans ; anti-injection par whitelist + validation typée »).
→ **Étendre le même principe aux PAGES fiches HTML** et à l'index A-Z, avec le
même mécanisme (variables `--aerolex-*`, whitelist, validation typée) et le même
propriétaire (le thème appartient au lexique, la pose choisit).

Bénéfice direct : c'est ce qui rend le **§5bis (embed chez un tiers)** présentable.
Un lexique embarqué doit ressembler au site hôte, pas à AeroLex.

⚠️ **Rappel de gouvernance déjà décidée — ne pas fusionner les deux axes** :
- le **thème** dit « **de quoi ça a l'air** » → CSS uniquement ;
- les **options** disent « **qu'est-ce qui existe** » → quels blocs sont émis
  (tableau de famille, xrefs, schéma, compteurs…).

Si on les fusionne, le CSS se met à créer/masquer du contenu : on ne sait plus ce
qui est réellement dans la page (mauvais pour le SEO, pour l'accessibilité, et
indébuggable). Un bloc masqué en CSS est toujours envoyé ; un bloc non émis, non.
Deux champs distincts dans le modèle de données, jamais un seul.

---

## 8. 🔗 FICHE À N DÉCLENCHEURS / ANNUAIRE MULTI-ENTRÉES (Louis 04/08 02h34→02h50) — À TRANCHER

### Ce que Louis a dit (verbatim)

**02h34** : « je vois le terme "masse maximale au décollage" je me dis que c'est
la même chose que "MTOW". On devrait dans ce cas là avoir la possibilité d'écrire
une fiche "masse maximale au décollage (MTOW)" qui peut être déclenchée par
plusieurs termes non ? A discuter ensemble et à mettre en ToDo pour trancher pour
plus tard »

**02h39** : « MTOW est le terme le plus facile à retenir je pense, et masse
maximale au décollage pourrait être la variante aussi... dans le langage aéro,
MTOW est peut-être la fiche de base ? D'un autre côté dans l'annuaire des termes
les deux doivent pouvoir exister donc peut-être que c'est deux noms qui renvoient
vers le même contenu ? »

**02h50** : « Peu importe l'URL canonique du contenu, on peut mettre dans
l'annuaire les différentes formes de recherche, ici par exemple MTOW et masse
maximale au décollage ou toute autre forme jugée réellement utile / utilisée. »

### ✅ Décision acquise (04/08 02h50)

**L'annuaire (index A-Z) liste PLUSIEURS formes pointant vers UN contenu unique.**
Une fiche a N déclencheurs (matching) **et** N entrées d'annuaire (navigation),
pour un seul contenu rédigé.
**L'URL canonique est un choix technique/SEO, pas éditorial** — donc elle ne doit
plus bloquer la décision de contenu. C'est ce qui débloque le cas MTOW : on n'a
plus à élire « le vrai nom », seulement « la vraie adresse ».

Conséquence sur le modèle de données : les formes de surface (`MTOW`,
`masse maximale au décollage`, `MTOM`) sont un **jeu de clés** attaché à la fiche,
utilisé à la fois par le moteur de surlignage ET par le générateur d'index A-Z.
Aujourd'hui `variantes` sert au matching mais **pas** à l'annuaire → c'est le
delta à implémenter.

### ⬜ Reste à trancher

1. **Quelle forme est canonique, fiche par fiche.** Piste proposée (à valider) :
   - **sigle canonique** quand c'est le terme d'usage réel du métier :
     `MTOW`, `METAR`, `QNH`, `PAPI`, `TAF`, `ATIS`…
   - **terme français canonique** quand le sigle est rare ou ambigu.
   - champ `canonique: true` **décidé fiche par fiche**, pas par règle automatique.
   - Volume réel : **~30-50 cas concernés**, pas 1 300. Ce n'est pas un chantier
     de masse, c'est une liste à relire une fois.
2. **Titre d'affichage** : `masse maximale au décollage (MTOW)` est acceptable —
   **MAIS** le sigle doit rester une **variante déclarée** dans les données, et ne
   JAMAIS être matché en parsant le titre. (Sinon on reconstruit un flag menteur :
   une donnée déduite d'une chaîne d'affichage → §5 « leçon de la soirée ».)
3. **SEO / redirections** : faut-il une page de redirection légère `mtow.html` →
   canonique, pour ne pas perdre les entrées de recherche sur le sigle ?
   Options : page HTML minimale avec `rel=canonical` + `<meta refresh>`, ou vraie
   301 côté Cloudflare. À trancher avec le chantier `aerolex.prunel.net`.

### ⚠️ Ne pas confondre avec la multi-définition (§4ter)

Deux axes **indépendants**, à ne jamais mélanger dans le modèle :

| | Axe | Exemple | Mécanisme |
|---|---|---|---|
| **§8 (ici)** | **UN sens, plusieurs noms** | MTOW = masse maximale au décollage = MTOM | N déclencheurs + N entrées d'annuaire → 1 contenu |
| **§4ter** | **UN nom, plusieurs sens** | `dérive` = navigation / empennage | 1 forme → `definitions[]` (N contenus) |

Une fiche peut cumuler les deux (plusieurs noms **et** plusieurs sens) : c'est
justement pour ça qu'il faut deux champs séparés et pas un bricolage commun.

---

## 7ter. 🎯 PRIORITÉ DE MATCHING : LONGEST-MATCH + EXCLUSIONS CONTEXTUELLES (Louis 04/08 03h07)

Point de départ de Louis : « si `nœud papillon` apparaît dans un texte, il ne faut
pas surligner `nœud` » → « qu'en penses-tu ? ». **DEUX mécanismes distincts, à ne
jamais fusionner** : le premier est automatique et sans maintenance, le second est
manuel et doit rester rare.

### (a) Longest-match — priorité, automatique, ZÉRO maintenance ✅ déjà en place

Principe standard de tokenisation : si `nœud papillon` est lui-même un terme du
lexique, le moteur le préfère à `nœud` **sans qu'on déclare quoi que ce soit**.

**MESURÉ dans le run du 04/08 : oui, le moteur fait du longest-match.**
`buildRegex()` (`dist/aerolex.js`) trie les surfaces par **nb de mots DESC puis
longueur DESC** avant de les joindre en alternation ; une alternation JS retient la
première branche qui matche, donc la plus longue gagne. Vérifié : la 1ʳᵉ branche est
`services de sauvetage et de lutte contre l'incendie des aéronefs` (63 car.), la
dernière `θ` (1 car.).

⚠️ **Ce tri était FAUX jusqu'au correctif de ce run** : `buildRegex` poussait dans
la regex le terme CANONIQUE au lieu de la SURFACE (`{t: ciMap[lc].canon||lc}` →
`{t: lc}`). Le longest-match s'appliquait donc aux canoniques, pas aux formes
réellement cherchées — et surtout **1477 surfaces sur 2763 (les variantes, pluriels
et abréviations) n'entraient jamais dans la regex**. C'est la cause racine du
« `nœuds` pas surligné » (ce n'était PAS un problème de ligature `œ`).

**Collisions mesurées** : **744 surfaces sur 2763** sont sous-chaîne d'une autre
surface du lexique. Elles sont donc déjà arbitrées par le tri — mais uniquement pour
les surfaces réellement présentes dans le texte. Exemples : `1013` ⊂ `1013,25 hPa`,
`7500` ⊂ `code 7500`, `100LL` ⊂ `carburant 100LL`, `25 kHz` ⊂ `espacement 25 kHz`,
`500 pieds` ⊂ `hauteur de 500 pieds`, `AAL` ⊂ `ft AAL`, `abaque` ⊂ `abaques`,
`cap` ⊂ `cap magnétique`, `finale` ⊂ `courte finale`, `piste` ⊂ `axe de piste`.

**À faire** : rien pour le cas `nœud papillon` — il suffit que l'expression longue
SOIT un terme du lexique. Corollaire à documenter dans la procédure d'ajout (§4) :
*ajouter l'expression longue comme terme est la bonne réponse à une collision, pas
déclarer une exclusion*.

### (b) Exclusions contextuelles — DERNIER RECOURS, manuel

Utile seulement quand l'expression longue **n'a pas** vocation à être un terme du
lexique (`nœud papillon` dans un lexique aéro : hors sujet, on ne va pas créer la
fiche). On veut alors bloquer `nœud` sur cette expression précise.

**Modélisation retenue : attachée AU TERME, pas globale.** C'est `kt` qui déclare
son exclusion, dans sa propre fiche :

```json
"kt": { "v": ["nœud","nœuds"], "excl": ["nœud papillon", "nœud coulant"] }
```

Raison : l'exclusion **voyage avec la fiche**. Export d'un lexique, réutilisation
d'un terme dans un autre index, suppression du terme → l'exclusion suit ou disparaît
avec lui. Une liste globale d'exclusions serait un fichier orphelin que personne ne
nettoie, et qui référencerait des termes supprimés.

Sémantique : `excl` = liste d'expressions ; si une occurrence du terme tombe DANS
une de ces expressions, elle n'est pas surlignée. Implémentation côté moteur
partagé (`applyGlossaryToTextNode` + `resolveSurface`), jamais en local.

### 🚨 Règle d'usage à graver — l'exclusion est le DERNIER recours

**Avant de déclarer une exclusion, vérifier que la variante elle-même n'est pas
fautive.** Ordre obligatoire :

1. La variante est-elle légitime ? (`nœud` comme variante de `kt` : oui) — sinon
   **corriger/supprimer la variante**, pas ajouter une exclusion.
2. L'expression longue devrait-elle être un terme ? → l'ajouter, le longest-match
   (a) règle le cas tout seul, zéro maintenance.
3. Un contexte requis (`ctx`, déjà au modèle) suffit-il ? → le préférer.
4. **Seulement alors**, une exclusion.

**Risques explicites** (à surveiller, pas à ignorer) :
- **un champ que personne ne remplit** : l'exclusion demande d'anticiper des
  expressions absentes du corpus → il restera vide et donnera une fausse impression
  de couverture ;
- **rempli à la place de corriger une mauvaise variante** : c'est le vrai danger.
  Une exclusion masque le symptôme d'une variante trop large (ex. `l` pour `litre`)
  au lieu de la retirer. Toute exclusion ajoutée doit citer laquelle des 4 étapes
  ci-dessus a été écartée et pourquoi.
- Corollaire mesuré ce run : les surfaces de 1-2 caractères (`l`, `m`, `s`, `cc`,
  `co`, `cv`, `cm`, `fl`, `lb`… — **13 surfaces**) sont des variantes trop larges.
  Traitées par une règle générale (unité signifiante seulement si précédée d'un
  nombre ou en casse exacte), PAS par 13 exclusions. Illustration de l'étape 1.

### (c) Règle xref / famille (issue de l'audit du 04/08, §T3)

Dérivée du cas `tour-de-piste` :
- xref pointant vers un **membre d'une famille du terme** = **bruit** → le tableau
  de famille l'affiche déjà, le xref n'ajoute rien ;
- xref pointant vers une **autre famille** = **signal qu'une famille manque** au
  terme → candidat multi-familles.

**Mesuré sur les 1300 fiches : 966 xrefs de bruit / 943 candidats** (1909 xrefs au
total, soit 50,6 % de bruit, sur 519 fiches). **Pathologie de fond, pas un cas
isolé.** Détail : `data/audit-xrefs-familles.md` + `.json`.

Ordre de correction : **multi-familles d'abord, purge du bruit ensuite** (un xref
hors famille devient intra-famille dès que la 2ᵉ famille existe → le bruit augmente
mécaniquement, purger avant serait mesurer sur une base fausse). Le rendu client
accepte DÉJÀ un tableau de familles (`_payloadFamilles`) et produit un tableau par
famille : côté client, rien à faire.
