# PLAN — Rédaction des fiches de glossaire (Aero Coach PPL)

> Généré le 02/08/2026. **Aucune fiche n'est rédigée dans ce document** : c'est le plan de travail.
> Source lexique : `lexique-filtre.txt` (1092 termes après retrait villes/immatriculations).
> Source glossaire : `projects/aero-coach/data_glossaire.py` (112 entrées, 202 formes couvertes).

---

## 1. Structure EXACTE d'une fiche (relevée dans `data_glossaire.py`)

Le dictionnaire s'appelle `GLOSSAIRE`. La clé est le terme affiché ; la valeur est un dict.
**7 champs réels** existent dans le fichier — 2 obligatoires, 5 optionnels :

| Champ | Obligatoire | Type | Rôle |
|---|---|---|---|
| `definition` | ✅ oui | str | 1-2 phrases, ton instructeur. HTML autorisé : `<strong>` et `<em>` UNIQUEMENT (jamais de balise de bloc). |
| `categorie` | ✅ oui | str | Regroupement dans l'index alphabétique. |
| `variantes` | non | list[str] | Formes ALTERNATIVES à lier vers cette fiche (pluriels, casse, sigles, anglicismes). C'est le champ anti-doublon. |
| `synonymes` | non | list[str] | Termes équivalents, affichés à l'utilisateur comme synonymes. |
| `xrefs` | non | list[str] | Renvois « voir aussi » vers d'autres clés du glossaire. |
| `contexte_requis` | non | list[str] | Garde-fou polysémie : le mot n'est lié QUE si l'un de ces marqueurs est présent dans le texte. |
| `schema` | non | str | Identifiant du schéma illustratif à afficher (ex. `azimut_vrai_magnetique`, `piste_seuils_qfu`, `manche_a_air`). |

### Exemple complet réel (entrée `seuil de piste`, la plus richement dotée)

```python
    "seuil de piste": {
        "schema": "piste_seuils_qfu",
        "definition": "…",
        "categorie": "Aérodrome & cartes",
        "variantes": ["seuil", "seuils", "seuils de piste"],
        "synonymes": ["seuil"],
        "contexte_requis": ["piste", "QFU", "atterriss", "seuil décalé", "zébra"],
    },
```

### Catégories existantes (9) et leur remplissage actuel

| Catégorie | Entrées |
|---|---|
| Météo | 28 |
| Vitesses & performances | 19 |
| Aérodrome & cartes | 15 |
| Vent | 12 |
| Altimétrie | 10 |
| Navigation | 9 |
| Réglementation & docs | 9 |
| Unités | 6 |
| Aérodynamique | 4 |

La rédaction à venir déséquilibre ces catégories : il faudra en **créer 3** — `Moteur & systèmes`, `Instruments`, `Facteurs humains` (voir les lots ci-dessous).

---

## 2. ⚠️ Anti-doublon — 9 collisions DÉJÀ présentes dans le glossaire

Rappel du bug silencieux : `composante de travers` déclaré 2×. Le contrôle par forme normalisée
(minuscules, accents retirés, ponctuation neutralisée) révèle **9 collisions actuelles**, où deux clés
distinctes revendiquent la même forme. À arbitrer AVANT d'ajouter des fiches, sinon le problème grossit :

| Forme normalisée | Clés en conflit |
|---|---|
| `(chaîne vide)` | `°` / `θ` |
| `cap magnetique` | `cap magnétique` / `nord magnétique` |
| `cap vrai` | `cap vrai` / `nord vrai` |
| `declinaison` | `déclinaison` / `déclinaison magnétique` |
| `va` | `VA` / `Va` |
| `vfe` | `VFE` / `Vfe` |
| `vne` | `VNE` / `Vne` |
| `vno` | `VNO` / `Vno` |
| `vs` | `VS0` / `VS1` / `Vs` |

