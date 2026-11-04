# AeroLex

**Le lexique aéronautique français, libre et posable sur n'importe quel site.**

AeroLex est un glossaire aéro de plus de 1 100 termes, plus un script JS qui souligne
automatiquement le vocabulaire aéronautique d'une page et affiche la définition au clic.
Une ligne à ajouter, rien à configurer.

```html
<script src="https://aerolex.prunel.net/aerolex.js" defer></script>
```

C'est tout. Le script scanne le texte, reconnaît les termes du lexique, les souligne
discrètement et ouvre une définition au clic.

---

## Pourquoi

Le vocabulaire aéro est une barrière réelle pour qui apprend à voler. QNH, calage
standard, TORA, décrabage, collationner, effet de site — chaque mot inconnu casse la
lecture. Les glossaires existants sont des pages à part, qu'on ne consulte jamais en
lisant.

AeroLex met la définition **là où le mot apparaît**, sur le site de n'importe quel
club, école ou blog de pilote.

---

## État

| | |
|---|---|
| Termes au lexique | **1 101** |
| Fiches rédigées | 124 |
| Fiches en construction | 977 |

Les fiches non rédigées affichent « Fiche en construction. » — le lien reste actif,
la rédaction se fait au fil de l'eau. Contributions bienvenues.

### Deux statuts d'origine

- **`corpus`** (962) — le terme apparaît réellement dans un corpus de cours vérifié
  → lien actif sur les pages
- **`metier`** (130) — vocabulaire aéro standard mais absent du corpus
  → fiche consultable, pas de lien actif

Le classement est **mécanique**, jamais un jugement : il découle d'un test de présence.

---

## Règles de conception

**LONGEST MATCH WINS.** Une expression de plusieurs mots est prioritaire sur une plus
courte : `point de rosée` gagne avant `point`, `vent arrière` avant `vent`, `ft/min`
avant `ft`. Une portion de texte déjà consommée par un lien n'est plus candidate.
C'est ce qui rend acceptable la présence d'atomes polysémiques (`va`, `moment`, `plan`,
`air`) qui portent un vrai sens aéro (Va = vitesse de manœuvre).

**Désambiguïsation par contexte.** « Tour » de contrôle et « tour » de piste : oui.
« Faire un tour » : non. Champ `contexte_requis` sur les entrées concernées.

**Variantes morphologiques.** Pluriels, accords, élisions, casse — `rafale` et
`rafales`, `magnétique` et `magnétiques`, `l'azimut`. Générés automatiquement pour les
réguliers, déclarés à la main pour le reste.

**Anti-doublon par forme normalisée.** Avant toute nouvelle fiche : normaliser
(minuscules, accents retirés, ponctuation neutralisée) et confronter à l'ensemble
`clés ∪ variantes ∪ synonymes`. Si collision → enrichir l'existant, ne pas créer.

**Ce qui n'est pas un terme aéro.** Les villes, régions et pays sont exclus (34 retirés) :
on ne définit pas Bordeaux dans un glossaire de vol. Les immatriculations aussi (une
immat identifie une machine, pas un concept). En revanche les **codes OACI sont
conservés** — `LFPN` désigne un terrain avec sa carte VAC, ses pistes et ses
procédures : ça mérite une fiche.

---

## Structure

```
data/
  lexique-filtre.txt        1 092 termes retenus (corpus + métier)
  lexique-candidats.txt     extraction brute avant filtrage
  data_glossaire.py         entrées validées via « Suggérer des termes » (origine=suggest) — entrée du import
  data_glossaire_full.py    STOCK CANONIQUE des fiches (1 303 : v1, lots v2, ajouts manuels) — lu par le build
  PLAN-redaction-fiches.md  méthode de rédaction, 13 lots thématiques
src/
  import_lexique.py         synchronise data_glossaire.py → data_glossaire_full.py (fusion additive)
  build_glossaire.py        génère la page index du glossaire
  svg_glossaire.py          schémas (piste, manche à air, rose des vents…)
dist/                       artefacts publiables (aerolex.js, lexique.json)
```

## Chaîne de construction

```
data/data_glossaire_full.py  ──┐ (stock canonique, fiches jamais écrasées)
data/data_glossaire.py ────────┴─► src/import_lexique.py --write ─► data_glossaire_full.py
                                     ├─► scripts/build_pages.py        (dist/aero/*.html, slugmap)
                                     ├─► scripts/build_terms_json.py
                                     ├─► scripts/build_search_json.py
                                     └─► build_index_js.py             (dist/aerolex.js, lexique.json)
```

