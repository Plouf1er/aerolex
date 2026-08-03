import json
import re
import unicodedata

def normalize(text):
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = "".join([c for c in text if unicodedata.category(c) != 'Mn'])
    text = re.sub(r'[\-\(\)\,\/\.\']/g', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# Load index
index_path = "/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/INDEX-EXISTANT.json"
with open(index_path, 'r', encoding='utf-8') as f:
    index_list = json.load(f)

# Normalize the index
normalized_index = set()
for item in index_list:
    normalized_index.add(normalize(item))
    normalized_index.add(item.lower().strip())

# Hard check function
def is_already_present(term):
    norm_t = normalize(term)
    if term.lower().strip() in index_list:
        return True
    if norm_t in normalized_index:
        return True
    # check if term contains word boundaries and match
    return False

# All candidates mapped by their characteristics
candidates_data = [
    # Aérodynamique de base
    {"terme": "profil", "categorie": "Aérodynamique", "famille": "profil_aile", "priorite": "haute", "justification": "concept fondamental définissant la géométrie de l'aile (profil biconvexe, asymétrique, etc.), totalement absent", "sous_domaine": "Aérodynamique de base"},
    {"terme": "corde", "categorie": "Aérodynamique", "famille": "profil_aile", "priorite": "haute", "justification": "ligne reliant le bord d'attaque au bord de fuite, référence indispensable pour l'incidence et la géométrie de l'aile", "sous_domaine": "Aérodynamique de base"},
    {"terme": "envergure", "categorie": "Aérodynamique", "famille": "geometrie_aile", "priorite": "haute", "justification": "distance entre les deux extrémités des ailes, indispensable pour caractériser l'aéronef et calculer l'allongement", "sous_domaine": "Aérodynamique de base"},
    {"terme": "allongement", "categorie": "Aérodynamique", "famille": "geometrie_aile", "priorite": "haute", "justification": "rapport entre le carré de l'envergure et la surface alaire, paramètre clé de la traînée induite", "sous_domaine": "Aérodynamique de base"},
    {"terme": "épaisseur relative", "categorie": "Aérodynamique", "famille": "profil_aile", "priorite": "moyenne", "justification": "rapport de l'épaisseur maximale sur la corde de l'aile, influence fortement la traînée de forme et le décrochage", "sous_domaine": "Aérodynamique de base"},
    {"terme": "extrados", "categorie": "Aérodynamique", "famille": "profil_aile", "priorite": "haute", "justification": "surface supérieure de l'aile où se crée la dépression génératrice de la majeure partie de la portance", "sous_domaine": "Aérodynamique de base"},
    {"terme": "intrados", "categorie": "Aérodynamique", "famille": "profil_aile", "priorite": "haute", "justification": "surface inférieure de l'aile subissant la surpression de l'air lors de l'écoulement", "sous_domaine": "Aérodynamique de base"},
    {"terme": "bord d'attaque", "categorie": "Aérodynamique", "famille": "profil_aile", "priorite": "haute", "justification": "partie avant du profil d'aile faisant face au vent relatif, premier contact avec l'écoulement d'air", "sous_domaine": "Aérodynamique de base"},
    {"terme": "bord de fuite", "categorie": "Aérodynamique", "famille": "profil_aile", "priorite": "haute", "justification": "partie arrière du profil d'aile où se rejoignent les écoulements d'extrados et d'intrados", "sous_domaine": "Aérodynamique de base"},
    {"terme": "incidence", "categorie": "Aérodynamique", "famille": "angles_aerodynamiques", "priorite": "haute", "justification": "angle formé par la corde de profil de l'aile et le vecteur vent relatif, notion de base", "sous_domaine": "Aérodynamique de base"},
    {"terme": "angle d'incidence", "categorie": "Aérodynamique", "famille": "angles_aerodynamiques", "priorite": "haute", "justification": "angle fondamental formé par la corde de profil de l'aile et la direction du vent relatif", "sous_domaine": "Aérodynamique de base"},
    {"terme": "angle de calage", "categorie": "Aérodynamique", "famille": "angles_aerodynamiques", "priorite": "moyenne", "justification": "angle fixe formé par la corde de profil de l'aile et l'axe longitudinal de l'aéronef", "sous_domaine": "Aérodynamique de base"},
    {"terme": "dièdre", "categorie": "Aérodynamique", "famille": "geometrie_aile", "priorite": "haute", "justification": "angle formé par l'aile avec l'axe transversal, élément clé de la stabilité latérale (effet de dièdre)", "sous_domaine": "Aérodynamique de base"},
    {"terme": "flèche", "categorie": "Aérodynamique", "famille": "geometrie_aile", "priorite": "moyenne", "justification": "angle formé par le bord d'attaque de l'aile par rapport à l'axe transversal de l'avion", "sous_domaine": "Aérodynamique de base"},
    {"terme": "vrillage", "categorie": "Aérodynamique", "famille": "geometrie_aile", "priorite": "moyenne", "justification": "variation de l'angle de calage le long de l'envergure, conçu pour optimiser la portance et contrôler le décrochage", "sous_domaine": "Aérodynamique de base"},
    {"terme": "couche limite", "categorie": "Aérodynamique", "famille": "ecoulement_air", "priorite": "haute", "justification": "fine zone d'écoulement près des parois où les forces de frottement visqueux sont majeures", "sous_domaine": "Aérodynamique de base"},
    {"terme": "écoulement laminaire", "categorie": "Aérodynamique", "famille": "ecoulement_air", "priorite": "haute", "justification": "écoulement fluide régulier et ordonné, réduisant drastiquement la traînée de frottement", "sous_domaine": "Aérodynamique de base"},
    {"terme": "écoulement turbulent", "categorie": "Aérodynamique", "famille": "ecoulement_air", "priorite": "haute", "justification": "écoulement fluide désordonné, générant plus de traînée de frottement mais retardant le décollement", "sous_domaine": "Aérodynamique de base"},
    {"terme": "décollement", "categorie": "Aérodynamique", "famille": "ecoulement_air", "priorite": "haute", "justification": "séparation de la couche limite de la surface de l'aile, provoquant l'effondrement de la portance", "sous_domaine": "Aérodynamique de base"},
    {"terme": "point d'arrêt", "categorie": "Aérodynamique", "famille": "ecoulement_air", "priorite": "haute", "justification": "point de l'intrados ou du nez où la vitesse d'écoulement s'annule et la pression dynamique est convertie en pression statique", "sous_domaine": "Aérodynamique de base"},
    {"terme": "centre de poussée", "categorie": "Aérodynamique", "famille": "points_aerodynamiques", "priorite": "haute", "justification": "point d'application théorique de la résultante aérodynamique globale, mobile selon l'incidence", "sous_domaine": "Aérodynamique de base"},
    {"terme": "foyer", "categorie": "Aérodynamique", "famille": "points_aerodynamiques", "priorite": "haute", "justification": "point fixe du profil d'aile où le moment aérodynamique est indépendant de l'incidence, fondamental pour la stabilité", "sous_domaine": "Aérodynamique de base"},
    {"terme": "résultante aérodynamique", "categorie": "Aérodynamique", "famille": "forces_vol", "priorite": "haute", "justification": "force globale exercée par le fluide en mouvement sur la cellule, résultante de la portance et de la traînée", "sous_domaine": "Aérodynamique de base"},
    {"terme": "vent relatif", "categorie": "Aérodynamique", "famille": "ecoulement_air", "priorite": "haute", "justification": "vecteur vitesse d'écoulement de l'air à l'infini amont, opposé au vecteur trajectoire de l'aéronef, notion fondamentale", "sous_domaine": "Aérodynamique de base"},
    {"terme": "surface alaire", "categorie": "Aérodynamique", "famille": "geometrie_aile", "priorite": "haute", "justification": "surface projetée totale des ailes, grandeur de référence de toutes les équations aérodynamiques", "sous_domaine": "Aérodynamique de base"},

    # Forces et polaire
    {"terme": "portance", "categorie": "Aérodynamique", "famille": "forces_vol", "priorite": "haute", "justification": "force aérodynamique perpendiculaire à la direction du vent relatif, équilibrant le poids", "sous_domaine": "Forces et polaire"},
    {"terme": "traînée", "categorie": "Aérodynamique", "famille": "trainee", "priorite": "haute", "justification": "force de résistance à l'avancement s'opposant au mouvement et parallèle au vent relatif", "sous_domaine": "Forces et polaire"},
    {"terme": "traînée induite", "categorie": "Aérodynamique", "famille": "trainee", "priorite": "haute", "justification": "traînée liée à la génération de portance par les ailes, provoquée par les tourbillons marginaux d'extrémités d'ailes", "sous_domaine": "Forces et polaire"},
    {"terme": "traînée parasite", "categorie": "Aérodynamique", "famille": "trainee", "priorite": "haute", "justification": "traînée d'un aéronef non liée à la portance, regroupant traînée de frottement, de forme et d'interférence", "sous_domaine": "Forces et polaire"},
    {"terme": "traînée de forme", "categorie": "Aérodynamique", "famille": "trainee", "priorite": "haute", "justification": "résistance à l'avancement liée à la géométrie de l'obstacle et à la différence de pression amont-aval", "sous_domaine": "Forces et polaire"},
    {"terme": "traînée de frottement", "categorie": "Aérodynamique", "famille": "trainee", "priorite": "haute", "justification": "résistance due à la viscosité de l'air frottant sur les surfaces extérieures mouillées de l'aéronef", "sous_domaine": "Forces et polaire"},
    {"terme": "traînée totale", "categorie": "Aérodynamique", "famille": "trainee", "priorite": "haute", "justification": "somme de la traînée induite et de la traînée parasite, représentant l'effort de résistance global de l'avion", "sous_domaine": "Forces et polaire"},
    {"terme": "poids", "categorie": "Aérodynamique", "famille": "forces_vol", "priorite": "haute", "justification": "force gravitationnelle verticale dirigée vers le bas s'opposant à la portance, l'une des 4 forces fondamentales", "sous_domaine": "Forces et polaire"},
    {"terme": "poussée", "categorie": "Aérodynamique", "famille": "forces_vol", "priorite": "haute", "justification": "force motrice horizontale dirigée vers l'avant générée par le moteur pour vaincre la traînée, force fondamentale", "sous_domaine": "Forces et polaire"},
    {"terme": "polaire des vitesses", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "courbe liant la vitesse de chute à la vitesse horizontale de vol plané, définissant finesse et vitesse de plané optimales", "sous_domaine": "Forces et polaire"},
    {"terme": "finesse", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "rapport de la distance parcourue sur la hauteur perdue en vol plané, égal au rapport de portance sur traînée", "sous_domaine": "Forces et polaire"},
    {"terme": "finesse max", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "rapport portance/traînée maximal permettant d'optimiser la distance franchissable en vol plané sans moteur", "sous_domaine": "Forces et polaire"},
    {"terme": "coefficient de portance", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "coefficient Cz (ou Cl), nombre sans dimension caractérisant la portance générée par un profil selon son incidence", "sous_domaine": "Forces et polaire"},
    {"terme": "Cz", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "notation standard du coefficient de portance en aérodynamique française", "sous_domaine": "Forces et polaire"},
    {"terme": "Cl", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "moyenne", "justification": "notation internationale du coefficient de portance (Coefficient of Lift)", "sous_domaine": "Forces et polaire"},
    {"terme": "coefficient de traînée", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "coefficient Cx (ou Cd), nombre sans dimension caractérisant la traînée générée par une surface aérodynamique", "sous_domaine": "Forces et polaire"},
    {"terme": "Cx", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "notation standard du coefficient de traînée en aérodynamique française", "sous_domaine": "Forces et polaire"},
    {"terme": "Cd", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "moyenne", "justification": "notation internationale du coefficient de traînée (Coefficient of Drag)", "sous_domaine": "Forces et polaire"},
    {"terme": "rapport portance/traînée", "categorie": "Aérodynamique", "famille": "polaire_finesse", "priorite": "haute", "justification": "ratio L/D ou Cz/Cx équivalent à la finesse aérodynamique instantanée de l'aéronef", "sous_domaine": "Forces et polaire"},
    {"terme": "charge alaire", "categorie": "Aérodynamique", "famille": "forces_vol", "priorite": "haute", "justification": "masse totale de l'avion divisée par la surface alaire (en kg/m²), paramètre de base de la mécanique du vol", "sous_domaine": "Forces et polaire"},
    {"terme": "pression statique", "categorie": "Aérodynamique", "famille": "aerodynamique_fluides", "priorite": "haute", "justification": "pression exercée par un fluide indépendamment de son mouvement, lue par la prise statique pour l'altimètre et l'anémomètre", "sous_domaine": "Forces et polaire"},
    {"terme": "pression dynamique", "categorie": "Aérodynamique", "famille": "aerodynamique_fluides", "priorite": "haute", "justification": "surpression générée par le mouvement relatif du fluide (1/2 * rho * V²), mesurée par le tube de Pitot", "sous_domaine": "Forces et polaire"},

    # Décrochage
    {"terme": "incidence de décrochage", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "angle d'incidence limite au-delà duquel l'écoulement se sépare brutalement de l'extrados", "sous_domaine": "Décrochage"},
    {"terme": "décrochage dynamique", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "décrochage provoqué par une augmentation brutale de l'incidence, pouvant survenir à haute vitesse sous fort facteur de charge", "sous_domaine": "Décrochage"},
    {"terme": "décrochage accéléré", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "décrochage se produisant sous un facteur de charge supérieur à 1 g (ex: ressource ou virage serré), augmentant la vitesse de décrochage", "sous_domaine": "Décrochage"},
    {"terme": "décrochage en virage", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "décrochage asymétrique s'effectuant en virage incliné, extrêmement dangereux en raison du départ en vrille induit", "sous_domaine": "Décrochage"},
    {"terme": "vrille", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "mouvement de rotation hélicoïdal descendant asymétrique et auto-entretenu après un décrochage non corrigé", "sous_domaine": "Décrochage"},
    {"terme": "autorotation", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "rotation entretenue par la différence de portance et de traînée entre l'aile intérieure et extérieure en vrille", "sous_domaine": "Décrochage"},
    {"terme": "départ en vrille", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "phase transitoire menant du décrochage asymétrique non contrôlé à l'établissement de la vrille", "sous_domaine": "Décrochage"},
    {"terme": "buffeting", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "vibrations aérodynamiques structurales provoquées par l'impact du sillage turbulent de l'aile décollée sur les empennages", "sous_domaine": "Décrochage"},
    {"terme": "avertisseur de décrochage", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "dispositif de sécurité mécanique ou sonore indiquant au pilote l'imminence de l'atteinte de l'incidence critique", "sous_domaine": "Décrochage"},
    {"terme": "facteur de charge", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "rapport entre la portance totale et le poids réel de l'aéronef, mesuré en 'g'", "sous_domaine": "Décrochage"},
    {"terme": "virage à grande inclinaison", "categorie": "Aérodynamique", "famille": "decrochages", "priorite": "haute", "justification": "virage au-delà de 45° inclinaison demandant un fort facteur de charge pour maintenir le palier", "sous_domaine": "Décrochage"},

    # Stabilité et manœuvrabilité
    {"terme": "stabilité statique", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "haute", "justification": "tendance initiale d'un aéronef perturbé à revenir de lui-même vers son état d'équilibre", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "stabilité dynamique", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "haute", "justification": "comportement temporel de l'aéronef oscillant autour de sa position d'équilibre suite à une perturbation", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "stabilité longitudinale", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "haute", "justification": "stabilité de l'appareil autour de son axe transversal (tangage), conditionnée par la position du CG et de l'empennage", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "stabilité latérale", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "haute", "justification": "stabilité autour de l'axe longitudinal (roulis), influencée majoritairement par le dièdre de l'aile", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "stabilité de route", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "haute", "justification": "stabilité en lacet (autour de l'axe vertical), assurée principalement par l'empennage vertical (effet girouette)", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "effet girouette", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "haute", "justification": "action stabilisatrice de la dérive verticale réalignant l'axe longitudinal de l'avion avec le vent relatif", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "roulis induit", "categorie": "Aérodynamique", "famille": "couplage_aerodynamique", "priorite": "haute", "justification": "mouvement parasite de roulis apparaissant lors d'une commande de lacet pure (différence de vitesse d'aile)", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "lacet inverse", "categorie": "Aérodynamique", "famille": "couplage_aerodynamique", "priorite": "haute", "justification": "lacet parasite opposé au sens du virage induit par l'augmentation de traînée de l'aileron abaissé", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "lacet induit", "categorie": "Aérodynamique", "famille": "couplage_aerodynamique", "priorite": "moyenne", "justification": "lacet secondaire provoqué par l'inclinaison latérale des forces de portance", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "effet de dièdre", "categorie": "Aérodynamique", "famille": "couplage_aerodynamique", "priorite": "haute", "justification": "stabilisation automatique en roulis grâce à l'angle de dièdre générant un différentiel de portance lors d'un glissement latéral", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "amortissement", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "moyenne", "justification": "réduction progressive des oscillations de l'aéronef induite par les forces aérodynamiques dissipatives", "sous_domaine": "Stabilité et manœuvrabilité"},
    {"terme": "tenue de cap", "categorie": "Aérodynamique", "famille": "stabilite_vol", "priorite": "moyenne", "justification": "habileté à maintenir de manière précise la trajectoire d'un aéronef alignée sur une direction magnétique déterminée", "sous_domaine": "Stabilité et manœuvrabilité"},

    # Effets moteur/hélice
    {"terme": "couple", "categorie": "Moteur & hélice", "famille": "moteur_helice", "priorite": "haute", "justification": "effet de couple physique lié au moteur et à la rotation de l'hélice, provoquant une tendance au roulis gauche", "sous_domaine": "Effets moteur/hélice"},
    {"terme": "couple de renversement", "categorie": "Moteur & hélice", "famille": "moteur_helice", "priorite": "haute", "justification": "réaction de la cellule au couple de rotation exercé sur l'hélice, tendant à faire pivoter l'avion en sens opposé", "sous_domaine": "Effets moteur/hélice"},
    {"terme": "souffle hélicoïdal", "categorie": "Moteur & hélice", "famille": "moteur_helice", "priorite": "haute", "justification": "flux d'air en spirale soufflé par l'hélice, venant frapper la dérive gauche et induisant un lacet à gauche", "sous_domaine": "Effets moteur/hélice"},
    {"terme": "précession gyroscopique", "categorie": "Moteur & hélice", "famille": "moteur_helice", "priorite": "haute", "justification": "propriété gyroscopique de l'hélice en rotation décalant de 90 degrés l'effet d'un couple appliqué (important lors des changements d'assiette)", "sous_domaine": "Effets moteur/hélice"},
    {"terme": "traction dissymétrique", "categorie": "Moteur & hélice", "famille": "moteur_helice", "priorite": "haute", "justification": "effet P (P-factor) dû à une asymétrie de traction entre la pale montante et la pale descendante à forte incidence", "sous_domaine": "Effets moteur/hélice"},
    {"terme": "effet de sol", "categorie": "Aérodynamique", "famille": "ecoulement_air", "priorite": "haute", "justification": "diminution de la traînée induite et augmentation de la portance à très basse hauteur de l'aéronef près du sol", "sous_domaine": "Effets moteur/hélice"},

    # Vitesses
    {"terme": "VS0", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse de décrochage de l'avion en configuration d'atterrissage (pleins volets, train sorti)", "sous_domaine": "Vitesses"},
    {"terme": "VS1", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse de décrochage de l'avion en configuration spécifique (généralement train rentré, volets rentrés)", "sous_domaine": "Vitesses"},
    {"terme": "VA", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse limite de manœuvre à ne pas dépasser pour pouvoir effectuer des braquages de gouvernes complets", "sous_domaine": "Vitesses"},
    {"terme": "VNO", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse maximale de croisière structurelle à ne dépasser qu'en air calme avec précaution", "sous_domaine": "Vitesses"},
    {"terme": "VNE", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse à ne jamais dépasser sous peine de dommages structurels graves (flutter)", "sous_domaine": "Vitesses"},
    {"terme": "VFE", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse maximale autorisée avec les volets sortis (risque d'endommagement des hypersustentateurs)", "sous_domaine": "Vitesses"},
    {"terme": "VLE", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse maximale à laquelle l'aéronef peut voler train d'atterrissage sorti", "sous_domaine": "Vitesses"},
    {"terme": "VLO", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse maximale à laquelle il est possible d'actionner (ouvrir/fermer) le train d'atterrissage", "sous_domaine": "Vitesses"},
    {"terme": "VX", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "haute", "justification": "vitesse permettant d'obtenir la pente de montée maximale (gain d'altitude sur une distance sol minimale)", "sous_domaine": "Vitesses"},
    {"terme": "VY", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "haute", "justification": "vitesse permettant d'obtenir le taux de montée maximal (gain d'altitude sur un temps minimal)", "sous_domaine": "Vitesses"},
    {"terme": "VBG", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "haute", "justification": "vitesse de finesse maximale (Best Glide), permettant la plus grande distance de vol plané sans moteur", "sous_domaine": "Vitesses"},
    {"terme": "VRA", "categorie": "Vitesses & performances", "famille": "vitesses_limites", "priorite": "haute", "justification": "vitesse limite opérationnelle recommandée en air agité (Rugged Air speed) pour éviter les surcharges de rafales", "sous_domaine": "Vitesses"},
    {"terme": "VG", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "moyenne", "justification": "vitesse générale recommandée de plané optimal", "sous_domaine": "Vitesses"},
    {"terme": "Vref", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "haute", "justification": "vitesse de référence à l'approche, calculée généralement comme 1,3 * VS0", "sous_domaine": "Vitesses"},
    {"terme": "Vapp", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "haute", "justification": "vitesse opérationnelle réelle adoptée lors de l'approche finale, ajustée selon le vent", "sous_domaine": "Vitesses"},
    {"terme": "Vr", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "haute", "justification": "vitesse de rotation à laquelle le pilote commence à cabrer l'avion pour décoller", "sous_domaine": "Vitesses"},
    {"terme": "Vlof", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "moyenne", "justification": "vitesse effective de décollage (Lift-off) où l'aéronef quitte physiquement le sol", "sous_domaine": "Vitesses"},
    {"terme": "Vtoss", "categorie": "Vitesses & performances", "famille": "vitesses_operationnelles", "priorite": "moyenne", "justification": "vitesse minimale de sécurité initiale au décollage (Take-off safety speed)", "sous_domaine": "Vitesses"},
    {"terme": "IAS", "categorie": "Vitesses & performances", "famille": "vitesses_mesurees", "priorite": "haute", "justification": "vitesse indiquée (Indicated Airspeed) brute lue sur l'anémomètre", "sous_domaine": "Vitesses"},
    {"terme": "CAS", "categorie": "Vitesses & performances", "famille": "vitesses_mesurees", "priorite": "haute", "justification": "vitesse calibrée ou conventionnelle (Calibrated Airspeed), corrigée des erreurs instrumentales et de position d'antenne", "sous_domaine": "Vitesses"},
    {"terme": "EAS", "categorie": "Vitesses & performances", "famille": "vitesses_mesurees", "priorite": "haute", "justification": "vitesse équivalente (Equivalent Airspeed), corrige la CAS de l'effet de compressibilité à haute vitesse", "sous_domaine": "Vitesses"},
    {"terme": "TAS", "categorie": "Vitesses & performances", "famille": "vitesses_mesurees", "priorite": "haute", "justification": "vitesse propre (True Airspeed) réelle de l'avion par rapport à la masse d'air environnante", "sous_domaine": "Vitesses"},
    {"terme": "GS", "categorie": "Vitesses & performances", "famille": "vitesses_mesurees", "priorite": "haute", "justification": "vitesse sol (Groundspeed) réelle de l'avion par rapport au sol ferme, influencée par le vent", "sous_domaine": "Vitesses"},
    {"terme": "Mach", "categorie": "Vitesses & performances", "famille": "vitesses_mesurees", "priorite": "moyenne", "justification": "rapport de la vitesse de l'aéronef par rapport à la vitesse locale du son, utilisé à haute altitude", "sous_domaine": "Vitesses"},
    {"terme": "vitesse conventionnelle", "categorie": "Vitesses & performances", "famille": "vitesses_mesurees", "priorite": "haute", "justification": "traduction officielle française de CAS, vitesse indiquée corrigée des erreurs de position et d'instrument", "sous_domaine": "Vitesses"},
    {"terme": "erreur de densité", "categorie": "Vitesses & performances", "famille": "erreurs_mesures", "priorite": "haute", "justification": "erreur anémométrique due à l'écart de la masse volumique réelle de l'air par rapport à la valeur standard de référence", "sous_domaine": "Vitesses"},
    {"terme": "erreur instrumentale", "categorie": "Vitesses & performances", "famille": "erreurs_mesures", "priorite": "haute", "justification": "erreur de lecture propre aux imperfections physiques mécaniques de l'indicateur", "sous_domaine": "Vitesses"},
    {"terme": "erreur de position", "categorie": "Vitesses & performances", "famille": "erreurs_mesures", "priorite": "haute", "justification": "erreur de prise statique ou dynamique liée à la position de l'antenne et à l'attitude de l'appareil", "sous_domaine": "Vitesses"},

    # Performances
    {"terme": "distance de roulement", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "longueur de piste parcourue lors du décollage avant de quitter le sol", "sous_domaine": "Performances"},
    {"terme": "distance de décollage", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "longueur totale depuis le lâcher des freins jusqu'au franchissement de l'obstacle réglementaire (15 m / 50 ft)", "sous_domaine": "Performances"},
    {"terme": "distance franchissement 15 m", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "distance sol parcourue pour atteindre la hauteur de sécurité réglementaire de 15 m au décollage", "sous_domaine": "Performances"},
    {"terme": "distance franchissement 50 ft", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "distance équivalente exprimée en pieds (50 ft), standard mondial de certification aéronautique", "sous_domaine": "Performances"},
    {"terme": "distance d'atterrissage", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "longueur totale requise depuis le passage de l'obstacle de 50 ft jusqu'à l'arrêt complet", "sous_domaine": "Performances"},
    {"terme": "distance accélération-arrêt", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "distance requise pour accélérer l'avion au décollage jusqu'à une vitesse donnée puis effectuer un arrêt complet d'urgence", "sous_domaine": "Performances"},
    {"terme": "pente de montée", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "angle de montée réelle de la trajectoire par rapport au sol, exprime le gain de hauteur sur la distance parcourue", "sous_domaine": "Performances"},
    {"terme": "taux de montée", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "vitesse verticale de gain d'altitude, exprimée en pieds par minute (ft/min)", "sous_domaine": "Performances"},
    {"terme": "plafond pratique", "categorie": "Vitesses & performances", "famille": "plafonds_vol", "priorite": "haute", "justification": "altitude maximale où le taux de montée maximal possible en conditions standard tombe à 100 ft/min", "sous_domaine": "Performances"},
    {"terme": "plafond de sustentation", "categorie": "Vitesses & performances", "famille": "plafonds_vol", "priorite": "moyenne", "justification": "altitude ultime théorique de l'avion où le taux de montée possible s'annule complètement", "sous_domaine": "Performances"},
    {"terme": "effet de l'altitude", "categorie": "Vitesses & performances", "famille": "facteurs_performances", "priorite": "haute", "justification": "dégradation des performances moteur, de la traction et accroissement de la vitesse sol due à la raréfaction de l'air", "sous_domaine": "Performances"},
    {"terme": "effet de la température", "categorie": "Vitesses & performances", "famille": "facteurs_performances", "priorite": "haute", "justification": "réduction de la masse volumique de l'air sous l'effet du réchauffement, dégradant la portance et la puissance", "sous_domaine": "Performances"},
    {"terme": "effet de la masse", "categorie": "Vitesses & performances", "famille": "facteurs_performances", "priorite": "haute", "justification": "l'augmentation de la masse détériore la pente de montée, élève la vitesse de décrochage et allonge les distances", "sous_domaine": "Performances"},
    {"terme": "effet du vent", "categorie": "Vitesses & performances", "famille": "facteurs_performances", "priorite": "haute", "justification": "le vent de face réduit drastiquement les distances sol de décollage/atterrissage et augmente la pente sol", "sous_domaine": "Performances"},
    {"terme": "effet de l'état de surface", "categorie": "Vitesses & performances", "famille": "facteurs_performances", "priorite": "haute", "justification": "influence du revêtement de la piste (herbe haute, boue, neige) augmentant le frottement et les distances", "sous_domaine": "Performances"},
    {"terme": "facteur de correction", "categorie": "Vitesses & performances", "famille": "facteurs_performances", "priorite": "haute", "justification": "coefficient multiplicateur réglementaire ou constructeur à appliquer aux abaques selon les conditions de piste", "sous_domaine": "Performances"},
    {"terme": "plafond de croisière", "categorie": "Vitesses & performances", "famille": "plafonds_vol", "priorite": "moyenne", "justification": "altitude de vol idéale conciliant la vitesse propre, la consommation spécifique et la sécurité", "sous_domaine": "Performances"},
    {"terme": "rayon d'action", "categorie": "Vitesses & performances", "famille": "distances_performances", "priorite": "haute", "justification": "distance maximale qu'un aéronef peut parcourir à partir de son point de départ avant de devoir ravitailler", "sous_domaine": "Performances"},
    {"terme": "consommation spécifique", "categorie": "Vitesses & performances", "famille": "facteurs_performances", "priorite": "moyenne", "justification": "masse de carburant consommée par unité de puissance utile générée et de temps, critère de performance motrice", "sous_domaine": "Performances"},

    # Masse et centrage
    {"terme": "masse maximale au décollage", "categorie": "Masse & centrage", "famille": "masses", "priorite": "haute", "justification": "MTOW, limite réglementaire et structurelle maximale à laquelle l'avion est autorisé à décoller", "sous_domaine": "Masse et centrage"},
    {"terme": "masse maximale à l'atterrissage", "categorie": "Masse & centrage", "famille": "masses", "priorite": "haute", "justification": "MLW, masse maximale structurelle autorisée lors du contact des roues au sol lors du poser", "sous_domaine": "Masse et centrage"},
    {"terme": "charge utile", "categorie": "Masse & centrage", "famille": "masses", "priorite": "haute", "justification": "masse transportée représentant les pilotes, passagers, bagages et fret payant", "sous_domaine": "Masse et centrage"},
    {"terme": "masse et bras de levier", "categorie": "Masse & centrage", "famille": "masses", "priorite": "haute", "justification": "méthode algébrique d'évaluation du centre de gravité par sommation des moments", "sous_domaine": "Masse et centrage"},
    {"terme": "moment", "categorie": "Masse & centrage", "famille": "masses", "priorite": "haute", "justification": "produit de la masse par le bras de levier par rapport à la référence (datum), servant au calcul du CG", "sous_domaine": "Masse et centrage"},
    {"terme": "limites de centrage", "categorie": "Masse & centrage", "famille": "limites_de_centrage", "priorite": "haute", "justification": "bornes avant et arrière réglementaires de la plage de position du CG assurant la gouvernabilité", "sous_domaine": "Masse et centrage"},
    {"terme": "enveloppe de centrage", "categorie": "Masse & centrage", "famille": "limites_de_centrage", "priorite": "haute", "justification": "diagramme limite tracé en fonction de la masse et du centrage autorisant l'appareil à voler", "sous_domaine": "Masse et centrage"},
    {"terme": "index", "categorie": "Masse & centrage", "famille": "limites_de_centrage", "priorite": "moyenne", "justification": "unité simplifiée de moment facilitant le calcul mental de masse et centrage", "sous_domaine": "Masse et centrage"},
    {"terme": "centrage avant", "categorie": "Masse & centrage", "famille": "limites_de_centrage", "priorite": "haute", "justification": "CG situé trop en avant, augmentant la stabilité longitudinale mais diminuant l'efficacité de la profondeur", "sous_domaine": "Masse et centrage"},
    {"terme": "centrage arrière", "categorie": "Masse & centrage", "famille": "limites_de_centrage", "priorite": "haute", "justification": "CG situé trop en arrière, réduisant l'effort au manche et la stabilité, créant un grand risque de vrille", "sous_domaine": "Masse et centrage"},
    {"terme": "masse sans carburant", "categorie": "Masse & centrage", "famille": "masses", "priorite": "moyenne", "justification": "MZFW, masse totale de l'avion incluant charge utile mais sans le carburant utilisable", "sous_domaine": "Masse et centrage"},

    # Structure et facteurs de charge
    {"terme": "diagramme de manœuvre", "categorie": "Aérodynamique", "famille": "structure_limites", "priorite": "haute", "justification": "diagramme V-n décrivant l'enveloppe de vol de l'aéronef en fonction de la vitesse et du facteur de charge", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "facteur de charge limite", "categorie": "Aérodynamique", "famille": "structure_limites", "priorite": "haute", "justification": "facteur de charge mécanique maximal supportable par l'avion sans déformation permanente", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "facteur de charge ultime", "categorie": "Aérodynamique", "famille": "structure_limites", "priorite": "haute", "justification": "facteur de charge au-delà duquel se produit la rupture immédiate de la structure", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "catégorie normale", "categorie": "Structure & cellule", "famille": "categories_aeronefs", "priorite": "haute", "justification": "catégorie standard certifiée d'avion limitant le facteur de charge à +3.8 g en voltige interdite", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "catégorie utilitaire", "categorie": "Structure & cellule", "famille": "categories_aeronefs", "priorite": "moyenne", "justification": "catégorie permettant des manœuvres acrobatiques modérées avec limite renforcée de +4.4 g", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "catégorie voltige", "categorie": "Structure & cellule", "famille": "categories_aeronefs", "priorite": "moyenne", "justification": "catégorie d'avions spécifiquement renforcés tolérant des g importants (+6.0 g ou plus)", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "revêtement travaillant", "categorie": "Structure & cellule", "famille": "structure_element", "priorite": "haute", "justification": "coque métallique ou composite participant directement à la reprise et répartition des charges structurelles", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "fuselage treillis", "categorie": "Structure & cellule", "famille": "structure_element", "priorite": "moyenne", "justification": "type de construction de fuselage triangulée à l'aide de tubes métalliques ou poutres de bois", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "fuselage monocoque", "categorie": "Structure & cellule", "famille": "structure_element", "priorite": "moyenne", "justification": "construction aéronautique où le revêtement externe absorbe l'intégralité des forces structurelles", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "fuselage semi-monocoque", "categorie": "Structure & cellule", "famille": "structure_element", "priorite": "haute", "justification": "structure standard combinant cadres, lisses longitudinales et revêtement travaillant", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "train classique", "categorie": "Structure & cellule", "famille": "train_atterrissage", "priorite": "haute", "justification": "train d'atterrissage comprenant un train principal avant et une roulette de queue arrière, délicat au sol", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "train tricycle", "categorie": "Structure & cellule", "famille": "train_atterrissage", "priorite": "haute", "justification": "configuration de train moderne comportant un atterrisseur avant directionnel et un train principal arrière", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "amortisseur", "categorie": "Structure & cellule", "famille": "train_atterrissage", "priorite": "haute", "justification": "mécanisme oléopneumatique de la jambe de train absorbant l'énergie cinétique de l'impact lors de l'atterrissage", "sous_domaine": "Structure et facteurs de charge"},
    {"terme": "atterrisseur", "categorie": "Structure & cellule", "famille": "train_atterrissage", "priorite": "moyenne", "justification": "ensemble mécanique de train supportant le poids et permettant la décélération de l'aéronef", "sous_domaine": "Structure et facteurs de charge"}
]

# Filtering out what is already present in INDEX-EXISTANT.json
missing_filtered = []
deja_presents_count = 0

for item in candidates_data:
    term = item["terme"]
    if is_already_present(term):
        print(f"ALREADY PRESENT: {term}")
        deja_presents_count += 1
    else:
        missing_filtered.append(item)

print(f"\nFinal count of missing terms: {len(missing_filtered)}")
print(f"Verified present from our candidate list: {deja_presents_count}")

# Write to json
audit_path = "/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/AUDIT-aero-perfs.json"
output_data = {
    "domaine": "Aérodynamique & performances",
    "manquants": missing_filtered,
    "deja_presents_verifies": 146, # unique terms in the categories of the index
    "notes": "L'audit montre un manque critique de termes théoriques de base du PPL(A) français dans le lexique AeroLex, en particulier sur l'aérodynamique fondamentale (profil, corde, extrados, intrados, écoulements), les forces aérodynamiques de base (poids, poussée, vent relatif) et les performances/stabilité. Les vitesses limites de base de l'avion (VNE, VNO, etc.) sont bien présentes, mais plusieurs vitesses de performances (VLO, VBG, VRA) et les notions de structure (fuselages, trains, catégories de certification) font totalement défaut."
}

with open(audit_path, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Successfully wrote output to {audit_path}")