Les doublons de casse (`VA`/`Va`, `VFE`/`Vfe`, `VNE`/`Vne`, `VNO`/`Vno`) sont à fusionner :
une seule clé, l'autre casse passe en `variantes`. Les paires `cap X` / `nord X` sont un vrai
recouvrement sémantique à trancher (une fiche `cap`, une fiche `nord`, `xrefs` entre elles).

**Procédure obligatoire avant chaque nouvelle fiche** : normaliser le terme candidat et le
confronter à l'ensemble `clés ∪ variantes ∪ synonymes` du glossaire. Si collision → enrichir
la fiche existante (`variantes`), ne PAS créer d'entrée.

---

## 3. Périmètre chiffré

| | Corpus | Métier | Total |
|---|---|---|---|
| Termes au lexique | 962 | 130 | **1092** |
| Déjà couverts par le glossaire | 102 | 1 | **103** |
| **Fiches à créer** | **860** | **129** | **989** |

`corpus` = le terme apparaît dans les 37 séances → **lien actif** sur les pages.
`metier` = vocabulaire aéro standard absent du corpus → **fiche sans lien actif**.
Ce double marquage doit être reporté sur chaque fiche créée.

---

## 4. Découpage en LOTS thématiques

13 lots, ordonnés par ordre de rédaction recommandé (du plus mécanique au plus délicat).

| # | Lot | Termes | corpus | metier | `categorie` visée |
|---|---|---|---|---|---|
| 1 | Terrains & codes OACI | **50** | 20 | 30 | Aérodrome & cartes |
| 2 | Météo — nuages & phénomènes | **80** | 71 | 9 | Météo |
| 3 | Météo — vent & masses d'air | **52** | 45 | 7 | Vent |
| 4 | Aérodynamique & mécanique du vol | **120** | 101 | 19 | Aérodynamique |
| 5 | Moteur, hélice & systèmes | **89** | 79 | 10 | Moteur & systèmes (NOUVELLE) |
| 6 | Instruments & avionique | **59** | 55 | 4 | Instruments (NOUVELLE) |
| 7 | Navigation & cheminement | **106** | 94 | 12 | Navigation |
| 8 | Aérodrome, piste & tour de piste | **91** | 73 | 18 | Aérodrome & cartes |
| 9 | Espaces aériens & réglementation | **99** | 92 | 7 | Réglementation & docs |
| 10 | Phraséologie & radio | **68** | 63 | 5 | Phraséologie |
| 11 | Facteurs humains & sécurité des vols | **54** | 52 | 2 | Facteurs humains (NOUVELLE) |
| 12 | Atomes polysémiques & génériques | **100** | 97 | 3 | selon le sens retenu |
| 13 | Phases de vol & divers résiduel | **21** | 18 | 3 | Vitesses & performances / Météo |
| | **TOTAL** | **989** | **860** | **129** | |

---

## 5. Détail des lots

### Lot 1 — Terrains & codes OACI (50 termes)

`categorie` visée : **Aérodrome & cartes**

> 1 fiche = 1 terrain. Gabarit factorisable : nom du terrain, QFU/pistes, altitude, classe d'espace, fréquence, particularités. Les 30 `metier` sont des terrains jamais cités dans le corpus -> fiche sans lien actif.

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`lfpn`(46) `lfpo`(40) `lfox`(28) `lfmt`(24) `lfbd`(23) `lflc`(23) `lfsb`(23) `lfor`(19) `lflx`(18) `lfpg`(12) `lfac`·M `lfat` `lfbo` `lfeh`·M `lfen`·M `lfey`·M `lfjr`·M `lfll`·M `lfln`·M `lfmd`·M `lfml`·M `lfmn` `lfmp`·M `lfob`·M `lfod`·M `lfoe`·M `lfoh`·M `lfoi`·M `lfoj`·M `lfok`·M `lfoo`·M `lfot`·M `lfou`·M `lfow`·M `lfoy`·M `lfoz`·M `lfpb` `lfpk`·M `lfpt` `lfpv` `lfqq`·M `lfrb` `lfrd`·M `lfrg` `lfrn`·M `lfrs` `lfsn`·M `lfst`·M `lftw`·M `lfxu`

