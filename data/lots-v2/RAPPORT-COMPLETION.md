# RAPPORT-COMPLETION — 12 termes `a_rediger` du glossaire AeroLex

Date : 2026-08-03
Source : `data/data_glossaire_full.py` (1302 termes, **lu en seule lecture — non modifié**)
Livrable : `data/lots-v2/COMPLETION-12-TERMES.json` (7 fiches rédigées)

---

## 1. État initial vérifié (les 12 fiches, champ par champ)

Toutes les 12 ont bien `definition == ""` et `statut == "a_rediger"`. Aucune n'avait de `xrefs`. Détail mesuré :

| terme | definition | categorie | famille | variantes | origine |
|---|---|---|---|---|---|
| bande derobee | vide | Aérodrome & cartes | — | — | metier |
| bat | vide | Moteur & hélice | — | bats | corpus |
| branche | vide | Procédures | — | branches | corpus |
| cas | vide | Vitesses & performances | **vitesses_mesurees** | — | corpus |
| constante structurale | vide | Structure & cellule | — | — | metier |
| cos | vide | Vent | — | — | corpus |
| engine | vide | Moteur & hélice | — | engines | corpus |
| remise de gaz interrompue | vide | Procédures | — | remises de gaz interrompue | metier |
| sigma | vide | Aérodynamique | — | sigmas | metier |
| sin | vide | Vent | — | sins | corpus |
| station | vide | Masse & centrage | — | stations | corpus |
| structure | vide | Structure & cellule | — | structures | corpus |

### Graphe de référencement (qui cite ces termes)

Balayage exhaustif des 1302 fiches, champs `xrefs` et `variantes` :

| terme | cité en xref par | cité en variante par |
|---|---|---|
| **cas** | **`vitesse conventionnelle`** | — |
| les 11 autres | *(aucune fiche)* | *(aucune fiche)* |

**Conséquence directe** : `cas` est le SEUL des 12 dont la suppression casserait un lien existant.

---

## 2. Classement des 12

### VRAI_TERME_A_DEFINIR — 7 termes

