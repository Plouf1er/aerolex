# Rapport d'Importation Final du Lexique AeroLex (Fusion v1 + v2)

Ce rapport présente l'état final de la fusion et de la préparation du fichier d'importation pour le glossaire AeroLex (v2 vers v1).

## 1. Chiffres Clés de l'Importation

- **Nombre total de fiches v1 existantes :** 769 fiches (757 rédigées, 12 en attente)
- **Nombre total de fiches v2 brutes chargées :** 546 fiches
- **Fiches v2 exclues car doublons de v1 :** 5 fiches (portance, décrochage, aile, traînée, vitesse propre)
- **Fiches v2 filtrées car doublons internes v2 :** 8 fiches (ndb, mode s, rnav, etc. fusionnées en faveur du Lot 7)
- **Nombre final de fiches v2 uniques importées :** **533 fiches**
- **Nombre de catégories utilisées :** 16 / 16 (100% de conformité, 0 violation)
- **Nombre de familles utilisées :** 69 (100% de conformité, 0 violation)
- **Nombre de références croisées (xrefs) orphelines :** **0** (100% de résolution)
- **Nombre de fiches v2 avec moins de 2 xrefs :** **0** (conformité parfaite)

## 2. Analyse des 5 Doublons v1 vs v2 Exclus

Comme convenu, les 5 fiches suivantes de la v2 ont été exclues au profit de leur version v1 qui intègre déjà la taxonomie complète. Voici une analyse comparative de leurs définitions :

### `portance`
- **Source v2 :** `REDIGE-LOT-7-COMPLEMENT.json`
- **Définition v1 (conservée) :** "Force aérodynamique perpendiculaire au vent relatif, dirigée vers le haut, générée par l'écoulement de l'air autour de l'aile. En vol rectiligne stabilisé, la portance équilibre exactement la masse totale de l'avion."
- **Définition v2 (exclue) :** "Force aérodynamique perpendiculaire à l'écoulement du vent relatif, dirigée vers le haut, qui s'exerce sur la voilure d'un aéronef. Elle est générée par la différence de pression entre l'extrados et l'intrados."
- **Analyse comparative :**
  La définition v1 est excellente car elle mentionne l'équilibre en vol rectiligne stabilisé, tandis que la v2 complète utilement en explicitant la différence de pression intrados/extrados. La fusion des deux définitions pourrait être envisagée en production.

### `décrochage`
- **Source v2 :** `REDIGE-LOT-7-COMPLEMENT.json`
- **Définition v1 (conservée) :** "Perte brutale de portance quand l'angle d'attaque dépasse l'incidence critique — indépendant de la vitesse proprement dite: on décroche à n'importe quelle vitesse si on tire trop."
- **Définition v2 (exclue) :** "Perte brutale de portance due à un angle d'incidence trop élevé, provoquant le décollement des filets d'air sur l'extrados de l'aile et entraînant une chute rapide de l'altitude de l'aéronef."
- **Analyse comparative :**
  La définition v1 est très pédagogique car elle insiste sur le fait qu'on décroche à n'importe quelle vitesse si on dépasse l'incidence critique. La v2 est plus technique et descriptive de l'effet d'assiette. La v1 reste supérieure pour l'apprentissage pilote.

### `aile`
- **Source v2 :** `REDIGE-LOT-7-COMPLEMENT.json`
- **Définition v1 (conservée) :** "Voilure principale de l'aéronef destinée à générer la portance nécessaire au vol. Son profil aérodynamique crée une dépression sur l'extrados et une surpression sur l'intrados."
- **Définition v2 (exclue) :** "Surface portante principale d'un aéronef conçue pour générer la portance nécessaire au vol sustenté. Sa structure aérodynamique comprend généralement un bord d'attaque, un bord de fuite, un extrados et un intrados."
- **Analyse comparative :**
  La définition v1 est concise et centrée sur la physique (dépression/surpression), tandis que la v2 liste les composants géométriques de l'aile (bord d'attaque, bord de fuite, extrados, intrados). Les deux se complètent parfaitement.

### `traînée`
- **Source v2 :** `REDIGE-LOT-7-COMPLEMENT.json`
- **Définition v1 (conservée) :** "Force aérodynamique de résistance à l'avancement, parallèle à la trajectoire et opposée au mouvement de l'aéronef. Générée par le déplacement dans l'air, elle doit être compensée par la traction du moteur."
- **Définition v2 (exclue) :** "Force aérodynamique de résistance qui s'oppose au mouvement d'un aéronef dans l'air. Parallèle à l'écoulement, elle doit être compensée par la poussée du moteur pour maintenir une vitesse de vol constante."
- **Analyse comparative :**
  La définition v1 et la v2 sont très proches et excellentes. La v1 mentionne la traction du moteur tandis que la v2 mentionne la poussée. Les deux définitions sont d'une qualité équivalente.