### Lot 2 — Météo — nuages & phénomènes (80 termes)

`categorie` visée : **Météo**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`couche`(123) `temsi`(117) `humidité`(106) `orage`(106) `averses`(104) `sigmet`(98) `humide`(93) `instabilité`(90) `pluie`(89) `convection`(83) `thermique`(83) `saturation`(78) `saturé`(71) `grain`(63) `lenticularis`(63) `wintem`(63) `metar/taf`(62) `couches`(61) `précipitations`(61) `rayonnement`(61) `glace`(57) `fronts`(55) `thermiques`(51) `givrage`(44) `congestus`(38) `rosée`(38) `atmosphère standard`(33) `brouillard de rayonnement`(27) `castellanus`(27) `humilis`(26) `nuage`(25) `nuage du jour`(25) `stratus`(24) `averse`(23) `givrage carburateur`(23) `givre`(23) `basses couches`(22) `dalr`(20) `elr`(20) `gradient thermique`(16) `cu`(13) `isotherme`(13) `shra`(13) `front occlus`(12) `nuages`(12) `br`(11) `fractus`(11) `front`(11) `cumulus`(10) `calvus`(9) `mammatus`(9) `base des nuages`(6) `inversion de température`(4) `plafond nuageux`(4) `convection thermique`(3) `température standard`(3) `cisaillement basse couche`(2) `advection` `altocumulus` `altostratus` `ascendance thermique`·M `cirrostratus` `convergence` `couche d'inversion`·M `cumulonimbus` `cumulus congestus` `divergence` `givrage en vol`·M `givrage moteur`·M `givrage structural`·M `instabilité atmosphérique`·M `iso zero`·M `isotherme zero`·M `ligne de grain` `nimbostratus` `stabilité atmosphérique`·M `stratocumulus` `subsidence` `tropopause` `troposphere`

### Lot 3 — Météo — vent & masses d'air (52 termes)

`categorie` visée : **Vent**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`secondes`(122) `profondeur`(96) `travers`(93) `flux`(90) `rotor`(89) `rabattant`(80) `vent`(80) `vent fort`(75) `crête`(61) `prévention`(56) `masses`(55) `composantes`(52) `vallée`(50) `sillage`(47) `foehn`(45) `brise`(44) `brise de mer`(44) `face au vent`(37) `turbulence`(33) `turbulence mécanique`(33) `aileron au vent`(25) `kt de travers`(24) `turbulence de sillage`(22) `effet venturi`(20) `composante`(19) `traversier`(18) `vent réel`(18) `rafales`(17) `brise de terre`(16) `gradient de vent`(14) `ascendance`(13) `onde`(11) `relief`(11) `brise de pente`(8) `cisaillement de vent`(7) `rabattant sous le vent`(5) `vent anabatique`(5) `courant descendant`(4) `effet de foehn`(4) `brise de vallée`(3) `vent catabatique`(3) `vent effectif`(2) `brassage` `effet de pente` `hyperventilation` `mistral`·M `regime venturi`·M `relief environnant`·M `tramontane`·M `turbulence en air clair`·M `vent arriere de securite`·M `vent estimé`·M

### Lot 4 — Aérodynamique & mécanique du vol (120 termes)

