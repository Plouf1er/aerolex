# Rapport de Cohérence : Préparation de la Fusion AeroLex v1 + v2

Ce rapport présente l'audit complet de cohérence et de conformité pour la fusion des fiches aéronautiques de la **v1** (769 fiches dont 757 rédigées et 12 à rédiger) et de la **v2** (533 fiches neuves issues d'audits d'exhaustivité PPL). 

---

## 1. Identification de la Source v1 et Métadonnées

La source de vérité pour la version **v1** est le fichier **`data_glossaire_full.py`** (généré à partir de `data_glossaire.py`).

*   **Nombre de fiches total :** 769
*   **Fiches rédigées (`statut='redigee'`) :** 757
*   **Fiches en attente de rédaction (`statut='a_rediger'`) :** 12
*   **Champs présents dans la structure v1 :**
    `categorie`, `colonnes_tableau`, `contexte_requis`, `definition`, `famille`, `membres_famille`, `nb_seances`, `occurrences`, `origine`, `schema`, `statut`, `synonymes`, `variantes`, `xrefs`

---

## 2. Analyse des Doublons v1 vs v2

### A. Comparaison stricte des Termes Principaux
La comparaison des clés principales des fiches montre un résultat exceptionnel :
*   **Doublons stricts (exacte égalité de casse) :** **0**
*   **Doublons insensibles à la casse / accents / espaces :** **0**

**Conclusion :** Les 533 termes de la v2 sont lexicalement 100% disjoints des 769 termes de la v1. L'audit d'exhaustivité a parfaitement identifié des termes absents de la v1 pour concevoir la v2.

### B. Conflits sur les Variantes (Overlaps)
Bien que les termes principaux soient disjoints, il existe des **conflits de variantes** : dans **45 cas**, un terme principal de la v1 a été déclaré comme *variante* d'une fiche v2. Cela provoquerait un conflit à l'import car un même terme serait à la fois une fiche principale et une variante.

Voici la table complète de ces **45 conflits** avec les recommandations d'arbitrage :

