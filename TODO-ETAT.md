# AeroLex — État & TODO
_Dernière mise à jour : 2026-08-04 01:25_

## 0. 🔴 EN HAUT DE PILE — à faire dès que possible (Louis, 04/08 01h23)

### 0.1 `MTOW` en triple — casse une fonctionnalité en prod
**Demandé explicitement par Louis d'être remonté en haut de la todo.**

État mesuré le 04/08 sur `dist/aero/t/` — ce n'est pas un doublon mais un **triplon** :

| Slug | Terme affiché | Famille | Problème |
|---|---|---|---|
| `mtow` | `MTOW` | `documents_bord` | ❌ famille FAUSSE (c'est une masse, pas un document) |
| `masse-maximale-au-decollage` | `masse maximale au décollage` | `masses` | ✅ la bonne fiche — porte déjà `MTOW` en variante |
| `mtom` | `mtom` | — | ❌ 3e fiche, même notion (Maximum Take-Off Mass), casse minuscule |

**Conséquence réelle, constatée par Louis en usage** : `MTOW` est à la fois un terme autonome ET une variante de `masse maximale au décollage` → conflit de résolution → **`MTOW` ne se surligne pas dans les cours**. Une fonctionnalité cassée, pas une coquetterie de données.

Correction à appliquer :
1. **Canonique** = `masse-maximale-au-decollage`, famille `masses`, affichage `masse maximale au décollage`.
2. `MTOW` et `MTOM` deviennent des **variantes** de cette fiche (les 3 graphies doivent matcher et pointer vers UNE page).
3. Supprimer les fiches `mtow` et `mtom` — mais **fusionner les définitions avant** (les 3 sont rédigées, ne pas jeter le contenu à l'aveugle) → dépend de l'arbitrage (11) « quelle définition survit aux fusions ».
4. Vérifier les `xrefs` entrantes vers `mtow` / `mtom` avant suppression → sinon on crée des liens morts (on est à 0 aujourd'hui, ne pas régresser).
5. Re-tester le surlignage de `MTOW` dans une séance réelle **dans le navigateur** après correction.

⚠️ Ce cas est le **spécimen de référence** du contrôle n°3 de la méthode de nettoyage (« sigle présent à la fois comme terme ET comme variante d'un autre terme »). Voir `TODO-FEATURES.md` §5.

### 0.2 Casse des V-speeds — `case_sensitive` (tranché 04/08 01h21)
Décision prise, **pas encore implémentée** : les 4 faux positifs sur `VA` sont toujours en ligne. Détail complet en section 6.

## 1. État réel vérifié

| Sujet | État | Chiffres |
|---|---|---|
| Glossaire | ✅ sain | 1296 termes, 0 def vide |
| Familles | ⚠️ incomplet | 71 familles, 137 sans famille (était 380) |
| Famille `gouvernes_primaires` | ✅ corrigée | 10 termes, 4 intrus fuselage sortis |
| Index JS | ✅ à jour | 1296 entrées, tous s=1, 368,9 Ko / 106,8 Ko gzip |
| Règle d'URL (slug) | ✅ faite | `scripts/slugify.py`, 1296 slugs uniques, 1 collision (θ/°) |
| Pages `<slug>.html` | 🔄 génération en cours | — |
| Index A-Z public | 🔄 en cours | mots seuls, 0 définition |
| Lien popup « Voir dans le glossaire » | ❌ cassé | dépend des pages |
| Modèle de données | ✅ v3 | ~700 lignes, 14+ tables |
| Méthode SVG | ✅ retrouvée | 10 générateurs Python purs, SVG inline |
| Inventaire schémas | ⚠️ à refaire | 16 schémas / ~93 termes, rattachement manquant |

## 2. TODO priorisé

### P1 — bloquant visuel
- [ ] Terminer génération pages + index A-Z ; vérifier 0 lien mort
- [ ] Corriger lien popup `_renderGlos()` dans `aero-coach/assets/aero.js` (URL de base configurable, pas en dur)
- [ ] Vérif navigateur (CDP 18800, pas localhost)

### P2 — qualité du corpus
- [ ] Créer les 9 familles manquantes : `voilure` (13), `structure_fuselage` (10), `train_atterrissage` (8), `composantes_vent` (13), `domaine_de_vol` (8), `codes_oaci_terrains` (51), `categories_certification` (3), `personnel_navigant` (8)
- [ ] Rattacher les 137 orphelins → objectif couverture ~100 %
- [ ] **Termes fondamentaux ABSENTS à créer** : `aileron`, `dérive`, `gouverne de direction`, `gouverne de profondeur` (seul `aileron au vent` existe = procédure, pas la surface)
- [ ] Passe de cohérence aéro **par famille** (chaque famille = ensemble fermé relu comme un tout : intrus ? manquants ?)
- [ ] 12 xrefs orphelines préexistantes

### P3 — illustrations
- [ ] Refaire l'inventaire des schémas AVEC rattachement aux termes (16 pistes valables : étages nuageux, coupe de front, arcs anémomètre, profil espaces aériens, mécanique décrochage, axes/gouvernes…)
- [ ] 211 fiches héritées `schema:True` conservées dans `data/schemas-candidats-heritage.json` — enrichissement croisé (décision Louis : ne pas jeter)
- [ ] Générer les SVG avec `src/svg_glossaire.py` (Python pur, inline)

### P4 — plateforme
- [ ] Implémenter `embed_keys` (ID de pose) + modes de réponse dégradée
- [ ] CSS par pose (23 variables `--aerolex-*`) + éditeur simplifié
- [ ] Déploiement `aerolex.prunel.net` (DNS + tunnel, service dédié `aerolex/public/` — PAS le share monolithe)
- [ ] Éradiquer refs au glossaire dupliqué `aero-coach/data_glossaire.py`
- [ ] `innerHTML` → TreeWalker dans le moteur de surlignage

### P5 — LA MÉTHODE CODIFIÉE (idée Louis 04/08 — c'est le produit)
- [ ] Écrire `METHODE-LEXIQUE.md` : les 7 étapes découvertes ce soir, reproductibles pour un lexique tiers
      1. Import + normalisation des statuts
      2. Taxonomie (catégories/familles) — pas d'invention hors référentiel
      3. Audit des familles (intrus / orphelins / effectifs 3-36)
      4. Détection des flags menteurs (champ qui affirme sans porter la donnée)
      5. Règle d'URL partagée build↔JS + détection de collisions
      6. Génération pages + index + tableaux de famille
      7. Vérification liens morts = 0 + contrôle de cohérence par famille
- [ ] En faire un pipeline exécutable côté plateforme → l'offre devient « chaîne de fabrication de lexique », pas « widget »

## 3. Décisions actées (ne pas re-débattre)

- **Plateforme multi-lexique** : `aerolex.prunel.net/<id>/`, premier lexique = `aero`
- **SEO** : une page par mot `<slug>.html` + index A-Z **liens seulement, aucune définition**
- **Visibilité** : `public|private` réversible, réglée par l'admin du compte ; `aero` = public
- **Rouge/stabilo** = déduit d'une définition vide, JAMAIS un flag en dur
- **Statique + DB** : Postgres = source de vérité + comptes ; artefacts statiques servis au bord
- **Surlignage discret PARTOUT**, même style que les pages de cours, pas de plafond de liens (décision Louis, contre ma proposition initiale)
- **Garde-fous techniques uniquement** : pas d'auto-lien, pas de récursion, pas de double span
- **SVG inline** dans les définitions (pas de fichiers statiques) — léger, stylable, zoomable, zéro requête
- **3 niveaux de fonctions avancées** : attribut HTML > config JSON du lexique > plugins plateforme (jamais de code tiers)
- **Zones** : table dédiée, exportées via `manifest.json` (TTL 300 s) → modif propagée < 5 min sans rebuild d'index
- **QCM** : exclusion obligatoire (surligner la réponse dans la question = bug pédagogique)
- **ID de pose** `embed_keys` : table distincte, clé **en clair** (publique par nature), préfixe `alxk_`
- **Réponse dégradée par défaut** (teaser) : index des mots servi → surlignage actif, définitions en 402 « Définitions réservées »
- **Jamais de message d'erreur au visiteur final** ; avertissement en console développeur
- **`access_mode`** : `open` = statique pur ; `keyed` = worker qui proxie **les mêmes** artefacts (jamais de variante par client)
- **Mesure d'usage** : compteurs agrégés (clé, jour, origine), pas d'événements unitaires
- **Thème CSS** : appartient au lexique, choisi par pose ; override 3 crans ; anti-injection par whitelist + validation typée
- **Schémas SVG = fonction payante** « illustrez votre lexique »
- **Ne PAS exposer `Projects/share`** entier (risque arkegreen/subteel/.git) → service dédié
- **Pas de nouvelle catégorie/famille sans go explicite de Louis**
- **Pas de commit/push depuis les sous-agents**

## 4. Arbitrages en attente de Louis
- Mesure d'usage en mode `open` : sessions approximatives vs exacte
- Tarif du plan pro « schémas »
- Message au visiteur sur clé révoquée (proposition : aucun)
- Sélecteur CSS réel des QCM sur les pages ATCF (à relever)
- Go/nogo création des 9 familles + 4 termes gouvernes manquants

### Arbitrages du modèle de données v4 (04/08)
- ✅ **(10) Casse des V-speeds — TRANCHÉ 04/08 01h21** → décision détaillée en section 6 (`case_sensitive` par terme). À implémenter.
- ⬜ (8) Famille primaire des unités transverses (`hPa`, `kt`, `ft`…)
- ⬜ (9) Sens par défaut des homonymes (quelle fiche prend la forme de surface nue)
- ⬜ (11) Quelle définition survit aux fusions de doublons
- ⬜ (12) Stubs ou rien pour les codes OACI
- ⬜ (13) Défauts plateforme des blocs popup
- ⬜ (14) Statut du bloc `count`

Arthur doit proposer une recommandation argumentée sur les 6 restants (Louis n'a pas encore dit oui à cette proposition).

## 5. Leçon de la soirée
5 flags « qui affirment sans porter la donnée » trouvés en une soirée (`statut:redige` sur fiches vides, `schema:True` sans cible ×204, compteurs en dur, `termes_couverts:93` avec liste vide, `context_required` plat).
→ **Règle** : ne jamais stocker un état dérivable. Le déduire à la lecture.

## 6. Nettoyage des données (nouvelle catégorie de la méthode — Louis 04/08)
Étape à codifier : tout lexique importé doit passer ce filtre AVANT génération.

### Cas réels trouvés dans `aero` (mesurés)
- **Permutations de mots** : `courte finale` / `finale courte` → 2 fiches, 2 définitions écrites séparément, même famille `circuit_branches`. Canonique = `courte finale` (porte déjà `short final`). L'autre doit devenir variante. Les 2 graphies doivent matcher.
- **Quasi-doublons tiret/accent** : `check-list` / `checklist` → 2 fiches pour un mot.
- **Sigle en double + mal rangé (CASSE une fonctionnalité)** : `MTOW` existe 2× → `MTOW` (famille `documents_bord`, FAUX) et `masse maximale au décollage` (famille `masses`, porte `MTOW` en variante). Plus `mtom` à côté. Conflit de résolution → MTOW ne se surligne pas dans les cours. **Constaté par Louis en usage réel.**
- **Casse des vitesses incohérente** (~40 termes) : `VNE/VNO/VFE/VLO/VA/VS0/VS1` majuscules, `Vapp/Vref/Vlof/Vtoss/Vx/Vy` capitale+minuscules, `vr/vc/vle` minuscules. `VLO` vs `vle` = même famille, casse opposée.
  → **TRANCHÉ par Louis le 04/08 01h21 — arbitrage 10 du modèle v4, à implémenter.**

#### ✅ Décision casse (Louis, 04/08) — `case_sensitive` par terme
Règle retenue, mot pour mot : « comparer en minuscules, et pour des mots avoir des options de matching précis où on indique casse exacte ; à ce moment-là le script vérifie aussi si la casse est la même, sinon n'affiche pas le truc. »

1. **Matching normalisé par défaut** (minuscules + sans accents) pour les ~1 250 termes normaux → « Tour De Piste », « TOUR DE PISTE », « tour de piste » matchent tous avec une seule entrée. Comportement inchangé.
2. **Champ `case_sensitive` (booléen) par terme**, opt-in, PAS de réglage global. Quand il est vrai, le moteur compare la **forme réellement trouvée dans la page** à la forme d'affichage ; si la casse diffère → aucun surlignage, aucune popup.
   - « il **va** falloir » → casse ≠ `VA` → ignoré.
   - « la **VA** est de 95 kt » → casse identique → surligné.
3. **Périmètre d'application** : tous les sigles de 2-3 lettres qui sont aussi un mot français courant, PAS seulement ceux qui posent problème dans la séance actuelle (`VA` = 4 faux positifs mesurés, « va se stabiliser », « ça va vite »… ; `VC`/`VR`/`VG` propres aujourd'hui mais dangereux par nature). Sinon un nouveau cours réintroduit le bug.
4. Le garde-fou `HOMOGRAPHES_FR` (129 mots) existe déjà et fonctionne → `case_sensitive` le complète, ne le remplace pas.

⚠️ **PIÈGE À NE PAS OUBLIER — ne pas confondre avec la normalisation des données.**
Corriger la casse d'affichage des vitesses (`vr` → `VR` selon convention PPL) est un chantier SÉPARÉ de celui-ci. Et il ne faut PAS passer mécaniquement toutes les vitesses en majuscules : `vc` (vicinity) et `vrb` (variable) sont des **codes METAR** qui s'écrivent légitimement en minuscules. Ce sont des termes distincts qui doivent rester distincts. Traiter les deux séparément, jamais dans le même passe-partout.
- **Symboles sans lettre latine** : `°` et `θ` → slug vide, collision. Désambiguïsation par suffixe.

### Contrôles à automatiser dans la méthode
1. Permutations de mots (mêmes mots, ordre différent)
2. Quasi-doublons après normalisation (accents, tirets, apostrophes, espaces)
3. Sigle présent à la fois comme terme ET comme variante d'un autre terme → conflit
4. Familles d'abréviations à casse instable
5. Termes sans caractère latin (slug impossible)
6. Un terme et sa variante ne doivent jamais être 2 fiches

## 7. Multi-familles (Louis 04/08) — À PRÉVOIR
Aujourd'hui `famille` = champ UNIQUE, un seul par terme. Limite réelle :
- `hPa` = unité ET terme d'altimétrie
- `VNE` = vitesse ET limitation
- `MTOW` = masse ET donnée de document de bord
→ Besoin : un terme appartient à **N familles**. Impacte index, fichiers `t/*.json`, tableaux de famille, pages HTML.
→ **À faire en base** (table de liaison terme↔famille), pas en champ texte. À intégrer au chantier Postgres.
→ Familles validées par Louis en attente de rattachement : `unites` (kg, psi, kt, NM, hPa, ft…), `codes_aerodromes` (~60 codes, seul LFPN mérite une vraie fiche).

## 8. Piège infra trouvé (04/08 01:18)
**2 copies de `aero.js`** : `aero-coach/assets/aero.js` (modifié) et `atcf-ppl/assets/aero.js` (servi à la séance, resté périmé). La séance chargeait l'ancien → overlays rouges. Purge Cloudflare inutile : le disque servait le vieux fichier.
→ Remplacer la copie par un lien symbolique, sinon la divergence se reproduira à chaque modif.