`categorie` visée : **Aérodynamique**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`moment`(224) `assiette`(220) `trim`(207) `attitude`(151) `force`(122) `cabré`(110) `énergie`(106) `charge`(103) `commandes`(102) `verticale`(100) `ailerons`(94) `horizontal`(92) `inclinaison`(92) `palonnier`(83) `piqué`(79) `traction`(74) `plat`(73) `accélération`(72) `forces`(70) `vertical`(63) `plané`(62) `commande`(61) `composite`(60) `filet`(60) `tangage`(58) `abaque`(56) `couple`(56) `structurale`(52) `volets sortis`(50) `gouverne`(49) `coordonné`(48) `charges`(45) `vrille`(45) `ailes à plat`(41) `charge de travail`(41) `vitesse de décrochage`(35) `stabilité`(34) `stabilité statique`(34) `atterrissage forcé`(30) `domaine`(30) `domaine de vol`(30) `virage`(30) `virage horizontal stabilisé`(30) `volets rentrés`(30) `traînée`(28) `traînée induite`(28) `datum`(26) `mm aft datum`(26) `aileron`(25) `double commande`(23) `incidence`(23) `masse`(23) `portance`(23) `stall`(23) `stall warning`(23) `ailes`(21) `cellule`(21) `flaps`(21) `aile`(20) `centrage`(20) `masse du jour`(20) `masse et centrage`(20) `diagramme v-n`(19) `nez`(19) `bras de levier`(18) `correction de dérive`(18) `levier`(18) `visibilité verticale`(18) `fiche de pesée`(17) `pesée`(17) `volets`(17) `volets up`(17) `finesse max`(16) `lacet`(16) `lacet adverse`(16) `assiette de montée`(15) `traînée parasite`(15) `centre de gravité`(14) `dos`(13) `lisse`(13) `roulis`(13) `souffle hélicoïdal`(13) `angle d'attaque`(12) `cz max`(12) `incidence critique`(12) `manche`(11) `effort au manche`(8) `masse maximale`(8) `virage standard`(8) `visibilité horizontale`(8) `assiette de croisière`(4) `angle de dérive`(2) `abaque de centrage`·M `aerofrein`·M `assiette de reference`·M `attitude de vol`·M `autorotation` `becs`·M `compensateur` `constante structurale`·M `couple gyroscopique`·M `couple moteur`·M `devis de masse` `décrochage dynamique`·M `décrochage secondaire`·M `effet de sol`·M `effet gyroscopique`·M `empennage` `fuselage` `inclinaison standard`·M `intégration verticale`·M `longeron` `masse a vide` `moment de rappel`·M `nervure` `percée verticale`·M `plan de charge`·M `polaire` `récupération de décrochage`·M `vrille à plat`·M

### Lot 5 — Moteur, hélice & systèmes (89 termes)

`categorie` visée : **Moteur & systèmes (NOUVELLE)**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`puissance`(324) `régime`(225) `pompe`(124) `électrique`(124) `freins`(106) `voyant`(104) `frein`(95) `monomoteur`(78) `freinage`(73) `batterie`(72) `refroidissement`(70) `alternateur`(69) `réservoir`(61) `autonomie`(54) `mélange`(53) `carburateur`(51) `choke`(50) `engine`(50) `réducteur`(50) `prop`(49) `chauffage`(47) `essais`(47) `consommation`(45) `lean`(45) `l/h`(44) `magnéto`(38) `hélice`(35) `régime hélice`(35) `start`(35) `carburant`(31) `carburant utilisable`(31) `monomoteur léger`(28) `pompe électrique`(24) `fuel`(21) `fuel pump`(21) `fuel pump on`(21) `ignition`(21) `off ignition off`(21) `pump`(21) `volt`(21) `huile`(20) `aquila`(19) `bilan carburant`(18) `kg/l`(18) `roue`(18) `régime moteur`(18) `rotax`(16) `rpm`(16) `selector`(16) `pas d'hélice`(15) `throttle`(15) `allumage`(14) `cht`(14) `idle`(14) `pression d'huile`(14) `psi`(14) `moteur`(13) `roulette`(13) `tcds`(13) `train`(13) `carbu`(12) `conso`(12) `feu moteur`(11) `oat`(11) `vitesse propre`(11) `température d'huile`(7) `coefficient de freinage`(4) `essai magnétos`(4) `sélecteur carburant`(4) `magnéto droite`(2) `richesse`(2) `réserve de carburant`(2) `température culasse`(2) `atterrissage train rentré`·M `autonomie carburant`·M `avitaillement`·M `calage helice`·M `carburant degagement`·M `carburant inutilisable` `consommation horaire`·M `magnéto gauche`·M `manette` `pas variable` `point fixe`·M `purge` `richesse mélange`·M `réchauffage carburateur`·M `tachymetre` `totalisateur`