| # | Terme v2 | Variante conflictuelle | Terme v1 existant | Statut v1 | Recommandation d'arbitrage |
|---|----------|------------------------|-------------------|-----------|----------------------------|
| 1 | `angle d'incidence` | `angle d'attaque` | `angle d'attaque` | `redigee` | Fusionner sous v1 (`incidence`). Ajouter `angle d'incidence` comme variante de `incidence`. |
| 2 | `angle d'incidence` | `incidence` | `incidence` | `redigee` | Fusionner sous v1 (`incidence`). Ajouter `angle d'incidence` comme variante de `incidence`. |
| 3 | `poussée` | `traction` | `traction` | `redigee` | Garder les deux en fiches séparées. Retirer `traction` de la liste des variantes de `poussée` dans v2. |
| 4 | `rapport portance/traînée` | `finesse` | `finesse` | `redigee` | Fusionner sous v1 (`finesse`). Ajouter `rapport portance/traînée` comme variante de `finesse`. |
| 5 | `incidence de décrochage` | `incidence critique` | `incidence critique` | `redigee` | Fusionner sous v1 (`incidence critique`). Ajouter `incidence de décrochage` comme variante de `incidence critique`. |
| 6 | `décrochage accéléré` | `décrochage dynamique` | `décrochage dynamique` | `redigee` | Fusionner sous v1 (`décrochage dynamique`). Ajouter `décrochage accéléré` comme variante. |
| 7 | `couple` | `couple moteur` | `couple moteur` | `redigee` | Fusionner sous v1 (`couple moteur`). Ajouter `couple` comme variante. |
| 8 | `vitesse conventionnelle` | `cas` | `cas` | `a_rediger` | Fusionner sous v2 (`vitesse conventionnelle`). Conserver la définition v2 (très précise) et renommer le terme v1 en `vitesse conventionnelle` en plaçant `CAS` en variante. |
| 9 | `Vlof` | `vitesse d'envol` | `vitesse d'envol` | `redigee` | Fusionner sous v2 (`Vlof`). Renommer la fiche v1 en `Vlof` et mettre `vitesse d'envol` comme variante. |
| 10 | `signaux lumineux de la tour` | `signaux lumineux` | `signaux lumineux` | `redigee` | Fusionner sous v1 (`signaux lumineux`). Le terme v1 est plus court et générique. |
| 11 | `zone P` | `zone interdite` | `zone interdite` | `redigee` | Garder les deux (v2 = code technique OACI, v1 = terme français). Retirer `zone interdite` de la variante de `zone P`. |
| 12 | `zone D` | `zone dangereuse` | `zone dangereuse` | `redigee` | Garder les deux (v2 = code technique OACI, v1 = terme français). Retirer `zone dangereuse` de la variante de `zone D`. |
| 13 | `secteur d'information de vol` | `siv` | `siv` | `redigee` | Fusionner sous v1 (`siv`). Renommer ou garder `SIV` comme clé principale et ajouter `secteur d'information de vol` comme variante. |
| 14 | `obstacle` | `obstacle artificiel` | `obstacle artificiel` | `redigee` | Garder les deux (obstacle est générique, obstacle artificiel est spécifique aux cartes), mais retirer les variantes croisées. |
| 15 | `TWR` | `tour de contrôle` | `tour de contrôle` | `redigee` | Fusionner sous v1 (`tour de contrôle`). Ajouter `TWR` comme variante de `tour de contrôle`. |
| 16 | `agent AFIS` | `afis` | `afis` | `redigee` | Garder les deux (AFIS = service, agent AFIS = personne). Retirer `afis` de la liste des variantes de `agent AFIS`. |
| 17 | `point de compte rendu` | `point de report` | `point de report` | `redigee` | Fusionner sous v1 (`point de report`). Ce sont de parfaits synonymes. |
| 18 | `pression atmosphérique` | `pression` | `pression` | `redigee` | Fusionner sous v2 (`pression atmosphérique`) qui est beaucoup plus précis. Mettre `pression` comme variante. |
| 19 | `surface isobare` | `isobare` | `isobare` | `redigee` | Fusionner sous v1 (`isobare`). Ils sont synonymes. |
| 20 | `congestus` | `cumulus congestus` | `cumulus congestus` | `redigee` | Fusionner sous v1 (`cumulus congestus`) pour garder la nomenclature météo complète. Mettre `congestus` en variante. |
| 21 | `onde orographique` | `onde de relief` | `onde de relief` | `redigee` | Fusionner sous v1 (`onde de relief`). Ils sont synonymes. |
| 22 | `rafale descendante` | `courant descendant` | `courant descendant` | `redigee` | Garder les deux (rafale descendante est une micro-rafale violente de cumulonimbus, courant descendant est général). Retirer `courant descendant` de la variante de `rafale descendante`. |
| 23 | `cat` | `turbulence en air clair` | `turbulence en air clair` | `redigee` | Fusionner sous v1 (`turbulence en air clair`). Ajouter `CAT` comme variante de `turbulence en air clair`. |
| 24 | `visibilité météo` | `visibilité` | `visibilité` | `redigee` | Fusionner sous v1 (`visibilité`). Ajouter `visibilité météo` comme variante. |
| 25 | `visibilité météo` | `visibilité horizontale` | `visibilité horizontale` | `redigee` | Fusionner sous v1 (`visibilité`). Ajouter `visibilité météo` comme variante. |
| 26 | `rvr` | `portée visuelle de piste` | `portée visuelle de piste` | `redigee` | Fusionner sous v1 (`portée visuelle de piste`). Ajouter `RVR` comme variante. |
| 27 | `ra` | `pluie` | `pluie` | `redigee` | Garder les deux. v2 est le code METAR abrégé (`RA`), v1 is the concept in French. Clean cross-variant. |
| 28 | `fg` | `brouillard` | `brouillard` | `redigee` | Garder les deux. v2 est le code METAR abrégé (`FG`), v1 is the concept in French. Clean cross-variant. |
| 29 | `sh` | `averse` | `averse` | `redigee` | Garder les deux. v2 est le code METAR abrégé (`SH`), v1 is the concept in French. Clean cross-variant. |
| 30 | `1013,25 hPa` | `calage standard` | `calage standard` | `redigee` | Fusionner sous v1 (`calage standard`). Ajouter `1013,25 hPa` comme variante. |
| 31 | `TL` | `niveau de transition` | `niveau de transition` | `redigee` | Fusionner sous v1 (`niveau de transition`). Ajouter `TL` comme variante. |
| 32 | `compas magnétique` | `compas` | `compas` | `redigee` | Fusionner sous v1 (`compas`). Ils sont synonymes. |
| 33 | `mode C` | `transpondeur mode c` | `transpondeur mode c` | `redigee` | Fusionner sous v1 (`transpondeur mode c`). |
| 34 | `accusé de réception` | `roger` | `roger` | `redigee` | Garder les deux (Roger est un mot de phraséologie, accusé de réception est un concept). Retirer `roger` de la variante v2. |
| 35 | `mille nautique` | `NM` | `NM` | `redigee` | Fusionner sous v2 (mille nautique). Conserver le terme complet comme clé principale et mettre l'abréviation v1 (NM) en variante. |
| 36 | `kilogramme` | `kg` | `kg` | `redigee` | Fusionner sous v2 (kilogramme). Conserver le terme complet comme clé principale et mettre l'abréviation v1 (KG) en variante. |
| 37 | `kilomètre` | `km` | `km` | `redigee` | Fusionner sous v2 (kilomètre). Conserver le terme complet comme clé principale et mettre l'abréviation v1 (KM) en variante. |
| 38 | `conditions de vol à vue` | `VMC` | `VMC` | `redigee` | Fusionner sous v1 (`VMC`). Ajouter `conditions de vol à vue` comme variante. |
| 39 | `conditions de vol à vue` | `conditions vmc` | `conditions vmc` | `redigee` | Fusionner sous v1 (`VMC`). Ajouter `conditions de vol à vue` comme variante. |
| 40 | `niveau de croisière` | `niveau de vol` | `niveau de vol` | `redigee` | Fusionner sous v1 (`niveau de vol`). Ce sont de parfaits synonymes. |
| 41 | `plan de vol déposé` | `plan de vol` | `plan de vol` | `redigee` | Fusionner sous v1 (`plan de vol`). |
| 42 | `effet de trou noir` | `trou noir` | `trou noir` | `redigee` | Fusionner sous v1 (`trou noir`). |
| 43 | `situation awareness` | `conscience de la situation` | `conscience de la situation` | `redigee` | Fusionner sous v1 (`conscience de la situation`). |
| 44 | `régime` | `régime moteur` | `régime moteur` | `redigee` | Fusionner sous v1 (`régime moteur`). |
| 45 | `tours/minute` | `rpm` | `rpm` | `redigee` | Fusionner sous v1 (`rpm`). |