### `vitesse propre`
- **Source v2 :** `REDIGE-LOT-7-COMPLEMENT.json`
- **Définition v1 (conservée) :** "Vitesse de l'aéronef par rapport à l'air environnant non perturbé. Également appelée vitesse vraie, elle s'obtient en corrigeant la vitesse indiquée des erreurs de densité de l'air dues à l'altitude et à la température."
- **Définition v2 (exclue) :** "Vitesse réelle d'un aéronef par rapport à la masse d'air environnante. Elle est calculée en corrigeant la vitesse conventionnelle des variations de température et de densité de l'air liées à l'altitude."
- **Analyse comparative :**
  La définition v1 est excellente et mentionne l'erreur de densité due à la température et l'altitude, tandis que la v2 est concise et claire. Les deux définitions se complètent parfaitement.

## 3. Gestion des Doublons Internes à la v2

8 termes étaient définis en doublon au sein même des lots v2 (présents à la fois dans le Lot 4 ou 6 et dans le Lot 7 Complément). Ces doublons ont été résolus en **conservant la version révisée et enrichie du Lot 7 Complément** et en écartant les anciennes versions.

| Terme doublon | Fichiers d'origine | Décision appliquée |
|---|---|---|
| `NDB` | REDIGE-LOT-4.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |
| `mode S` | REDIGE-LOT-4.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |
| `prise Pitot` | REDIGE-LOT-4.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |
| `réchauffage Pitot` | REDIGE-LOT-4.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |
| `tube de Pitot` | REDIGE-LOT-4.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |
| `RNAV` | REDIGE-LOT-4.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |
| `carburant 100LL` | REDIGE-LOT-6.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |
| `UL91` | REDIGE-LOT-6.json, REDIGE-LOT-7-COMPLEMENT.json | Conservé la version `REDIGE-LOT-7-COMPLEMENT.json` (définition plus précise et enrichie). |

## 4. Résolution des Variantes Conflictueles (~50)

Un total de **46 conflits** a été détecté où une variante de fiche v2 correspondait à un terme principal existant en v1.

**Action corrective automatique :**
1. Retrait de la variante conflictuelle de la liste `variantes` de la fiche v2.
2. Ajout d'une référence croisée (`xrefs`) de la fiche v2 vers la fiche v1 correspondante.

Voici la liste des conflits résolus :

| Terme v2 | Variante retirée | Terme v1 lié en xref |
|---|---|---|
| `1013,25 hPa` | `calage standard` | `calage standard` |
| `TL` | `niveau de transition` | `niveau de transition` |
| `TWR` | `tour de contrôle` | `tour de contrôle` |
| `Vlof` | `vitesse d'envol` | `vitesse d'envol` |
| `accusé de réception` | `Roger` | `roger` |
| `agent AFIS` | `AFIS` | `afis` |
| `angle d'incidence` | `incidence` | `incidence` |
| `angle d'incidence` | `angle d'attaque` | `angle d'attaque` |
| `cat` | `turbulence en air clair` | `turbulence en air clair` |
| `compas magnétique` | `compas` | `compas` |
| `conditions de vol à vue` | `VMC` | `VMC` |
| `conditions de vol à vue` | `conditions VMC` | `conditions vmc` |
| `congestus` | `cumulus congestus` | `cumulus congestus` |
| `couple` | `couple moteur` | `couple moteur` |
| `décrochage accéléré` | `décrochage dynamique` | `décrochage dynamique` |
| `effet de trou noir` | `trou noir` | `trou noir` |
| `fg` | `brouillard` | `brouillard` |
| `incidence de décrochage` | `incidence critique` | `incidence critique` |
| `kilogramme` | `kg` | `kg` |
| `kilomètre` | `km` | `km` |
| `mille nautique` | `NM` | `NM` |
| `mode C` | `transpondeur mode C` | `transpondeur mode c` |
| `niveau de croisière` | `niveau de vol` | `niveau de vol` |
| `obstacle` | `obstacle artificiel` | `obstacle artificiel` |
| `onde orographique` | `onde de relief` | `onde de relief` |
| `plan de vol déposé` | `plan de vol` | `plan de vol` |
| `point de compte rendu` | `point de report` | `point de report` |
| `poussée` | `traction` | `traction` |
| `pression atmosphérique` | `pression` | `pression` |
| `ra` | `pluie` | `pluie` |
| `rafale descendante` | `courant descendant` | `courant descendant` |
| `rapport portance/traînée` | `finesse` | `finesse` |
| `rvr` | `portée visuelle de piste` | `portée visuelle de piste` |
| `régime` | `régime moteur` | `régime moteur` |
| `secteur d'information de vol` | `SIV` | `siv` |
| `sh` | `averse` | `averse` |
| `signaux lumineux de la tour` | `signaux lumineux` | `signaux lumineux` |
| `situation awareness` | `conscience de la situation` | `conscience de la situation` |
| `surface isobare` | `isobare` | `isobare` |
| `tours/minute` | `RPM` | `rpm` |
| `tube de pitot` | `Pitot` | `pitot` |
| `visibilité météo` | `visibilité` | `visibilité` |
| `visibilité météo` | `visibilité horizontale` | `visibilité horizontale` |
| `vitesse conventionnelle` | `CAS` | `cas` |
| `zone D` | `zone dangereuse` | `zone dangereuse` |
| `zone P` | `zone interdite` | `zone interdite` |