### Lot 6 — Instruments & avionique (59 termes)

`categorie` visée : **Instruments (NOUVELLE)**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`grandeur`(195) `instruments`(188) `ils`(180) `anémomètre`(161) `taux`(145) `calage`(131) `compas`(124) `vitesses`(124) `tableau`(118) `statique`(97) `scan`(90) `altimètre`(83) `vapp`(79) `arc`(74) `dme`(69) `courbe`(59) `vor`(59) `pitot`(55) `ktas`(53) `recalage`(53) `asi`(52) `instrument`(50) `vitesse sol`(50) `altimétrie`(49) `arc vert`(40) `taux de montée`(38) `vitesse air`(37) `arc blanc`(32) `arc jaune`(32) `plan continuation bias`(30) `cas`(23) `horizon`(19) `horizon artificiel`(19) `calage altimétrique`(17) `triangle des vitesses`(17) `cap compas`(16) `trait rouge`(15) `bille`(13) `red lines`(13) `gps`(11) `déviation compas`(8) `taux de chute`(7) `vol aux instruments`(4) `adf` `arc dme` `badin` `conservateur` `gnss` `gyroscope` `machmetre` `moulinet` `recalage en route`·M `tableau de déviation`·M `variometre` `vitesse corrigee`·M `vitesse vraie` `vle` `vr` `vso`·M

### Lot 7 — Navigation & cheminement (106 termes)

`categorie` visée : **Navigation**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`carte`(548) `circuit`(388) `distance`(343) `trajectoire`(308) `nav`(306) `wca`(232) `minutes`(225) `navigation`(161) `distances`(152) `ouest`(150) `heure`(139) `holding`(120) `branche`(105) `attente`(104) `utc`(98) `heures`(80) `déroutement`(76) `triangle`(76) `intégration`(74) `radiale`(72) `qcm`(70) `cartes`(69) `carte oaci`(67) `oaci`(67) `agl`(65) `ft agl`(65) `géométrie`(65) `ft aal`(63) `niveaux`(62) `eta`(58) `trajet`(56) `ft amsl`(55) `mise en route`(53) `route`(53) `sud`(52) `altitudes`(50) `minute`(50) `orientation`(50) `secteur`(50) `circuits`(49) `conversion`(48) `amers`(46) `carnet de route`(45) `repère`(45) `durée`(44) `étape`(44) `plan de vol`(43) `niveau`(36) `alt`(35) `point d'attente`(35) `m/s`(29) `mm`(26) `perte de position`(24) `degrés vrais`(23) `niveaux de vol`(23) `magnétique`(22) `nord`(22) `altitude`(21) `altitude de croisière`(21) `carte vac`(21) `altitude de sécurité`(20) `cos`(20) `east is least`(19) `cap`(16) `mag`(16) `niveau de transition`(16) `cm`(15) `distance de décollage`(15) `eet`(15) `km`(15) `nearest airfield`(15) `distance de roulement`(14) `déviation`(14) `fpl`(13) `hauteur`(13) `km/h`(13) `qdm`(13) `qdr`(13) `état de piste`(13) `pression standard`(12) `distance d'atterrissage`(11) `ft/min`(11) `sin`(11) `altitude densité`(4) `heure d'arrivée`(4) `heure de départ`(4) `altitude minimale`(2) `hauteur de sécurité`(2) `heure estimée`(2) `temps estimé`(2) `altitude pression`·M `altitude tour de piste`·M `carte topographique`·M `circuit basse hauteur`·M `demi-tour standard`·M `derive constatee`·M `distance de franchissement`·M `estime` `hauteur tour de piste`·M `hippodrome`·M `percee` `point de decision` `point de non retour`·M `procedure d'attente`·M `temps de reaction` `tour de piste basse hauteur`·M

### Lot 8 — Aérodrome, piste & tour de piste (91 termes)

