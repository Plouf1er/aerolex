# Audit xrefs vs familles — 2026-08-04

Généré par le run AeroLex de la nuit du 04/08. **Aucune donnée du corpus n'a été
modifiée** : audit + recommandation seulement.

## Règle appliquée

Dérivée du cas `tour-de-piste` (famille `circuit_procedures`, 17 membres ; xrefs
`vent arrière` / `étape de base` / `finale` / `remise des gaz` — aucun des 4 dans
la famille, tous dans `circuit_branches`) :

- un xref qui pointe vers un **membre d'une famille du terme** = **bruit** 
  (le tableau de famille le montre déjà → le xref n'ajoute rien, à supprimer) ;
- un xref qui pointe vers une **autre famille** = **signal qu'une famille manque**
  au terme (candidat multi-familles).

## Chiffres globaux (1300 fiches)

| Mesure | Valeur |
|---|---|
| Fiches auditées | 1300 |
| xrefs au total | 1909 |
| **Bruit** (xref déjà membre d'une famille du terme) | **966** (50 %) |
| **Candidats** multi-familles (xref hors famille) | **943** (49 %) |
| Fiches avec au moins 1 xref de bruit | 519 |
| Fiches avec au moins 1 candidat | 489 |

## Verdict : pathologie de fond, pas un cas isolé

`tour-de-piste` n'est pas une exception : **966 xrefs sur 1909**
(50 %) redisent ce que le tableau de famille affiche déjà,
répartis sur **519 fiches**. Symétriquement **943 xrefs**
sur 489 fiches désignent une famille voisine : ce sont les
candidats du futur multi-familles.

## Top familles voisines citées en xref

Un couple qui revient souvent = deux familles que le corpus traite comme liées ;
candidat naturel à une 2ᵉ famille sur les termes concernés.

| n | famille du terme | famille citée en xref |
|---|---|---|
| 14 | `unites` | `navigation_caps_et_routes` |
| 13 | `espaces_controles` | `regles_vol` |
| 12 | `codes_meteo_etat` | `conditions_visibilite` |
| 11 | `radio_phraseologie` | `regles_vol` |
| 11 | `radio_phraseologie` | `espaces_controles` |
| 10 | `(sans famille)` | `trainee` |
| 10 | `circuit_branches` | `circuit_procedures` |
| 9 | `dimensions_piste` | `pistes` |
| 9 | `distances_performances` | `trainee` |
| 8 | `documents_bord` | `radio_phraseologie` |
| 8 | `documents_bord` | `espaces_controles` |
| 8 | `facteurs_humains_physiologie` | `fh_modeles_et_biais` |
| 7 | `stabilite_atmospherique` | `isothermes_temperatures` |
| 7 | `circuit_procedures` | `circuit_branches` |
| 7 | `messages_meteo_evolutions` | `messages_meteo_types` |
| 7 | `fh_modeles_et_biais` | `fh_prise_de_decision` |
| 6 | `calages_altimetriques` | `altitudes` |
| 6 | `espaces_controles` | `radio_phraseologie` |
| 6 | `altitudes` | `cartes_aeronautiques` |
| 6 | `circuit_branches` | `atterrissages` |
| 6 | `facteurs_humains_physiologie` | `fh_prise_de_decision` |
| 6 | `isothermes_temperatures` | `stabilite_atmospherique` |
| 6 | `regles_vol` | `altitudes` |
| 5 | `regles_vol` | `radio_phraseologie` |
| 5 | `documents_bord` | `regles_vol` |

## Recommandation

1. **Ne pas supprimer les 966 xrefs de bruit maintenant** : ils deviendront
   redondants automatiquement quand le tableau de famille sera partout (déplié
   par défaut depuis ce run). Supprimer d'abord, c'est perdre l'information si
   la famille du terme change ensuite.
2. **Traiter les 943 candidats avec le multi-familles** : le rendu client accepte
   DÉJÀ un tableau de familles (`_payloadFamilles`) et produit un tableau par
   famille — seul le producteur n'émet qu'une chaîne. Côté client, rien à faire.
3. Ordre : multi-familles d'abord, purge des xrefs de bruit ensuite, en mesurant
   à nouveau avec ce script (le bruit devrait augmenter mécaniquement, puisqu'un
   xref hors famille devient un xref intra-famille dès que la 2ᵉ famille existe).

Détail par fiche : `data/audit-xrefs-familles.json` (clé `detail`).