---

## 3. Analyse des Références Croisées (XREFS) Cassées

### A. Validation des 6 cibles de la v2 absentes de la v2 elle-même
L'audit de la v2 seule identifiait **35 occurrences** pointant vers 6 cibles absentes de la v2 : `"portance"` (16), `"décrochage"` (10), `"aile"` (4), `"traînée"` (2), `"vitesse"` (0, voir note), et `"vitesse propre"` (3).

**Ces cibles existent-elles en v1 ?**
*   `portance` : **OUI** (exactement écrit `portance` en v1)
*   `décrochage` : **OUI** (exactement écrit `décrochage` en v1)
*   `aile` : **OUI** (exactement écrit `aile` en v1)
*   `traînée` : **OUI** (exactement écrit `traînée` en v1)
*   `vitesse` : **OUI** (exactement écrit `vitesse` en v1)
*   `vitesse propre` : **OUI** (exactement écrit `vitesse propre` en v1)

*Note sur la mesure de la v2 :* L'analyse montre qu'il y a 3 occurrences de `"vitesse propre"` et 0 occurrence de `"vitesse"` dans les xrefs orphelines de la v2 seule (les xrefs vers `"vitesse conventionnelle"` sont valides car `"vitesse conventionnelle"` est dans la v2). Les 35 occurrences se décomposent ainsi : `portance` (16) + `décrochage` (10) + `aile` (4) + `vitesse propre` (3) + `traînée` (2) = 35.

**Grâce à la fusion, ces 35 xrefs cassées de la v2 sont 100% résolues par la v1 !**

### B. Validation des xrefs cassées de la v1 résolues par la v2
La v1 seule contenait **22 xrefs cassées** (insensibles à la casse).
La fusion avec la v2 résout **5 de ces xrefs** :
*   `altitude` (3 occurrences dans la v1) est résolue car la v2 apporte la fiche `altitude`.
*   `hauteur` (2 occurrences dans la v1) est résolue car la v2 apporte la fiche `hauteur`.

### C. Analyse sur le corpus FUSIONNÉ (1 290 fiches actives v1+v2)
Sur le corpus fusionné, il reste **17 occurrences** d'xrefs cassées (pointant vers 10 cibles uniques) :