## 5. Répartition Taxonomique Finale

Les 533 fiches importées ont été réparties de manière équilibrée au sein des 16 catégories et 71 familles pédagogiques existantes de la v1, sans aucune création de catégorie ou de famille.

### Répartition par Catégorie

| Catégorie v1 | Nombre de fiches importées |
|---|---|
| Météo | 78 |
| Réglementation & docs | 69 |
| Aérodynamique | 59 |
| Aérodrome & cartes | 58 |
| Moteur & hélice | 52 |
| Sécurité & facteurs humains | 39 |
| Navigation | 36 |
| Instruments | 26 |
| Vitesses & performances | 26 |
| Radio & phraséologie | 25 |
| Altimétrie | 16 |
| Unités | 15 |
| Structure & cellule | 11 |
| Masse & centrage | 11 |
| Procédures | 8 |
| Vent | 4 |

### Répartition Détaillée par Catégorie et Famille

#### Catégorie : Altimétrie (16 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `altitudes` | 12 | 1000 ft agglomération, 500 ft, altitude minimale de sécurité, couche de transition |
| `calages_altimetriques` | 1 | 1013,25 hPa |
| `references_verticales` | 3 | altitude, altitude vraie, hauteur |

#### Catégorie : Aérodrome & cartes (58 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `cartes_aeronautiques` | 10 | AD, AIC, carte OACI 1/500 000, complément aux cartes |
| `circuit_procedures` | 4 | dégagement de piste, point d'entrée, point de compte rendu, point de sortie |
| `dimensions_piste` | 16 | aire de manœuvre, aire de mouvement, aire de sécurité d'extrémité, aire de trafic |
| `pistes` | 22 | balisage basse intensité, balisage de taxiway, balisage haute intensité, barre d'arrêt |
| `procedures_sol` | 6 | croix blanche, damier, panneau de signalisation, pistolet à signaux |

#### Catégorie : Aérodynamique (59 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `assiettes` | 4 | angle d'incidence, angle de calage, centre de poussée, foyer |
| `decrochages` | 10 | avertisseur de décrochage, buffeting, diagramme de manœuvre, décrochage accéléré |
| `hypersustentateurs` | 13 | allongement, bord d'attaque, bord de fuite, corde |
| `trainee` | 22 | Cd, charge alaire, Cl, coefficient de portance |
| `virages` | 10 | amortissement, effet de dièdre, lacet induit, lacet inverse |

#### Catégorie : Instruments (26 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `instruments_anemobarometriques` | 8 | alternat, blocage Pitot, blocage statique, prise dynamique |
| `instruments_gyroscopiques` | 6 | conservateur de cap, coordinateur de virage, directionnel, erreurs gyroscopiques |
| `instruments_radionavigation` | 11 | 7000 (VFR), code 7500, code 7600, code 7700 |
| `references_magnetiques` | 1 | compas magnétique |

#### Catégorie : Masse & centrage (11 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `limites_de_centrage` | 5 | centrage arrière, centrage avant, enveloppe de centrage, index |
| `masses` | 6 | charge utile, masse et bras de levier, masse maximale au décollage, masse maximale à l'atterrissage |

#### Catégorie : Moteur & hélice (52 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `commandes_cockpit` | 8 | carburateur, correcteur d'altitude, EGT, injection |
| `givrage` | 2 | antigivrage, dégivrage |
| `helice` | 11 | calage d'hélice, couple, couple de renversement, effet de couple |
| `magnetos` | 2 | bougie, encrassement des bougies |
| `pannes_moteur` | 4 | auto-allumage, cliquetis, détonation, panne sèche |
| `parametres_moteur` | 25 | 100LL, admission, alimentation croisée, ampèremètre |

