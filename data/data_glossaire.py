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
        "variantes": ["above mean sea level", "AMSL", "altitude AMSL"],
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
        "variantes": ["TAF", "TAF AMD", "prévision d'aérodrome", "AMD", "TAF amendé"],
    },
    "CAVOK": {
        "definition": "<em>Ceiling And Visibility OK</em> : visibilité ≥ 10 km, aucun nuage sous 5000 ft (ou sous la plus haute altitude de secteur), pas de CB ni de temps significatif. Attention : CAVOK ne dit rien du vent ni de la turbulence.",
        "categorie": "Météo",
    },
    "NOSIG": {
        "definition": "<em>No significant change</em> : pas d'évolution significative attendue dans les 2 heures suivant le METAR. Ce n'est pas une promesse, juste l'absence de changement prévu par l'observateur.",
        "categorie": "Météo",
        "variantes": ["NOSIG", "no significant change", "pas de changement significatif"],
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
        "variantes": ["observation automatique", "AUTO", "station automatique", "stations automatiques", "station météo automatique"],
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
        "variantes": ["anticyclone", "anticyclones", "haute pression", "anticyclonique", "anticycloniques", "régime anticyclonique", "situation anticyclonique"],
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
        "variantes": ["vitesse sol", "GS", "Ground Speed", "GS réelle", "GS réelles", "vitesse sol réelle"],
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
        "variantes": ["facteurs de charge", "facteur de charge g", "facteur g", "load factor", "load factors"],
    },
    "décrochage": {
        "definition": "Perte brutale de portance quand l'angle d'attaque dépasse l'incidence critique — indépendant de la vitesse proprement dite : on décroche à n'importe quelle vitesse si on tire trop.",
        "categorie": "Aérodynamique",
        "variantes": ["décrochages", "décrocher", "incidence critique", "stall", "angle critique", "angle d'attaque critique", "angle d'incidence critique"],
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
        "contexte_requis": ["piste", "QFU", "atterriss", "seuil décalé", "zébra", "approche", "finale", "atterri", "arrondi", "PAPI", "remise de gaz", "roulage", "décoller", "vitesse de seuil", "touche", "ILS", "VAC", "court"],
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
        "variantes": ["girouettes", "effet girouette", "girouettage"],
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
        "contexte_requis": ["piste", "aérodrome", "terrain", "dégagée", "strip", "marquage", "RWY", "TDZ", "side stripes"],
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
        "variantes": ["vent de travers", "composantes de travers", "crosswind", "composante traversière", "composantes traversières", "vent travers", "travers moyen", "travers rafale"],
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
        "variantes": ["décraber", "décrabé", "crabe", "décrabages", "décabage", "crab"],
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
        "contexte_requis": ["vent", "METAR", "V", "direction", "kt", "secteur", "°", "VRB", "ATIS", "QFU", "rafale"],
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
        "contexte_requis": ["tour de piste", "finale", "vent arrière", "circuit", "piste", "trafic", "numéro", "virage", "étape", "remise de gaz"],
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
        "contexte_requis": ["piste", "atterriss", "axe", "tour de piste", "approche", "QFU", "remise des gaz", "remise de gaz", "go-around", "circuit", "vent arrière", "base/", "base-", "étape de base", "virage", "PAPI", "pente", "arrondi", "trafic", "tour de contrôle", "la tour", "seuil", "Vref", "palier", "volets", "gradient", "IAS", "couche", "toucher", "cisaillement", "LDG", "gaz", "cabré", "nuit", "vent de travers", "vent de face", "vent faible", "vent fort", "décroch", "facteur de charge", "stabilis"],
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
        "variantes": ["derniers virages", "virage de base en finale", "dernier virage base-finale", "base-finale", "base finale", "virage base-finale"],
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
        "contexte_requis": ["piste", "décollage", "atterriss", "distance", "sol", "frein", "vitesse", "TOD", "TORA", "Take-Off", "abaque", "POH", "lift-off", "ground roll", "lâcher", "panne", "herbe", "pente", "corrigé", "décoll", "atterri", "freinage"],
        "xrefs": ["décollage", "roulage", "composante arrière", "arrondi"],
    },
    "alignement": {
        "definition": "Action de placer l'avion sur l'axe de la piste, dans le sens du décollage, avant de mettre la puissance. C'est le dernier moment où l'on vérifie que la piste et l'approche sont libres, que la piste est la bonne, et que les instruments sont cohérents avec le cap attendu. Le terme désigne aussi, en vol, le fait de se mettre dans l'axe de piste en finale.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["alignements", "s'aligner", "aligné", "alignement piste"],
        "contexte_requis": ["piste", "axe", "QFU", "décollage", "finale", "seuil", "cap", "clairance", "roulage", "holding", "point d'attente", "décoller", "atterri", "arrondi", "tour", "TWR", "tenir", "alignez", "stop bar", "attendez", "frein", "s'aligner", "lâcher", "trafic"],
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
        "contexte_requis": ["tour de piste", "circuit", "terrain", "aérodrome", "piste", "VAC", "verticale", "radio", "point de report", "CTR", "LFLX", "LFPN", "arrivée", "clairance", "organisme", "report", "transit", "roulage", "tours", "trafic", "vent arrière", "finale", "LFPV"],
        "xrefs": ["tour de piste", "verticale terrain", "VAC", "vent arrière"],
    },
    "verticale terrain": {
        "definition": "Passage à l'aplomb de l'aérodrome, au-dessus de la hauteur du tour de piste, pour observer le terrain avant de s'y intégrer. On y lit la manche à air, on identifie la piste en service et son sens de tour de piste, et on repère les avions déjà en circuit. C'est le mode d'arrivée classique quand on ne connaît pas le terrain ou qu'il n'y a personne à la radio pour renseigner la piste utilisée.",
        "categorie": "Aérodrome & cartes",
        "variantes": ["verticale du terrain", "verticale de terrain", "verticale" ],
        "contexte_requis": ["terrain", "aérodrome", "intégration", "tour de piste", "piste", "manche à air", "circuit", "vent arrière", "VAC", "point de report", "overhead", "altitude de circuit", "dead side"],
        "xrefs": ["intégration", "tour de piste", "manche à air", "VAC"],
    },
    "vent de face": {
        "definition": "Vent qui vient de l'avant, dans l'axe de la piste. Il est favorable : il réduit la vitesse par rapport au sol, donc raccourcit le décollage comme l'atterrissage, et c'est pour ça qu'on choisit en principe de décoller et d'atterrir face au vent. Sa valeur chiffrée est la <strong>composante de face</strong>, calculée à partir de l'écart entre la direction du vent et l'axe de piste.",
        "categorie": "Vent",
        "variantes": ["vents de face", "de face", "face au vent"],
        "contexte_requis": ["piste", "vent", "décollage", "atterriss", "QFU", "composante", "kt", "axe", "travers", "θ", "cos", "face =", "dérive", "IAS", "badin", "chute", "nav", "vent de", "vent relatif", "vent fort", "vent faible", "le vent", "du vent", "au vent", "vent parfaitement", "vent exactement", "vitesse", "relatif", "Vapp", "Vref", "diminu", "rafale", "baisse", "énergie"],
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
        "variantes": ["famille des vitesses", "vitesses caractéristique", "les V", "vitesses repères", "V-speeds", "V-speed", "V speed"],
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
    # ---------------- Suggestions validées (suggest) ----------------
    "datum": {
        "definition": "Ligne ou plan de référence choisi par le constructeur, à partir duquel on mesure tous les bras de levier du calcul de masse et centrage. Sa position est donnée dans le manuel de vol ou la fiche de pesée : c'est par rapport à lui que s'expriment le centre de gravité (« mm aft datum »), le moment de la masse à vide et celui de chaque passager, bagage ou litre de carburant. Peu importe où il se trouve, tant qu'on utilise le même datum pour tout le calcul.",
        "categorie": "Masse & centrage",
        "famille": "masses",
        "variantes": ["référence datum", "plan de référence", "datum de référence"],
        "xrefs": ["bras de levier", "mm aft datum", "moment", "masse à vide", "fiche de pesée"],
        "origine": "suggest",
    },
    "emplanture": {
        "definition": "L'emplanture est la zone de jonction entre l'aile et le fuselage où les longerons et nervures s'ancrent à la structure centrale. Elle assure la transmission des efforts aérodynamiques de la voilure vers le fuselage et doit résister aux flexions et torsions. C'est une région critique pour la rigidité et la sécurité de l'ensemble cellule.",
        "categorie": "À classer",
        "famille": "structure_aile",
        "xrefs": ["aile", "longeron", "nervure", "corde", "profil", "bord de fuite"],
        "origine": "suggest",
    },
    "chandelle": {
        "definition": "Manœuvre de voltige verticale consistant à cabrer l'avion jusqu'à la position verticale, moteur à fond, puis à laisser l'avion retomber en ligne droite après le point mort. Elle permet de travailler la coordination et la maîtrise des faibles vitesses.",
        "categorie": "À classer",
        "famille": "virages",
        "origine": "suggest",
    },
    "surface de transition": {
        "definition": "Surface inclinée qui s’élève à partir des bords de la piste et des surfaces d’approche. Elle assure un espace dégagé pour les trajectoires d’avions en phase d’atterrissage ou de décollage. Sa pente est généralement de 14,3 % (1:7) pour les pistes de code 3 et 4.",
        "categorie": "À classer",
        "famille": "pistes",
        "origine": "suggest",
    },
    "masse totale": {
        "definition": "La masse totale est la somme de la masse à vide de l'aéronef et de toutes les masses ajoutées (pilote, passagers, carburant, bagages). Elle est exprimée en kilogrammes ou en livres. Elle doit rester inférieure à la masse maximale au décollage (MTOM — Maximum Take-Off Mass) indiquée dans le manuel de vol.",
        "categorie": "À classer",
        "famille": "masses",
        "variantes": ["poids total", "masse brute"],
        "xrefs": ["masse maximale au décollage", "masse maximale à l'atterrissage", "charge utile", "masse à vide", "masse du jour", "masse sans carburant", "devis de masse", "manuel de vol"],
        "origine": "suggest",
    },
    "aérodrome": {
        "definition": "Un aérodrome est une surface définie, sur terre ou sur l'eau, aménagée pour l'arrivée, le départ et les mouvements des aéronefs : piste ou aire d'atterrissage, voies de circulation, aire de stationnement, bâtiments et installations. Il est dit contrôlé quand une tour de contrôle y assure le service du contrôle, non contrôlé sinon. Sur les cartes il est abrégé en AD (Aerodrome — aérodrome) ; la carte VAC (Visual Approach Chart — carte d'approche à vue) en donne les pistes, les fréquences et les procédures d'arrivée.",
        "categorie": "Aérodrome & cartes",
        "famille": "cartes_aeronautiques",
        "origine": "corpus",
        "variantes": ["aérodromes", "aerodrome", "aéroport", "aéroports"],
        "xrefs": ["piste", "atz", "tour de contrôle", "VAC"],
    },
    "myopie du champ vide": {
        "definition": "<em>empty field myopia</em>. Dans un ciel vide ou une brume uniforme, l'œil se met au repos à 1 ou 2 mètres et ne voit plus les avions lointains. On la contre en fixant d'abord un repère lointain (horizon, nuage, point de la carte) avant de balayer le ciel.",
        "categorie": "À classer",
        "famille": "physiologie",
        "variantes": ["myopies du champ vide", "empty field myopia", "myopie de ciel vide"],
        "xrefs": ["conscience de la situation"],
        "origine": "suggest",
    },
    "cataractagenitus": {
        "definition": "Nom spécial de l'OMM pour un nuage né de l'évaporation au pied d'une cascade ou d'une chute d'eau. C'est une curiosité de nomenclature, sans effet sur le vol.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "xrefs": ["nuage"],
        "origine": "suggest",
    },
    "homomutatus": {
        "definition": "Nom spécial de l'OMM pour un nuage d'origine humaine qui s'est transformé en autre chose : par exemple une traînée de condensation persistante qui s'étale en cirrus. Il fait suite à l'homogenitus (trainée récente).",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["cirrus homomutatus"],
        "xrefs": ["cirrus", "nuage"],
        "origine": "suggest",
    },
    "undulatus": {
        "definition": "Variété de nuage de l'OMM : nuage en bancs ou nappes ondulés, souvent avec des bandes parallèles. Elle est fréquente sur stratocumulus et altocumulus et traduit un faible cisaillement de vent entre couches.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["nuage ondulé"],
        "xrefs": ["stratocumulus", "altocumulus", "cisaillement"],
        "origine": "suggest",
    },
    "autokinésie": {
        "definition": "Illusion visuelle de la nuit : un point lumineux fixe, regardé longtemps sans repère, semble bouger. Le pilote peut croire qu'il s'agit d'un autre aéronef ou d'un mouvement de son propre avion. On l'évite en déplaçant son regard et en s'appuyant sur les instruments.",
        "categorie": "À classer",
        "famille": "physiologie",
        "variantes": ["autokinésies", "effet autocinétique"],
        "xrefs": ["illusion sensorielle", "effet de trou noir", "faux horizon"],
        "origine": "suggest",
    },
    "rebond (marsouinage)": {
        "definition": "<em>porpoising</em>. Oscillations en tangage de plus en plus amples au toucher ou à l'arrondi (comme un marsouin) provoquées par une mauvaise correction du pilote. On les stoppe en remettant les gaz plutôt que de tenter de les corriger au manche. Le rebond est lié à une vitesse excessive ou à un arrondi mal calé.",
        "categorie": "À classer",
        "famille": "atterrissages",
        "variantes": ["rebonds (marsouinage)s", "marsouinage", "marsouinages", "porpoising"],
        "xrefs": ["arrondi", "remise des gaz", "effet de sol"],
        "origine": "suggest",
    },
    "démarreur": {
        "definition": "<em>starter motor</em>. Moteur électrique qui entraîne le moteur thermique pour le lancer. On l'active avec la clé ou le bouton de démarrage, sans le maintenir plus de quelques secondes (risque de surchauffe). À ne pas confondre avec « starter » (choke).",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["démarreurs", "starter motor"],
        "xrefs": ["choke", "batterie", "alternateur", "magnéto"],
        "origine": "suggest",
    },
    "UHF": {
        "definition": "<em>Ultra High Frequency</em> — « Ultra haute fréquence ». Bande de fréquences radioélectriques de 300 MHz à 3 GHz. En aviation civile, on la rencontre surtout dans le DME (Distance Measuring Equipment — équipement de mesure de distance ; 960 à 1 215 MHz) et dans la radio militaire (225 à 400 MHz). La radio civile des pilotes privés reste en VHF (Very High Frequency — très haute fréquence).",
        "categorie": "À classer",
        "famille": "radio_phraseologie",
        "variantes": ["Ultra High Frequency", "Ultra haute fréquence", "ultras hautes fréquences"],
        "xrefs": ["DME", "fréquence", "vor"],
        "origine": "suggest",
    },
    "Organisation météorologique mondiale": {
        "definition": "<em>Organisation météorologique mondiale</em>. Agence spécialisée des Nations unies qui coordonne la météorologie mondiale. Son Atlas international des nuages (édition 2017) fixe la nomenclature officielle des nuages : genres, espèces, variétés, particularités supplémentaires. Les définitions des nuages du cours en sont issues.",
        "categorie": "À classer",
        "famille": "divers",
        "variantes": ["World Meteorological Organization", "OMM", "WMO", "Atlas international des nuages", "Atlas OMM"],
        "xrefs": ["cumulonimbus", "nuage"],
        "origine": "suggest",
    },
    "FAA": {
        "definition": "<em>Federal Aviation Administration</em> — « autorité de l'aviation civile américaine ». Autorité de l'aviation civile des États-Unis (Federal Aviation Administration). Elle publie des manuels et des circulaires que les cours citent pour des ordres de grandeur (temps utile de conscience, contournement d'un orage, ondes de relief). Ces chiffres sont pédagogiques : en Europe la référence réglementaire est l'EASA (European Union Aviation Safety Agency — Agence de l'Union européenne pour la sécurité aérienne) et, en France, la DGAC (Direction Générale de l'Aviation Civile).",
        "categorie": "À classer",
        "famille": "divers",
        "variantes": ["Federal Aviation Administration", "autorité de l'aviation civile américaine"],
        "xrefs": ["easa", "dgac"],
        "origine": "suggest",
    },
    "NCD": {
        "definition": "<em>No Cloud Detected</em> — « aucun nuage détecté ». Code d'un METAR (Meteorological Aerodrome Report — message d'observation météorologique d'aérodrome) automatique (AUTO — Automated observation — observation automatique) qui signifie que la station n'a détecté aucun nuage. Ce n'est pas un CAVOK (Ceiling And Visibility OK — plafond et visibilité OK) : la station peut ne pas voir un nuage en altitude ou ne pas mesurer la visibilité de la même façon. Il est proche de NSC (No Significant Cloud — pas de nuage significatif) mais s'emploie uniquement pour les stations automatiques.",
        "categorie": "À classer",
        "famille": "codes_meteo_etat",
        "variantes": ["No Cloud Detected", "aucun nuage détecté"],
        "xrefs": ["AUTO", "CAVOK", "METAR"],
        "origine": "suggest",
    },
    "CDI": {
        "definition": "<em>Course Deviation Indicator</em> — « indicateur d'écart de route ». Aiguille verticale du récepteur VOR (VHF Omnidirectional Range — radiophare omnidirectionnel VHF) : elle se centre quand l'avion est sur le radial choisi avec l'OBS (Omni Bearing Selector — sélecteur de radial), et se décale à droite ou à gauche quand il est à côté. Le drapeau « to/from » indique si la route sélectionnée mène vers la station ou s'en éloigne. Il montre l'écart, pas le cap à tenir.",
        "categorie": "À classer",
        "famille": "instruments_radionavigation",
        "variantes": ["Course Deviation Indicator", "indicateur d'écart de route", "aiguille de déviation"],
        "contexte_requis": ["vor", "obs", "radial", "dme", "gps", "drapeau", "aiguille"],
        "xrefs": ["vor", "radiale", "relèvement"],
        "origine": "suggest",
    },
    "OBS": {
        "definition": "<em>Omni Bearing Selector</em> — « sélecteur de radial ». Bouton du récepteur VOR (VHF Omnidirectional Range — radiophare omnidirectionnel VHF) qui permet de choisir le radial ou la route à suivre ; il affiche la valeur sélectionnée. Le drapeau « to/from » dépend de l'OBS : avec OBS 090 et « to », la route 090 mène à la station et l'avion est sur le radial 270. Avec le CDI (Course Deviation Indicator — indicateur d'écart de route) centré et « from », on lit sur l'OBS le radial sur lequel on se trouve.",
        "categorie": "À classer",
        "famille": "instruments_radionavigation",
        "variantes": ["Omni Bearing Selector", "sélecteur de radial"],
        "xrefs": ["vor", "radiale", "relèvement"],
        "origine": "suggest",
    },
    "BEA": {
        "definition": "<em>Bureau d'Enquêtes et d'Analyses pour la sécurité de l'aviation civile</em>. Organisme français chargé des enquêtes de sécurité sur les accidents et incidents graves de l'aviation civile. Son but est de comprendre les causes pour prévenir, non de désigner des responsables. Les rapports du BEA, par exemple sur les pertes de puissance au décollage des avions légers et des ULM (Ultra Léger Motorisé), servent de retour d'expérience en formation.",
        "categorie": "À classer",
        "famille": "divers",
        "variantes": ["Bureau d'Enquêtes et d'Analyses", "rapport du BEA"],
        "xrefs": ["NOTAM"],
        "origine": "suggest",
    },
    "AVGAS": {
        "definition": "<em>Aviation Gasoline</em> — « essence aviation ». Essence aviation pour moteurs à pistons, vendue en aviation générale. L'AVGAS 100LL (100 octane Low Lead, faible teneur en plomb), bleue et plombée, est la plus courante ; l'AVGAS UL91 (Unleaded 91 (octane) — essence aviation sans plomb 91 octanes) est sans plomb. Le POH (Pilot's Operating Handbook — manuel d'utilisation du pilote (manuel de vol)) précise les carburants approuvés : sur le Rotax 912 de l'AT01, l'essence auto EN228 est l'usage normal, et l'AVGAS 100LL, riche en plomb, use davantage le moteur.",
        "categorie": "À classer",
        "famille": "gestion_carburant",
        "variantes": ["Aviation Gasoline", "essence aviation"],
        "xrefs": ["carburant 100ll", "ul91", "mogas", "essence auto"],
        "origine": "suggest",
    },
    "silvagenitus": {
        "definition": "Nom spécial de l'OMM (Organisation météorologique mondiale ; Atlas international des nuages, 2017) pour un nuage formé au-dessus d'une forêt par l'humidité de l'évapotranspiration des arbres. Il appartient à la même série de noms en « -genitus » que l'homogenitus (activité humaine) et le flammagenitus (incendie) ; sans effet sur le vol.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "xrefs": ["nuage", "cataractagenitus"],
        "origine": "suggest",
    },
    "fibratus": {
        "definition": "Espèce de cirrus de l'OMM (Organisation météorologique mondiale) : filaments fins et presque droits, sans crochet. Les cirrus fibratus sont des nuages d'altitude de glace, sans danger direct pour le vol, mais ils peuvent précéder l'arrivée d'une perturbation.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["cirrus fibratus"],
        "xrefs": ["cirrus", "cirrostratus"],
        "origine": "suggest",
    },
    "uncinus": {
        "definition": "Espèce de cirrus de l'OMM (Organisation météorologique mondiale) en forme de crochet ou de virgule, avec une tête surmontée d'un petit crochet. Il annonce parfois une dégradation du temps à l'arrivée d'une perturbation.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["cirrus uncinus"],
        "xrefs": ["cirrus", "cirrostratus", "front chaud"],
        "origine": "suggest",
    },
    "praecipitatio": {
        "definition": "Particularité supplémentaire de l'OMM (Organisation météorologique mondiale) : précipitations (pluie, bruine, neige) qui atteignent le sol, issues d'un nuage. Elle accompagne surtout stratus, nimbostratus et cumulonimbus et réduit la visibilité. À distinguer de virga, où la précipitation s'évapore avant d'arriver.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["precipitatio"],
        "xrefs": ["virga", "nimbostratus", "pluie", "visibilité"],
        "origine": "suggest",
    },
    "murus": {
        "definition": "Nuage accessoire de l'OMM (Organisation météorologique mondiale) : abaissement localisé et persistant de la base d'un cumulonimbus, souvent signe d'un orage de forte intensité qui peut produire une tornade. On le nomme aussi nuage-mur (wall cloud). C'est une alerte : on reste très loin d'un cumulonimbus qui en porte un.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["nuage-mur", "wall cloud"],
        "xrefs": ["cumulonimbus", "orage supercellulaire", "tornade"],
        "origine": "suggest",
    },
    "asperitas": {
        "definition": "Particularité supplémentaire de l'OMM (Organisation météorologique mondiale), ajoutée en 2017 : ondulations bien délimitées sur la face inférieure du nuage, plus chaotiques que la variété undulatus, comme une mer agitée vue d'en dessous. Elle accompagne surtout les stratocumulus et les altocumulus ; le nom vient du latin asperitas, « rugosité ». Elle est inoffensive pour le vol.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["asperatus"],
        "xrefs": ["stratocumulus", "altocumulus", "mammatus", "undulatus"],
        "origine": "suggest",
    },
    "stratiformis": {
        "definition": "Espèce de nuage de l'OMM (Organisation météorologique mondiale) : nuage en nappe ou en couche horizontale étendue (altocumulus, stratocumulus, cirrocumulus). Distinct du caractère général « stratiforme » (nuages de type stratus). Il concerne des nuages en bancs, qui peuvent couvrir le ciel.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "xrefs": ["altocumulus", "stratocumulus", "lenticularis"],
        "origine": "suggest",
    },
    "incus": {
        "definition": "Particularité supplémentaire de l'OMM (Organisation météorologique mondiale) : sommet d'un cumulonimbus étalé en enclume, lisse, fibreux ou strié. Elle accompagne l'espèce capillatus (cumulonimbus capillatus incus), généralement liée à une averse ou à un orage, avec rafales et parfois de la grêle. L'enclume peut s'étendre très loin sous le vent de l'orage.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["enclume", "nuage en enclume", "cumulonimbus capillatus incus"],
        "xrefs": ["capillatus", "cumulonimbus", "orage", "CB"],
        "origine": "suggest",
    },
    "flammagenitus": {
        "definition": "Nom spécial de l'OMM (Organisation météorologique mondiale ; Atlas 2017) pour un nuage né de la convection déclenchée par la chaleur d'un feu de forêt, d'un incendie ou d'une activité volcanique. On le nomme avec le genre, par exemple Cumulus congestus flammagenitus ; le nom courant, non officiel, est pyrocumulus. Il peut se développer en cumulonimbus et donner orage et rafales.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["pyrocumulus", "cumulus flammagenitus"],
        "xrefs": ["cumulus congestus", "convection", "cumulonimbus"],
        "origine": "suggest",
    },
    "floccus": {
        "definition": "Espèce de nuage de l'OMM (Organisation météorologique mondiale), en petites touffes isolées au bas effiloché, présente sur cirrus, cirrocumulus, altocumulus, et stratocumulus. Un altocumulus floccus indique de l'instabilité à moyenne altitude et peut précéder des averses ou des orages.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "xrefs": ["altocumulus", "cirrus", "castellanus", "instabilité atmosphérique"],
        "origine": "suggest",
    },
    "velum": {
        "definition": "Nuage accessoire de l'OMM (Organisation météorologique mondiale) : voile nuageux de grande étendue horizontale placé au-dessus ou attaché au sommet d'un ou plusieurs nuages cumuliformes qui le percent souvent. Il accompagne surtout cumulus et cumulonimbus. Son pendant de petite taille est le pileus (un capuchon).",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["velums"],
        "xrefs": ["cumulus", "cumulonimbus"],
        "origine": "suggest",
    },
    "pileus": {
        "definition": "Nuage accessoire de l'OMM (Organisation météorologique mondiale) : capuchon de petite extension horizontale au-dessus du sommet ou attaché à la partie supérieure d'un nuage cumuliforme qu'il pénètre souvent. Il accompagne surtout cumulus et cumulonimbus et traduit une ascendance rapide. Plusieurs pileus peuvent se superposer.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["capuchon nuageux"],
        "xrefs": ["cumulonimbus", "cumulus"],
        "origine": "suggest",
    },
    "arcus": {
        "definition": "Particularité supplémentaire de l'OMM (Organisation météorologique mondiale) : rouleau ou arc sombre à la base d'un cumulonimbus (ou d'un cumulus), précurseur d'un front de rafales. À son passage, le vent saute, des rafales arrivent et la température chute. Un arcus visible à une dizaine de kilomètres de l'aérodrome signifie qu'il vaut mieux ne ni décoller ni atterrir.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["nuage en arc", "shelf cloud"],
        "xrefs": ["front de rafales", "cumulonimbus", "orage", "microburst"],
        "origine": "suggest",
    },
    "fluctus": {
        "definition": "Particularité supplémentaire de l'Atlas des nuages, édition 2017 de l'OMM (Organisation météorologique mondiale) : une formation ondulatoire de courte durée en volutes ou en vagues déferlantes, généralement sur la face supérieure du nuage (ondes de Kelvin-Helmholtz). Elle se voit surtout sur cirrus, altocumulus, stratocumulus et stratus. Elle signale un cisaillement de vent à ce niveau, donc une turbulence possible.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["nuage en vagues", "nuages en vagues", "vagues de Kelvin-Helmholtz", "ondes de Kelvin-Helmholtz"],
        "xrefs": ["cisaillement", "turbulence", "altocumulus", "stratocumulus"],
        "origine": "suggest",
    },
    "homogenitus": {
        "definition": "Nom spécial de l'OMM (Organisation météorologique mondiale ; Atlas 2017) pour un nuage formé par une activité humaine. L'exemple type est la traînée de condensation d'un avion qui persiste : elle prend le genre cirrus et le nom spécial homogenitus (cirrus homogenitus). Si elle s'étale et se transforme, on parle de homomutatus.",
        "categorie": "À classer",
        "famille": "nuages_especes",
        "variantes": ["traînée persistante", "cirrus homogenitus", "traînée de condensation persistante", "nuage d'origine humaine"],
        "xrefs": ["cirrus", "nuage", "homomutatus"],
        "origine": "suggest",
    },
    "courant-jet": {
        "definition": "<em>jet stream</em>. Courant d'air très rapide et étroit en haute altitude (vers 9 000 à 12 000 m), qui peut dépasser 100 kt. Il influence les performances en croisière (vent arrière ou de face) des avions en altitude. Il n'a pratiquement pas d'effet sur le vol VFR (Visual Flight Rules — vol à vue) à basse altitude, sauf par le cisaillement et la turbulence qu'il engendre.",
        "categorie": "À classer",
        "famille": "couches_atmospheriques",
        "variantes": ["jet stream", "jet-stream", "courant jet"],
        "contexte_requis": ["cisaillement", "turbulence", "vent", "altitude", "tropopause", "ondes"],
        "xrefs": ["tropopause", "cirrus", "cisaillement"],
        "origine": "suggest",
    },
    "ciel obscurci": {
        "definition": "<em>visibilité verticale (VV)</em>. Ciel dont aucun nuage n'est distinct parce que la visibilité verticale est limitée par du brouillard, une brume dense ou de fortes précipitations. Dans un METAR (Meteorological Aerodrome Report — message d'observation météorologique d'aérodrome), on lit VV suivi de la hauteur en centaines de pieds (VV002 = 200 ft). Il équivaut à un plafond très bas, souvent incompatible avec le VFR (Visual Flight Rules — vol à vue).",
        "categorie": "À classer",
        "famille": "nuages_couverture",
        "variantes": ["ciels obscurcis"],
        "xrefs": ["visibilité verticale", "plafond", "brouillard", "base des nuages", "plafond nuageux"],
        "origine": "suggest",
    },
    "condensation": {
        "definition": "Passage de la vapeur d'eau à l'état liquide quand l'air est saturé, par refroidissement ou apport d'humidité. Elle forme brume, brouillard et nuages, et libère de la chaleur latente qui entretient l'instabilité. Dans le carburateur, le refroidissement par détente du venturi et la vaporisation du carburant peuvent condenser puis givrer l'humidité de l'air.",
        "categorie": "À classer",
        "famille": "stabilite_atmospherique",
        "variantes": ["condensations"],
        "xrefs": ["saturation", "chaleur latente", "point de rosée", "givrage carburateur"],
        "origine": "suggest",
    },
    "halo": {
        "definition": "Cercle lumineux autour du soleil ou de la lune, causé par la réfraction de la lumière dans les cristaux de glace d'un voile de cirrostratus. Il précède souvent l'arrivée d'une perturbation (front chaud), avec une baisse de pression, dans les 12 à 24 heures. Ce n'est pas une règle absolue : le halo seul ne suffit pas à prévoir le temps.",
        "categorie": "À classer",
        "famille": "nuages_genres",
        "variantes": ["halos", "halo solaire", "halo lunaire"],
        "xrefs": ["cirrostratus", "front chaud", "cirrus", "pression atmosphérique"],
        "origine": "suggest",
    },
    "masse d'air": {
        "definition": "<em>Air mass</em>. Vaste volume d'air (des centaines de kilomètres) aux propriétés de température et d'humidité à peu près uniformes, acquises sur sa région d'origine. On la dit chaude ou froide, humide ou sèche, stable ou instable. Une masse d'air instable donne cumulus, averses, orages et bonne visibilité entre les averses ; une masse d'air stable donne stratus, brume et mauvaise visibilité.",
        "categorie": "À classer",
        "famille": "stabilite_atmospherique",
        "variantes": ["Air mass"],
        "xrefs": ["front", "instabilité atmosphérique", "stabilité atmosphérique", "advection"],
        "origine": "suggest",
    },
    "écart T−Td": {
        "definition": "<em>écart température / point de rosée</em>. Différence entre la température de l'air et son point de rosée. Plus l'écart est faible, plus l'air est proche de la saturation : brume, brouillard, givrage possibles. Pour un cumulus de convection, on estime la base à 400 ft × (T − Td) au-dessus du terrain (T − Td = 8 °C donne environ 3 200 ft).",
        "categorie": "À classer",
        "famille": "isothermes_temperatures",
        "variantes": ["écart température / point de rosée", "spread", "écart T-Td", "écart T/Td", "T-Td"],
        "xrefs": ["point de rosée", "saturation", "humidité relative", "base des nuages"],
        "origine": "suggest",
    },
    "cumuliforme": {
        "definition": "Se dit d'un nuage à développement vertical en tas, qui naît de la convection dans un air instable (cumulus, cumulus congestus, cumulonimbus). Ces nuages donnent averses, turbulence, rafales et, pour les plus développés, orages. Leur base se situe grossièrement à 400 ft × (T − Td) au-dessus du terrain.",
        "categorie": "À classer",
        "famille": "nuages_genres",
        "variantes": ["cumuliformes", "nuage cumuliforme", "nuages cumuliformes"],
        "xrefs": ["cumulus", "cumulonimbus", "convection"],
        "origine": "suggest",
    },
    "stratiforme": {
        "definition": "Se dit d'un nuage qui s'étale en nappe ou en couche horizontale étendue (stratus, altostratus, nimbostratus, cirrostratus). Ces nuages se forment dans un air plutôt stable : ciel couvert, précipitations continues et faibles, peu de turbulence mais givrage possible. À ne pas confondre avec l'espèce « stratiformis » (altocumulus ou stratocumulus en nappe).",
        "categorie": "À classer",
        "famille": "nuages_genres",
        "variantes": ["stratiformes", "nuage stratiforme", "nuages stratiformes"],
        "xrefs": ["stratus", "nimbostratus", "stabilité atmosphérique"],
        "origine": "suggest",
    },
    "vapor lock": {
        "definition": "<em>bouchon de vapeur</em>. Formation de bulles de vapeur dans le circuit carburant (canalisations, pompe) sous l'effet de la chaleur ou d'une basse pression, qui gêne ou interrompt l'alimentation du moteur et peut faire perdre de la puissance. Il touche surtout les essences volatiles par temps chaud. La pompe électrique de secours et un carburant adapté en limitent le risque.",
        "categorie": "À classer",
        "famille": "gestion_carburant",
        "variantes": ["bouchon de vapeur", "vapour lock"],
        "xrefs": ["circuit carburant", "mogas", "pompe électrique"],
        "origine": "suggest",
    },
    "piston": {
        "definition": "Pièce mobile qui coulisse dans le cylindre : elle est poussée par la combustion et transmet l'effort au vilebrequin par la bielle. Un moteur à pistons (Rotax 912 : quatre cylindres) tourne à régime élevé ; le piston subit la chaleur et le frottement.",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["pistons"],
        "xrefs": ["moteur à 4 temps", "compression"],
        "origine": "suggest",
    },
    "jauge d'huile": {
        "definition": "<em>réglette</em>. Réglette graduée plongée dans le réservoir d'huile pour contrôler le niveau à la visite prévol. Le POH (Pilot's Operating Handbook — manuel d'utilisation du pilote (manuel de vol)) de l'AT01 demande de la croiser avec la jauge du tableau de bord, avion à peu près horizontal, car deux sources valent mieux qu'une. Un niveau trop bas ou trop haut s'ajuste avant le vol.",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["dipstick", "réglette d'huile", "jauge à huile"],
        "xrefs": ["pression d'huile", "température d'huile", "jauge", "visite prévol"],
        "origine": "suggest",
    },
    "carter sec": {
        "definition": "<em>dry sump</em>. Mode de lubrification où l'huile est stockée dans un réservoir séparé et non dans le carter du moteur, une pompe l'y renvoie. Il permet de garder une pression d'huile même en assiette inhabituelle. Le Rotax 912 de l'AT01 a une lubrification à carter sec avec réservoir d'huile séparé (d'où la jauge d'huile à vérifier).",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["dry sump", "lubrification à carter sec"],
        "xrefs": ["pression d'huile", "température d'huile"],
        "origine": "suggest",
    },
    "régulateur de régime": {
        "definition": "<em>Propeller governor</em>. Dispositif hydraulique de l'hélice à régime constant qui ajuste automatiquement le pas pour tenir le régime choisi avec le levier d'hélice, quelle que soit la vitesse ou la puissance. Sur l'AT01, une panne d'huile du régulateur donne un pas minimal automatique, avec pleine puissance disponible. Le « régulateur » de tension de l'alternateur est un autre composant.",
        "categorie": "À classer",
        "famille": "helice",
        "variantes": ["Propeller governor", "governor", "régulateur d'hélice", "régulateur de pas"],
        "xrefs": ["hélice à pas variable", "calage d'hélice", "plein gaz"],
        "origine": "suggest",
    },
    "braquage": {
        "definition": "Angle de déflexion d'une gouverne (aileron, profondeur, direction) ou d'un volet par rapport à sa position neutre. Plus le braquage est grand, plus l'effet est fort, mais plus la traînée et le risque de décrochage augmentent. La vitesse de manœuvre (VA — Maneuvering Speed) protège la structure d'un seul braquage complet, pas de braquages complets répétés ou simultanés.",
        "categorie": "À classer",
        "famille": "gouvernes_primaires",
        "variantes": ["braquages", "braquage de volets", "braquage des gouvernes"],
        "xrefs": ["gouverne de profondeur", "VA", "volets"],
        "origine": "suggest",
    },
    "délaminage": {
        "definition": "Décollement des couches d'un matériau composite (fibres, âme), signe d'un impact ou de fatigue. Il se repère par une bosse, une zone blanchie ou un son creux au tapotement, parfois sans trace sur la peau. On le recherche à la visite prévol ; un doute impose de demander l'avis de l'instructeur ou du mécanicien.",
        "categorie": "À classer",
        "famille": "cellule_fuselage",
        "variantes": ["délaminages", "delamination"],
        "xrefs": ["composite", "visite prévol", "cellule"],
        "origine": "suggest",
    },
    "carénage": {
        "definition": "Enveloppe profilée qui recouvre un élément saillant (roues, jonction aile-fuselage, train) pour réduire la traînée de forme. Sur l'AT01, rouler sans les carénages de roues peut coûter jusqu'à 10 % de performance, d'après le POH (Pilot's Operating Handbook — manuel d'utilisation du pilote (manuel de vol)). Des carénages mal ajustés augmentent aussi la traînée d'interférence.",
        "categorie": "À classer",
        "famille": "cellule_fuselage",
        "variantes": ["carénages", "carénage de roue", "carénages de roues"],
        "xrefs": ["traînée parasite", "cellule", "roue", "composite"],
        "origine": "suggest",
    },
    "voltmètre": {
        "definition": "Instrument qui indique la tension du réseau électrique de bord, en volts. Sur l'AT01, l'arc vert va de 12 à 15 V : en charge normale, il montre que l'alternateur recharge la batterie, et une tension trop basse que la batterie se décharge. On le surveille avec les instruments moteur.",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["voltmètres", "voltmètre de bord"],
        "xrefs": ["ampèremètre", "alternateur", "batterie", "disjoncteur"],
        "origine": "suggest",
    },
    "verrière": {
        "definition": "Partie vitrée transparente du cockpit qui protège l'équipage et assure la visibilité. Elle doit être propre, sans fissure ni rayure gênante, et verrouillée avant le décollage. On la contrôle à la visite prévol (cabine).",
        "categorie": "À classer",
        "famille": "cellule_fuselage",
        "variantes": ["verrières"],
        "xrefs": ["visite prévol", "cellule", "check-list décollage", "composite"],
        "origine": "suggest",
    },
    "vilebrequin": {
        "definition": "Arbre coudé du moteur qui transforme le mouvement alternatif des pistons en rotation. Sur le Rotax 912, il tourne vite (environ 5 800 tr/min à 2 385 tr/min d'hélice) et l'hélice est entraînée à travers un réducteur de rapport 2,43 : 1. Le tachymètre de l'AT01 affiche donc le régime hélice, pas celui du vilebrequin.",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["vilebrequins", "arbre moteur", "crankshaft"],
        "xrefs": ["réducteur", "tachymètre", "moteur à 4 temps"],
        "origine": "suggest",
    },
    "culasse": {
        "definition": "Pièce qui ferme le haut du cylindre et abrite la chambre de combustion, les soupapes et la bougie. Sur le Rotax 912 de l'AT01, les culasses sont refroidies par liquide et les cylindres par air (refroidissement mixte). Sa température est surveillée en vol : elle doit rester dans le vert.",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["culasses", "tête de cylindre", "têtes de cylindre", "cylinder head"],
        "xrefs": ["température culasse", "température d'huile", "moteur à 4 temps"],
        "origine": "suggest",
    },
    "avionique": {
        "definition": "<em>Avionics</em>. Ensemble des équipements électroniques de bord : radios, transpondeur, GPS (Global Positioning System — système mondial de positionnement), instruments électroniques. Un interrupteur dédié (avionics master) les alimente ; on le met sur « off » au démarrage du moteur pour éviter les pointes de tension, puis sur « on » ensuite. Sur l'AT01, il se règle dans la check-list avant le roulage.",
        "categorie": "À classer",
        "famille": "commandes_cockpit",
        "variantes": ["avioniques", "avionics", "avionics master", "interrupteur avionique"],
        "xrefs": ["transpondeur", "fréquence", "alternateur", "disjoncteur"],
        "origine": "suggest",
    },
    "puissance maximale continue": {
        "definition": "<em>Maximum Continuous Power</em>. Puissance maximale que le moteur peut fournir sans limite de durée, plus faible que la puissance maximale au décollage qui n'est autorisée que quelques minutes. Sur le Rotax 912 S3 de l'AT01, le POH (Pilot's Operating Handbook — manuel d'utilisation du pilote (manuel de vol)) donne 92,5 hp à 2 260 tr/min en continu, contre 98,6 hp à 2 385 tr/min pendant 5 minutes maximum.",
        "categorie": "À classer",
        "famille": "parametres_moteur",
        "variantes": ["Maximum Continuous Power", "puissance continue", "MCP", "puissance continue maximale"],
        "xrefs": ["plein gaz", "tachymètre", "température culasse"],
        "origine": "suggest",
    },
    "pale": {
        "definition": "Élément de l'hélice : un petit profil d'aile en rotation, qui produit une portance dirigée vers l'avant, la traction. L'angle qu'elle fait avec le plan de rotation est le calage (le pas) : il détermine l'incidence vue par le profil selon le régime et la vitesse. Sur une hélice à régime constant, le régulateur modifie ce calage automatiquement.",
        "categorie": "À classer",
        "famille": "helice",
        "variantes": ["pales", "pale d'hélice", "pales d'hélice"],
        "contexte_requis": ["hélice", "calage", "profil", "portance", "traction", "rotation", "régime"],
        "xrefs": ["calage d'hélice", "hélice", "hélice à pas variable"],
        "origine": "suggest",
    },
    "facteur P": {
        "definition": "<em>P-factor</em>. Dissymétrie de traction de l'hélice quand son axe n'est pas aligné avec le vent relatif (assiette cabrée, basse vitesse, forte puissance) : la pale descendante voit une incidence plus grande que la pale montante, donc tire davantage. Il donne un lacet que l'on corrige au palonnier. Il est maximal au décollage ou à la remise de gaz, avec un risque de décrochage à basse hauteur.",
        "categorie": "À classer",
        "famille": "helice",
        "variantes": ["facteurs P", "effet de la pale descendante"],
        "xrefs": ["effet de couple", "couple gyroscopique", "effet gyroscopique", "décrochage"],
        "origine": "suggest",
    },
    "circuit pitot-statique": {
        "definition": "<em>Pitot-static system</em>. Ensemble formé de la prise de pression totale (tube de Pitot) et des prises de pression statique qui alimentent l'anémomètre (badin), l'altimètre et le variomètre. Une prise statique bouchée dérègle les trois instruments d'un coup : altimètre figé, variomètre à zéro, badin faux. Savoir reconnaître cette signature est un classique d'examen.",
        "categorie": "À classer",
        "famille": "instruments_anemobarometriques",
        "variantes": ["circuits pitot-statiques", "Pitot-static system", "système anémobarométrique", "pitot-statique", "système pitot-statique", "pitot-static"],
        "xrefs": ["tube de pitot", "prise statique", "blocage statique", "blocage Pitot"],
        "origine": "suggest",
    },
    "VHF": {
        "definition": "<em>Very High Frequency</em> — « très haute fréquence ». Bande de fréquences de 30 à 300 MHz. En aviation, la radiotéléphonie air-sol utilise 118 à 136,975 MHz (portée liée à la vue directe, donc à l'altitude), et la radionavigation, avec le VOR (VHF Omnidirectional Range — radiophare omnidirectionnel VHF) et l'ILS (Instrument Landing System — système d'atterrissage aux instruments), utilise 108 à 117,95 MHz. La fréquence de détresse VHF est 121,5 MHz.",
        "categorie": "À classer",
        "famille": "radio_phraseologie",
        "variantes": ["Very High Frequency", "très haute fréquence", "radio VHF", "bande VHF"],
        "xrefs": ["fréquence", "121,5 MHz", "vor", "canal 8,33 kHz"],
        "origine": "suggest",
    },
    "ATA": {
        "definition": "<em>Actual Time of Arrival</em> — « heure d'arrivée réelle ». Heure réelle d'arrivée au point de report ou à destination, relevée pendant le vol. On la compare à l'ETA (Estimated Time of Arrival — heure estimée d'arrivée ; heure estimée) pour recaler la navigation et réestimer la suite du vol. L'écart entre l'ATA et l'ETA révèle un écart de vitesse sol par rapport à l'estimation.",
        "categorie": "À classer",
        "famille": "heures_estimations",
        "variantes": ["Actual Time of Arrival", "heure d'arrivée réelle"],
        "xrefs": ["eta", "eet", "GS"],
        "origine": "suggest",
    },
    "isogone": {
        "definition": "Ligne de la carte qui relie les points où la déclinaison magnétique (variation) est la même. La carte aéronautique en trace avec la valeur et l'année de validité : on y lit la variation pour passer des routes vraies aux routes magnétiques. Elle évolue lentement, d'où l'année de mise à jour.",
        "categorie": "À classer",
        "famille": "references_magnetiques",
        "variantes": ["isogones", "ligne isogone", "lignes isogones"],
        "xrefs": ["compas magnétique", "nord compas", "cap compas", "rose des vents"],
        "origine": "suggest",
    },
    "niveau moyen de la mer": {
        "definition": "<em>Mean Sea Level</em>. Surface de référence moyenne des océans à partir de laquelle on mesure l'altitude. L'altitude lue avec le QNH calé est une hauteur au-dessus du niveau moyen de la mer (AMSL — Above Mean Sea Level — altitude au-dessus du niveau moyen de la mer). La pression « ramenée au niveau de la mer » (QNH) et les performances en atmosphère standard (ISA — International Standard Atmosphere) font aussi référence à ce niveau.",
        "categorie": "À classer",
        "famille": "references_verticales",
        "variantes": ["Mean Sea Level", "MSL"],
        "xrefs": ["AMSL", "QNH", "altitude", "atmosphère standard"],
        "origine": "suggest",
    },
    "organisme de formation": {
        "definition": "<em>Approved Training Organisation / Declared Training Organisation</em> — « organisme de formation agréé / déclaré ». Structure qui dispense la formation au pilotage. L'ATO (Approved Training Organisation — organisme de formation agréé) est un organisme de formation agréé par l'autorité ; le DTO (Declared Training Organisation — organisme de formation déclaré) est un organisme de formation simplement déclaré, comme un aéroclub ou une école. La théorie et la pratique du PPL (Private Pilot Licence — licence de pilote privé) se préparent dans l'un ou l'autre.",
        "categorie": "À classer",
        "famille": "equipage_formation",
        "variantes": ["ATO", "DTO", "ATO / DTO", "Approved Training Organisation", "Declared Training Organisation", "organisme de formation agréé", "organisme de formation déclaré"],
        "contexte_requis": ["formation", "organisme", "ppl", "théorie", "aéroclub", "école", "examen"],
        "xrefs": ["ppl", "commandant de bord", "certificat médical"],
        "origine": "suggest",
    },
    "certificat acoustique": {
        "definition": "Document qui atteste le niveau de bruit de l'aéronef. Il fait partie des documents à bord, avec le certificat d'immatriculation, le certificat de navigabilité, la licence de station d'aéronef et l'assurance. Il ne faut pas le confondre avec le certificat de navigabilité, qui atteste l'aptitude au vol.",
        "categorie": "À classer",
        "famille": "documents_bord",
        "variantes": ["certificats acoustiques"],
        "xrefs": ["certificat de navigabilité", "certificat d'immatriculation", "licence de station d'aéronef", "assurance"],
        "origine": "suggest",
    },
    "voltige": {
        "definition": "Enchaînement de manœuvres intentionnelles à assiette, inclinaison ou accélération anormales (boucle, tonneau, renversement). Elle exige une certification et une qualification particulières ; elle est interdite sur l'AT01, dont le POH (Pilot's Operating Handbook — manuel d'utilisation du pilote (manuel de vol)) interdit la voltige et les vrilles. Un virage de plus de 60° d'inclinaison est déjà hors du domaine normal.",
        "categorie": "À classer",
        "famille": "regles_vol",
        "variantes": ["voltiges", "acrobatie", "acrobaties"],
        "xrefs": ["vrille", "facteur de charge limite", "catégorie voltige"],
        "origine": "suggest",
    },
    "corde aérodynamique moyenne": {
        "definition": "<em>Mean Aerodynamic Chord</em>. Corde moyenne de l'aile, qui sert de référence pour exprimer la position du centre de gravité. Sur l'AT01, la plage de centrage s'exprime en pourcentage de la MAC (Mean Aerodynamic Chord — corde aérodynamique moyenne) : de 31 % à l'avant à 40 % à l'arrière. Elle permet de comparer le centrage de l'avion avec la limite avant et arrière.",
        "categorie": "À classer",
        "famille": "structure_aile",
        "variantes": ["cordes aérodynamiques moyennes", "Mean Aerodynamic Chord", "MAC"],
        "xrefs": ["centre de gravité", "limites de centrage", "corde", "enveloppe de centrage"],
        "origine": "suggest",
    },
    "aviation générale": {
        "definition": "<em>GA</em>. Ensemble de l'aviation civile hors transport aérien commercial réglementé : vols de loisir, écoles, aéroclubs, vols privés et travail aérien. Les vols du pilote privé relèvent de l'aviation générale non commerciale, régie par le règlement UE (Union européenne) 965/2012 (Part-NCO). Sur le plan de vol, la lettre G indique un vol d'aviation générale (case 8).",
        "categorie": "À classer",
        "famille": "regles_vol",
        "variantes": ["aviations générales", "general aviation", "aviation générale non commerciale"],
        "contexte_requis": ["pilote", "vol", "avion", "aéroclub", "commercial", "accident", "part-nco"],
        "xrefs": ["plan de vol", "commandant de bord"],
        "origine": "suggest",
    },
    "POB": {
        "definition": "<em>Persons On Board</em> — « personnes à bord ». Nombre total de personnes à bord, équipage compris, qui doit figurer sur le plan de vol (case 19) et que l'ATC (Air Traffic Control — contrôle de la circulation aérienne) ou les secours peuvent demander (« confirmez POB »). Il sert à dimensionner la recherche et le sauvetage en cas de problème. On répond clairement par le chiffre exact.",
        "categorie": "À classer",
        "famille": "documents_bord",
        "variantes": ["Persons On Board", "personnes à bord", "nombre de personnes à bord"],
        "xrefs": ["plan de vol", "autonomie", "ELT", "plan de vol déposé"],
        "origine": "suggest",
    },
    "conditions givrantes": {
        "definition": "<em>Icing conditions</em>. Conditions dans lesquelles du givre peut se former en vol : humidité visible (nuage, pluie, bruine) et température proche ou inférieure à 0 °C, avec de l'eau surfondue. Le POH (Pilot's Operating Handbook — manuel d'utilisation du pilote (manuel de vol)) de l'AT01 interdit le vol volontaire dans ces conditions : l'avion n'est pas certifié, même avec un pitot chauffé. On se détourne ou on descend vers une zone plus chaude.",
        "categorie": "À classer",
        "famille": "givrage",
        "variantes": ["Icing conditions", "conditions de givrage", "conditions givrantes connues"],
        "xrefs": ["givrage en vol", "surfusion", "antigivrage", "givrage mixte"],
        "origine": "suggest",
    },
    "certification": {
        "definition": "Démarche par laquelle une autorité, en Europe l'EASA (European Union Aviation Safety Agency — Agence de l'Union européenne pour la sécurité aérienne), vérifie qu'un type d'aéronef, de moteur ou d'hélice respecte les spécifications de navigabilité (CS — Certification Specifications — spécifications de certification), puis délivre le certificat de type. Les limites du manuel de vol (masse, vitesses, conditions d'emploi) sont celles démontrées lors de cette certification. Un avion « non certifié pour le vol en conditions givrantes » ne doit pas y être engagé, même avec un pitot chauffé.",
        "categorie": "À classer",
        "famille": "regles_vol",
        "variantes": ["certification de type"],
        "xrefs": ["certificat de navigabilité", "vent de travers démontré"],
        "origine": "suggest",
    },
    "incursion sur piste": {
        "definition": "<em>Runway Incursion</em>. Présence incorrecte d'un aéronef, d'un véhicule ou d'une personne sur l'aire protégée d'une piste, même sans collision (définition internationale). Elle vient souvent d'une clairance mal comprise ou d'une entrée sur la piste sans autorisation. On l'évite en collationnant, en restant au point d'attente tant que l'autorisation n'est pas explicite et en sachant que « alignez-vous et attendez » n'est jamais « décollez ».",
        "categorie": "À classer",
        "famille": "pistes",
        "variantes": ["incursions sur piste", "Runway Incursion", "incursion de piste", "incursions de piste"],
        "xrefs": ["point d'attente", "collationnement clairance", "alignement"],
        "origine": "suggest",
    },
    "AIRPROX": {
        "definition": "<em>Aircraft Proximity</em> — « rapprochement dangereux ». Mot-code utilisé pour qualifier une situation où la distance entre deux aéronefs, leur position relative ou leur vitesse relative ont pu compromettre la sécurité. Le pilote ou le contrôleur dépose un compte rendu AIRPROX auprès des services concernés, dans une logique de retour d'expérience et non de sanction. Il est distinct d'une collision évitée de justesse ; il sert à apprendre.",
        "categorie": "À classer",
        "famille": "regles_vol",
        "variantes": ["Aircraft Proximity", "rapprochement dangereux", "compte rendu AIRPROX"],
        "origine": "suggest",
    },
    "perte de contrôle en vol": {
        "definition": "<em>Loss Of Control In-flight</em>. Situation où le pilote n'est plus maître de la trajectoire ou de l'attitude de l'avion ; c'est l'une des premières causes d'accidents mortels en aviation légère. Elle suit typiquement un décrochage ou une vrille à basse hauteur (virage serré en base-finale), une désorientation spatiale en conditions dégradées, ou un mauvais réglage de commande. On la prévient en gardant la vitesse, l'incidence et l'inclinaison dans les limites.",
        "categorie": "À classer",
        "famille": "decrochages",
        "variantes": ["Loss Of Control In-flight", "perte de maîtrise", "perte de contrôle", "LOC-I", "loss of control"],
        "xrefs": ["décrochage", "décrochage en virage", "désorientation spatiale"],
        "origine": "suggest",
    },
    "amerrissage": {
        "definition": "<em>Ditching</em>. Atterrissage forcé sur l'eau. On l'évite quand c'est possible : la survie dépend de la ceinture, du gilet et de la sortie rapide. Si la panne survient en vol, on choisit un lieu proche d'un secours, on ouvre la porte avant l'impact et on évacue sans tarder.",
        "categorie": "À classer",
        "famille": "pannes_moteur",
        "variantes": ["atterrissage sur l'eau", "amerrir", "ditching", "amerrissage forcé"],
        "xrefs": ["atterrissage forcé", "atterrissage de précaution", "panne moteur", "ELT"],
        "origine": "suggest",
    },
    "fovéa": {
        "definition": "Zone centrale de la rétine, riche en cônes, qui donne la vision détaillée et colorée sur un champ très petit. En dehors d'elle, la vision périphérique repère les mouvements mais pas le détail ; d'où l'intérêt du balayage visuel. La nuit, on regarde un peu à côté d'un objet pour le voir avec les bâtonnets.",
        "categorie": "À classer",
        "famille": "physiologie",
        "variantes": ["fovéas", "fovéal"],
        "xrefs": ["tache aveugle", "vision nocturne"],
        "origine": "suggest",
    },
    "éblouissement": {
        "definition": "Perte momentanée de la vision causée par une lumière trop forte (soleil bas, phares, éclairs). Il est dangereux au décollage et à l'atterrissage, notamment dans l'axe du soleil. On le limite avec des lunettes de soleil de bonne qualité et en gardant la verrière propre.",
        "categorie": "À classer",
        "famille": "physiologie",
        "variantes": ["éblouissements"],
        "xrefs": ["vision nocturne"],
        "origine": "suggest",
    },
    "minima personnels": {
        "definition": "<em>Personal minimums</em>. Limites que le pilote se fixe lui-même, plus strictes que la réglementation : plafond, visibilité, vent de travers, expérience récente. On les décide au sol, à froid, pour ne pas les négocier en vol sous la pression. Elles protègent contre le biais de continuation du plan et le get-there-itis.",
        "categorie": "À classer",
        "famille": "fh_prise_de_decision",
        "variantes": ["Personal minimums", "limites personnelles", "minimum personnel"],
        "xrefs": ["get-there-itis", "minima", "plan continuation bias"],
        "origine": "suggest",
    },
    "illusion de Coriolis": {
        "definition": "Illusion vestibulaire provoquée par un mouvement de tête pendant un virage prolongé, qui stimule plusieurs canaux semi-circulaires à la fois : sensation soudaine de rotation ou de chute, vertige, désorientation. On l'évite en gardant la tête immobile en virage serré et en préparant la carte avant. Elle est surtout redoutable sans repère extérieur, de nuit ou en IMC (Instrument Meteorological Conditions — conditions météorologiques de vol aux instruments).",
        "categorie": "À classer",
        "famille": "facteurs_humains_physiologie",
        "variantes": ["illusions de Coriolis", "effet Coriolis vestibulaire"],
        "xrefs": ["oreille interne", "illusion somatogyrale", "désorientation spatiale", "force de Coriolis"],
        "origine": "suggest",
    },
    "trompe d'Eustache": {
        "definition": "Petit canal qui relie l'oreille moyenne au fond de la gorge et égalise la pression de part et d'autre du tympan. En montée, l'air sort seul ; en descente, il faut le faire entrer (déglutir, bâiller ou manœuvre de Valsalva). Un rhume la bloque : douleur, voire otite barotraumatique.",
        "categorie": "À classer",
        "famille": "facteurs_humains_physiologie",
        "variantes": ["trompes d'Eustache", "trompe auditive"],
        "xrefs": ["otite barotraumatique", "oreille interne"],
        "origine": "suggest",
    },
    "TUC": {
        "definition": "<em>Time of Useful Consciousness</em> — « temps utile de conscience ». Durée entre le moment où l'organisme manque d'oxygène (altitude trop haute, décompression) et celui où le pilote n'est plus capable d'agir efficacement. Elle raccourcit vite avec l'altitude : environ 20 à 30 minutes à 18 000 ft, 3 à 5 minutes à 25 000 ft (FAA — Federal Aviation Administration — autorité de l'aviation civile américaine). L'hypoxie donne euphorie et jugement altéré, d'où l'intérêt d'agir tôt.",
        "categorie": "À classer",
        "famille": "physiologie",
        "variantes": ["Time of Useful Consciousness", "temps utile de conscience", "temps de conscience utile"],
        "xrefs": ["hypoxie", "hyperventilation", "monoxyde de carbone", "altitude"],
        "origine": "suggest",
    },
    "spirale engagée": {
        "definition": "<em>Graveyard spiral</em>. Virage de plus en plus incliné avec descente de plus en plus rapide que le pilote ne perçoit pas, car un roulis lent reste sous le seuil de détection des canaux semi-circulaires (environ 2°/s). La vitesse augmente, la sensation est celle d'un vol à plat. On la sort en remettant d'abord les ailes à plat, puis en rétablissant l'assiette.",
        "categorie": "À classer",
        "famille": "physiologie",
        "variantes": ["spirales engagées", "Graveyard spiral", "spirale de la mort"],
        "xrefs": ["illusion somatogyrale", "désorientation spatiale"],
        "origine": "suggest",
    },
    "système vestibulaire": {
        "definition": "Ensemble de l'oreille interne qui détecte l'équilibre : trois canaux semi-circulaires pour les rotations et les otolithes pour les accélérations linéaires et l'inclinaison par rapport à la pesanteur. Sans repère visuel, il donne des informations trompeuses (illusions somatogyrale, somatogravique, Coriolis). On s'en défie en volant aux instruments.",
        "categorie": "À classer",
        "famille": "facteurs_humains_physiologie",
        "variantes": ["vestibulaire", "appareil vestibulaire"],
        "xrefs": ["oreille interne", "illusion somatogyrale", "illusion somatogravique", "désorientation spatiale"],
        "origine": "suggest",
    },
    "tunnélisation attentionnelle": {
        "definition": "Focalisation excessive de l'attention sur un seul élément (un instrument, un problème, un objectif) au détriment du reste de la situation. Le pilote ne perçoit plus d'informations pourtant importantes : trafic, altitude, carburant, évolution météo. Le stress, la charge de travail et la fatigue la favorisent ; on la combat par le balayage, les check-lists et le partage des tâches.",
        "categorie": "À classer",
        "famille": "fh_modeles_et_biais",
        "variantes": ["fixation attentionnelle", "tunnel attentionnel", "tunnélisation", "tunnélisation de l'attention"],
        "xrefs": ["conscience de la situation", "complaisance", "fatigue"],
        "origine": "suggest",
    },
    "manœuvre de Valsalva": {
        "definition": "Manœuvre d'équilibrage des oreilles : on pince le nez, bouche fermée, et on souffle doucement pour faire entrer l'air dans l'oreille moyenne par les trompes d'Eustache. Elle sert surtout en descente, quand la pression extérieure remonte. Elle est impossible, et le blocage douloureux, si les trompes sont obstruées par un rhume.",
        "categorie": "À classer",
        "famille": "facteurs_humains_physiologie",
        "variantes": ["manœuvres de Valsalva", "équilibrage des oreilles", "Valsalva", "manoeuvre de Valsalva"],
        "xrefs": ["otite barotraumatique", "oreille interne"],
        "origine": "suggest",
    },
    "balayage visuel": {
        "definition": "Technique de recherche visuelle du trafic : le regard parcourt le ciel par petits secteurs successifs d'environ 10°, en s'arrêtant 1 à 2 secondes sur chacun, car seule la fovéa donne une image nette sur un champ très étroit. Un avion sur trajectoire de collision paraît immobile dans le pare-brise : c'est un signal à ne pas manquer. On alterne extérieur et instruments.",
        "categorie": "À classer",
        "famille": "facteurs_humains_physiologie",
        "variantes": ["balayages visuels", "scan visuel", "balayage extérieur"],
        "xrefs": ["conscience de la situation"],
        "origine": "suggest",
    },
    "état indésirable de l'aéronef": {
        "definition": "<em>Undesired Aircraft State</em>. Dans le modèle TEM (Threat and Error Management), situation non voulue de l'avion (écart de trajectoire, de vitesse, de configuration) qui réduit les marges de sécurité. Elle résulte d'une menace ou d'une erreur mal gérée. Si on la détecte et la corrige à temps, elle ne devient pas incident ou accident.",
        "categorie": "À classer",
        "famille": "fh_prise_de_decision",
        "variantes": ["Undesired Aircraft State", "UAS", "état indésirable", "états indésirables"],
        "xrefs": ["tem", "menace", "erreur", "chaîne des erreurs"],
        "origine": "suggest",
    },
    "vent nul": {
        "definition": "Absence de vent ou vent calme, que le METAR (Meteorological Aerodrome Report — message d'observation météorologique d'aérodrome) note 00000KT. C'est le cas de référence des tableaux de performances et des calculs « sans vent » (no-wind) : distance de décollage ou de croisière sans composante de vent. Il sert de point de départ pour corriger ensuite d'un vent de face ou arrière.",
        "categorie": "À classer",
        "famille": "description_vent",
        "variantes": ["vents nuls", "no-wind", "no wind", "vent calme"],
        "contexte_requis": ["sol", "calme", "metar", "cavok", "performances", "décollage", "composante", "calcul"],
        "xrefs": ["composante de face", "distance de roulement", "girouette"],
        "origine": "suggest",
    },
    "vent moyen": {
        "definition": "Vent mesuré en moyenne sur les 10 minutes qui précèdent l'observation METAR (Meteorological Aerodrome Report — message d'observation météorologique d'aérodrome ; direction et vitesse), sans les rafales ni les variations. C'est la valeur de base du calcul de la composante de travers ; on ajoute l'effet des rafales séparément (travers moyen, travers rafale).",
        "categorie": "À classer",
        "famille": "description_vent",
        "variantes": ["vents moyens", "vent moyen sur 10 minutes", "vent moyen de surface"],
        "xrefs": ["rafale", "composante de travers", "METAR", "girouette"],
        "origine": "suggest",
    },
    "glissade": {
        "definition": "<em>slip</em>. Mouvement où l'avion glisse latéralement vers l'intérieur d'un virage, ou volontaire en ligne droite : aile basse côté vent et palonnier opposé pour garder l'axe. On l'emploie en approche par vent de travers (méthode de l'aile basse) ou pour perdre de la hauteur sans prendre de vitesse, car la traînée augmente. La bille est du côté de l'aile basse.",
        "categorie": "À classer",
        "famille": "virages",
        "variantes": ["glissades", "slip", "glissade aile basse"],
        "contexte_requis": ["aile basse", "palonnier", "vent", "travers", "bille", "slip"],
        "xrefs": ["décrabage", "composante de travers", "vent traversier"],
        "origine": "suggest",
    },
    "puissance nécessaire": {
        "definition": "Puissance qu'il faut fournir pour maintenir le vol horizontal stabilisé à une vitesse donnée : P ≈ traînée × vitesse. Elle est la somme de la traînée parasite (qui croît comme V³) et de la traînée induite (qui décroît comme 1/V), ce qui dessine une courbe en crochet. Son minimum est la puissance minimale (endurance maximale), distinct du minimum de traînée.",
        "categorie": "À classer",
        "famille": "trainee",
        "variantes": ["puissances nécessaires", "puissance requise", "courbe de puissance nécessaire"],
        "xrefs": ["puissance minimale", "traînée parasite", "second régime", "traînée induite"],
        "origine": "suggest",
    },
    "puissance disponible": {
        "definition": "Puissance que le groupe motopropulseur (moteur + hélice) peut fournir à une vitesse et une altitude données ; elle diminue avec l'altitude pour un moteur atmosphérique. Comparée à la puissance nécessaire au vol palier, l'excédent donne la capacité de monter : taux de montée = excédent de puissance / poids. À l'extrême, l'écart nul définit le plafond de sustentation.",
        "categorie": "À classer",
        "famille": "trainee",
        "variantes": ["puissances disponibles", "puissance utile", "courbe de puissance disponible"],
        "xrefs": ["puissance minimale", "taux de montée", "plafond de sustentation"],
        "origine": "suggest",
    },
    "densité": {
        "definition": "Pour l'air, masse par unité de volume (environ 1,225 kg/m³ au niveau de la mer en atmosphère standard) : elle diminue avec l'altitude et la chaleur, et elle conditionne la portance, la traction de l'hélice et la puissance d'un moteur atmosphérique. Pour le carburant, la densité (environ 0,72 kg/l pour la planification) permet de convertir litres et kilos dans le calcul de masse et centrage. Une altitude-densité élevée dégrade tout : roulement long, montée faible.",
        "categorie": "À classer",
        "famille": "couches_atmospheriques",
        "variantes": ["densités", "masse volumique", "densité de l'air", "densité du carburant"],
        "contexte_requis": ["air", "carburant", "kg/l", "altitude", "isa", "masse volumique", "portance"],
        "xrefs": ["altitude-densité", "erreur de densité", "carburant utilisable", "atmosphère standard"],
        "origine": "suggest",
    },
    "règle des tiers": {
        "definition": "Estimation mentale de la composante de travers à partir de l'angle entre le vent et la piste : de 0 à 30°, un tiers du vent ; de 30 à 60°, deux tiers ; de 60 à 90°, la totalité. Exemple : 15 kt à 45° donnent environ 10 kt de travers. On la compare à la limite démontrée de l'avion.",
        "categorie": "À classer",
        "famille": "composantes_vent",
        "variantes": ["règles des tiers", "règle des 1/3 2/3"],
        "xrefs": ["composante de travers", "vent de travers démontré", "décrabage", "composante de face"],
        "origine": "suggest",
    },
    "dérapage": {
        "definition": "<em>skid</em>. Mouvement où l'avion glisse latéralement vers l'extérieur du virage : la bille de l'indicateur de virage part vers l'extérieur et le vent relatif arrive de côté. C'est le résultat d'un excès de palonnier dans le virage ou d'une inclinaison trop faible. À basse hauteur, sur la base-finale, il peut déclencher le décrochage d'une aile puis la vrille ; on corrige en appuyant sur le palonnier du côté de la bille.",
        "categorie": "À classer",
        "famille": "virages",
        "variantes": ["dérapages", "skid"],
        "contexte_requis": ["palonnier", "bille", "virage", "vrille", "skid", "vent relatif"],
        "xrefs": ["décrochage en virage", "indicateur de virage", "coordinateur de virage"],
        "origine": "suggest",
    },
    "levier d'hélice": {
        "definition": "<em>Propeller control lever</em>. Commande qui règle le régime de l'hélice à travers le régulateur. Sur l'AT01, le levier bleu vers l'avant donne le petit pas (position « start », régime élevé) et vers l'arrière le gros pas (régime bas). Il agit en plus de la manette des gaz, qui règle la pression d'admission.",
        "categorie": "À classer",
        "famille": "commandes_cockpit",
        "variantes": ["Propeller control lever", "commande d'hélice", "levier bleu"],
        "xrefs": ["hélice à pas variable", "calage d'hélice", "plein gaz", "manette"],
        "origine": "suggest",
    },
    "ASFC": {
        "definition": "<em>Above Surface</em> — « au-dessus de la surface ». Hauteur au-dessus de la surface survolée, sol ou eau. On la rencontre dans les minima VFR (Visual Flight Rules — vol à vue) du SERA (Standardised European Rules of the Air — règles de l'air européennes standardisées), par exemple 1 000 ft ASFC. C'est l'équivalent pratique de l'AGL (Above Ground Level — hauteur au-dessus du sol), avec la surface d'eau en plus ; ne pas la confondre avec l'AMSL (Above Mean Sea Level — altitude au-dessus du niveau moyen de la mer), altitude au-dessus du niveau moyen de la mer.",
        "categorie": "À classer",
        "famille": "references_verticales",
        "variantes": ["Above Surface", "hauteur au-dessus de la surface", "ft ASFC"],
        "xrefs": ["agl", "AAL", "AMSL", "distance aux nuages"],
        "origine": "suggest",
    },
    "minimum fuel": {
        "definition": "<em>carburant minimal</em>. Expression radio qui prévient l'ATC (Air Traffic Control — contrôle de la circulation aérienne) qu'on ne peut plus accepter de retard : le carburant est limité, sans être encore une urgence. Elle précède le message « mayday fuel » si la situation empire. On la passe tôt, au lieu d'attendre la dernière marge.",
        "categorie": "À classer",
        "famille": "radio_phraseologie",
        "variantes": ["carburant minimal", "carburants minimaux"],
        "xrefs": ["mayday", "PAN PAN", "autonomie", "réserve finale"],
        "origine": "suggest",
    },
    "NSC": {
        "definition": "<em>No Significant Cloud</em> — « pas de nuage significatif ». Code METAR (Meteorological Aerodrome Report — message d'observation météorologique d'aérodrome)/TAF (Terminal Aerodrome Forecast — prévision d'aérodrome) qui signifie qu'il n'y a pas de nuage significatif : aucun nuage sous 5 000 ft (ou sous l'altitude minimale de secteur si plus haute), ni CB (Cumulonimbus) ni TCU (Towering Cumulus — cumulus congestus). On l'emploie quand le CAVOK (Ceiling And Visibility OK — plafond et visibilité OK) ne s'applique pas, par exemple avec une visibilité inférieure à 10 km. À ne pas confondre avec un ciel totalement dégagé.",
        "categorie": "À classer",
        "famille": "codes_meteo_etat",
        "variantes": ["No Significant Cloud", "pas de nuage significatif"],
        "contexte_requis": ["metar", "taf", "cavok", "nuage", "tcu", "plafond"],
        "xrefs": ["CAVOK", "BECMG", "plafond"],
        "origine": "suggest",
    },
    "CS-VLA": {
        "definition": "<em>Certification Specifications for Very Light Aeroplanes</em> — « spécifications de certification des avions très légers ». Spécifications de certification de l'EASA (European Union Aviation Safety Agency — Agence de l'Union européenne pour la sécurité aérienne) pour les avions très légers : un ou deux sièges, masse maximale au décollage de 750 kg, un seul moteur, vitesse de décrochage inférieure à 45 kt. L'AT01 y est certifié. Elles imposent notamment un avertisseur de décrochage et des limites de structure.",
        "categorie": "À classer",
        "famille": "regles_vol",
        "variantes": ["Certification Specifications for Very Light Aeroplanes", "avion très léger", "CS VLA"],
        "xrefs": ["avertisseur de décrochage", "facteur de charge limite", "vent de travers démontré"],
        "origine": "suggest",
    },
    "Part-NCO": {
        "definition": "<em>Non-Commercial Operations with other-than-complex motor-powered aircraft</em>. Partie du règlement (UE — Union européenne) n° 965/2012 qui fixe les règles de vol des aéronefs à moteur non complexes en exploitation non commerciale, donc l'aviation générale du pilote privé. Ses articles fixent les devoirs du commandant de bord, les procédures d'exploitation et les équipements ; l'un d'eux liste les documents à bord.",
        "categorie": "À classer",
        "famille": "regles_vol",
        "variantes": ["règles d'exploitation non commerciale", "NCO", "Part NCO", "NCO.GEN", "NCO.GEN.135"],
        "xrefs": ["commandant de bord"],
        "origine": "suggest",
    },
    "Part-MED": {
        "definition": "<em>exigences médicales</em>. Partie du règlement (UE — Union européenne) n° 1178/2011 qui fixe les exigences médicales des pilotes. Le certificat médical valide est obligatoire pour exercer les privilèges de la licence, y compris en solo. Pour le PPL (Private Pilot Licence — licence de pilote privé), le certificat médical de classe 2 est exigé ; le LAPL (Light Aircraft Pilot Licence — licence de pilote d'aéronef léger) admet un certificat médical spécifique.",
        "categorie": "À classer",
        "famille": "equipage_formation",
        "variantes": ["Part MED"],
        "xrefs": ["certificat médical", "certificat médical classe 2", "commandant de bord", "LAPL"],
        "origine": "suggest",
    },
    "Part-FCL": {
        "definition": "<em>licences des équipages</em>. Partie du règlement (UE — Union européenne) n° 1178/2011 qui fixe les conditions de délivrance des licences de pilote, dont le PPL (Private Pilot Licence — licence de pilote privé). Pour le PPL, 45 heures minimum d'instruction dont 25 en double commande et 10 en solo supervisé. Un article de cette partie impose au pilote d'avoir sur lui sa licence, son certificat médical valide et une pièce d'identité.",
        "categorie": "À classer",
        "famille": "equipage_formation",
        "variantes": ["Part FCL", "FCL"],
        "xrefs": ["certificat médical", "commandant de bord", "ppl", "licence"],
        "origine": "suggest",
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