`categorie` visée : **Aérodrome & cartes**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`remise`(275) `pente`(237) `approche`(160) `remise de gaz`(153) `clôture`(148) `créneau`(145) `performances`(139) `feu`(127) `surface`(120) `kg`(119) `poids`(119) `densité`(116) `atterrir`(111) `feux`(106) `herbe`(104) `obstacle`(100) `performance`(95) `obstacles`(93) `palier`(92) `arrondi`(90) `démontré`(90) `décoller`(88) `majoration`(88) `monter`(88) `piste`(87) `landing`(86) `alignement`(79) `dégagement`(78) `terrains`(75) `signaux`(71) `roulement`(70) `rugosité`(69) `marges`(68) `mtom`(64) `roll`(64) `descendre`(60) `pistes`(58) `montée initiale`(51) `t/o`(51) `ldg`(48) `démontrés`(46) `largeur`(45) `piste en service`(41) `axe de piste`(38) `montée`(38) `terrain`(35) `herbe sèche`(31) `parking`(27) `vitesse d'approche`(25) `choix de piste`(24) `atterrissage`(23) `atterrissage de précaution`(23) `ground roll`(23) `signaux lumineux`(23) `point d'arrêt`(22) `piste mouillée`(20) `largeur de piste`(19) `descente`(17) `décollage`(15) `gradient`(14) `pente de montée`(14) `aérodrome`(13) `marge`(13) `contrôle d'aérodrome`(12) `terrain de dégagement`(11) `finale courte`(9) `longueur de piste`(6) `plan de descente`(4) `approche finale`(2) `check-list atterrissage`(2) `portée visuelle de piste`(1) `approche interrompue`·M `atterrissage precaution`·M `aérodrome de dégagement`·M `bande derobee`·M `check-list décollage`·M `descente initiale`·M `feu cabine`·M `marge de decrochage` `marge de franchissement`·M `obstacle artificiel`·M `palier de croisière`·M `pente de descente`·M `piste contaminée`·M `prolongement d'arret`·M `remise de gaz interrompue`·M `reserve finale` `roulage au sol`·M `sens du tour de piste`·M `servitude`·M `surface de piste`·M

### Lot 9 — Espaces aériens & réglementation (99 termes)

`categorie` visée : **Réglementation & docs**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`zone`(386) `procédure`(254) `obligatoire`(247) `ppl`(245) `règle`(240) `interdit`(232) `réserve`(204) `check`(181) `instructeur`(180) `brief`(173) `bagages`(169) `priorité`(165) `autorisé`(156) `classe`(155) `espaces`(147) `consignes`(137) `limites`(134) `mission`(132) `procédures`(130) `check-list`(127) `légal`(122) `zones`(120) `danger`(118) `dangereux`(117) `passager`(111) `fenêtre`(109) `carnet`(96) `vigueur`(96) `médical`(95) `scénario`(95) `siège`(93) `espace`(90) `réglementaire`(88) `formation`(80) `licence`(79) `règles`(75) `validité`(70) `check-lists`(66) `examen`(64) `cabine`(61) `navigabilité`(61) `porte`(60) `document`(59) `élève`(56) `certificat`(55) `dangereuse`(54) `manuel de vol`(54) `consigne`(53) `plancher`(51) `séparation`(49) `documents`(46) `interdite`(43) `publiée`(43) `tma paris`(35) `biais de confirmation`(25) `règle d'or`(25) `briefing départ`(24) `minima`(23) `espaces aériens`(20) `espace aérien`(19) `certificat médical`(18) `dgac`(15) `limite`(15) `briefing`(14) `prévol`(14) `visite prévol`(14) `easa`(13) `espace contrôlé`(13) `fi`(13) `lâcher`(13) `prorogation`(13) `sep`(13) `solo`(13) `checklist`(12) `pax`(11) `pré-lâcher`(11) `règles de l'air`(11) `service d'information`(11) `zone dangereuse`(11) `réserve réglementaire`(8) `minima météo`(6) `zone interdite`(4) `briefing arrivée`(2) `conditions imc`(2) `conditions vmc`(2) `zone de contrôle`(2) `action vitale`·M `atz`·M `espacement réglementaire`·M `fir` `information trafic`·M `limite arriere` `limite avant` `rmz` `sup aip` `tmz` `uir`·M `verification vitale`·M `zone stabilisée`·M

