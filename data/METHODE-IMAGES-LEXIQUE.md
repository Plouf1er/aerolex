# Méthode — produire les schémas d'un lexique aéro (AeroLex)

> Version 2, 2026-08-04. La v1 (SVG à la main, contrôle géométrique seul) a produit
> 10 planches jugées « décevantes » par Louis. Ce document acte pourquoi et par quoi
> on remplace.

## 0. Le principe qui commande tout

**Un schéma n'est pas validé parce qu'il est bien rangé. Il est validé parce qu'un
lecteur qui n'a pas le brief comprend l'idée.**

La v1 vérifiait « XML valide + rien ne déborde + rien ne se chevauche ». Ces trois
tests sont vrais sur une planche vide, et ils étaient vrais sur une planche
**physiquement fausse** (incidence négative présentée comme le vol normal, repérée
par Louis en une phrase). Le contrôle de forme ne dit rien sur le fond.

## 1. Test de compréhension à l'aveugle (obligatoire)

Après chaque planche, lancer un **sous-agent juge** qui reçoit **l'image seule**,
sans le brief, sans le titre attendu, sans la liste des termes.

Questions posées au juge :
1. Qu'est-ce que ce schéma cherche à t'expliquer ? (une phrase)
2. Quel est le point de vue de chaque dessin ? Où est l'avant de l'avion ?
3. Qu'est-ce qui est ambigu, illisible ou contradictoire ?
4. Si tu devais changer UNE chose pour que ça se comprenne mieux, quoi ?

**Lecture du résultat** : on compare la réponse 1 à l'intention. Si le juge n'a pas
retrouvé l'idée, **c'est la planche qui a tort, pas le juge.** On corrige avec sa
réponse 4, on relance.

**Boucle : 4 itérations maximum.** On sort dès que le juge retrouve l'intention.
Si 4 tours ne suffisent pas, le sujet est mal découpé → revoir le découpage
(souvent : deux idées dans une planche) plutôt que le dessin.

Ne jamais donner le brief au juge « pour l'aider ». Un juge aidé ne mesure plus rien.

## 2. Règles de dessin (issues des échecs constatés)

### 2.1 Un seul point de vue par cadre, étiqueté en clair
La faute majeure de la v1 : mélanger dessus / côté / face dans un dessin unique.
Louis : « on ne comprend même pas l'avant et l'arrière et les plans sont mélangés ».

- Une planche peut contenir **plusieurs cadres**, chacun avec son étiquette
  (`VUE DE DESSUS`, `VUE DE COTE`, `VUE DE FACE`).
- Un axe/phénomène est montré **uniquement dans la vue où il se voit**.
  Le roulis ne se voit pas de dessus → il n'y figure pas.
- **Jamais** de flèche de rotation 3D posée sur une vue plate.

### 2.2 Lever l'ambiguïté avant/arrière, systématiquement
- Marquer `nez` en vert dans chaque vue où la confusion est possible.
- Sur la vue de face : **dessiner la dérive** (elle pointe vers le haut ⇒ repère
  immédiat « je regarde de face, pas de dessus »). Demande explicite de Louis,
  validée : « qu'on comprenne encore mieux ».
- Éviter les ailes en flèche marquée sur une vue de dessus : ça donne l'illusion
  que l'avion vole à reculons (constaté deux fois).

### 2.3 Contrôle de cohérence physique (pas seulement géométrique)
Avant de publier, vérifier dans le script :
- **Signe de l'incidence** : corde au-dessus du vent relatif ⇒ α positive. Attention,
  en SVG l'axe Y est inversé (y croît vers le bas) : c'est l'erreur qui a produit
  l'incidence négative.
- **Vent relatif = opposé de la trajectoire**, et les deux doivent être
  visuellement distincts (couleur + style de trait).
- Position de l'angle : l'arc doit être **entre les deux droites** qu'il mesure.

### 2.4 Habillage : réutiliser ce qui marchait déjà
Source de référence : `src/svg_glossaire.py` (9 générateurs des jours précédents,
jugés meilleurs par Louis). Ne pas réinventer.

- Cadre `viewBox` 640×N, fond `#e0f2fe`, coins arrondis `rx="8"`.
- **Titre + sous-titre** centrés dans chaque planche (la v1 n'en avait aucun).
- Palette : `#1e3a5f` bleu nuit (traits/texte), `#64748b` gris (secondaire),
  `#2563eb` flèches neutres, `#dc2626` alerte/rotation, `#16a34a` vert (repères),
  `#f59e0b` + `#b45309` surfaces mobiles, `#cbd5e1` remplissage avion.
- Flèches via `<marker>` réutilisables, pas de triangles dessinés à la main.
- **Bandeau de lecture en bas** : clé des couleurs + une phrase de garde
  (ex. « ne jamais chercher le roulis sur la vue de dessus »).
- Aucun texte < 11 px. Cadre rempli : pas de grandes zones vides.

### 2.5 Indexation (contrainte AeroLex, non négociable)
- Légendes = **vrai texte** `<text>` / `<tspan>`, jamais des paths.
- Chaque terme du lexique porte `class="aerolex-terme" data-slug="<slug>"`.
- Le slug doit exister dans le lexique, sinon le clic ne résout pas
  (cas rencontré : `portance` absent de `mots_couverts`).
- Le contenu tabulaire pur (ex. les 26 lettres de l'alphabet OACI) **n'est pas**
  un schéma et ne crée pas de fiches : passer par `data/extra_content.py`.

## 3. Chaîne de publication (les pièges qui ont coûté du temps)

1. Écrire le SVG dans `dist/svg/<id>.svg` (id fichier = id planche).
2. Valider le XML (`xml.dom.minidom`) + le contrôle physique du §2.3.
3. **Purger le cache Cloudflare** sur l'URL exacte.
4. **Vérifier que le public sert bien la nouvelle version** (comparer la taille
   disque vs servie, ou grep d'un marqueur nouveau). Piège vécu : disque à jour,
   public servant l'ancienne image.
5. **Regarder le rendu au screenshot** avant d'annoncer quoi que ce soit.
6. Lancer le juge à l'aveugle (§1).

### Accès navigateur
`file://` et `127.0.0.1` sont **bloqués par la politique**. Ce n'est pas le
navigateur qui est cassé. Toujours passer par l'**URL publique** — ce qui est de
toute façon la règle côté Louis : il n'est jamais sur la machine, tout livrable
visuel doit être une URL publique cliquable depuis un téléphone.

## 4. Anti-patterns (constatés, à ne pas refaire)

| Anti-pattern | Conséquence |
|---|---|
| Livrer sans avoir regardé l'image | 10 planches décevantes livrées d'un coup |
| Se fier au contrôle géométrique seul | incidence négative non détectée |
| Mélanger les points de vue | avant/arrière incompréhensible |
| Réinventer l'habillage | perte de la palette et des titres qui marchaient |
| Déléguer le dessin à un sous-agent | 3 runs morts, aucun rendu exploitable |
| Livrer 10 planches avant validation du style | 10× le coût de correction |
| Donner le brief au juge | le test ne mesure plus rien |

## 5. Ordre de travail recommandé

1. Une **planche témoin** dans le style cible → validation humaine.
2. Puis industrialiser, planche par planche, avec juge à l'aveugle sur chacune.
3. Corriger via la réponse 4 du juge, max 4 tours.
4. Rapport final : ce qui est passé, ce qui a résisté, ce qui reste faux.
