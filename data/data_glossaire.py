# -*- coding: utf-8 -*-
"""Glossaire aéronautique PPL (plan §5.1) — dictionnaire source unique.

Chaque entrée :
    "TERME": {"definition": "…", "categorie": "…"}

Consommateurs :
- build_glossaire.py  -> sessions/glossaire.html (index alphabétique)
                        + assets/glossaire-data.js (dictionnaire pour l'overlay)
- glos_utils.wrap_glossaire -> span .glos cliquable dans les séances

Règles de rédaction : définition en 1-2 phrases, français impeccable, ton
instructeur, aucun HTML autre que <strong>/<em> (jamais de balise de bloc).
Catégories : Météo · Altimétrie · Vent · Vitesses & performances · Aérodrome &
cartes · Navigation · Réglementation & docs · Phraséologie · Aérodynamique.
"""

GLOSSAIRE = {
    # ---------------- Altimétrie ----------------
    "QNH": {
        "definition": "<em>Q-code QNH</em> — « calage altimétrique au niveau de la mer ». Pression au niveau de la mer ramenée de la station, calculée selon l'atmosphère standard. Calé au QNH, ton altimètre indique l'<strong>altitude</strong> (AMSL) ; au sol sur le terrain, il doit afficher l'altitude de l'aérodrome.",
        "categorie": "Altimétrie",
    },
    "QFE": {
        "definition": "<em>Q-code QFE</em> — « calage altimétrique au niveau du terrain ». Pression réelle régnant sur l'aérodrome. Calé au QFE, l'altimètre indique la <strong>hauteur</strong> au-dessus du terrain (0 ft au sol). Peu utilisé en France, courant au Royaume-Uni.",
        "categorie": "Altimétrie",
    },
    "QNE": {
        "definition": "<em>Q-code QNE</em> — « calage standard 1013,25 hPa ». Ce que lit l'altimètre quand il est calé au standard <strong>1013,25 hPa</strong> : l'altitude-pression. En croisière au-dessus de l'altitude de transition, on parle alors en niveaux de vol (FL).",
        "categorie": "Altimétrie",
    },
    "calage standard": {
        "definition": "Calage altimétrique à <strong>1013,25 hPa</strong> (29,92 inHg), utilisé en croisière au-dessus de l'altitude de transition. Tout le monde est sur la même référence : la séparation verticale est garantie.",
        "categorie": "Altimétrie",
    },
    "altitude-pression": {
        "definition": "Altitude lue avec un calage à 1013,25 hPa. C'est la référence commune de la croisière (niveaux de vol) et le point de départ du calcul des performances : c'est elle qu'on entre dans les abaques du manuel de vol.",
        "categorie": "Altimétrie",
        "famille": "references_verticales",
        "variantes": ["altitude pression", "altitudes-pression", "pressure altitude"],
        "xrefs": ["niveau de vol", "altitude-densité", "calage standard"],
    },
    "altitude-densité": {
        "definition": "Altitude-pression corrigée de la température : l'altitude à laquelle l'air « semble » se trouver pour ton avion. Air chaud = altitude-densité élevée = performances dégradées (distances allongées, montée médiocre).",
        "categorie": "Altimétrie",
    },
    "AAL": {
        "definition": "<em>Above Aerodrome Level</em> : au-dessus du niveau de l'aérodrome. Une hauteur, pas une altitude — « plafond à 1500 ft AAL » signifie 1500 ft au-dessus du terrain.",
        "categorie": "Altimétrie",
    },
    "AMSL": {
        "definition": "<em>Above Mean Sea Level</em> : au-dessus du niveau moyen de la mer. C'est l'<strong>altitude</strong>, celle que lit l'altimètre calé au QNH.",
        "categorie": "Altimétrie",
    },
    "niveau de vol": {
        "definition": "Altitude-pression exprimée en centaines de pieds, calage 1013,25 hPa : FL45 = 4500 ft altitude-pression. Utilisé en croisière au-dessus de l'altitude de transition.",
        "categorie": "Altimétrie",
        "famille": "references_verticales",
        "variantes": ["niveaux de vol", "FL", "flight level"],
        "synonymes": ["FL"],
        "xrefs": ["altitude-pression", "calage standard", "altitude de transition"],
    },
    "altitude de transition": {
        "definition": "Altitude au-dessus de laquelle on passe du QNH au calage standard 1013 hPa en montée. En France, généralement 3000 ft AAL sauf indication contraire sur les cartes.",
        "categorie": "Altimétrie",
    },
    # ---------------- Messages & codes météo ----------------
    "METAR": {
        "definition": "<em>METeorological Aerodrome Report</em> — « message d'observation météorologique d'aérodrome ». Émis toutes les 30 ou 60 minutes. Codé mais ultra-standardisé : vent, visibilité, phénomènes, nuages, température/point de rosée, QNH, tendance.",
        "categorie": "Météo",
    },
    "SPECI": {
        "definition": "<em>SPECIal report</em> — « message d'observation spéciale ». METAR spécial émis hors horaire quand un critère franchit un seuil (visibilité, vent, orage…). Un SPECI défavorable entre deux METAR calmes, ça se lit avant de partir.",
        "categorie": "Météo",
    },
    "TAF": {
        "definition": "<em>Terminal Aerodrome Forecast</em> — « prévision d'aérodrome ». Chiffrée sur 9 à 30 h selon la taille du terrain. Se décode comme un METAR, avec en plus les évolutions BECMG, TEMPO et les probabilités PROB.",
        "categorie": "Météo",
    },
    "CAVOK": {
        "definition": "<em>Ceiling And Visibility OK</em> : visibilité ≥ 10 km, aucun nuage sous 5000 ft (ou sous la plus haute altitude de secteur), pas de CB ni de temps significatif. Attention : CAVOK ne dit rien du vent ni de la turbulence.",
        "categorie": "Météo",
    },
    "NOSIG": {
        "definition": "<em>No significant change</em> : pas d'évolution significative attendue dans les 2 heures suivant le METAR. Ce n'est pas une promesse, juste l'absence de changement prévu par l'observateur.",
        "categorie": "Météo",
    },
    "BECMG": {
        "definition": "<em>Becoming</em> : dans un TAF, évolution durable des conditions, se produisant progressivement dans la fenêtre horaire indiquée. Après la fin de la fenêtre, la nouvelle condition est acquise.",
        "categorie": "Météo",
    },
    "TEMPO": {
        "definition": "<em>TEMPOrary</em> — « fluctuations temporaires ». Dans un TAF, variations <strong>temporaires</strong> (moins d'une heure chacune, et au total moins de la moitié de la période). C'est là que se cachent les grains du dîner de 18 h.",
        "categorie": "Météo",
    },
    "PROB30": {
        "definition": "<em>PROBability 30 %</em> — « probabilité de 30 % ». Chance que le phénomène annoncé se produise dans la fenêtre du TAF. À 30 %, tu ne planifies pas dessus mais tu gardes une porte de sortie.",
        "categorie": "Météo",
    },
    "PROB40": {
        "definition": "<em>PROBability 40 %</em> — « probabilité de 40 % ». Chance que le phénomène se produise. À partir de 40 %, considère le phénomène comme quasiment certain dans ta décision GO/NO GO.",
        "categorie": "Météo",
    },
    "AUTO": {
        "definition": "<em>AUTOmated observation</em> — « observation automatique ». Mention d'un METAR émis par une station automatique, sans intervention humaine. Fiable sur les paramètres mesurables, plus aveugle sur les nuages lointains et certains phénomènes.",
        "categorie": "Météo",
    },
    "RMK": {
        "definition": "<em>Remark</em> : commentaire en clair en fin de message (ex. <code>RMK FOEHN</code>). C'est souvent là que se cache l'information qui tue, en toutes lettres.",
        "categorie": "Météo",
    },
    "NSW": {
        "definition": "<em>Nil Significant Weather</em> : fin des phénomènes météo significatifs dans une prévision TAF (les nuages restants sont sans importance opérationnelle).",
        "categorie": "Météo",
    },
    "octas": {
        "definition": "Huitièmes de ciel couvert : FEW 1-2 octas, SCT 3-4, BKN 5-7, OVC 8/8. Le plafond, c'est la première couche BKN ou OVC. Une couverture SCT n'est donc jamais un plafond.",
        "categorie": "Météo",
    },
    "visibilité": {
        "definition": "Distance à laquelle tu distingues les repères au sol. En France, le VFR en vol contrôlé exige classiquement 5 km (moins dans certains espaces) : sous les minima, c'est NO GO, sans discussion.",
        "categorie": "Météo",
    },
    "plafond": {
        "definition": "Hauteur au-dessus du sol de la première couche nuageuse BKN ou OVC (5 octas et plus). C'est lui qui fixe ta hauteur de circuit et ta marge sous les nuages.",
        "categorie": "Météo",
    },
    "point de rosée": {
        "definition": "Température à laquelle l'air devient saturé en refroidissant. L'écart température/point de rosée te donne la base des cumulus (≈ 400 ft par degré d'écart) et annonce brume ou brouillard quand il se resserre.",
        "categorie": "Météo",
    },
    "brume": {
        "definition": "Suspension de gouttelettes donnant une visibilité entre 1 et 5 km. Souvent le matin à LFPN après une nuit claire : elle peut se lever vite… ou pas.",
        "categorie": "Météo",
    },
    "brouillard": {
        "definition": "Comme la brume mais avec une visibilité <strong>inférieure à 1 km</strong>. Un brouillard qui se forme au coucher du soleil sur ton terrain de déroutement, c'est un problème à traiter avant de décoller.",
        "categorie": "Météo",
    },
    # ---------------- Phénomènes & structures météo ----------------
    "CB": {
        "definition": "<em>CumulonimBus</em> — « cumulonimbus ». Le seul nuage cité nommément dans les METAR tant il est dangereux — turbulence extrême, givrage sévère, grêle, foudre, cisaillement. On contourne, on ne traverse jamais.",
        "categorie": "Météo",
    },
    "TCU": {
        "definition": "<em>Towering Cumulus</em> : cumulus congestus, petit frère du CB. Turbulence marquée, développement possible en CB dans l'après-midi : il mérite la même méfiance que le respect qu'on lui doit.",
        "categorie": "Météo",
    },
    "inversion": {
        "definition": "Couche où la température augmente avec l'altitude au lieu de diminuer. Couvercle stable : elle piège brume et pollution en dessous, et marque souvent le haut de la couche turbulente.",
        "categorie": "Météo",
    },
    "isobare": {
        "definition": "Ligne d'égale pression sur une carte météo. Des isobares serrées = gradient de pression fort = vent fort. C'est la première chose à regarder sur la carte du jour.",
        "categorie": "Météo",
    },
    "dépression": {
        "definition": "Zone de basse pression (centre « B » sur les cartes). Vent antihoraire et ascendant dans l'hémisphère nord : temps perturbé, plafonds bas, pluie. Un QNH qui chute de 10 hPa, ça se voit sur ton altimètre.",
        "categorie": "Météo",
    },
    "anticyclone": {
        "definition": "Zone de haute pression. Vent horaire, air descendant, temps généralement calme et stable — mais attention aux brumes matinales et à l'altitude-densité l'été.",
        "categorie": "Météo",
    },
    "front froid": {
        "definition": "Limite où l'air froid pousse l'air chaud. Passage net : grains, rafales, bascule du vent, puis amélioration franche. C'est le TEMPO du TAF qu'il faut lire avec attention.",
        "categorie": "Météo",
    },
    "front chaud": {
        "definition": "Limite où l'air chaud glisse au-dessus de l'air froid. Dégradation lente et insidieuse : plafond qui descend, pluie continue, visibilité qui pourrit sur des centaines de kilomètres.",
        "categorie": "Météo",
    },
    "occlusion": {
        "definition": "Front froid qui rattrape le front chaud : les deux systèmes fusionnent. Restes de pluie, plafonds bas, traînées — un occlus qui traîne sur l'Île-de-France peut pourrir toute une journée.",
        "categorie": "Météo",
    },
    "ISA": {
        "definition": "<em>International Standard Atmosphere</em> — « atmosphère standard internationale » : 1013,25 hPa et 15 °C au niveau de la mer, −2 °C par 1000 ft. Référence de tous les calculs d'écart — ton altimètre et tes tables de performances parlent ISA.",
        "categorie": "Météo",
    },
    # ---------------- Vent ----------------
    "rafale": {
        "definition": "Renforcement brutal et bref du vent. Dans un METAR, <code>14G24KT</code> = moyen 14 kt, rafales 24 kt : l'écart de 10 kt signe une journée turbulente et majore ta vitesse d'approche.",
        "categorie": "Vent",
        # pluriel régulier « rafales » généré auto par expand_termes()
    },
    "vent gradient": {
        "definition": "Variation du vent avec la hauteur près du sol : il faiblit et tourne en descendant vers la piste. En courte finale, la perte de composante de face fait fondre le badin — d'où la majoration pour rafales.",
        "categorie": "Vent",
    },
    "cisaillement": {
        "definition": "Changement brutal de direction ou de force du vent sur une courte distance. Signature cockpit : badin et vario qui bougent ensemble sans toucher aux commandes. Non maîtrisé = remise des gaz.",
        "categorie": "Vent",
    },
    "föhn": {
        "definition": "Vent chaud et sec dévalant le versant sous le vent d'un relief. Il annonce l'onde de montagne : rabattants violents, rotor, pression perturbée. Minima VFR respectés ne veut pas dire GO.",
        "categorie": "Vent",
    },
    "onde de relief": {
        "definition": "Ondulation de l'air en aval d'un relief par vent fort et stable, matérialisée par les lenticularis. Ascendances douces côté vent, rabattants et rotor côté sous le vent : marge verticale obligatoire.",
        "categorie": "Vent",
    },
        # ---------------- Vitesses & performances ----------------
    "IAS": {
        "definition": "<em>Indicated Air Speed</em> : la vitesse lue au badin. C'est elle qui commande la portance et les commandes — toutes les vitesses de référence (Vs, Vx, Vy…) sont en IAS. Notée <strong>KIAS</strong> quand elle est exprimée en nœuds.",
        "categorie": "Vitesses & performances",
        "variantes": ["KIAS", "kias", "vitesse indiquée"],
        "synonymes": ["vitesse indiquée", "KIAS"],
    },
    "TAS": {
        "definition": "<em>True Air Speed</em> : ta vitesse réelle dans la masse d'air. IAS corrigée de l'altitude-densité : plus tu montes, plus la TAS dépasse l'IAS (≈ +2 % par 1000 ft).",
        "categorie": "Vitesses & performances",
    },
    "GS": {
        "definition": "<em>Ground Speed</em> : vitesse sol, TAS corrigée du vent. C'est elle qui fait tes distances de décollage et d'atterrissage — et ton heure d'arrivée.",
        "categorie": "Vitesses & performances",
    },
    "Vx": {
        "definition": "Vitesse du meilleur <strong>angle</strong> de montée : le plus d'altitude gagnée par mètre parcouru au sol. C'est la vitesse du franchissement d'obstacle, tenue seulement le temps de le passer. Sur l'AT01-100A : <strong>52 KIAS</strong> (manuel de vol).",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["VX", "vx", "V X", "meilleur angle de montée"],
        "xrefs": ["Vy", "vitesses caractéristiques"],
    },
    "Vy": {
        "definition": "Vitesse du meilleur <strong>taux</strong> de montée : le plus d'altitude gagnée par minute. C'est la montée normale, une fois les obstacles dégagés. Sur l'AT01-100A : <strong>65 KIAS</strong> (manuel de vol).",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["VY", "vy", "V Y", "meilleur taux de montée"],
        "xrefs": ["Vx", "vitesses caractéristiques"],
    },
    # PURGE DES COLLISIONS DE CASSE (02/08/2026, décision Louis) —
    # les entrées `Va`, `Vfe`, `Vno`, `Vne` qui vivaient ici ont été FUSIONNÉES
    # dans les fiches canoniques en majuscules du bloc F5 (VA, VFE, VNO, VNE),
    # où elles figurent désormais comme `variantes`. Motif : deux clés qui ne
    # diffèrent que par la casse normalisent vers la même forme et s'écrasent
    # silencieusement (même classe de bug que le doublon `composante de
    # travers`). Le matching de glos_utils est déjà insensible à la casse pour
    # les surfaces déclarées : une seule fiche suffit.
    # `Vs` (ambigu : VS0 ou VS1 ?) est devenu la fiche « vitesse de décrochage »
    # ci-dessous, qui présente les deux avec le tableau de famille.
    "vitesse de décrochage": {
        "definition": "Vitesse minimale à laquelle l'aile porte encore, dans une configuration donnée : en dessous, l'incidence nécessaire dépasse l'incidence critique et la portance s'effondre. Elle n'est pas unique — on en distingue deux au manuel : <strong>VS0</strong> volets sortis (configuration d'atterrissage) et <strong>VS1</strong> volets rentrés (configuration lisse). Elle <strong>augmente avec la masse et avec le facteur de charge</strong> : en virage serré, elle grimpe.",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["Vs", "VS", "vs", "V S", "vitesses de décrochage", "vitesse de decrochage"],
        "synonymes": ["Vs"],
        "xrefs": ["VS0", "VS1", "décrochage", "facteur de charge", "vitesses caractéristiques"],
    },
    "Vref": {
        "definition": "Vitesse de référence à l'atterrissage, avant majorations. Typiquement 1,3 × Vs0 ; on y ajoute la majoration pour rafales selon la consigne de l'école.",
        "categorie": "Vitesses & performances",
    },
    "finesse": {
        "definition": "Rapport distance parcourue / hauteur perdue moteur coupé. Une finesse de 12, c'est 12 km planés par 1000 m perdu : c'est elle qui décide si ton point d'aboutissement est atteignable.",
        "categorie": "Vitesses & performances",
    },
    "facteur de charge": {
        "definition": "Rapport portance / poids : 1 en vol rectiligne stabilisé, 2 en virage à 60°. La vitesse de décrochage augmente avec sa racine carrée — à 60° d'inclinaison, Vs monte de 41 %.",
        "categorie": "Aérodynamique",
    },
    "décrochage": {
        "definition": "Perte brutale de portance quand l'angle d'attaque dépasse l'incidence critique — indépendant de la vitesse proprement dite : on décroche à n'importe quelle vitesse si on tire trop.",
        "categorie": "Aérodynamique",
    },
    # ---------------- Aérodrome & cartes ----------------
    "QFU": {
        "definition": "<em>Q-code QFU</em> — « direction magnétique de la piste en service ». Orientation magnétique de l'axe de piste, exprimée en dizaines de degrés : piste 25 = axe 250° magnétique. C'est la référence de tous tes calculs de composantes de vent.",
        "categorie": "Aérodrome & cartes",
    },
    "VAC": {
        "definition": "<em>Visual Approach Chart</em> : carte d'approche à vue officielle d'un aérodrome (SIA en France). Pistes, circuits, points de report, fréquences, dangers : elle se relit avant chaque vol, même sur ton terrain.",
        "categorie": "Aérodrome & cartes",
    },
    "ATIS": {
        "definition": "<em>Automatic Terminal Information Service</em> — « service automatique d'information de région terminale ». Message automatique et permanent d'information d'aérodrome : QNH, QFU en service, vent, état de piste. On l'écoute et on le note <strong>avant</strong> le premier contact radio, lettre d'information comprise.",
        "categorie": "Aérodrome & cartes",
    },
    "CTR": {
        "definition": "<em>Control Traffic Region</em> : zone de contrôle autour d'un aérodrome. À LFPN, tu y vis en permanence : pénétrer dedans suppose le contact radio et l'autorisation.",
        "categorie": "Aérodrome & cartes",
    },
    "TMA": {
        "definition": "<em>Terminal Control Area</em> : espace contrôlé au-dessus d'une zone d'aérodromes. Celle de Paris plafonne bas autour de LFPN : une verticale mal gérée, et tu chatouilles les couloirs d'Orly.",
        "categorie": "Aérodrome & cartes",
    },
    # ---------------- Navigation ----------------
    # PURGE DES RECOUVREMENTS (02/08/2026) — `déclinaison` était une clé ici ET
    # une variante de `déclinaison magnétique` (bloc F3) : la variante était
    # morte. Les deux notions n'en font qu'une → une seule fiche,
    # « déclinaison magnétique », qui porte `déclinaison` en variante.
    # Idem `cap vrai` / `cap magnétique` : ce sont des notions DISTINCTES de
    # `nord vrai` / `nord magnétique` (un cap est une direction suivie, un nord
    # est une référence). Elles gardent donc leur fiche, et ont été retirées
    # des `variantes` de nord vrai / nord magnétique où elles étaient mortes.
    "cap vrai": {
        "definition": "Cap mesuré par rapport au <strong>nord vrai</strong> (géographique), celui des méridiens de la carte. C'est la direction que l'on trace sur la carte ; on la convertit en cap magnétique par la déclinaison magnétique avant de voler au compas.",
        "categorie": "Navigation",
        "variantes": ["caps vrais", "route vraie", "Cv", "cap géographique"],
        "xrefs": ["cap magnétique", "nord vrai", "déclinaison magnétique"],
    },
    "cap magnétique": {
        "definition": "Cap mesuré par rapport au <strong>nord magnétique</strong>, celui vers lequel pointe le compas. C'est le cap que tu annonces, que tu tiens et qui se compare au QFU. Cap vrai converti par la déclinaison magnétique ; le compas lui-même se corrige encore de la déviation propre à l'avion.",
        "categorie": "Navigation",
        "variantes": ["caps magnétiques", "route magnétique", "Cm"],
        "xrefs": ["cap vrai", "nord magnétique", "déclinaison magnétique", "QFU"],
    },
    "dérive": {
        "definition": "Angle entre l'axe de l'avion et sa trajectoire au sol, créé par le vent de travers. On la compense en mettant le nez au vent : « cap = route + correction de dérive ».",
        "categorie": "Navigation",
    },
    # ---------------- Réglementation & docs ----------------
    "NOTAM": {
        "definition": "<em>Notice to Airmen</em> : avis officiel aux navigateurs — travaux, activations de zones, glissance, feux d'artifice. La lecture des NOTAM fait partie de la préparation, même pour un tour de piste.",
        "categorie": "Réglementation & docs",
    },
    "AIP": {
        "definition": "<em>Aeronautical Information Publication</em> : la documentation aéronautique officielle d'un pays, publiée par cycles AIRAC de 28 jours. Les VAC en sont l'extrait le plus utilisé par le pilote VFR.",
        "categorie": "Réglementation & docs",
    },
    "AIRAC": {
        "definition": "<em>Aeronautical Information Regulation And Control</em> — « régulation et contrôle de l'information aéronautique ». Cycle de 28 jours au rythme duquel les données aéronautiques officielles sont mises à jour. Une carte « à jour » = un cycle AIRAC en vigueur : vérifie la date d'effet, pas celle du téléchargement.",
        "categorie": "Réglementation & docs",
    },
    "VFR": {
        "definition": "<em>Visual Flight Rules</em> : vol à vue — tu vois, tu évites, tu te repères. Il suppose des conditions VMC respectées et la vue du sol (ou des références) en permanence.",
        "categorie": "Réglementation & docs",
    },
    "VMC": {
        "definition": "<em>Visual Meteorological Conditions</em> : minima de visibilité et de distances aux nuages exigés pour voler VFR, selon la classe d'espace et l'altitude. En dessous, c'est de l'IMC — interdit sans qualif IFR.",
        "categorie": "Réglementation & docs",
    },
    "IFR": {
        "definition": "<em>Instrument Flight Rules</em> : vol aux instruments, qui décharge l'évitement visuel sur la procédure et le contrôle. Exige qualification, avion équipé et plan de vol.",
        "categorie": "Réglementation & docs",
    },
    "IMC": {
        "definition": "<em>Instrument Meteorological Conditions</em> : conditions dans les nuages ou sous les minima VMC. Sans qualification IFR, y entrer est la première cause d'accident mortel du pilote privé.",
        "categorie": "Réglementation & docs",
    },
    "POH": {
        "definition": "<em>Pilot's Operating Handbook</em> : le manuel de vol de l'avion, document officiel de l'<strong>exemplaire immatriculé</strong>. Vitesses, masses, distances : seules ses valeurs font foi pour ton vol.",
        "categorie": "Réglementation & docs",
    },
    "GO/NO GO": {
        "definition": "<em>GO / NO GO decision</em> — « décision de partir ou de renoncer ». Décision binaire et assumée, fondée sur des critères écrits (minima, performances, état de fatigue) — jamais sur l'envie ou le rendez-vous. « NO GO » est une décision de commandant, pas un échec.",
        "categorie": "Réglementation & docs",
    },
    # ---------------- Unités (plan §9quater.4) ----------------
    # Une seule fiche par grandeur : toutes les graphies (kt/KT/nœuds…) pointent
    # ici via `variantes`. Les valeurs chiffrées (« 14 kt ») rendent l'UNITÉ
    # cliquable, pas le nombre (frontières de mot dans glos_utils).
    "kt": {
        "definition": "<em>Knot</em> — nœud : 1 mille marin par heure (1 kt = 1 NM/h ≈ 1,852 km/h ≈ 0,514 m/s). Unité unique du vent aéronautique, des tables de performance et de l'ATIS. Convertir un METAR « 15 kt » en « 15 km/h » sous-estime le vent d'un facteur ~2 — dangereux.",
        "categorie": "Unités",
        "variantes": ["KT", "kts", "KTS", "nœud", "nœuds", "noeud", "noeuds"],
        "synonymes": ["nœud", "knot"],
    },
    "hPa": {
        "definition": "Hectopascal : unité de pression atmosphérique du QNH/QFE (1 hPa = 1 mbar). Le calage standard vaut <strong>1013,25 hPa</strong>. Ne pas confondre avec inHg (pouces de mercure, usage US).",
        "categorie": "Unités",
        "variantes": ["HPA", "hectopascal", "hectopascals", "mbar"],
        "synonymes": ["hectopascal", "millibar"],
    },
    "ft": {
        "definition": "<em>Foot / feet</em> — pied : unité d'altitude et de hauteur en aviation (1 ft = 0,3048 m). Les plafonds METAR, les niveaux de vol et l'altimètre parlent en pieds, pas en mètres.",
        "categorie": "Unités",
        "variantes": ["FT", "pied", "pieds", "feet", "foot"],
        "synonymes": ["pied"],
    },
    "NM": {
        "definition": "<em>Nautical Mile</em> — mille marin : 1852 m exactement. Unité de distance horizontale en navigation aérienne et maritime. 1 kt = 1 NM/h.",
        "categorie": "Unités",
        "variantes": ["nm", "mille marin", "milles marins", "nautical mile", "nautical miles"],
        "synonymes": ["mille marin"],
    },
    "°C": {
        "definition": "Degré Celsius : unité de température du METAR (T/Td) et des tables de performances. En ISA, 15 °C au niveau de la mer, −2 °C par 1000 ft.",
        "categorie": "Unités",
        "variantes": ["° C", "deg C", "degrés Celsius", "degré Celsius"],
    },
    "°": {
        "definition": "Degré d'angle : direction du vent, cap, QFU, θ (angle vent–piste). Un QFU s'écrit en dizaines de degrés (25 = 250°) ; un vent METAR est en degrés vrais sur 360.",
        "categorie": "Unités",
        "variantes": ["degré", "degrés", "deg"],
        "synonymes": ["degré"],
    },
    # ---------------- F1 · Vocabulaire de terrain (plan §9quater.1) ----------------
    # `contexte_requis` : le mot n'est lié QUE s'il a son sens aéronautique.
    "TORA": {
        "schema": "distances_piste",
        "definition": "<em>Take-Off Run Available</em> — « distance de roulement au décollage ». Longueur de piste rev\u00eatue disponible pour le roulement au d\u00e9collage, du d\u00e9but de la piste jusqu'\u00e0 son extr\u00e9mit\u00e9. C'est la distance sur laquelle l'avion peut acc\u00e9l\u00e9rer roues au sol. On la compare \u00e0 la distance de roulement donn\u00e9e par le manuel de vol, corrig\u00e9e de la temp\u00e9rature, de l'altitude, de la pente et de l'\u00e9tat de surface.",
        "categorie": "A\u00e9rodrome & cartes",
        "famille": "distances_piste",
        "casse_sensible": True,
        "xrefs": ["TODA", "ASDA", "LDA", "piste"],
    },
    "TODA": {
        "schema": "distances_piste",
        "definition": "<em>Take-Off Distance Available</em> \u2014 \u00ab distance de d\u00e9collage utilisable \u00bb. Distance disponible pour le d\u00e9collage : la <strong>TORA</strong> augment\u00e9e du prolongement d\u00e9gag\u00e9 quand le terrain en publie un. Le prolongement d\u00e9gag\u00e9 est un espace libre d'obstacles au-del\u00e0 de la piste, que l'avion peut survoler en mont\u00e9e initiale mais o\u00f9 il ne roule pas. C'est la distance qui compte pour franchir un obstacle en bout de piste.",
        "categorie": "A\u00e9rodrome & cartes",
        "famille": "distances_piste",
        "casse_sensible": True,
        "xrefs": ["TORA", "ASDA", "LDA", "piste"],
    },
    "ASDA": {
        "schema": "distances_piste",
        "definition": "<em>Accelerate-Stop Distance Available</em> — « distance accélération-arrêt utilisable ». Distance disponible pour acc\u00e9l\u00e9rer puis s'arr\u00eater : la <strong>TORA</strong> augment\u00e9e du prolongement d'arr\u00eat quand il existe. Le prolongement d'arr\u00eat est une surface am\u00e9nag\u00e9e capable de supporter l'avion en cas de d\u00e9collage interrompu, sans \u00eatre utilisable pour le d\u00e9collage normal. C'est la distance de r\u00e9f\u00e9rence si tu interromps ton d\u00e9collage.",
        "categorie": "A\u00e9rodrome & cartes",
        "famille": "distances_piste",
        "casse_sensible": True,
        "xrefs": ["TORA", "TODA", "LDA", "piste"],
    },
    "LDA": {
        "schema": "distances_piste",
        "definition": "<em>Landing Distance Available</em> — « distance d'atterrissage utilisable ». Longueur de piste disponible pour l'atterrissage, mesur\u00e9e depuis le <strong>seuil</strong> jusqu'\u00e0 l'extr\u00e9mit\u00e9 de la piste. Quand le seuil est d\u00e9cal\u00e9, la LDA est plus courte que la TORA : la partie situ\u00e9e avant le seuil reste utilisable au d\u00e9collage mais pas \u00e0 l'atterrissage. On la compare \u00e0 sa distance d'atterrissage, marge de s\u00e9curit\u00e9 comprise.",
        "categorie": "A\u00e9rodrome & cartes",
        "famille": "distances_piste",
        "casse_sensible": True,
        "xrefs": ["TORA", "TODA", "ASDA", "seuil de piste", "piste"],
    },
    "piste": {
        "famille": "distances_piste",
        "definition": "Bande de terrain ou de revêtement aménagée pour le décollage et l'atterrissage des avions. Elle porte un numéro — son <strong>QFU</strong> arrondi à la dizaine de degrés, lu dans le sens où on l'utilise : une même bande de béton s'appelle donc 07 dans un sens et 25 dans l'autre (les deux numéros diffèrent toujours de 18). On choisit son sens d'utilisation face au vent, ce qui réduit la vitesse sol au décollage comme à l'atterrissage.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["pistes"],
        "xrefs": ["QFU", "seuil de piste", "tour de piste", "vent de face", "composante de travers"],
    },
    "seuil de piste": {
        "famille": "distances_piste",
        "schema": "piste_seuils_qfu",
        "definition": "Début de la partie de piste utilisable à l'atterrissage, matérialisé par des bandes blanches parallèles (« zébras »). Le numéro peint juste après le seuil donne le <strong>QFU</strong> arrondi à la dizaine de degrés : un seuil marqué 25 s'utilise au cap 250°.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["seuil", "seuils", "seuils de piste"],
        "synonymes": ["seuil"],
        "contexte_requis": ["piste", "QFU", "atterriss", "seuil décalé", "zébra"],
    },
    "manche à air": {
        "schema": "manche_a_air",
        "definition": "Cône en tissu au bord de piste : il donne le vent <strong>réel au sol, à l'endroit où tu vas te poser</strong>. Gonflée à l'horizontale ≈ 15 kt ou plus ; molle et pendante ≈ 5 kt. Elle prime sur un METAR vieux de 20 minutes.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["manches à air", "biroute"],
        "synonymes": ["biroute"],
    },
    "girouette": {
        "definition": "Dispositif qui s'oriente face au vent et en indique la provenance. En aéronautique, tout se dit en « vent venant de » : une girouette pointant vers 270° annonce un vent d'ouest. Un avion au sol, non freiné, tend à se comporter en girouette et à s'aligner face au vent.",
        "categorie": "Vent",
        "variantes": ["girouettes", "effet girouette"],
    },
    "roulage": {
        "definition": "Déplacement de l'avion au sol par ses propres moyens, entre le parking et la piste. Par vent fort, on braque le manche pour empêcher le vent de soulever une aile — c'est là que beaucoup d'incidents au sol se produisent.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["rouler", "taxi", "taxiway"],
        "synonymes": ["taxi"],
    },
    "bande": {
        "definition": "Surface dégagée qui entoure la piste, destinée à limiter les dégâts en cas de sortie. Elle n'est pas une piste : s'y poser ou y rouler n'est pas prévu.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["bande de piste", "bandes"],
        "contexte_requis": ["piste", "aérodrome", "terrain", "dégagée"],
    },
    # ---------------- F2 · Composantes du vent ----------------
    "composante de face": {
        "definition": "Part du vent qui souffle dans l'axe de la piste, face à toi. Référence exacte : <strong>V × cos θ</strong>, où θ est l'écart entre le QFU et la direction du vent. Elle raccourcit le décollage et l'atterrissage — c'est la composante qui t'aide. En briefing, on se concentre d'abord sur le <strong>travers</strong> (règle des tiers).",
        "categorie": "Vent",
        "famille": "composantes_vent",
        # « vent de face » devient une fiche autonome (02/08/2026) : c'est le
        # mot que l'élève cherche, « composante » est le mot du calcul.
        "variantes": ["composantes de face", "vent debout"],
        "synonymes": ["vent debout"],
        "xrefs": ["composante de travers", "composante arrière", "vent de face", "θ"],
    },
    "composante de travers": {
        "schema": "composantes_face_travers",
        "definition": "Part du vent perpendiculaire à la piste. <strong>Méthode PPL enseignée</strong> : règle des tiers par secteurs — 0–30° ≈ 1/3 du vent, 30–60° ≈ 2/3, 60–90° ≈ totalité. Référence exacte (abaque / devoir posé) : <strong>V × sin θ</strong>. C'est elle qu'on compare à la limite de l'avion (15 kt de travers démontré sur l'Aquila AT01). Se calcule sur la <strong>rafale</strong> et sur l'extrême du secteur variable, jamais sur la seule moyenne.",
        "categorie": "Vent",
        "famille": "composantes_vent",
        # « vent traversier » SORT d'ici (02/08/2026) : dans le tour de piste
        # c'est le nom de la BRANCHE qui suit le décollage, pas la composante.
        # « vent de travers » reste : là, c'est bien le synonyme courant.
        "variantes": ["vent de travers", "composantes de travers", "crosswind"],
        "synonymes": ["vent de travers", "crosswind"],
        "xrefs": ["composante de face", "décrabage", "vent traversier", "θ"],
    },
    "composante arrière": {
        "definition": "Vent qui te pousse par l'arrière : il allonge fortement le décollage et l'atterrissage. Souvent limité à 5 ou 10 kt selon l'avion — au-delà, on change de piste. Une composante de face négative est une composante arrière.",
        "categorie": "Vent",
        "famille": "composantes_vent",
        # ⚠️ « vent arrière » N'EST PLUS une variante ici (02/08/2026).
        # C'est désormais une fiche à part entière — la BRANCHE du tour de
        # piste — qui récupère la surface par défaut et AIGUILLE vers cette
        # fiche-ci (champ `homonyme`) dès que le contexte parle de calcul de
        # composante. Tant que « vent arrière » était capté ici, la branche
        # était strictement inatteignable : la clé « vent arrière (branche) »
        # ne pouvait pas matcher un texte où personne n'écrit la parenthèse.
        "variantes": ["composantes arrière", "tailwind"],
        "synonymes": ["tailwind"],
        "xrefs": ["composante de face", "vent arrière"],
    },
    "décrabage": {
        "schema": "decrabage",
        "definition": "Manœuvre finale par vent de travers : on approche « en crabe », nez décalé face au vent pour tenir l'axe, puis juste avant le toucher on aligne le nez sur l'axe de piste au palonnier en contrant la dérive à l'aileron. Objectif : toucher <strong>roues alignées</strong> avec l'axe, sinon on impose un effort latéral au train.",
        "categorie": "Vent",
        "variantes": ["décraber", "décrabé", "crabe" ],
        "xrefs": ["composante de travers"],
    },
    "θ": {
        "definition": "Écart angulaire entre l'axe de piste (QFU) et la direction d'où vient le vent. C'est l'angle qui commande tout. En briefing PPL on place θ dans un secteur (0–30 / 30–60 / 60–90) pour le travers mental ; la référence exacte reste face = V × cos θ, travers = V × sin θ. À θ = 0° tout est de face ; à 90°, tout est de travers.",
        "categorie": "Vent",
        "famille": "composantes_vent",
        "variantes": ["theta", "angle vent-piste", "écart angulaire"],
        "synonymes": ["angle vent–piste"],
        "xrefs": ["composante de face", "composante de travers"],
    },
    "secteur variable": {
        "definition": "Vent dont la direction oscille, noté <strong>240V300</strong> dans un METAR (varie de 240° à 300°). Piège classique : on calcule le travers sur la direction moyenne et on oublie que l'<strong>extrême du secteur</strong>, combiné à la rafale, peut faire exploser la composante de travers.",
        "categorie": "Vent",
        "variantes": ["secteurs variables", "vent variable", "variable"],
        "contexte_requis": ["vent", "METAR", "V", "direction", "kt", "secteur"],
        "xrefs": ["composante de travers", "rafale"],
    },
    # ---------------- F3 · Vrai / magnétique / compas ----------------
    "nord vrai": {
        "definition": "Direction du pôle Nord géographique, référence des méridiens de la carte. Le vent des <strong>messages METAR/TAF est donné en degrés vrais</strong> — contrairement au vent annoncé par la tour, qui est magnétique.",
        "categorie": "Navigation",
        # `cap vrai` et `route vraie` retirés : ce sont des directions suivies,
        # pas la référence nord. Ils appartiennent à la fiche `cap vrai`
        # (variantes mortes ici avant la purge du 02/08/2026).
        "variantes": ["Nord vrai", "nord géographique", "nord Vrai", "pole nord géographique"],
        "synonymes": ["nord géographique"],
        "xrefs": ["nord magnétique", "déclinaison magnétique", "cap vrai"],
    },
    "nord magnétique": {
        "definition": "Direction indiquée par l'aiguille du compas, vers le pôle magnétique — qui ne coïncide pas avec le pôle géographique et se déplace. Les <strong>QFU et les caps sont magnétiques</strong> ; le vent METAR est vrai. Mélanger les deux fausse le calcul de travers.",
        "categorie": "Navigation",
        # `cap magnétique` / `route magnétique` retirés : ils appartiennent à la
        # fiche `cap magnétique` (variantes mortes ici avant la purge).
        "variantes": ["Nord magnétique", "nord Magnétique", "pole nord magnétique"],
        "xrefs": ["nord vrai", "déclinaison magnétique", "QFU", "cap magnétique"],
    },
    "déclinaison magnétique": {
        "schema": "azimut_vrai_magnetique",
        "definition": "Écart angulaire entre le nord vrai et le nord magnétique en un lieu donné, positif vers l'est. En France métropolitaine elle est faible (de l'ordre de quelques degrés) et évolue lentement : la valeur exacte se lit sur la <strong>carte ou la VAC en vigueur</strong>, jamais de mémoire. C'est elle qui fait passer d'un cap vrai à un cap magnétique — et donc du vent METAR (vrai) au QFU (magnétique).",
        "categorie": "Navigation",
        "variantes": ["déclinaison", "déclinaisons", "declinaison", "variation magnétique", "déclinaisons magnétiques"],
        "synonymes": ["déclinaison", "variation magnétique"],
        "xrefs": ["nord vrai", "nord magnétique", "cap vrai", "cap magnétique"],
    },
    "rose des vents": {
        "schema": "rose_des_vents",
        "definition": "Cercle gradué de 0 à 360° servant à lire une direction. En aéronautique, 360 = nord, 090 = est, 180 = sud, 270 = ouest, et une direction de vent se lit toujours comme la provenance.",
        "categorie": "Navigation",
        "variantes": ["roses des vents"],
    },
    "azimut": {
        "definition": "Direction horizontale mesurée en degrés depuis le nord, dans le sens des aiguilles d'une montre. Un azimut de 270° pointe vers l'ouest. C'est la grandeur commune au cap, à la route, au QFU et à la direction du vent.",
        "categorie": "Navigation",
        "variantes": ["azimuts", "azimutal"],
    },
    # ---------------- F4 · Tour de piste et ses branches ----------------
    "tour de piste": {
        "schema": "tour_de_piste",
        "definition": "Circuit rectangulaire volé autour de la piste pour s'y présenter à l'atterrissage ou enchaîner des touchés. Il enchaîne cinq branches : décollage, vent traversier, vent arrière, base, finale. Son sens (à gauche ou à droite) et sa hauteur sont fixés par la <strong>carte VAC</strong> du terrain.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["tours de piste", "circuit d'aérodrome", "circuit de piste"],
        "synonymes": ["circuit d'aérodrome"],
        "contexte_requis": ["piste", "aérodrome", "finale", "vent arrière", "circuit", "QFU", "intégration"],
        "xrefs": ["vent arrière", "étape de base", "finale", "remise des gaz"],
    },
    # ⚠️ HOMONYME RÉSOLU (02/08/2026). L'ancienne clé « vent arrière (branche) »
    # est SUPPRIMÉE : la parenthèse n'est jamais écrite dans un texte, la fiche
    # ne matchait donc rien et 100 % des occurrences partaient sur la
    # composante. La branche récupère maintenant la surface « vent arrière »
    # par défaut, et le champ `homonyme` renvoie sur « composante arrière »
    # quand le contexte parle de calcul de vent (composante, θ, kt, distance…).
    "vent arrière": {
        "schema": "tour_de_piste",
        "famille": "tour_de_piste",
        "definition": "Branche du tour de piste parallèle à la piste, parcourue en sens inverse du sens d'atterrissage. C'est la branche où l'on prépare l'atterrissage : actions avant atterrissage, annonce radio de position, réglage de la trajectoire par rapport à la piste, et repérage du point où l'on amorcera la descente vers la base. On y surveille l'espacement avec la piste et le trafic déjà en circuit. <strong>Attention</strong> : la même expression désigne aussi la <em>composante</em> de vent qui pousse l'avion par l'arrière — c'est un tout autre sujet, celui du calcul de piste.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["branche vent arrière", "vent-arrière", "downwind" ],
        "synonymes": ["downwind"],
        # Aiguillage : par défaut = la branche. Si l'un de ces motifs entoure
        # l'occurrence, on bascule sur la fiche « composante arrière ».
        # Motifs choisis d'après le corpus réel (séance 003 : les 16
        # occurrences y parlent TOUTES de la composante — calcul de piste).
        # Vocabulaire relevé dans le corpus réel (séance 003) : dès qu'on parle
        # de CHIFFRES, de DISTANCES, de VITESSES ou d'ACCEPTER/REFUSER une
        # piste, « vent arrière » désigne la composante, pas la branche. La
        # branche, elle, vit dans un contexte de TRAJECTOIRE (étape de base,
        # intégration, annonce radio, main gauche/droite).
        "homonyme": {
            "cible": "composante arrière",
            "contexte": [
                "composante", "composantes", "cos", "sin", "θ", "theta",
                "vent arrière de", "kt de vent arrière", "nœuds de vent arrière",
                "noeuds de vent arrière", "avec vent arrière", "vent arrière au",
                "longitudinal", "contre-qfu", "allongement", "distance de roulement",
                "atterrissage plus long", "décollage plus long", "no go",
                "allonge", "allongent", "raccourc", "kt allonge",
                "arrière de", "arrière de 10", "distances",
            ],
        },
        "xrefs": ["tour de piste", "étape de base", "composante arrière"],
    },
    "étape de base": {
        "schema": "tour_de_piste",
        "famille": "tour_de_piste",
        "definition": "Branche du tour de piste perpendiculaire à l'axe de piste, volée entre le vent arrière et la finale. C'est la branche de transition : on y ajuste le plan de descente, on sort la configuration prévue, et on vérifie que la finale est libre avant de s'y engager. Une base trop serrée oblige à un dernier virage appuyé ; une base trop large étire la finale.",
        "categorie": "Aérodrome & cartes",
        # « base » reste une VARIANTE de cette fiche (pas de clé « base »
        # séparée : ce serait un doublon, exactement le bug déjà payé avec
        # « composante de travers »).
        "variantes": ["base", "branche de base", "étapes de base", "étape base" ],
        "synonymes": ["base", "branche de base"],
        "contexte_requis": ["tour de piste", "finale", "vent arrière", "circuit", "piste"],
        "xrefs": ["tour de piste", "finale", "dernier virage", "vent arrière"],
    },
    "finale": {
        "definition": "Dernière branche du tour de piste, alignée sur l'axe de piste jusqu'au toucher. C'est là que se joue l'atterrissage : on tient l'axe et le plan, on stabilise la vitesse d'approche, on gère le vent de travers (approche en crabe puis décrabage), et on décide sans hésiter d'une éventuelle remise des gaz si l'approche n'est pas stabilisée.",
        "categorie": "Aérodrome & cartes",
        # « courte finale » et « longue finale » sont désormais des FICHES
        # autonomes (elles désignent des moments distincts, avec des actions
        # distinctes) : elles ne sont plus listées ici. Le linker les préfère
        # de toute façon à « finale » seule (tri par nombre de mots).
        "variantes": ["final"],
        "contexte_requis": ["piste", "atterriss", "axe", "tour de piste", "approche", "QFU", "remise des gaz"],
        "xrefs": ["tour de piste", "décrabage", "remise des gaz", "courte finale", "longue finale", "arrondi"],
    },
    "courte finale": {
        "famille": "tour_de_piste",
        "definition": "Toute dernière partie de la finale, juste avant le seuil de piste. C'est le moment où plus rien ne se corrige en profondeur : la trajectoire, la vitesse et la configuration doivent déjà être bonnes. On y surveille l'axe, le plan et la vitesse, on garde la main sur les gaz, et c'est le dernier instant confortable pour décider une remise des gaz. Le gradient de vent et les turbulences dues au relief ou aux bâtiments se font sentir surtout ici.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["courtes finales", "short final"],
        "synonymes": ["short final"],
        "xrefs": ["finale", "arrondi", "remise des gaz", "seuil de piste", "approche stabilisée"],
    },
    "longue finale": {
        "schema": "tour_de_piste",
        "famille": "tour_de_piste",
        "definition": "Partie initiale de la finale, loin du seuil, juste après l'alignement sur l'axe de piste. On y installe l'approche : axe, plan de descente et vitesse sont mis en place pendant qu'il reste de la distance pour corriger tranquillement. C'est aussi la position qu'on annonce à la radio en arrivant de l'extérieur du circuit, pour se faire connaître des avions déjà en tour de piste.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["longues finales", "long final"],
        "synonymes": ["long final"],
        "xrefs": ["finale", "courte finale", "intégration", "alignement"],
    },
    "dernier virage": {
        "famille": "tour_de_piste",
        "definition": "Virage qui fait passer de la base à la finale, alignant l'avion sur l'axe de piste. Il se fait relativement bas et à vitesse réduite, ce qui en fait un virage à surveiller : la tentation de resserrer l'inclinaison pour « rattraper » un axe manqué se combine mal avec une vitesse déjà faible. La réponse propre à un axe manqué n'est pas d'appuyer le virage, mais de reprendre de la marge — quitte à remettre les gaz.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["derniers virages", "virage de base en finale", "dernier virage base-finale"],
        "xrefs": ["étape de base", "finale", "décrochage", "remise des gaz"],
    },
    "vent traversier": {
        "schema": "tour_de_piste",
        "famille": "tour_de_piste",
        "definition": "Branche du tour de piste volée perpendiculairement à l'axe de piste, juste après le décollage et la montée initiale, pour rejoindre le vent arrière. C'est une branche courte : on y termine la montée vers la hauteur du tour de piste et on surveille le trafic avant de s'insérer en vent arrière. <strong>À ne pas confondre</strong> avec le <em>vent de travers</em>, qui désigne la composante de vent perpendiculaire à la piste — un sujet de calcul, pas une branche.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["branche vent traversier", "crosswind leg", "traversier"],
        "synonymes": ["crosswind leg"],
        "xrefs": ["tour de piste", "montée initiale", "vent arrière", "composante de travers"],
    },
    "montée initiale": {
        "schema": "tour_de_piste",
        "famille": "tour_de_piste",
        "definition": "Phase de montée dans l'axe de piste qui suit immédiatement le décollage, avant tout virage. On y tient l'axe, la vitesse de montée retenue et la trajectoire, sans se précipiter pour tourner. C'est une phase à faible hauteur et forte puissance : la priorité est de piloter la vitesse et de garder un terrain d'atterrissage en tête en cas de panne, pas de gérer la radio.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["montées initiales", "montée initiale dans l'axe", "initial climb"],
        "synonymes": ["initial climb"],
        "xrefs": ["décollage", "vent traversier", "tour de piste", "Vy"],
    },
    "décollage": {
        "definition": "Phase qui mène l'avion de l'arrêt sur la piste à l'envol, en accélérant jusqu'à la vitesse de rotation puis en quittant le sol. Elle enchaîne trois choses : l'accélération au roulement, la rotation, puis le passage en montée. Le vent, l'état de la piste, la masse et l'altitude-densité en modifient directement la distance nécessaire — c'est pour ça qu'on la calcule avant de partir plutôt que de la découvrir en fin de piste.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["décollages", "décoller" ],
        "xrefs": ["roulement", "montée initiale", "altitude-densité", "composante de face", "tour de piste"],
    },
    "roulement": {
        "definition": "Partie d'un décollage ou d'un atterrissage où l'avion roule sur la piste, roues au sol, en accélération ou en décélération. Au décollage il dure jusqu'à l'envol, à l'atterrissage du toucher jusqu'à l'arrêt ou la sortie de piste. C'est la portion qui consomme de la longueur de piste : un vent qui pousse par l'arrière ou une piste mouillée l'allongent nettement. À ne pas confondre avec le <strong>roulage</strong>, qui est le déplacement au sol entre le parking et la piste.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["roulements", "roulement au décollage", "roulement à l'atterrissage"],
        "contexte_requis": ["piste", "décollage", "atterriss", "distance", "sol", "frein", "vitesse"],
        "xrefs": ["décollage", "roulage", "composante arrière", "arrondi"],
    },
    "alignement": {
        "definition": "Action de placer l'avion sur l'axe de la piste, dans le sens du décollage, avant de mettre la puissance. C'est le dernier moment où l'on vérifie que la piste et l'approche sont libres, que la piste est la bonne, et que les instruments sont cohérents avec le cap attendu. Le terme désigne aussi, en vol, le fait de se mettre dans l'axe de piste en finale.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["alignements", "s'aligner", "aligné", "alignement piste"],
        "contexte_requis": ["piste", "axe", "QFU", "décollage", "finale", "seuil", "cap"],
        "xrefs": ["QFU", "décollage", "finale", "seuil de piste"],
    },
    "arrondi": {
        "schema": "tour_de_piste",
        "famille": "tour_de_piste",
        "definition": "Manœuvre qui met fin à la descente juste avant le toucher : on réduit progressivement le taux de descente en cabrant doucement, pour poser l'avion en douceur sur le train principal plutôt que de l'enfoncer dans la piste. Trop haut, l'avion retombe ; trop tard, il touche encore en descente. Elle se fait au regard porté loin devant, pas sur les instruments, et s'accompagne de la réduction des gaz.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["arrondis", "arrondir", "flare"],
        "synonymes": ["flare"],
        "xrefs": ["courte finale", "roulement", "décrabage", "remise des gaz"],
    },
    "intégration": {
        "definition": "Manière de rejoindre le tour de piste d'un terrain en arrivant de l'extérieur, sans gêner ni surprendre les avions déjà en circuit. Elle suit un cheminement publié : la <strong>carte VAC</strong> du terrain indique les points d'entrée, le sens du tour de piste et la hauteur à respecter. L'objectif est d'être vu, entendu et prévisible — on annonce sa position et ses intentions à la radio avant d'entrer dans le circuit.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["intégrations", "s'intégrer", "intégration au tour de piste", "intégration verticale"],
        "contexte_requis": ["tour de piste", "circuit", "terrain", "aérodrome", "piste", "VAC", "verticale", "radio"],
        "xrefs": ["tour de piste", "verticale terrain", "VAC", "vent arrière"],
    },
    "verticale terrain": {
        "definition": "Passage à l'aplomb de l'aérodrome, au-dessus de la hauteur du tour de piste, pour observer le terrain avant de s'y intégrer. On y lit la manche à air, on identifie la piste en service et son sens de tour de piste, et on repère les avions déjà en circuit. C'est le mode d'arrivée classique quand on ne connaît pas le terrain ou qu'il n'y a personne à la radio pour renseigner la piste utilisée.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["verticale du terrain", "verticale de terrain", "verticale" ],
        "contexte_requis": ["terrain", "aérodrome", "intégration", "tour de piste", "piste", "manche à air", "circuit"],
        "xrefs": ["intégration", "tour de piste", "manche à air", "VAC"],
    },
    "vent de face": {
        "definition": "Vent qui vient de l'avant, dans l'axe de la piste. Il est favorable : il réduit la vitesse par rapport au sol, donc raccourcit le décollage comme l'atterrissage, et c'est pour ça qu'on choisit en principe de décoller et d'atterrir face au vent. Sa valeur chiffrée est la <strong>composante de face</strong>, calculée à partir de l'écart entre la direction du vent et l'axe de piste.",
        "categorie": "Vent",
        "variantes": ["vents de face", "de face", "face au vent"],
        "contexte_requis": ["piste", "vent", "décollage", "atterriss", "QFU", "composante", "kt", "axe"],
        "xrefs": ["composante de face", "composante arrière", "composante de travers", "QFU"],
    },
    "remise des gaz": {
        "schema": "remise_des_gaz",
        "definition": "Décision d'interrompre l'atterrissage : plein gaz, on remonte, on refait un tour. Ce n'est <strong>ni un échec ni une faute</strong> — c'est la manœuvre de sécurité la plus utile du pilote. Elle doit être décidée tôt et sans état d'âme dès que l'approche n'est pas stabilisée.",
        "categorie": "Aérodrome & cartes",
        # « remise de gaz » (sans s) : faute courante mais très répandue à
        # l'oral et à l'écrit — on la capture en variante plutôt que d'en
        # faire une fiche doublon.
        "variantes": ["remises des gaz", "remise de gaz", "remises de gaz", "remettre les gaz", "remis les gaz", "go around", "go-around", "goaround"],
        "synonymes": ["go around", "go-around"],
        "xrefs": ["finale", "courte finale", "tour de piste", "approche stabilisée"],
    },
    "approche stabilisée": {
        "definition": "Approche où l'avion est, avant un seuil convenu, sur l'axe, sur le plan, à la bonne vitesse, en configuration d'atterrissage et avec un taux de descente maîtrisé. Si l'un des critères manque, la réponse est la <strong>remise des gaz</strong>.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["approche non stabilisée", "stabilisée"],
        "xrefs": ["remise des gaz", "finale"],
    },
    # ---------------- F5 · Famille des vitesses (Aquila AT01-100A) ----------------
    # Valeurs sourcées du manuel de vol. Chaque V renvoie aux autres (xrefs).
    "vitesses caractéristiques": {
        "definition": "Famille des vitesses repères d'un avion, notées <strong>V</strong> suivi d'un indice, et lues sur l'anémométre en KIAS (vitesse indiquée). Sur l'Aquila AT01-100A : VNE 165, VNO 130, VA 112, VFE 90, VS1 49, VS0 39 KIAS. Ce sont les valeurs du <strong>manuel de vol de l'exemplaire</strong> qui font foi.",
        "categorie": "Vitesses & performances",
        "variantes": ["famille des vitesses", "vitesses caractéristique", "les V", "vitesses repères"],
        "famille": "vitesses",
        "xrefs": ["VNE", "VNO", "VA", "VFE", "VS0", "VS1", "IAS"],
    },
    "VNE": {
        "definition": "<em>Velocity Never Exceed</em> — vitesse à ne jamais dépasser, trait rouge de l'anémomètre : <strong>165 KIAS</strong> sur l'Aquila AT01-100A. Au-delà, risque de rupture structurale ou de flottement. Elle se rapproche vite en descente moteur affiché.",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["Vne", "vne", "V NE", "V_NE", "V-NE"],
        "xrefs": ["VNO", "VA", "vitesses caractéristiques"],
    },
    "VNO": {
        "definition": "<em>Velocity Normal Operating</em> — vitesse maximale d'utilisation normale, haut de l'arc vert : <strong>130 KIAS</strong> sur l'Aquila AT01-100A. Entre VNO et VNE (arc jaune), on ne vole qu'en air calme et avec douceur.",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["Vno", "vno", "V NO", "V_NO", "V-NO"],
        "xrefs": ["VNE", "VA", "vitesses caractéristiques"],
    },
    "VA": {
        "definition": "<em>Velocity of maneuvering</em> — vitesse de manœuvre : <strong>112 KIAS</strong> à masse maximale sur l'Aquila AT01-100A. En dessous, une commande brutale fait décrocher l'aile <strong>avant</strong> que la structure ne subisse un facteur de charge destructeur ; au-dessus, elle peut casser la structure directement. C'est la vitesse à adopter en turbulence. Elle <strong>diminue quand la masse diminue</strong>.",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["Va", "va", "V A", "V_A", "V-A", "vitesse de manœuvre", "vitesse de manoeuvre"],
        "synonymes": ["vitesse de manœuvre"],
        "xrefs": ["VNO", "VNE", "vitesses caractéristiques"],
    },
    "VFE": {
        "definition": "<em>Velocity Flaps Extended</em> — vitesse maximale volets sortis, haut de l'arc blanc : <strong>90 KIAS</strong> sur l'Aquila AT01-100A. La dépasser volets sortis peut endommager les volets et leurs commandes.",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["Vfe", "vfe", "V FE", "V_FE", "V-FE"],
        "xrefs": ["VS0", "vitesses caractéristiques"],
    },
    "VS1": {
        "definition": "<em>Velocity Stall clean configuration</em> — vitesse de décrochage en configuration lisse (volets rentrés), bas de l'arc vert : <strong>49 KIAS</strong> sur l'Aquila AT01-100A. Elle augmente avec la masse et en virage incliné.",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["Vs1", "vs1", "V S1", "VS₁", "V-S1"],
        "xrefs": ["VS0", "décrochage", "vitesse de décrochage", "vitesses caractéristiques"],
    },
    "VS0": {
        "definition": "<em>Velocity Stall landing configuration</em> — vitesse de décrochage en configuration d'atterrissage (volets sortis), bas de l'arc blanc : <strong>39 KIAS</strong> sur l'Aquila AT01-100A. Base de calcul de la vitesse d'approche, traditionnellement de l'ordre de 1,3 × VS0.",
        "categorie": "Vitesses & performances",
        "famille": "vitesses",
        "variantes": ["Vs0", "vs0", "V S0", "VS₀", "V-S0", "vso"],
        "xrefs": ["VS1", "VFE", "décrochage", "vitesse de décrochage", "vitesses caractéristiques"],
    },
    # ---------------- F6 · Énergie & inertie ----------------
    "énergie cinétique": {
        "definition": "Énergie que possède l'avion du fait de sa vitesse. Elle croît avec le <strong>carré</strong> de la vitesse : arriver 10 % trop vite au toucher, c'est environ 20 % d'énergie en plus à dissiper, donc une distance d'arrêt sensiblement allongée.",
        "categorie": "Aérodynamique",
        "variantes": ["énergie cinétiques"],
        "xrefs": ["inertie"],
    },
    "inertie": {
        "definition": "Tendance de l'avion à conserver son mouvement : plus il est lourd et rapide, plus il met de temps et de distance à changer d'état. C'est pourquoi une correction tardive en finale par vent de travers ne « rattrape » pas instantanément la trajectoire.",
        "categorie": "Aérodynamique",
        "variantes": ["inertiel", "inertielle"],
        "xrefs": ["énergie cinétique"],
    },
}