### Lot 10 — Phraséologie & radio (68 termes)

`categorie` visée : **Phraséologie**

> Inclut l'alphabet OTAN (alpha, bravo, foxtrot...) : envisager UNE fiche `alphabet aviation` avec les lettres en `variantes` plutôt que 26 fiches.

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`radio`(714) `message`(339) `fréquence`(311) `pan`(157) `fréquences`(145) `urgence`(137) `détresse`(115) `read-back`(112) `panne`(108) `panne radio`(108) `transpondeur`(89) `afis`(88) `annonce`(75) `collationnement`(74) `clairances`(68) `messages`(65) `phraséologie`(65) `ats`(63) `both`(62) `roger`(60) `panne moteur`(57) `canal`(56) `ovc`(56) `collationner`(54) `premier contact`(51) `autorisation`(47) `com`(45) `micro`(45) `points de report`(45) `report`(45) `alpha`(42) `foxtrot`(42) `hotel`(42) `tango`(36) `few`(34) `canal unique`(26) `point de report`(25) `mayday`(19) `sct`(19) `silence radio`(17) `panne électrique`(16) `vrb`(16) `bkn`(15) `indicatif`(15) `say again`(15) `atc`(14) `bravo`(14) `clairance`(13) `alphabet`(12) `mike`(12) `prob`(12) `victor`(12) `golf`(11) `x-ray`(11) `clairance de décollage`(6) `détresse mayday`(6) `transpondeur 7600`(4) `transpondeur 7700`(3) `collationnement clairance`(2) `urgence pan pan`(1) `alphabet aviation`·M `autorisation atterrissage`·M `barotraumatisme` `radiocompas`·M `siv` `squawk` `transpondeur 7500`·M `transpondeur mode c`·M

### Lot 11 — Facteurs humains & sécurité des vols (54 termes)

`categorie` visée : **Facteurs humains (NOUVELLE)**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`décision`(458) `risque`(307) `sécurité`(241) `discipline`(135) `situation`(127) `réflexe`(126) `erreurs`(113) `no-go`(107) `tem`(94) `imsafe`(90) `diagnostic`(83) `hypoxie`(82) `menace`(82) `yeux`(81) `vision`(78) `sensation`(75) `secours`(70) `jugement`(69) `continuation`(61) `illusions`(61) `pièges`(59) `aviate`(57) `illusion`(56) `alcool`(55) `sommeil`(55) `facteurs humains`(53) `oreille`(53) `cerveau`(52) `piège`(51) `piège classique`(51) `vigilance`(51) `oxygène`(50) `piégeux`(47) `menaces`(46) `accident`(45) `échec`(45) `trou noir`(36) `biais`(25) `mémoire de travail`(23) `fatigue`(18) `mal de l'air`(18) `stress`(18) `facteur humain`(16) `fromage suisse`(16) `crm`(15) `erreur`(15) `oreille interne`(15) `tache aveugle`(14) `vitesse de sécurité`(2) `aerocolique`·M `chaine des erreurs`·M `conscience de la situation` `illusion somatogyrale` `vision nocturne`

### Lot 12 — Atomes polysémiques & génériques (100 termes)

`categorie` visée : **selon le sens retenu**

