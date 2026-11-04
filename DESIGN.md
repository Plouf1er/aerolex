# DESIGN.md — AeroLex (pages site : index et fiches)

Contexte (format Impeccable). Registre : **produit** (outil de consultation, le design sert la lecture).
Périmètre : les pages publiques `dist/aero/*.html` (index + fiches) et leurs feuilles
`dist/aerolex-page.css` (base + fiches) et `dist/aerolex-indexpage.css` (index).
Le widget embarqué (`aerolex.css`, popups) reste séparé : il est chargé sur des sites tiers et ne
doit jamais porter de règles de mise en page globales.

## Utilisateurs et usage
Louis et des élèves-pilotes, **surtout sur iPhone (390 px)**, en consultation rapide : « c'est quoi
QNH ? », « que veut dire TMA ? ». On cherche un mot, on lit un développé, on repart. Mobile-first,
une main, lecture au soleil (bon contraste).

## Principes
1. **Le sigle d'abord** : terme en gras, développé en petit gris dessous (même hiérarchie que les popups).
2. **La recherche est l'entrée principale** : champ toujours accessible (barre collante), résultat visible sans défiler.
3. **Zéro bruit** : une lettre sans mot n'existe pas (ni dans la barre, ni dans la liste).
4. **Le contenu ne bouge pas** : aucune modification des liens, développés, familles ; le style habille.

## Couleurs (OKLCH, neutres teintés bleu, stratégie *restreinte* : un accent ≤ 10 %)
| Jeton | Valeur | Usage |
|---|---|---|
| `--pg-bg` | oklch(0.975 0.006 250) | fond de page |
| `--pg-card` | oklch(0.995 0.003 250) | cartes, listes, champs |
| `--pg-ink` | oklch(0.24 0.02 250) | texte principal |
| `--pg-ink-sec` | oklch(0.48 0.025 250) | développés, méta (≥ 5:1) |
| `--pg-line` / `--pg-line-strong` | oklch(0.915 …) / oklch(0.8 …) | séparateurs / bordures de champs |
| `--pg-accent` | oklch(0.5 0.19 262) | liens, lettre de groupe, focus |
| `--pg-tint` | oklch(0.95 0.025 262) | survol / suggestion active |
| `--pg-badge-bg` / `--pg-badge-ink` | oklch(0.94 0.03 262) / oklch(0.38 0.12 262) | badge famille |

Jamais de #000 / #fff purs.

## Typographie
Pile système (`-apple-system, Segoe UI, Roboto…`), 16 px de base (17 px bureau pour les fiches).
Champs et sélecteurs à **16 px minimum** (sinon iOS zoome au focus). Titres 650-750, développés .86rem.

## Composants
- **Barre collante** (`.ix-bar`) : champ de recherche (48 px) + rangée de lettres (défilement horizontal
  avec fondu sur mobile, une ligne sur bureau). Fond translucide + flou.
- **Suggestions** (`.ix-sug`) : lignes ≥ 48 px, terme en gras, développé en gris, « aussi : variante »
  en italique quand la correspondance vient d'une variante. Flèches/Entrée/Échap au clavier, tap au doigt.
- **Liste** (`.ix-group` > `.ix-list`) : un bloc par lettre, lignes séparées par un filet (pas de
  cartes imbriquées), badge famille à droite (bureau) ou sous le texte (mobile).
- **Fiche** : fil de navigation collant (préc. / index / suiv.), en-tête `.fiche-head` (titre, sigle
  développé, pastilles Catégorie/Famille), définition en carte à barre d'accent, listes famille / voir aussi
  en lignes aérées (2 colonnes ≥ 720 px), développé en gris sous le libellé.
- **Pastille** (`.chip`, `.ix-fam`) : 12 px, rayon 999, fond teinté.

## Accessibilité
Focus visibles (anneau accent), `role=combobox/listbox`, `aria-live` sur le compteur de résultats,
cibles tactiles ≥ 40 px, `prefers-reduced-motion` respecté (défilement fluide désactivé).

## Moteur de recherche
`dist/aerolex-searchbox.js` = copie autonome du moteur `_alxMountSearch` (projects/aero-coach/assets/aero.js),
même normalisation et même barème ; la donnée reste `dist/aerolex-search.json` (non dupliquée).
Si le barème change dans l'un, le répercuter dans l'autre.

## Cache
Les feuilles/scripts de l'index sont dans `asset_fingerprint.ASSET_FILES` : l'URL `?v=` change à chaque modification (Cloudflare).

## Pistes non faites
Mode sombre ; lettre active surlignée au défilement ; mise en évidence du terme cherché dans la liste.