# ===========================================================================
# MODE DEV — fiches à rédiger (02/08/2026, demande Louis)
# ===========================================================================
# Termes du LEXIQUE qu'on sait devoir traiter mais qui n'ont pas encore de
# définition. En mode dev (AERO_GLOS_DEV=1) ils sont injectés dans GLOSSAIRE
# avec une définition vide : le linker les souligne donc comme les autres, le
# clic ouvre l'overlay, et l'overlay affiche le badge « ⚠️ FICHE À RÉDIGER »
# au lieu d'une carte muette. Objectif : repérer les trous d'un balayage.
#
# EN PRODUCTION (défaut) ces entrées N'EXISTENT PAS : ni span, ni fiche, ni
# ligne dans le glossaire. Aucun risque de publier une fiche vide.
#
# Format allégé : {"terme": {"categorie": …, "variantes": […]}}. Pas de
# "definition" — c'est justement ce qui manque. Dès qu'un terme est rédigé,
# on le déplace dans GLOSSAIRE ci-dessus et on le retire d'ici.
FICHES_A_REDIGER = {
    # --- Tour de piste / phases de vol restant à traiter ---
    "encadrement": {"categorie": "Aérodrome & cartes"},
    "point d'arrêt": {
        "categorie": "Aérodrome & cartes",
        "variantes": ["points d'arrêt"],
    },
    "tour de piste basse hauteur": {"categorie": "Aérodrome & cartes"},
    "touché": {"categorie": "Aérodrome & cartes", "variantes": ["touch and go"]},
    "posé-décollé": {"categorie": "Aérodrome & cartes"},
    "vent de travers démontré": {"categorie": "Vent"},
    "effet de site": {"categorie": "Vent", "variantes": ["effets de site"]},
    "turbulence de sillage": {"categorie": "Vent"},
    "plan de descente": {"categorie": "Aérodrome & cartes"},
    "taux de descente": {"categorie": "Vitesses & performances"},
    "Vapp": {"categorie": "Vitesses & performances", "variantes": ["vapp"]},
    "majoration rafale": {"categorie": "Vitesses & performances"},
    "distance d'atterrissage": {"categorie": "Vitesses & performances"},
    "distance de décollage": {"categorie": "Vitesses & performances"},
    "piste mouillée": {"categorie": "Aérodrome & cartes"},
    "aérofreinage": {"categorie": "Aérodynamique"},
    "effet de sol": {"categorie": "Aérodynamique"},
}