Historique : le full a été construit par étapes (v1 757 fiches, lots v2 533, ajouts manuels,
séances) et enrichi (famille, schema, xrefs). L'ancien import « tout reconstruire depuis le
lexique » est périmé : il aurait supprimé ~200 fiches. Depuis la remise à niveau
`import_lexique.py` est une **fusion additive** : il garde le full tel quel, y ajoute les
fiches de `data_glossaire.py` qui n'y sont pas (clé exacte), et n'injecte plus les stubs du
lexique brut (monomots purgés exprès ; option `--with-stubs` si besoin).

**Sécurité** : `python3 src/import_lexique.py` = essai à blanc (affiche le diff, n'écrit rien) ;
`--write` applique (écriture atomique) ; `--check` retourne 1 s'il y a un diff.
Test de non-régression : `python3 scripts/test_import_lexique.py` (rejoue dans un dossier
temporaire, diff = 0 contre le full réel).

## Rédiger une fiche

1. Fiche nouvelle : l'écrire dans `data/data_glossaire.py` (ou la valider via Suggérer), puis
   `python3 src/import_lexique.py --write` pour la propager au full.
   Fiche existante : la corriger directement dans `data/data_glossaire_full.py`
   (l'import n'écrase jamais une fiche déjà présente).
2. Reconstruire les pages (`scripts/build_pages.py` etc., voir la chaîne ci-dessus)

Une fiche minimale porte `definition` (1-2 phrases, ton instructeur) et `categorie`.
Champs optionnels : `variantes`, `synonymes`, `xrefs`, `contexte_requis`, `schema`.

Les 13 lots thématiques de `PLAN-redaction-fiches.md` donnent un ordre de travail
recommandé, du plus mécanique (terrains, codes OACI) au plus délicat (atomes
polysémiques).

---

## Familles (règle : tout terme a une famille)

**Chaque terme, dans TOUT lexique AeroLex (aero et lexiques futurs, cf. `data-lexicon`), a une famille.**
Si aucune famille ne convient : la famille **« Divers »** (slug `divers`). Ça force à classer chaque nouveau
mot, ou à le mettre explicitement dans Divers.

- **« Divers »** existe d'office dans le catalogue des familles de chaque lexique (`scripts/term_display.py` :
  `DIVERS_SLUG`, libellé non surchargeable ; `LexiconIndex.families` dans `suggest_core.py`), toujours affichée
  **en dernier** (index, listes, menu de la carte Suggérer).
- **Suggérer** : le modèle doit répondre par une famille existante, `divers`, ou une nouvelle famille justifiée
  (justification obligatoire + au moins 2 rattachements, ou accord explicite du relecteur). Le contrôle de cohérence
  **bloque** une famille vide et le forçage est impossible pour ce cas. La carte a un menu « Famille » (existantes +
  Divers + « nouvelle famille… ») qui change la famille sans relancer le modèle.
- **Import** : `src/import_lexique.py --write` refuse d'ajouter un terme sans famille (message listant les termes).
  `--default-famille-divers` les met explicitement dans Divers (ne pas l'utiliser sur le vrai lexique).
  Les fiches existantes sans famille (héritage) ne bloquent pas : avertissement avec leur nombre (build_pages.py, import).
- **Nouveau lexique** : il n'existe pas de script de création ; un lexique = une entrée de `LEXICONS` (suggest_core.py)
  + son glossaire. Il hérite d'office de Divers et de la même règle (aucun terme sans famille à l'import).
- **Test** : `python3 scripts/test_familles.py` (0 nouveau terme sans famille, Divers partout, suggest bloque,
  import refuse). Les fiches orphelines historiques sont listées dans `data/familles_orphelines_baseline.txt`
  (avertissement) ; `--strict` échoue s'il en reste, à activer une fois le classement appliqué (puis supprimer
  le fichier baseline).

## Reconnaissance : règles du moteur (aerolex.js v1.3.0)

Une seule fonction décide (`findMatches`, exposée en test par `window.AeroLexCore`) ; tests : `python3 scripts/test_matching.py`.

- **Frontières de mot Unicode** : une lettre accentuée n'est plus une coupure (« écarte » ne contient pas « carte »). Le trait d'union ne
  bloque à gauche que derrière une lettre : « -SHRA » (METAR) est reconnu. Pas de repli d'accents global : « estimé » ≠ « estime ».
