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

index_path = "/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/INDEX-EXISTANT.json"
with open(index_path, 'r', encoding='utf-8') as f:
    index_list = json.load(f)

# Build normalized index set
normalized_index = set()
for item in index_list:
    normalized_index.add(normalize(item))
    # also add exact lowercase item
    normalized_index.add(item.lower().strip())

print(f"Loaded {len(index_list)} terms in index.")
print(f"Normalized index has {len(normalized_index)} unique entries.")

# Let's write the candidates from the prompt and test them
candidates = {
    "Aérodynamique de base": [
        "profil", "corde", "envergure", "allongement", "épaisseur relative", 
        "extrados", "intrados", "bord d'attaque", "bord de fuite", "incidence", 
        "angle d'incidence", "angle de calage", "dièdre", "flèche", "vrillage", 
        "couche limite", "écoulement laminaire", "écoulement turbulent", 
        "décollement", "point d'arrêt", "centre de poussée", "foyer", "résultante aérodynamique"
    ],
    "Forces et polaire": [
        "portance", "traînée", "traînée induite", "traînée parasite", "traînée de forme", 
        "traînée de frottement", "polaire des vitesses", "finesse", "finesse max", 
        "coefficient de portance", "Cz", "Cl", "coefficient de traînée", "Cx", "Cd", 
        "rapport portance/traînée", "charge alaire"
    ],
    "Décrochage": [
        "incidence de décrochage", "décrochage dynamique", "décrochage accéléré", 
        "décrochage en virage", "vrille", "autorotation", "départ en vrille", 
        "buffeting", "avertisseur de décrochage", "facteur de charge", "virage à grande inclinaison"
    ],
    "Stabilité et manœuvrabilité": [
        "stabilité statique", "stabilité dynamique", "stabilité longitudinale", 
        "stabilité latérale", "stabilité de route", "effet girouette", "roulis induit", 
        "lacet inverse", "lacet induit", "effet de dièdre", "amortissement", "tenue de cap"
    ],
    "Effets moteur/hélice": [
        "couple", "souffle hélicoïdal", "précession gyroscopique", "traction dissymétrique", "effet de sol"
    ],
    "Vitesses": [
        "VS0", "VS1", "VA", "VNO", "VNE", "VFE", "VLE", "VLO", "VX", "VY", 
        "VBG", "VRA", "VG", "Vref", "Vapp", "Vr", "Vlof", "Vtoss", 
        "IAS", "CAS", "EAS", "TAS", "GS", "Mach", 
        "vitesse indiquée", "vitesse conventionnelle", "vitesse propre", "vitesse vraie", "vitesse sol", 
        "erreur de densité", "erreur instrumentale", "erreur de position"
    ],
    "Performances": [
        "distance de roulement", "distance de décollage", "distance franchissement 15 m", 
        "distance franchissement 50 ft", "distance d'atterrissage", "distance accélération-arrêt", 
        "pente de montée", "taux de montée", "plafond pratique", "plafond de sustentation", 
        "altitude densité", "effet de l'altitude", "effet de la température", "effet de la masse", 
        "effet du vent", "effet de l'état de surface", "effet de la pente", "facteur de correction", 
        "abaque", "plafond de croisière", "rayon d'action", "autonomie", "consommation spécifique"
    ],
    "Masse et centrage": [
        "masse à vide", "masse maximale au décollage", "masse maximale à l'atterrissage", 
        "charge utile", "masse et bras de levier", "moment", "limites avant de centrage", 
        "limites arrière de centrage", "enveloppe de centrage", "index", 
        "centrage avant", "centrage arrière", "masse sans carburant", 
        "carburant utilisable", "carburant inutilisable"
    ],
    "Structure et facteurs de charge": [
        "diagramme de manœuvre", "diagramme V-n", "facteur de charge limite", 
        "facteur de charge ultime", "catégorie normale", "catégorie utilitaire", 
        "catégorie voltige", "rafale", "fatigue", "longeron", "nervure", 
        "revêtement travaillant", "fuselage treillis", "fuselage monocoque", 
        "fuselage semi-monocoque", "train classique", "train tricycle", 
        "amortisseur", "atterrisseur"
    ]
}

missing = {}
present = {}

for category, terms in candidates.items():
    missing[category] = []
    present[category] = []
    for term in terms:
        norm_t = normalize(term)
        # also check sub-variations or partial matches inside index to see if it's there
        # For instance, if index has "profil d'aile" and term is "profil", "profil" might be a separate general term we want, but if index has exactly "profil", then it is present.
        # Let's check exact match first:
        found_exact = False
        if term.lower().strip() in index_list or norm_t in normalized_index:
            found_exact = True
            
        if found_exact:
            present[category].append(term)
        else:
            missing[category].append(term)

print("\n--- PRESENT ---")
for cat, terms in present.items():
    if terms:
        print(f"{cat}: {', '.join(terms)}")

print("\n--- MISSING ---")
for cat, terms in missing.items():
    if terms:
        print(f"{cat}: {', '.join(terms)}")
