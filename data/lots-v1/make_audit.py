import json
import unicodedata

INDEX_PATH = "/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/INDEX-EXISTANT.json"
OUTPUT_PATH = "/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/AUDIT-nav-radio.json"

with open(INDEX_PATH, "r", encoding="utf-8") as f:
    existing_index = json.load(f)

# Normalize functions for matching
def clean_term(s):
    s = s.lower().strip()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.replace('-', '').replace(' ', '').replace(',', '').replace('.', '').replace('\'', '').replace('«', '').replace('»', '')
    if s.endswith('s') and len(s) > 3:
        s = s[:-1]
    return s

clean_index_set = {clean_term(x) for x in existing_index}

# List of ALL terms of interest mentioned in the prompt with their metadata
all_terms_of_interest = [
    # 1. Terre et coordonnées
    {
        "terme": "latitude",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Coordonnée géographique angulaire nord-sud essentielle pour le repérage sur carte",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "longitude",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Coordonnée géographique angulaire est-ouest essentielle pour le repérage sur carte",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "méridien",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Ligne de longitude constante reliant les pôles géographiques, servant de référence de direction",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "parallèle",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Cercle imaginaire parallèle à l'équateur reliant les points de même latitude",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "équateur",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Grand cercle terrestre de latitude 0° séparant les hémisphères nord et sud",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "grand cercle",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "moyenne",
        "justification": "Intersection de la surface terrestre avec un plan passant par son centre, chemin le plus court (orthodromie)",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "loxodromie",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "moyenne",
        "justification": "Trajectoire à cap constant coupant tous les méridiens sous le même angle",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "orthodromie",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "moyenne",
        "justification": "Chemin le plus court entre deux points à la surface de la terre (grand cercle)",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "mille nautique",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de distance aéronautique correspondant à une minute d'arc de grand cercle terrestre (1852 m)",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "minute d'arc",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "moyenne",
        "justification": "Unité de mesure d'angle de latitude ou longitude, une minute de latitude vaut un mille nautique",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "coordonnées géographiques",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Système de latitude et longitude permettant de positionner précisément un aéronef ou un point de report",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "projection Lambert",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Système de projection conique conforme standard utilisé pour les cartes de navigation OACI",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "projection Mercator",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Système de projection cylindrique utilisé notamment pour les régions équatoriales",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "échelle",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Rapport entre la distance mesurée sur la carte et la distance réelle sur le terrain (ex: 1/500 000)",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "déclinaison magnétique",
        "categorie": "Navigation",
        "famille": "references_magnetiques",
        "priorite": "haute",
        "justification": "Angle formé entre le nord vrai et le nord magnétique, variant géographiquement",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "inclinaison magnétique",
        "categorie": "Navigation",
        "famille": "compas_et_magnetisme",
        "priorite": "moyenne",
        "justification": "Angle que fait le champ magnétique terrestre avec le plan horizontal, créant des erreurs de virage au compas",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "nord vrai",
        "categorie": "Navigation",
        "famille": "references_magnetiques",
        "priorite": "haute",
        "justification": "Direction géographique du pôle Nord",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "nord magnétique",
        "categorie": "Navigation",
        "famille": "references_magnetiques",
        "priorite": "haute",
        "justification": "Direction indiquée par le pôle Nord magnétique vers lequel s'orientent les lignes de force",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "nord compas",
        "categorie": "Navigation",
        "famille": "compas_et_magnetisme",
        "priorite": "haute",
        "justification": "Direction indiquée par le compas de bord, influencée par la déclinaison et la déviation",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "déviation compas",
        "categorie": "Navigation",
        "famille": "compas_et_magnetisme",
        "priorite": "haute",
        "justification": "Angle formé entre le nord magnétique et le nord compas, dû aux perturbations magnétiques internes",
        "sous_domaine": "Terre et coordonnées"
    },
    {
        "terme": "courbe de déviation",
        "categorie": "Navigation",
        "famille": "compas_et_magnetisme",
        "priorite": "haute",
        "justification": "Tableau ou graphique de correction indiquant la déviation du compas magnétique pour chaque cap",
        "sous_domaine": "Terre et coordonnées"
    },

    # 2. Caps et routes
    {
        "terme": "cap vrai",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle entre le nord vrai et l'axe longitudinal de l'aéronef",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "cap magnétique",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle entre le nord magnétique et l'axe longitudinal de l'aéronef",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "cap compas",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle entre le nord compas et l'axe longitudinal de l'aéronef",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "route vraie",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle formé par le nord vrai et la route théorique ou réelle projetée au sol",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "route magnétique",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle formé par le nord magnétique et la route projetée au sol",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "route sol",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Trajectoire réelle suivie par l'aéronef par rapport au sol (somme vectorielle du cap et du vent)",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "dérive",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle formé entre l'axe longitudinal de l'aéronef et sa trajectoire sol, provoqué par le vent",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "angle de dérive",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Valeur angulaire de l'écart provoqué par l'effet du vent de travers",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "correction de dérive",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle à appliquer au cap (WCA) pour maintenir la route souhaitée en présence de vent",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "vent effectif",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Composante du vent parallèle à la route de l'aéronef, modifiant sa vitesse sol",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "vent traversier",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Composante du vent perpendiculaire à la route de l'aéronef, provoquant la dérive",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "triangle des vitesses",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Représentation vectorielle de la relation entre vitesse propre, vitesse sol, cap et vent",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "base de temps",
        "categorie": "Navigation",
        "famille": "heures_estimations",
        "priorite": "haute",
        "justification": "Calcul systématique des temps de vol inter-repères pour suivre l'estime",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "facteur de base",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Coefficient (60/Vp) permettant de calculer rapidement la dérive maximale et le temps de vol",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "règle du 1 en 60",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "moyenne",
        "justification": "Règle de calcul mental estimant l'erreur de cap (1 NM d'écart après 60 NM parcourus correspond à 1° d'écart)",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "radiale",
        "categorie": "Navigation",
        "famille": "navigation_satellitaire",
        "priorite": "haute",
        "justification": "Demi-droite orientée issue d'une station VOR définissant un relèvement magnétique particulier",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "relèvement",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle entre une direction de référence (nord vrai, magnétique ou compas) et la ligne de visée d'une station ou d'un amère",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "gisement",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Angle entre l'axe longitudinal de l'aéronef et la direction d'une station ou d'un repère",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "QDM",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Relèvement magnétique vers la station (cap magnétique à suivre pour aller vers la station sans vent)",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "QDR",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Relèvement magnétique depuis la station (radiale)",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "QTE",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "moyenne",
        "justification": "Relèvement vrai d'un aéronef par rapport à une station radiogoniométrique",
        "sous_domaine": "Caps et routes"
    },
    {
        "terme": "QUJ",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "moyenne",
        "justification": "Route vraie à suivre vers une station radiogoniométrique sans vent",
        "sous_domaine": "Caps et routes"
    },

    # 3. Navigation à l'estime
    {
        "terme": "estime",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Méthode de navigation consistant à déterminer sa position à partir du cap suivi, de la vitesse propre et du vent calculé",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "point tournant",
        "categorie": "Navigation",
        "famille": "points_navigation",
        "priorite": "haute",
        "justification": "Point de changement de cap prévu dans le log de navigation reliant deux branches",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "repère caractéristique",
        "categorie": "Navigation",
        "famille": "points_navigation",
        "priorite": "haute",
        "justification": "Élément du sol remarquable (ligne de chemin de fer, pont, lac) utilisé pour vérifier sa position",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "dérive constatée",
        "categorie": "Navigation",
        "famille": "navigation_caps_et_routes",
        "priorite": "haute",
        "justification": "Écart constaté visuellement par rapport à la route sol prévue",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "recalage",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Action de corriger sa position estimée et son heure d'arrivée estimée lors du passage vertical un repère identifié",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "dead reckoning",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "moyenne",
        "justification": "Terme anglais équivalent à la navigation à l'estime",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "log de navigation",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Feuille de route préparée contenant les routes, caps, altitudes, vents, vitesses et temps de vol estimés",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "journal de navigation",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Document de bord équivalent au log de navigation où le pilote note ses observations en vol",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "temps sans vent",
        "categorie": "Navigation",
        "famille": "heures_estimations",
        "priorite": "haute",
        "justification": "Temps théorique nécessaire pour parcourir une distance sans aucune composante de vent",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "temps estimé",
        "categorie": "Navigation",
        "famille": "heures_estimations",
        "priorite": "haute",
        "justification": "Temps calculé pour effectuer un trajet reliant deux repères caractéristiques",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "heure estimée",
        "categorie": "Navigation",
        "famille": "heures_estimations",
        "priorite": "haute",
        "justification": "Horaire prévu de passage à la verticale d'un repère ou d'un aérodrome",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "ETA",
        "categorie": "Navigation",
        "famille": "heures_estimations",
        "priorite": "haute",
        "justification": "Heure d'arrivée estimée (Estimated Time of Arrival)",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "ETD",
        "categorie": "Navigation",
        "famille": "heures_estimations",
        "priorite": "haute",
        "justification": "Heure estimée de départ (Estimated Time of Departure)",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "EOBT",
        "categorie": "Navigation",
        "famille": "heures_estimations",
        "priorite": "haute",
        "justification": "Heure estimée de mise en route ou de début de mouvement (Estimated Off-Block Time)",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "cheminement",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Technique de navigation à vue consistant à suivre une ligne continue du sol (autoroute, rivière, côte)",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "navigation à vue",
        "categorie": "Navigation",
        "famille": "navigation_termes",
        "priorite": "haute",
        "justification": "Navigation basée sur l'observation visuelle directe du sol par rapport à la carte",
        "sous_domaine": "Navigation à l'estime"
    },
    {
        "terme": "dernier point connu",
        "categorie": "Navigation",
        "famille": "points_navigation",
        "priorite": "moyenne",
        "justification": "Dernière position géographique certifiée de l'aéronef avant une perte de repères visuels",
        "sous_domaine": "Navigation à l'estime"
    },

    # 4. Altimétrie
    {
        "terme": "QNH",
        "categorie": "Altimétrie",
        "famille": "calages_altimetriques",
        "priorite": "haute",
        "justification": "Pression atmosphérique de la station ramenée au niveau moyen de la mer",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "QFE",
        "categorie": "Altimétrie",
        "famille": "calages_altimetriques",
        "priorite": "haute",
        "justification": "Pression atmosphérique au niveau d'un point de référence au sol, souvent l'aérodrome",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "QNE",
        "categorie": "Altimétrie",
        "famille": "calages_altimetriques",
        "priorite": "haute",
        "justification": "Hauteur lue à l'atterrissage lorsque l'altimètre est calé sur 1013,25 hPa",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "calage standard",
        "categorie": "Altimétrie",
        "famille": "calages_altimetriques",
        "priorite": "haute",
        "justification": "Calage barométrique universel calé sur la pression de 1013,25 hPa pour exprimer l'altitude sous forme de Flight Levels",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "1013,25 hPa",
        "categorie": "Altimétrie",
        "famille": "references_pression",
        "priorite": "haute",
        "justification": "Valeur de la pression atmosphérique standard au niveau de la mer en atmosphère standard (ISA)",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "altitude",
        "categorie": "Altimétrie",
        "famille": "references_verticales",
        "priorite": "haute",
        "justification": "Distance verticale d'un niveau ou d'un point par rapport au niveau moyen de la mer (calage QNH)",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "hauteur",
        "categorie": "Altimétrie",
        "famille": "references_verticales",
        "priorite": "haute",
        "justification": "Distance verticale d'un niveau ou d'un point par rapport à la surface du sol (calage QFE)",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "niveau de vol",
        "categorie": "Altimétrie",
        "famille": "references_verticales",
        "priorite": "haute",
        "justification": "Altitude de pression exprimée en centaines de pieds avec calage standard 1013,25 hPa",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "altitude-pression",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Altitude lue sur l'altimètre calé sur la pression standard 1013,25 hPa",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "altitude densité",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Altitude-pression corrigée des variations de température par rapport à l'atmosphère standard",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "altitude vraie",
        "categorie": "Altimétrie",
        "famille": "references_verticales",
        "priorite": "haute",
        "justification": "Altitude réelle au-dessus du niveau moyen de la mer, tenant compte des erreurs de température de l'air",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "altitude de transition",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Altitude à laquelle ou au-dessous de laquelle la position verticale d'un aéronef est exprimée en altitude",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "niveau de transition",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Niveau de vol le plus bas utilisable au-dessus de l'altitude de transition",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "couche de transition",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "moyenne",
        "justification": "Espace aérien compris entre l'altitude de transition (TA) et le niveau de transition (TL)",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "TA",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Transition Altitude, altitude sous laquelle le calage altimétrique est calé sur le QNH local",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "TL",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Transition Level, niveau de vol le plus bas au-dessus de la couche de transition",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "erreur altimétrique",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Écart de lecture dû à l'erreur instrumentale, de pression (calage) ou thermique",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "effet température sur l'altimètre",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Erreur de l'altimètre par température non standard (l'altimètre sous-estime l'altitude dans l'air chaud et la surestime dans l'air froid)",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "du chaud vers le froid, gare aux dégâts",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Règle mnémotechnique avertissant que le vol vers des zones froides à calage identique réduit la hauteur réelle",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "altitude minimale de sécurité",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Altitude minimale à respecter pour garantir un espacement vertical suffisant avec le relief",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "MSA",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Altitude minimale de secteur (Minimum Sector Altitude) assurant 1000 ft de marge de franchissement d'obstacles",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "MEF",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Maximum Elevation Figure, altitude maximale du relief indiquée par carré sur les cartes de navigation VFR OACI",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "MORA",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "moyenne",
        "justification": "Minimum Off-Route Altitude, altitude de sécurité hors route garantissant le franchissement d'obstacles",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "hauteur de survol",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Hauteur minimale réglementaire à respecter au-dessus des obstacles ou des agglomérations",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "500 ft",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Hauteur minimale réglementaire de survol au-dessus de toute personne ou obstacle en VFR (hors agglomération)",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "1000 ft agglomération",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Hauteur de survol minimale imposée au-dessus de certaines agglomérations ou rassemblements de personnes",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "AGL",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Above Ground Level, hauteur mesurée au-dessus du niveau du sol",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "AMSL",
        "categorie": "Altimétrie",
        "famille": "altimetrie_references",
        "priorite": "haute",
        "justification": "Above Mean Sea Level, altitude mesurée par rapport au niveau moyen de la mer",
        "sous_domaine": "Altimétrie"
    },
    {
        "terme": "QFU",
        "categorie": "Altimétrie",
        "famille": "calages_altimetriques",
        "priorite": "haute",
        "justification": "Orientation magnétique de la piste d'atterrissage exprimée en dizaines de degrés",
        "sous_domaine": "Altimétrie"
    },

    # 5. Instruments
    {
        "terme": "anémomètre",
        "categorie": "Instruments",
        "famille": "instruments_mesure",
        "priorite": "haute",
        "justification": "Instrument anémobarométrique affichant la vitesse de l'aéronef dans la masse d'air (badin)",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "altimètre",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Instrument anémobarométrique affichant l'altitude ou la hauteur de l'aéronef en fonction de la pression statique",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "variomètre",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Instrument anémobarométrique affichant la vitesse verticale de l'aéronef (taux de montée ou de descente)",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "horizon artificiel",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Instrument gyroscopique affichant l'attitude de l'aéronef en tangage et en roulis par rapport à l'horizon",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "conservateur de cap",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Instrument gyroscopique indicateur de direction qui doit être périodiquement recalé sur le compas magnétique",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "directionnel",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Terme aéronautique alternatif courant pour désigner le conservateur de cap",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "compas magnétique",
        "categorie": "Instruments",
        "famille": "compas_et_magnetisme",
        "priorite": "haute",
        "justification": "Instrument autonome indiquant le nord magnétique de bord, soumis aux erreurs de virage et d'accélération",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "bille",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Indicateur physique de symétrie du vol (bille au milieu pour un vol coordonné)",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "indicateur de virage",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Instrument combinant un gyroscope mesurant le taux de virage et une bille mesurant la symétrie",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "coordinateur de virage",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Évolution de l'indicateur de virage sensible à la fois au taux de lacet et au taux de roulis",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "gyroscope",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Organe mécanique rotatif dont les propriétés d'inertie et de précession sont exploitées dans les instruments de bord",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "prise statique",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Orifice mesurant la pression atmosphérique ambiante extérieure, nécessaire au fonctionnement de l'altimètre, variomètre et anémomètre",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "prise dynamique",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Prise d'air de Pitot mesurant la pression totale (pression dynamique + pression statique) pour l'anémomètre",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "prise Pitot",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Autre désignation de l'entrée de pression dynamique (tube de Pitot)",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "tube de Pitot",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Sonde orientée face au vent relatif mesurant la pression dynamique utile au calcul de la vitesse propre",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "réchauffage Pitot",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Système de chauffage électrique de la sonde Pitot prévenant ou éliminant l'accumulation de givre",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "blocage Pitot",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Dysfonctionnement majeur où le blocage de la pression dynamique fige ou fausse les indications de vitesse de l'anémomètre",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "blocage statique",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Dysfonctionnement bloquant l'altimètre et le variomètre, et faussant l'anémomètre",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "alternat",
        "categorie": "Instruments",
        "famille": "instruments_pression",
        "priorite": "haute",
        "justification": "Prise statique de secours ou sélecteur alternatif en cas d'obstruction de la prise principale",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "erreurs gyroscopiques",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Erreurs de lecture des instruments gyroscopiques dues au frottement ou à la précession",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "précession",
        "categorie": "Instruments",
        "famille": "instruments_gyroscopiques",
        "priorite": "haute",
        "justification": "Propriété du gyroscope provoquant un décalage angulaire de l'axe de rotation sous l'effet d'une force externe",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "transpondeur",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Émetteur-récepteur radar secondaire permettant au contrôle d'identifier et de suivre l'altitude de l'aéronef",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "mode A",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Mode de transpondeur transmettant uniquement le code d'identification à quatre chiffres (Squawk)",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "mode C",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Mode de transpondeur transmettant le code d'identification plus l'altitude-pression (alticodage)",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "mode S",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Mode de transpondeur transmettant l'identité unique de l'appareil, le code et l'altitude précise",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "code 7500",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Code transpondeur d'urgence international signalant une intervention illicite à bord (détournement)",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "code 7600",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Code transpondeur d'urgence international signalant une panne de radiocommunication",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "code 7700",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Code transpondeur d'urgence international signalant une situation de détresse générale",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "7000 (VFR)",
        "categorie": "Instruments",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Code transpondeur standard utilisé en vol VFR en espace non contrôlé en Europe",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "ELT",
        "categorie": "Instruments",
        "famille": "instruments_mesure",
        "priorite": "haute",
        "justification": "Emergency Locator Transmitter, balise de détresse à déclenchement automatique ou manuel émettant sur 121.5 et 406 MHz",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "GPS",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "haute",
        "justification": "Global Positioning System, système par satellites permettant la localisation tridimensionnelle précise",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "RNAV",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "moyenne",
        "justification": "Navigation de zone (Area Navigation) permettant l'utilisation de trajectoires définies par des capteurs multiples",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "VOR",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "haute",
        "justification": "VHF Omnidirectional Range, radioalignement omnidirectionnel au sol permettant de définir des radiales mag",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "NDB",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "haute",
        "justification": "Non-Directional Beacon, radiophare omnidirectionnel au sol fonctionnant en BF/MF",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "ADF",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "haute",
        "justification": "Automatic Direction Finder, récepteur automatique à bord indiquant le gisement ou relèvement magnétique d'un NDB",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "DME",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "haute",
        "justification": "Distance Measuring Equipment, équipement de mesure de distance oblique par rapport à une station sol",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "ILS",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "haute",
        "justification": "Instrument Landing System, système d'approche de précision composé du Localizer et du Glide Path",
        "sous_domaine": "Instruments"
    },
    {
        "terme": "marqueur",
        "categorie": "Instruments",
        "famille": "instruments_radionavigation",
        "priorite": "moyenne",
        "justification": "Balise radioélectrique verticale (Marker Beacon) indiquant la distance sur l'axe d'approche ILS (Outer/Middle/Inner Marker)",
        "sous_domaine": "Instruments"
    },

    # 6. Radio et phraséologie
    {
        "terme": "indicatif",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Identifiant d'une station aéronautique ou d'un aéronef pour les radiocommunications",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "collationner",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Répéter des instructions de sécurité critiques transmises par le contrôleur (ex: calages, pistes, clairances)",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "accusé de réception",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Message radio confirmant qu'une transmission a été reçue et comprise",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "message d'urgence",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Message de priorité élevée concernant la sécurité d'un aéronef ou d'une personne à bord sans détresse immédiate",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "MAYDAY",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Signal radio international de détresse de priorité absolue, répété trois fois",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "PAN PAN",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Signal de radiotéléphonie international répété trois fois indiquant un message d'urgence",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "détresse",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Situation de menace grave et imminente nécessitant une assistance immédiate",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "urgence",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Situation concernant la sécurité d'un aéronef mais n'exigeant pas d'assistance immédiate",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "alphabet OACI",
        "categorie": "Radio & phraséologie",
        "famille": "alphabet_oaci",
        "priorite": "haute",
        "justification": "Alphabet phonétique international (Alfa à Zulu) standardisé pour épeler les immatriculations et repères",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "chiffres en phraséologie",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Prononciation spécifique des chiffres pour éviter les ambiguïtés (ex: 'trois', 'quatre', 'cinq' bien articulés)",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "fréquence",
        "categorie": "Radio & phraséologie",
        "famille": "radio_communications",
        "priorite": "haute",
        "justification": "Valeur en mégahertz (VHF) désignant le canal d'émission/réception radio",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "canal 8,33 kHz",
        "categorie": "Radio & phraséologie",
        "famille": "radio_communications",
        "priorite": "haute",
        "justification": "Espacement réduit des canaux radio VHF de communication imposé en Europe",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "25 kHz",
        "categorie": "Radio & phraséologie",
        "famille": "radio_communications",
        "priorite": "haute",
        "justification": "Ancien espacement standard des canaux radio VHF encore utilisé hors espace contrôlé",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "121,5 MHz",
        "categorie": "Radio & phraséologie",
        "famille": "radio_communications",
        "priorite": "haute",
        "justification": "Fréquence aéronautique d'urgence internationale de détresse",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "alternat",
        "categorie": "Radio & phraséologie",
        "famille": "radio_communications",
        "priorite": "haute",
        "justification": "Bouton d'émission radio (Push-To-Talk) situé sur le manche ou volant permettant l'alternance émission-réception",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "blocage micro",
        "categorie": "Radio & phraséologie",
        "famille": "radio_communications",
        "priorite": "haute",
        "justification": "Situation accidentelle où le bouton d'émission reste bloqué, paralysant la fréquence radio",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "essai radio",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Procédure d'évaluation de la qualité de transmission et de réception de la radio",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "lisibilité 1 à 5",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Échelle d'évaluation standardisée de la qualité de réception d'un signal radio (1 = illisible, 5 = parfaitement lisible)",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "autorisation",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Accord délivré par le contrôle aérien permettant au pilote d'exécuter une action sous contrôle",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "instruction",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Ordre obligatoire émis par le contrôle aérien que le pilote doit exécuter et collationner",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "information de trafic",
        "categorie": "Radio & phraséologie",
        "famille": "info_trafic",
        "priorite": "haute",
        "justification": "Renseignements émis par l'ATC pour aider le pilote à repérer et éviter les autres aéronefs à proximité",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "clairance",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Autorisation accordée à un aéronef de manoeuvrer selon les conditions spécifiées par un organisme de contrôle",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "WILCO",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Abréviation radio signifiant 'Will Comply' (compris et j'exécuterai l'instruction)",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "ROGER",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Expression de transmission signifiant 'bien reçu'",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "AFFIRM",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Expression radio standardisée signifiant 'Oui' ou 'Affirmatif' pour éviter l'ambiguïté",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "NEGATIVE",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Expression radio standardisée signifiant 'Non' ou 'Négatif'",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "STANDBY",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Expression signifiant 'Attendez' ou 'Restez à l'écoute'",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "SAY AGAIN",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Expression de phraséologie demandant de répéter la transmission",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "READ BACK",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Terme anglais équivalent au collationnement obligatoire",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "REPORT",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Instruction de phraséologie demandant de signaler un passage vertical ou une étape",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "LINE UP",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Instruction de phraséologie ordonnant de s'aligner sur la piste de décollage",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "HOLD SHORT",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Instruction d'attente avant la piste imposant de s'arrêter avant la ligne d'effet du point d'arrêt",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "CLEARED",
        "categorie": "Radio & phraséologie",
        "famille": "radio_phraséologie",
        "priorite": "haute",
        "justification": "Terme de phraséologie anglaise signifiant 'Autorisé'",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "auto-information",
        "categorie": "Radio & phraséologie",
        "famille": "radio_communications",
        "priorite": "haute",
        "justification": "Procédure de transmission d'intentions sur une fréquence commune en l'absence d'organisme de contrôle au sol",
        "sous_domaine": "Radio et phraséologie"
    },
    {
        "terme": "transpondeur en mode standby",
        "categorie": "Radio & phraséologie",
        "famille": "codes_transpondeur",
        "priorite": "haute",
        "justification": "Mise sous tension du transpondeur sans émission active vers le radar secondaire",
        "sous_domaine": "Radio et phraséologie"
    },

    # 7. Unités et conversions
    {
        "terme": "pied",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de mesure de l'altitude, de la hauteur et de l'espacement vertical (ft)",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "mètre",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de distance verticale ou horizontale alternative au pied dans certains pays",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "kilomètre",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité métrique de distance horizontale",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "nœud",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de mesure de vitesse équivalant à un mille nautique par heure (kt)",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "km/h",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Kilomètres par heure, unité de vitesse",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "m/s",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Mètres par seconde, unité de vitesse verticale",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "ft/min",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Pieds par minute, unité de vitesse verticale utilisée pour le variomètre",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "hectopascal",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité barométrique standard de mesure de la pression (hPa)",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "pouce de mercure",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de pression barométrique (inHg) couramment utilisée aux États-Unis pour les calages altimétriques",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "inHg",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Symbole ou abréviation de pouce de mercure (inch of mercury)",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "litre",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité métrique de volume de carburant et de lubrifiant",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "gallon",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité impériale ou US de volume de carburant, équivalant à environ 3.78 litres (US) ou 4.54 litres (UK)",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "kilogramme",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité métrique de masse utilisée pour le devis de poids et centrage",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "livre",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de masse anglo-saxonne (lbs) couramment utilisée en aéronautique",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "degré Celsius",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité métrique de température utilisée pour l'atmosphère standard (ISA) et le moteur",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "Fahrenheit",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "moyenne",
        "justification": "Unité anglo-saxonne de température",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "UTC",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Temps universel coordonné, référence horaire absolue pour la navigation",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "heure locale",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Heure du fuseau horaire local, distincte de l'heure universelle UTC nécessaire à la navigation",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "minute",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de temps et de mesure d'arc angulaire",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "seconde",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité de temps de base",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "degré",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Unité angulaire servant aux coordonnées géographiques, caps et directions",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "facteur de conversion pied/mètre",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Rapport numérique (1 m = 3.28 ft) essentiel pour convertir l'altitude ou les obstacles",
        "sous_domaine": "Unités et conversions"
    },
    {
        "terme": "litre/gallon",
        "categorie": "Unités",
        "famille": "unites",
        "priorite": "haute",
        "justification": "Rapport de conversion volumétrique indispensable pour la gestion de carburant lors des avitaillements",
        "sous_domaine": "Unités et conversions"
    }
]

manquants = []
deja_presents = 0
checked_set = set()

for item in all_terms_of_interest:
    t = item["terme"]
    ct = clean_term(t)
    
    # Avoid duplicate checking in our input list (e.g. mille nautique, alternat appear twice but we should audit once)
    if ct in checked_set:
        continue
    checked_set.add(ct)
    
    if ct in clean_index_set:
        deja_presents += 1
    else:
        manquants.append(item)

# Sort manquants by category and sub_domaine for clean structure
manquants.sort(key=lambda x: (x["categorie"], x["sous_domaine"], x["terme"]))

# Output structure
audit_result = {
    "domaine": "Navigation & radio",
    "manquants": manquants,
    "deja_presents_verifies": deja_presents,
    "notes": f"Audit d'exhaustivité réalisé sur {len(checked_set)} termes uniques du programme PPL(A) français. {len(manquants)} termes détectés manquants et {deja_presents} déjà présents dans l'INDEX-EXISTANT.json après normalisation (accents, pluriels, espaces)."
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(audit_result, f, indent=2, ensure_ascii=False)

print(f"Audit completed: {len(manquants)} missing, {deja_presents} already present.")