| terme | justification |
|---|---|
| **bande derobee** | Terme métier réel (aire d'atterrissage occasionnelle non aménagée). Origine `metier`, pas `corpus` : saisi volontairement. Cohérent avec la fiche `bande` déjà présente. |
| **branche** | Vrai terme de procédure. Le mot est employé dans 5 définitions du corpus comme concept structurant (`finale` : « Dernière branche du tour de piste » ; `vent arrière`, `vent traversier`, `étape de base` s'ouvrent tous sur « Branche du tour de piste… » ; `temps estimé` : « une branche de navigation »). Une famille dédiée `circuit_branches` existe (9 membres) mais la tête de notion manquait. |
| **cas** | **REQUALIFIÉ — PAS un artefact.** Trois preuves convergentes : (1) `famille = "vitesses_mesurees"` était déjà renseignée, seule des 12 à porter une famille ; (2) il est membre de cette famille aux côtés de `IAS`, `TAS`, `EAS`, `GS`, `Mach` — la série complète des vitesses anémométriques ; (3) il est **cité en xref par `vitesse conventionnelle`** (dont les xrefs sont `['erreur instrumentale', 'erreur de position', 'cas']`), c'est-à-dire par sa propre traduction française. C'est bien CAS = Calibrated Air Speed. Le supprimer aurait laissé une xref orpheline. |
| **constante structurale** | Terme métier de dimensionnement. Origine `metier`. Catégorie `Structure & cellule` cohérente, s'articule avec `facteur de charge limite` / `facteur de charge ultime` déjà présents. |
| **remise de gaz interrompue** | Terme métier de sécurité (la remise des gaz abandonnée en cours, configuration accidentogène classique). Origine `metier`. `remise des gaz` et `approche interrompue` existent déjà : ce terme complète la série. |
| **station** | Vrai terme, sens de masse & centrage : emplacement de chargement repéré par son bras de levier. La catégorie déjà posée (`Masse & centrage`) désambiguïse et écarte l'autre sens du mot (station radio au sol, employé dans 15 définitions du corpus — `NDB`, `QDM`, `VOR`, `QNH`…). Le sens chargement est le bon ici. |
| **structure** | Vrai terme, notion faîtière. Le mot apparaît dans 25 définitions du corpus. Les éléments constitutifs sont tous des fiches existantes (`longeron`, `nervure`, `fuselage`, `revêtement travaillant`) mais la tête de notion était vide. |

### ARTEFACT_A_SUPPRIMER — 5 termes

| terme | justification | référencement |
|---|---|---|
| **bat** | Aucun sens aéro FR en `Moteur & hélice`. Zéro occurrence du mot dans les 1302 définitions du corpus. Variante `bats` générée mécaniquement (pluralisation automatique), signature d'extraction. Probable capture de l'anglais *battery/BAT* ou d'un fragment. | **non référencé** (0 xref, 0 variante) |
| **cos** | Fragment de formule trigonométrique. Preuve d'origine : `composante de face` contient « (V × cos θ, où θ est l'écart au QFU) » et la fiche `θ` contient « (V × cos θ) ». L'extracteur a capturé `cos` depuis ces formules. Catégorie `Vent` = exactement les fiches sources. | **non référencé** (0 xref, 0 variante) |
| **sin** | Symétrique de `cos`. `composante de travers` contient « (V × sin θ, où θ est l'écart au QFU) », et `θ` « et de travers (V × sin θ) ». Même mécanisme, même catégorie `Vent`. Variante `sins` mécanique. | **non référencé** (0 xref, 0 variante) |
| **engine** | Mot anglais nu. Preuve d'origine : la fiche `sep` contient « Single Engine Piston ». L'extracteur a isolé `engine` de cet acronyme développé. Variante `engines` mécanique. Le glossaire est francophone, `moteur` couvre la notion. | **non référencé** (0 xref, 0 variante) |
| **sigma** | Lettre grecque nue en `Aérodynamique` (σ = rapport de densité, ou contrainte). Zéro occurrence de « sigma » dans les 1302 définitions : aucune fiche ne l'utilise ni ne le définit en creux. Variante `sigmas` mécanique. Pas de contenu à rattacher. | **non référencé** (0 xref, 0 variante) |

> **Note pour arbitrage** : les 5 artefacts sont tous supprimables sans casser un seul lien du graphe (vérifié par balayage exhaustif). `sigma` est le seul cas discutable — si tu veux garder une entrée pour σ (rapport de densité), il faudrait le renommer `rapport de densité` plutôt que de définir la lettre. Je ne l'ai pas fait : ce serait créer un terme, pas compléter celui-ci.

---

## 3. Les 7 définitions rédigées

### bande derobee — *Aérodrome & cartes / pistes* — 36 mots
> Bande de terrain sommairement aménagée, dérobée à la culture ou au pâturage, utilisable comme aire d'atterrissage occasionnelle. Sans balisage ni services, elle impose une reconnaissance en vol de l'état du sol et des obstacles avant usage.

xrefs : `bande`, `piste`, `plateforme`

### branche — *Procédures / circuit_branches* — 31 mots
> Segment rectiligne d'une trajectoire, qu'il s'agisse d'un côté du tour de piste ou d'une portion de route entre deux points tournants. Chaque branche se pilote à cap, vitesse et altitude définis.

xrefs : `tour de piste`, `vent arrière`, `étape de base`, `point tournant`

### cas — *Vitesses & performances / vitesses_mesurees* — 31 mots
> Calibrated Air Speed: vitesse conventionnelle, soit la vitesse indiquée corrigée des erreurs d'instrument et de position de l'antenne statique. Elle sert de référence aux limitations publiées dans le manuel de vol.

xrefs : `vitesse conventionnelle`, `IAS`, `erreur de position`, `erreur instrumentale`

### constante structurale — *Structure & cellule* — 31 mots
> Grandeur caractérisant la résistance retenue au dimensionnement d'un élément de cellule, exprimée comme rapport entre charge admissible et section sollicitée. Elle fixe la marge conservée entre effort de service et rupture.

xrefs : `facteur de charge limite`, `facteur de charge ultime`, `longeron`

### remise de gaz interrompue — *Procédures / atterrissages* — 32 mots
> Remise des gaz abandonnée en cours d'exécution pour reprendre l'atterrissage, ou au contraire mal engagée puis reprise. Cette hésitation cumule les inconvénients des deux options et constitue une configuration reconnue comme dangereuse.

xrefs : `remise des gaz`, `approche interrompue`, `courte finale`

### station — *Masse & centrage / masses* — 32 mots
> Emplacement de chargement repéré sur l'appareil par sa distance à la référence de centrage: sièges, soutes, réservoirs. Le devis de masse affecte à chaque station une masse et son bras de levier.

xrefs : `bras de levier`, `devis de masse`, `moment`, `centrage`

### structure — *Structure & cellule* — 29 mots
> Ensemble des éléments de la cellule qui reprennent et transmettent les efforts: longerons, nervures, cadres et revêtement. Elle est dimensionnée pour encaisser les charges de vol sans déformation permanente.

xrefs : `longeron`, `nervure`, `fuselage`, `revêtement travaillant`

---

## 4. Auto-vérification (mesurée par script contre le GLOSSAIRE)

| contrôle | résultat |
|---|---|
| définitions écrites | **7** |
| longueur mots min / moy / max | **29 / 31,7 / 36** (borne 20–45 respectée) |
| xrefs totales | 25 |
| **xrefs non résolues** | **0** |
| xrefs par fiche | 3 minimum (exigence : ≥ 2) |
| catégories hors taxonomie | **0** (7 valeurs prises dans les 16 existantes) |
| familles hors taxonomie | **0** (`pistes`, `circuit_branches`, `vitesses_mesurees`, `atterrissages`, `masses` + 2 × `null`, toutes préexistantes) |
| balises / entités HTML | **0** |
| valeurs chiffrées | **0** (aucun chiffre dans les 7 définitions) |
| `statut = "redige"` | 7/7 |
| `origine = "v2-completion"` | 7/7 |

**Total violations : 0.**

Note sur les familles : `constante structurale` et `structure` reçoivent `famille: null`. C'est délibéré — les 3 familles disponibles sous `Structure & cellule` (`commandes_cockpit`, `gouvernes_primaires`, `hypersustentateurs`) ne conviennent à aucun des deux, et 16 des 36 fiches de cette catégorie sont déjà à `null` (dont `longeron`, `nervure`, `fuselage`). Inventer une famille était interdit.

---

## 5. Suites (côté parent)

1. Injecter les 7 fiches de `COMPLETION-12-TERMES.json` dans `GLOSSAIRE`.
2. Arbitrer la suppression des 5 artefacts : `bat`, `cos`, `sin`, `engine`, `sigma` — tous à 0 référence entrante, suppression sans casse.
3. Après injection, `a_rediger` doit passer de 12 à 0 (7 rédigés + 5 supprimés).