- **Sigles de 2 lettres** : acceptés en MAJUSCULES exactes (CG, FL, AD, TS, °C) ou sous leur forme déclarée avec majuscule (Vy, Vx, Cz, Cm…) ;
  refusés en minuscules et pour 1 lettre (sauf nombre à gauche : « 50 l »). Un sigle suivi d'un exposant (« GS² ») n'est pas un sigle.
  `contexte_sigle: [...]` (fiche) : le SIGLE de la fiche n'est lié que si un de ces mots est dans la fenêtre de 70 caractères
  (« CL = 7 » code OMM ≠ Cl ; « SS PLUS30 » ≠ SS).
- **Pluriel automatique** : une expression nom + adjectif sans mot-outil s'accorde en entier (« milles nautiques ») ; avec un mot-outil
  seule la tête varie (« points de rosée »). **Singulier automatique** : « volets » → « volet », « flaps » → « flap » (mots invariants et
  exceptions comme « indices » ↛ « indice » dans INVARIANTS_S / SINGULIER_EXCLUS). `contexte_singulier: [...]` : le singulier généré
  n'est lié que dans ce contexte (« volet radio » exclu). Les surfaces déclarées l'emportent toujours sur les surfaces générées.
- **Contexte / homonyme / casse** (champs de la fiche `contexte_requis`, `homonyme`, `casse_sensible`) : exportés dans l'index (`ctx`,
  `hom`, `cs`) et appliqués. Ils vivent dans `data_glossaire.py` ; `import_lexique.py --write` les COPIE (additif, jamais d'écrasement) vers
  le full pour les fiches existantes — avant le 2026-11-04 cette copie manquait : l'index n'avait aucun `ctx`/`hom`/`cs`.
- **AD** : fiche « AD » (sigle d'aérodrome) ; `homonyme` → « consignes de navigabilité » si la fenêtre contient navigabilité, CRS, Part-M,
  entretien, visite, airworthiness. La fiche « aérodrome » explique le concept (AD y est développé à la 1re occurrence).
- **Titres accentués** : le titre d'une fiche porte ses accents (variomètre) ; l'ancienne graphie reste en variante, le slug (sans accent)
  est inchangé.

## Licence

- **Code** (script JS, outils Python) : MIT
- **Contenu du lexique** (définitions, schémas) : CC BY-SA 4.0

Réutilisation libre, y compris commerciale. Attribution demandée pour le contenu.

---

## Projets liés

- **[AeroTest](https://aerotest.prunel.net)** — banque de questions PPL avec suivi de progression
- **Aero Coach ATCF** — cours PPL qui utilisent AeroLex et AeroTest

## Suggérer des termes (`/aero/suggest.html`)
- **Soumission ouverte, sans jeton** (termes ou fichier ≤ 5 Mo, 300 termes max, suivi `?job=<id>`). Garde-fous de coût : 30 termes envoyés au LLM / h / IP et 300 / jour / IP (IP réelle via `CF-Connecting-IP`), plafond global 2 $/24 h (puis Qwopus local, puis refus poli), 20 analyses de fichier / h / IP. Cache, index et contrôles déterministes : illimités.
- **Revue / validation = mot de passe** : bouton « Espace relecteur » -> POST /login ; session = cookie HttpOnly/Secure/SameSite=Strict 30 j (table SQLite sessions, hachée) ; bouton « Se déconnecter » ; mot de passe hors dépôt (~/.aerolex-suggest-password, 0600, comparaison en temps constant) ; 5 échecs/IP -> blocage 15 min. Plus de jeton. Sous-onglets « À valider » / « Écartés » (repêchage).
- **Écartés automatiquement** : nombre, valeur+unité, unité courante, mot courant sans sens aéro, fragment de phrase, faute de frappe d'un terme existant (distance ≤ 2), puis LLM (`domaine=false` / `pertinent=false`).
- **Contrôle avant « Valider »** (`check_proposal`) : terme absent de l'index courant (alias compris), famille, définition 2-4 phrases non circulaire, initiales du développé = sigle, cohérence avec les fiches voisines (LLM court), confiance < 0,6 → avertissement. Échec = bloquant, avec « Forcer ».
- **Le modèle regarde l'existant** : avant l'appel LLM, les 12 fiches voisines les plus proches (lexical + variantes + TF-IDF local sur définitions/voir aussi ; pas d'index d'embeddings dans le projet) sont passées au prompt (terme | famille | début de définition | voir aussi), avec le catalogue complet des familles (libellé + 3 exemples) et la liste des fiches sans famille. Sortie : famille existante si elle convient, sinon nouvelle famille (libellé lisible + justification), fiches existantes sans famille à rattacher, voir aussi, variantes. La carte affiche « Fiches voisines consultées » (liens), la famille avec libellé et justification, et des cases « Fiches à rattacher à cette famille ».
- **Relance commentée** (session relecteur, plafond de coût du LLM) : champ « Commentaire pour le modèle » -> `POST /proposals/<id>/relaunch`. Le modèle reçoit sa proposition précédente, le commentaire et les voisins, renvoie une nouvelle version ; historique v1, v2… sur la carte, `/proposals/<id>/revert` pour revenir (table `proposal_versions`). La relance contourne et invalide le cache du terme.
- **Rattachements** : à la validation, les fiches cochées reçoivent la famille dans `data_glossaire_full.py` (une ligne ajoutée par fiche, jamais d'écrasement d'une famille existante) et le libellé d'une nouvelle famille est écrit dans `data/familles_labels.json` — dans la même opération sûre (sauvegarde, `import_lexique --write`, rebuild, `test_links_resolve`, restauration auto).
- Tests : `python3 scripts/test_suggest.py`.

### Règles de qualité appliquées d'office à l'ajout d'un mot (2026-11-04)

Le code vit dans `scripts/suggest_rules.py` (règles) et `scripts/suggest_core.py` (prompt d'analyse **et** de relance, contrôles avant « Valider », post-traitement). Chaque carte de proposition montre :

- **Forme de base** : le modèle renvoie `forme_base` ; la forme est comparée au corpus (séances + définitions) : « variometre » alors que le corpus écrit « variomètre » → avertissement + bouton « Utiliser « variomètre » comme terme ». Un pluriel est ramené au singulier ; le sigle reste forme de base seulement si c'est l'usage (VOR, METAR, AVGAS, BEA).
- **Variantes d'appel générées**, une case à cocher chacune (décocher = ne pas écrire dans la fiche) : pluriel/singulier, forme sans accent, équivalent anglais, sigle ↔ développé, synonymes. Sont écartées avec leur raison : toute forme de moins de 3 lettres en minuscules, tout mot grammatical, toute forme déjà appelée par une autre fiche.
- **Fiche existante** : si le terme est une forme d'appel d'une fiche (« vario » → variomètre, « anticyclonique » → anticyclone : abréviation, même radical, ou `variante_de` du modèle), la carte propose le bouton **« Ajouter comme variante de X »** (`POST /api/suggest/proposals/<id>/as-variant`) à la place d'une nouvelle fiche : application sûre (verrou, sauvegarde, ajout dans `data_glossaire_full.py` de cette seule entrée, import + rebuild + test des liens, **restauration automatique** en cas d'échec).
- **Soulignements simulés** (contrôle anti-ridicule, `POST …/simulate` pour la ligne seule) : le moteur `dist/aerolex.js` (exécuté sous Node) est lancé sur le corpus des séances `aero-coach/sessions` avec la nouvelle fiche et ses variantes cochées ; la ligne donne le nombre de nouveaux soulignements, les formes en cause et 3 exemples. **Bloquant (non forçable)** si une forme à risque (homographe courant : liste interne, `homographe_courant` du modèle, ou forme dont plus de 80 % des passages n'ont aucun mot de la définition alentour) souligne plus de 3 cas ou plus de 5 % de faux probables sans `contexte_requis` : il faut fournir les mots déclencheurs (champ « Contexte requis » de l'édition, proposés par le modèle) ou décocher la variante.
- Toujours en place : sigles développés à la 1re occurrence (avec traduction FR ; le développé d'un terme qui est lui-même un sigle entre dans `term_expansions.py`), famille obligatoire ou Divers, slug sûr (translittération, slugs réservés, jamais générique), contrôle des initiales des sigles, fiches voisines, relance commentée, sauvegarde/restauration. Jamais de validation en prod par un script : seul le relecteur valide.

## Créer un nouveau lexique

```
python3 scripts/new_lexicon.py --slug voile --label "Voile" \
    [--source termes.txt] [--famille greement="Gréement et voiles" ...] [--audience "…"] [--scope "…"] \
    [--corpus DOSSIER_DE_PAGES_HTML] [--analysis items.json | --no-llm]
python3 scripts/check_lexicon.py voile        # verdict : LEXIQUE PROPRE ✓ / NON CONFORME ✗
```

Le script crée `lexicons/<slug>/` (racine propre : `data/`, `dist/<slug>/`, et `scripts/`, `src/`, `build_index_js.py` **liés** à la chaîne du projet : une seule chaîne de build, pilotée par `AEROLEX_LEXICON` / `AEROLEX_LEXROOT`, cf. `scripts/lexicon_env.py`) avec d'office :

- famille **Divers** + catalogue de familles de départ (`data/familles_labels.json`, option `--famille`) ; structure `data/` ; métadonnées `data/lexicon.json` ;
- pages **index** (lettres vides masquées, autocomplétion, popups mis en page) et **suggest** (`/<slug>/suggest.html`), slugmap, JSON des fiches / de recherche / de l'index du moteur (`aerolex-<slug>-search.json`, `aerolex-<slug>-index.json`), overlay (recherche + bouton Index) ;
- **moteur v1.3.0** (frontières Unicode, sigles de 2 lettres en casse exacte, pluriel/singulier, `contexte_requis`) copié dans `dist/` ; **cache-bust** par empreinte (`build-info.json`) ;
- déclaration dans `lexicons/registry.json` (lu par `suggest_core` ; **redémarrer** le service `com.prunel.aerolex` pour l'activer).

Avec `--source` (liste de termes `.txt .csv .md .pdf .docx`), les termes passent **en lot** par le même pipeline que « Suggérer » (entonnoir gratuit → analyse du modèle → forme de base → variantes → famille → sigles → anti-ridicule, plus post-traitement automatique : forme de base adoptée, variantes à risque décochées, `contexte_requis` proposé d'après la définition, à relire) et sont déposés dans la file **« À valider »** : rien n'est publié. `--analysis` fournit des analyses déjà faites (JSON, contrat du modèle ; voir `scripts/fixtures/demo-voile-items.json`), `--no-llm` ne contacte pas le modèle (définitions « à rédiger », famille Divers : la validation reste bloquée tant que la définition est vide). Après relecture et « Valider » dans l'espace relecteur, `check_lexicon.py` doit passer du premier coup (preuve : `scripts/test_new_lexicon.py`, lexique de démonstration de 15 termes dont 3 sigles, un mot sans accent, un pluriel, un homographe courant). Limites connues : `term_expansions.py` (développés de sigles) est commun à tous les lexiques ; un sigle dont le développé contient des mots courts (« Safety **Of** Life **At** Sea ») n'est pas résolu par `term_display` (le test des sigles le signale) ; les assets de `dist/` sont copiés à la création (les recopier si le moteur change).

## Règles de qualité d'un lexique

Un lexique est propre quand **toutes** ces règles tiennent (`scripts/check_lexicon.py <slug>` les enchaîne et rend un verdict) :

1. **Forme de base correcte** : accents comme dans les cours/le corpus, singulier, forme française usuelle ; le sigle seulement si c'est l'usage. Titre sans accent alors que le corpus l'accentue = non conforme (contrôle « titres accentués »).
2. **Variantes d'appel** générées et décochables : pluriel/singulier (tous les mots pleins), forme sans accent, équivalent anglais, sigle ↔ développé, synonymes.
3. **Pas de doublon d'appel** : un terme qui n'est qu'une forme d'appel d'une fiche existante devient une variante de cette fiche (bouton « Ajouter comme variante »), pas une nouvelle fiche.
4. **Anti-ridicule bloquant** : simulation du soulignement sur le corpus des séances (nombre de nouveaux soulignements + 3 exemples) ; homographe courant ⇒ `contexte_requis` exigé ou variante retirée ; **aucune variante de moins de 3 lettres en minuscules, aucun mot grammatical** (contrôles « variantes » de `check_lexicon`).
5. **Sigles développés** à la 1re occurrence (traduction française si le développé est étranger), initiales cohérentes avec le sigle (tests `acronyms`, `family_acronyms`).
6. **Famille obligatoire** (Divers à défaut), catalogue de familles cohérent (`familles --strict`).
7. **Slug sûr** (translittération, slugs réservés évités, jamais générique) et liens résolus (`slugs`, `links_resolve`) ; fiches voisines proposées.
8. **Moteur v1.3.0** : frontières Unicode, sigles de 2 lettres en casse exacte, pluriel/singulier, `contexte_requis` (`matching` ; aller-retour : chaque titre et chaque variante est reconnu et mène à sa fiche).
9. **Chaîne officielle sans écart** : `import_lexique --write → build_pages → build_terms_json → build_search_json → build_index_js` ; `import --check` = 0 écart ; cache-bust à jour ; index à lettres vides masquées avec autocomplétion.
10. **Sauvegarde/restauration** à chaque validation ; relance commentée ; **jamais de validation en prod par un script**.

Tests : `python3 scripts/test_suggest.py` (règles de qualité en section 13), `python3 scripts/test_new_lexicon.py`, `python3 scripts/check_lexicon.py aero`. (Pas de `CODING.md` dans ce projet : les règles de code sont dans `projects/coding-rules.md`.)