| # | Cible orpheline | Occurrences | Diagnostic & Solution recommandée |
|---|-----------------|-------------|-----------------------------------|
| 1 | `vent` | 6 | **Terme manquant.** Créer une fiche générique `vent` ou rediriger vers `vent relatif` / `effet du vent`. |
| 2 | `vent de travers` | 2 | **Redirection.** Ce terme est une variante de `composante de travers` en v1. Rediriger l'xref vers `composante de travers`. |
| 3 | `température` | 2 | **Terme manquant.** Créer une fiche générique `température` ou rediriger vers `OAT`. |
| 4 | `météorologie` | 1 | **Terme manquant.** Créer une fiche `météorologie`. |
| 5 | `préparation du vol` | 1 | **Terme manquant.** Créer une fiche `préparation du vol`. |
| 6 | `vitesse de référence` | 1 | **Redirection.** C'est une variante de `Vref` en v1. Rediriger vers `Vref`. |
| 7 | `circuit d'aérodrome` | 1 | **Redirection.** C'est une variante de `tour de piste` en v1. Rediriger vers `tour de piste`. |
| 8 | `route magnétique` | 1 | **Redirection.** C'est une variante de `cap magnétique` en v1. Rediriger vers `cap magnétique`. |
| 9 | `vol plané` | 1 | **Terme manquant.** Créer une fiche `vol plané`. |
| 10 | `toucher` | 1 | **Terme manquant.** Créer une fiche `toucher` (type d'atterrissage). |

**Note sur la casse :** Il existe **38 autres occurrences** d'xrefs cassées dues uniquement à des écarts de casse (ex. `"mode a"` au lieu de `"mode A"`, `"ndb"` au lieu de `"NDB"`). Elles se résoudront automatiquement en normalisant les xrefs par rapport à la casse exacte des clés lors de l'import.

---

## 4. Analyse Taxonomique

### A. Domaines v2 vs Classification v1
Le système v1 possède **16 catégories** et **71 familles pédagogiques**, tandis que la v2 utilise **5 grands domaines**.

Les deux structures sont parfaitement compatibles. En effet, les 5 domaines v2 se projettent naturellement sur les catégories de la v1 :
*   `regl-proc` (134 fiches) -> `Réglementation & docs` (66) & `Procédures` (75)
*   `nav-radio` (116 fiches) -> `Navigation` (45) & `Radio & phraséologie` (36)
*   `aero-perfs` (111 fiches) -> `Aérodynamique` (50), `Vitesses & performances` (53) & `Masse & centrage` (18)
*   `aerodrome` (88 fiches) -> `Aérodrome & cartes` (111)
*   `meteo` (84 fiches) -> `Météo` (105) & `Vent` (39)

### B. Recommandation pour la structure finale
**La structure de la v1 (16 catégories et 71 familles) doit rester la cible finale absolue.**
Il ne faut surtout pas aplatir la v1 vers les 5 domaines de la v2, ce qui ruinerait la granularité pédagogique. Il est recommandé d'attribuer une `categorie` et une `famille` de la v1 à chacune des 533 fiches de la v2.

### C. Analyse des familles et catégories vides ou orphelines
*   **Avant fusion :** Aucune catégorie ni famille dans la v1 n'est vide (toutes possèdent au moins 2 fiches rédigées).
*   **Après fusion :** Comme la fusion est purement additive, aucune structure existante ne deviendra orpheline ou vide. Au contraire, certaines petites familles v1 (ex. `pannes_moteur` : 2 fiches, `physiologie` : 2 fiches) recevront de nouvelles fiches de la v2, renforçant leur pertinence.

---

## 5. Recommandations Stratégiques d'Import

1.  **Non-concurrence des termes :** L'absence de doublons stricts ou insensibles à la casse valide la qualité d'isolation de la v2. On peut importer les 533 termes l'esprit serein.
2.  **Traitement des 45 conflits de variantes :** 
    *   Pour les synonymes stricts (35 termes) : fusionner la définition v2 en variante/contenu de la fiche v1 ou inversement selon la qualité de la rédaction (voir table).
    *   Pour les notions distinctes (10 termes, ex: `poussée` / `traction`) : conserver les deux fiches principales, mais supprimer la variante conflictuelle de la fiche v2.
3.  **Nettoyage automatique des xrefs :**
    *   Mettre en place un script de post-import pour normaliser la casse des xrefs (ex. `mode a` -> `mode A`). Cela corrige immédiatement 38 alertes.
    *   Appliquer les 4 redirections de variantes identifiées (`vent de travers` -> `composante de travers`). Cela corrige 5 autres alertes.
    *   Rédiger les 6 fiches génériques manquantes (`vent`, `température`, `météorologie`, `préparation du vol`, `vol plané`, `toucher`) pour atteindre un score parfait de **0 xrefs cassées**.
4.  **Taxonomie :** Associer les fiches v2 à des couples `(categorie, famille)` v1 lors de l'import, plutôt que de conserver le champ générique `domaine`.