> ⚠️ LOT LE PLUS RISQUÉ. Ces mots sont aussi du français courant. Pour chacun : soit renseigner `contexte_requis` (ex. `seuil` a déjà `["piste","QFU",...]`), soit préférer une expression composée déjà présente au lexique et NE PAS créer l'atome seul. Décision terme par terme, à valider avec Louis avant rédaction.

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`vol`(1334) `air`(750) `vitesse`(698) `avion`(505) `tour`(411) `nuit`(362) `seul`(330) `froid`(306) `basse`(303) `courte`(290) `chaud`(279) `plein`(279) `bord`(255) `haute`(249) `trafic`(218) `position`(214) `contrôle`(209) `départ`(204) `stable`(197) `contact`(188) `couper`(185) `ciel`(165) `mer`(159) `ligne`(158) `destination`(155) `matin`(154) `structure`(152) `perte`(141) `code`(140) `chute`(133) `utilisable`(133) `stabilisé`(131) `vue`(127) `sec`(124) `rotation`(121) `blanc`(108) `chaleur`(108) `configuration`(103) `longue`(102) `cockpit`(101) `voler`(100) `élevée`(98) `soleil`(95) `station`(92) `dense`(90) `profil`(90) `sèche`(90) `caution`(89) `terre`(85) `jaune`(84) `aviation`(80) `instable`(76) `catégorie`(74) `séquence`(71) `eau`(70) `phase`(70) `précaution`(68) `champ`(65) `arrivée`(63) `pilotage`(62) `schéma`(62) `trou`(62) `soir`(55) `évitement`(53) `entrée`(52) `organisme`(52) `plongée`(52) `hiver`(51) `stabiliser`(51) `conflit`(50) `essai`(50) `sortis`(50) `alerte`(49) `aéronautique`(49) `rayon`(48) `récupération`(46) `interception`(45) `piloter`(45) `bat`(38) `vert`(38) `rentrés`(30) `rouge`(29) `sol`(27) `cg`(23) `warning`(23) `cv`(21) `up`(17) `effet`(16) `enveloppe`(15) `angle`(14) `config`(14) `axe`(12) `température`(12) `pression`(11) `sortie`(11) `manoeuvre`(3) `manœuvre`·M `papillon` `sigma`·M `vireur`·M

### Lot 13 — Phases de vol & divers résiduel (21 termes)

`categorie` visée : **Vitesses & performances / Météo**

Termes (occurrences au corpus entre parenthèses ; `·M` = bloc METIER, sans lien actif) :

`météo`(490) `gaz`(487) `demi-tour`(116) `plein gaz`(113) `tod`(93) `météo du jour`(74) `vol lent`(59) `cruise`(46) `commandant de bord`(29) `croisière`(21) `vitesse de croisière`(20) `vol de nuit`(19) `info trafic`(16) `vitesse de rotation`(10) `vol à vue`(5) `chute de pression`(4) `tour de contrôle`(4) `région terminale`(2) `iac`·M `modele threat and error`·M `vitesse d'envol`·M

---

## 6. Règle permanente de couverture (inscrite au projet)

Cette règle est reportée dans `projects/aero-coach/PLAN-rubriques-meteo-nuage-glossaire.md`
et `projects/aero-coach/REPRISE.md`. Rappel :

**À chaque création ou modification d'un texte de séance**, le vocabulaire aéro du texte doit
être extrait par programme, comparé au glossaire, et tout terme manquant doit recevoir sa fiche
AVANT livraison. Un texte dont le vocabulaire n'est pas couvert ne se livre pas.

## 7. Ordre de travail recommandé

1. **D'abord purger les 9 collisions** de la section 2 — sinon chaque lot en ajoute.
2. Lots 1 à 3 (OACI, météo) : gabarits réguliers, rendement élevé.
3. Lots 4 à 9 (aéro, moteur, instruments, nav, piste, réglementation) : le cœur pédagogique.
4. Lots 10-11 (phraséologie, facteurs humains) : factoriser via `variantes`.
5. **Lot 12 en dernier, après arbitrage avec Louis** : les 100 atomes polysémiques exigent
   `contexte_requis` terme par terme, ou l'abandon de l'atome au profit d'une expression composée.
6. Lot 13 : résidu à reclasser au fil de l'eau.

Le champ `variantes` est le levier de productivité : une fiche bien dotée en variantes couvre
5 à 10 formes du lexique. Les 989 termes n'impliquent donc PAS 989 fiches rédigées — l'estimation
réaliste est de **550 à 650 fiches** une fois les pluriels, casses et sigles factorisés.
