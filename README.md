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
- **Revue / validation = jeton** (`~/.aerolex-suggest-token`, onglet visible seulement si `#t=…` a été posé en localStorage). Sous-onglets « À valider » / « Écartés » (repêchage).
- **Écartés automatiquement** : nombre, valeur+unité, unité courante, mot courant sans sens aéro, fragment de phrase, faute de frappe d'un terme existant (distance ≤ 2), puis LLM (`domaine=false` / `pertinent=false`).
- **Contrôle avant « Valider »** (`check_proposal`) : terme absent de l'index courant (alias compris), famille, définition 2-4 phrases non circulaire, initiales du développé = sigle, cohérence avec les fiches voisines (LLM court), confiance < 0,6 → avertissement. Échec = bloquant, avec « Forcer ».
- Tests : `python3 scripts/test_suggest.py`.