#### Catégorie : Météo (78 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `codes_meteo_etat` | 22 | bruine, ds, dz, fc |
| `conditions_visibilite` | 5 | brouillard d'advection, brouillard d'évaporation, brume sèche, rvr |
| `couches_atmospheriques` | 1 | stratosphère |
| `effets_vent_relief` | 2 | force de Coriolis, vent géostrophique |
| `fronts_meteorologiques` | 4 | front polaire, front stationnaire, secteur chaud, traîne |
| `givrage` | 3 | givrage clair, givrage mixte, givre blanc |
| `isothermes_temperatures` | 4 | gradient adiabatique saturé, gradient adiabatique sec, isothermie, salr |
| `messages_meteo_types` | 5 | airmet, carte isobarique, coupe verticale, gamet |
| `nuages_couverture` | 3 | étage inférieur, étage moyen, étage supérieur |
| `nuages_especes` | 5 | capillatus, congestus, humilis, mediocris |
| `nuages_genres` | 2 | cirrocumulus, cirrus |
| `stabilite_atmospherique` | 19 | adiabatique, cellule orageuse, chaleur latente, col barométrique |
| `turbulences` | 3 | cat, front de rafales, turbulence thermique |

#### Catégorie : Navigation (36 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `heures_estimations` | 3 | base de temps, ETD, temps sans vent |
| `navigation_caps_et_routes` | 30 | cheminement, coordonnées géographiques, dead reckoning, dernier point connu |
| `references_magnetiques` | 3 | courbe de déviation, inclinaison magnétique, nord compas |

#### Catégorie : Procédures (8 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `briefings` | 1 | briefing décollage |
| `pannes_moteur` | 3 | demi-tour impossible, panne moteur au décollage, vent arrière basse hauteur |
| `phases_vol` | 3 | arrêt moteur, dégagement, procédure de mise en route |
| `procedures_sol` | 1 | essais moteur |

#### Catégorie : Radio & phraséologie (25 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `alphabet_oaci` | 1 | alphabet OACI |
| `radio_phraseologie` | 24 | 121,5 MHz, 25 kHz, accusé de réception, AFFIRM |

#### Catégorie : Réglementation & docs (69 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `altitudes` | 2 | hauteurs minimales de survol, niveau de croisière |
| `documents_bord` | 19 | activation, APRS, assurance, carnet de vol |
| `espaces_controles` | 20 | ACC, agent AFIS, APP, AWY |
| `espaces_reglementes` | 4 | zone D, zone de ségrégation, zone P, zone R |
| `regles_vol` | 24 | ALERFA, aéronef intercepté, conditions de vol à vue, DETRESFA |

#### Catégorie : Structure & cellule (11 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `commandes_cockpit` | 7 | amortisseur, atterrisseur, catégorie normale, catégorie utilitaire |
| `gouvernes_primaires` | 4 | fuselage monocoque, fuselage semi-monocoque, fuselage treillis, revêtement travaillant |

#### Catégorie : Sécurité & facteurs humains (39 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `facteurs_humains_physiologie` | 17 | aérosinusite, ceinture, don du sang, déshydratation |
| `fh_modeles_et_biais` | 11 | chaîne causale, chaîne des causes, complaisance, erreur |
| `fh_prise_de_decision` | 4 | DODAR, prise de décision, situation awareness, évacuation |
| `physiologie` | 7 | désorientation spatiale, effet de trou noir, fausse horizon, faux horizon |

#### Catégorie : Unités (15 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `unites_altitude_pression` | 4 | facteur de conversion pied/mètre, inHg, kilomètre, mètre |
| `unites_masse_carburant` | 5 | gallon, kilogramme, litre, litre/gallon |
| `unites_moteur_temps` | 6 | Fahrenheit, heure locale, mille nautique, minute |

#### Catégorie : Vent (4 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `brises` | 1 | brise de montagne |
| `effets_vent_relief` | 1 | onde orographique |
| `turbulences` | 2 | microburst, rafale descendante |

#### Catégorie : Vitesses & performances (26 fiches)
| Famille v1 | Nombre de fiches | Exemples de termes importés |
|---|---|---|
| `distances_performances` | 11 | consommation spécifique, distance accélération-arrêt, distance franchissement 15 m, distance franchissement 50 ft |
| `performances_verticales` | 3 | plafond de croisière, plafond de sustentation, plafond pratique |
| `vitesses_limites` | 2 | VLO, VRA |
| `vitesses_mesurees` | 6 | EAS, erreur de densité, erreur de position, erreur instrumentale |
| `vitesses_operationnelles` | 4 | VBG, VG, Vlof, Vtoss |