def _injecter_fiches_a_rediger() -> None:
    """Mode dev : ajoute les stubs à GLOSSAIRE (definition vide + drapeau).

    Le drapeau `a_rediger: True` traverse tout le pipeline :
      - glos_utils les traite comme n'importe quel terme (span cliquable) ;
      - build_glossaire les exporte avec "todo": 1 dans glossaire-data.js ;
      - aero.js affiche le badge « ⚠️ FICHE À RÉDIGER » et la carte rouge.

    Une entrée déjà rédigée dans GLOSSAIRE gagne TOUJOURS : si un terme est
    listé ici par oubli après avoir été rédigé, il n'est pas écrasé par un
    stub vide (c'est exactement le scénario du doublon silencieux qu'on a
    déjà payé avec `composante de travers`).
    """
    from glos_utils import dev_mode

    if not dev_mode():
        return
    for terme, meta in FICHES_A_REDIGER.items():
        if terme in GLOSSAIRE:
            continue                      # déjà rédigé : on ne touche pas
        GLOSSAIRE[terme] = {
            "definition": "",
            "categorie": meta.get("categorie", "À classer"),
            "a_rediger": True,
            **({"variantes": meta["variantes"]} if meta.get("variantes") else {}),
        }


_injecter_fiches_a_rediger()
