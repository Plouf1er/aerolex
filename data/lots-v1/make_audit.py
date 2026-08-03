import json
import unicodedata
import os

# Read the existing index
with open("/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/INDEX-EXISTANT.json", "r") as f:
    existant = json.load(f)

def clean_term(t):
    t = t.lower().strip()
    t_clean = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
    return t_clean

existant_clean = {clean_term(x) for x in existant}

# Expanded PPL Meteorology Syllabus Candidates
candidates = [
    # Atmosphère
    ("stratosphère", "Météo", "couches_atmosphere", "haute", "Couche de l'atmosphère située au-dessus de la tropopause, hors météo active", "Atmosphère"),
    ("gradient adiabatique sec", "Météo", "gradients_thermiques", "haute", "Taux de refroidissement théorique de l'air sec en montée (1°C / 100 m)", "Atmosphère"),
    ("gradient adiabatique saturé", "Météo", "gradients_thermiques", "haute", "Taux de refroidissement de l'air saturé en montée (0,5 à 0,9°C / 100 m)", "Atmosphère"),
    ("isothermie", "Météo", "gradients_thermiques", "haute", "Tranche d'atmosphère où la température reste constante avec l'altitude", "Atmosphère"),
    ("pression atmosphérique", "Météo", "isobares_pression", "haute", "Force exercée par l'air, indispensable pour comprendre l'altimétrie et les mouvements d'air", "Atmosphère"),
    ("humidité relative", "Météo", "generalites_atmosphere", "haute", "Rapport en % de la quantité d'eau présente à la capacité maximale de l'air", "Atmosphère"),
    ("surfusion", "Météo", "thermodynamique", "haute", "État de l'eau liquide restant fluide sous 0°C, cause principale du givrage en vol", "Atmosphère"),
    ("chaleur latente", "Météo", "thermodynamique", "haute", "Énergie libérée ou absorbée lors du changement d'état de l'eau, moteur de l'instabilité", "Atmosphère"),
    ("salr", "Météo", "gradients_thermiques", "moyenne", "Saturated Adiabatic Lapse Rate (sigle anglais du gradient adiabatique saturé)", "Atmosphère"),

    # Pression, densité, température
    ("surface isobare", "Météo", "isobares_pression", "haute", "Surface tridimensionnelle d'égale pression atmosphérique", "Pression, densité, température"),
    ("marais barométrique", "Météo", "systemes_pression", "haute", "Situation synoptique sans gradient de pression marqué, propice aux brumes/orages", "Pression, densité, température"),
    ("isallobare", "Météo", "isobares_pression", "basse", "Ligne d'égale variation de pression dans un temps donné, outil de prévision", "Pression, densité, température"),

    # Nuages
    ("cirrus", "Météo", "nuages_genres", "haute", "Genre de nuage de l'étage supérieur composé de cristaux de glace", "Nuages"),
    ("cirrocumulus", "Météo", "nuages_genres", "haute", "Genre de nuage de l'étage supérieur formant des rides ou des galets", "Nuages"),
    ("humilis", "Météo", "nuages_especes", "haute", "Espèce de cumulus aplati caractérisant des conditions stables de beau temps", "Nuages"),
    ("mediocris", "Météo", "nuages_especes", "haute", "Espèce de cumulus d'extension verticale modérée", "Nuages"),
    ("congestus", "Météo", "nuages_especes", "haute", "Espèce de cumulus bourgeonnant à fort développement vertical", "Nuages"),
    ("capillatus", "Météo", "nuages_especes", "haute", "Espèce de cumulonimbus caractérisé par son enclume fibreuse", "Nuages"),
    ("virga", "Météo", "nuages_especes", "haute", "Précipitations s'évaporant sous la base d'un nuage avant de toucher le sol", "Nuages"),
    ("étage supérieur", "Météo", "nuages_etages", "moyenne", "Tranche d'altitude au-dessus de 20 000 ft contenant les cirrus", "Nuages"),
    ("étage moyen", "Météo", "nuages_etages", "moyenne", "Tranche d'altitude (6 500 à 20 000 ft) contenant altocumulus et altostratus", "Nuages"),
    ("étage inférieur", "Météo", "nuages_etages", "moyenne", "Tranche d'altitude (du sol à 6 500 ft) contenant stratus et stratocumulus", "Nuages"),

    # Précipitations et hydrométéores
    ("bruine", "Météo", "precipitations", "haute", "Précipitation de très fines gouttelettes d'eau tombant du stratus", "Précipitations et hydrométéores"),
    ("grêle", "Météo", "precipitations", "haute", "Précipitation de grêlons durs émanant exclusivement du cumulonimbus", "Précipitations et hydrométéores"),
    ("grésil", "Météo", "precipitations", "haute", "Précipitation de petits grains de glace opaques ou translucides", "Précipitations et hydrométéores"),
    ("neige", "Météo", "precipitations", "haute", "Précipitation solide de cristaux de glace complexes assemblés en flocons", "Précipitations et hydrométéores"),
    ("pluie surfondue", "Météo", "precipitations", "haute", "Pluie liquide par température négative gelant instantanément à l'impact (givrage sévère)", "Précipitations et hydrométéores"),
    ("brouillard d'advection", "Météo", "brouillards_types", "haute", "Brouillard formé par le refroidissement d'un air chaud et humide sur sol froid", "Précipitations et hydrométéores"),
    ("brouillard d'évaporation", "Météo", "brouillards_types", "haute", "Brouillard sur plans d'eau par apport d'humidité chaude dans de l'air froid", "Précipitations et hydrométéores"),
    ("brume sèche", "Météo", "visibilite_phenomenes", "haute", "Réduction de visibilité par des particules microscopiques solides en suspension", "Précipitations et hydrométéores"),
    ("hydrométéore", "Météo", "generalites_meteo", "moyenne", "Tout phénomène lié à l'eau condensée ou précipitée dans l'atmosphère", "Précipitations et hydrométéores"),

    # Masses d'air et fronts
    ("front stationnaire", "Météo", "fronts_meteorologiques", "haute", "Frontière stable entre deux masses d'air de températures différentes", "Masses d'air et fronts"),
    ("front polaire", "Météo", "fronts_meteorologiques", "haute", "Surface de discontinuité majeure séparant l'air polaire de l'air tropical", "Masses d'air et fronts"),
    ("dorsale", "Météo", "systemes_pression", "haute", "Axe de hautes pressions prolongeant un anticyclone (temps généralement stable)", "Masses d'air et fronts"),
    ("thalweg", "Météo", "systemes_pression", "haute", "Axe de basses pressions prolongeant une dépression (temps perturbé)", "Masses d'air et fronts"),
    ("col barométrique", "Météo", "systemes_pression", "haute", "Région de transition de pression neutre entre deux dépressions et deux anticyclones", "Masses d'air et fronts"),
    ("secteur chaud", "Météo", "fronts_meteorologiques", "haute", "Espace d'air doux situé entre le front chaud antérieur et le front froid postérieur", "Masses d'air et fronts"),
    ("traîne", "Météo", "fronts_meteorologiques", "haute", "Ciel post-frontal instable caractérisé par des averses, du vent et de belles éclaircies", "Masses d'air et fronts"),

    # Stabilité, instabilité, inversion
    ("subsidence", "Météo", "mouvements_verticaux", "haute", "Mouvement de descente lente de l'air créant de la stabilité et une inversion de subsidence", "Stabilité, instabilité, inversion"),
    ("thermique", "Météo", "mouvements_verticaux", "haute", "Courant d'air chaud ascendant engendré par l'échauffement solaire du sol", "Stabilité, instabilité, inversion"),
    ("adiabatique", "Météo", "thermodynamique", "haute", "Évolution thermique d'une masse d'air sans échange de chaleur avec l'extérieur", "Stabilité, instabilité, inversion"),

    # Vent
    ("force de Coriolis", "Météo", "force_vent", "haute", "Force fictive déviant les vents vers la droite dans l'hémisphère nord", "Vent"),
    ("vent géostrophique", "Météo", "force_vent", "haute", "Vent théorique parallèle aux isobares résultant de l'équilibre gradient/Coriolis", "Vent"),
    ("brise de montagne", "Vent", "brises", "haute", "Brise nocturne descendant des reliefs froids vers la vallée", "Vent"),
    ("brise de vallée", "Vent", "brises", "haute", "Brise diurne remontant les reliefs réchauffés", "Vent"),
    ("onde orographique", "Vent", "effets_vent_relief", "haute", "Mouvement ondulatoire en aval de reliefs montagneux par vent fort stable", "Vent"),
    ("rafale descendante", "Vent", "turbulences", "haute", "Courant d'air vertical descendant très violent d'origine convective (sous orage)", "Vent"),
    ("microburst", "Vent", "turbulences", "haute", "Rafale descendante extrêmement localisée et violente, mortelle au décollage", "Vent"),

    # Givrage
    ("givre blanc", "Météo", "givrage", "haute", "Glace granuleuse opaque se formant par congélation instantanée de petites gouttelettes surfondues", "Givrage"),
    ("givrage clair", "Météo", "givrage", "haute", "Glace compacte et transparente très adhérente, formée de grosses gouttes surfondues", "Givrage"),
    ("givrage mixte", "Météo", "givrage", "haute", "Mélange dangereux de givre blanc et de glace claire", "Givrage"),
    ("dégivrage", "Moteur & hélice", "systemes_degivrage", "haute", "Action d'éliminer la glace accumulée sur l'aéronef", "Givrage"),
    ("antigivrage", "Moteur & hélice", "systemes_degivrage", "haute", "Action d'empêcher le dépôt de glace sur les surfaces de l'aéronef", "Givrage"),

    # Turbulence
    ("cat", "Météo", "turbulences", "haute", "Clear Air Turbulence, turbulence sévère en air clair liée aux cisaillements de jet-stream", "Turbulence"),
    ("turbulence thermique", "Météo", "turbulences", "haute", "Secousses provoquées par des bulles d'air chaud ascendantes (convection)", "Turbulence"),

    # Visibilité
    ("visibilité météo", "Météo", "visibilite_phenomenes", "haute", "Distance horizontale maximale d'identification d'objets ou de repères noirs", "Visibilité"),
    ("rvr", "Météo", "visibilite_phenomenes", "haute", "Runway Visual Range (portée visuelle de piste, mesurée aux instruments)", "Visibilité"),

    # Documentation et messages
    ("airmet", "Météo", "messages_meteo_types", "haute", "Message d'alerte météo en route destiné à l'aviation de basse altitude", "Documentation et messages"),
    ("gamet", "Météo", "messages_meteo_types", "haute", "Prévision de zone en basse couche, déclinée par sections", "Documentation et messages"),
    ("volmet", "Météo", "messages_meteo_types", "haute", "Service radio transmettant en phonie continue les METAR/TAF d'aérodromes", "Documentation et messages"),
    ("carte isobarique", "Météo", "cartes_meteo", "haute", "Carte météorologique montrant les isobares au sol et les systèmes de pression", "Documentation et messages"),
    ("coupe verticale", "Météo", "cartes_meteo", "haute", "Profil altimétrique décrivant les nuages, vents et isothermes le long d'un parcours", "Documentation et messages"),
    # Codes OACI METAR/TAF de temps présent
    ("ra", "Météo", "codes_meteo_etat", "haute", "Rain (abréviation OACI pour pluie)", "Documentation et messages"),
    ("sn", "Météo", "codes_meteo_etat", "haute", "Snow (abréviation OACI pour neige)", "Documentation et messages"),
    ("ts", "Météo", "codes_meteo_etat", "haute", "Thunderstorm (abréviation OACI pour orage)", "Documentation et messages"),
    ("fg", "Météo", "codes_meteo_etat", "haute", "Fog (abréviation OACI pour brouillard)", "Documentation et messages"),
    ("dz", "Météo", "codes_meteo_etat", "haute", "Drizzle (abréviation OACI pour bruine)", "Documentation et messages"),
    ("gr", "Météo", "codes_meteo_etat", "haute", "Hail (abréviation OACI pour grêle)", "Documentation et messages"),
    ("sh", "Météo", "codes_meteo_etat", "haute", "Showers (abréviation OACI pour averses)", "Documentation et messages"),
    ("fz", "Météo", "codes_meteo_etat", "haute", "Freezing (abréviation OACI pour se congelant/surfondu)", "Documentation et messages"),
    ("vc", "Météo", "codes_meteo_etat", "haute", "Vicinity (abréviation OACI pour au voisinage)", "Documentation et messages"),
    ("hz", "Météo", "codes_meteo_etat", "haute", "Haze (abréviation OACI pour brume sèche)", "Documentation et messages"),
    ("fu", "Météo", "codes_meteo_etat", "haute", "Smoke (abréviation OACI pour fumée)", "Documentation et messages"),
    ("sq", "Météo", "codes_meteo_etat", "haute", "Squalls (abréviation OACI pour grains)", "Documentation et messages"),
    ("po", "Météo", "codes_meteo_etat", "haute", "Dust/sand whirls (abréviation OACI pour tourbillons de poussière)", "Documentation et messages"),
    ("fc", "Météo", "codes_meteo_etat", "haute", "Funnel cloud (abréviation OACI pour trombe ou tornade)", "Documentation et messages"),
    ("ds", "Météo", "codes_meteo_etat", "haute", "Duststorm (abréviation OACI pour tempête de poussière)", "Documentation et messages"),
    ("ss", "Météo", "codes_meteo_etat", "haute", "Sandstorm (abréviation OACI pour tempête de sable)", "Documentation et messages"),

    # Phénomènes dangereux
    ("orage", "Météo", "phenomenes_dangereux", "haute", "Phénomène orageux complet avec ascendance violente, grêle, foudre et grains", "Phénomènes dangereux"),
    ("cellule orageuse", "Météo", "phenomenes_dangereux", "haute", "Unité convective autonome à l'origine de l'orage", "Phénomènes dangereux"),
    ("orage multicellulaire", "Météo", "phenomenes_dangereux", "haute", "Système orageux formé de plusieurs cellules à des stades différents de leur cycle", "Phénomènes dangereux"),
    ("orage supercellulaire", "Météo", "phenomenes_dangereux", "haute", "Orage monocellulaire géant caractérisé par un courant ascendant rotatif (extrêmement dangereux)", "Phénomènes dangereux"),
    ("tornade", "Météo", "phenomenes_dangereux", "haute", "Tourbillon de vent de très petite échelle extrêmement destructeur sous cumulonimbus", "Phénomènes dangereux"),
    ("trombe", "Météo", "phenomenes_dangereux", "haute", "Phénomène tourbillonnaire similaire à une tornade se développant sur l'eau", "Phénomènes dangereux"),
    ("front de rafales", "Météo", "turbulences", "haute", "Limite de l'air froid descendant d'un cumulonimbus, marquée par de violentes rafales au sol", "Phénomènes dangereux"),
]

# Run diff analysis
missing_terms = []
present_count = 0

def is_present(term):
    t = clean_term(term)
    variations = {
        t,
        t + "s",
        t + "x",
        t[:-1] if t.endswith(("s", "x")) else t,
    }
    return any(v in existant_clean for v in variations)

for term, cat, fam, prio, just, sd in candidates:
    if is_present(term):
        present_count += 1
    else:
        missing_terms.append({
            "terme": term,
            "categorie": cat,
            "famille": fam,
            "priorite": prio,
            "justification": just,
            "sous_domaine": sd
        })

# Load the PAR-CATEGORIE.json file
with open("/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/PAR-CATEGORIE.json", "r") as f:
    par_cat = json.load(f)

deja_presents_verifies = len(par_cat.get("Météo", [])) + len(par_cat.get("Vent", []))

output_data = {
    "domaine": "Météo",
    "manquants": missing_terms,
    "deja_presents_verifies": deja_presents_verifies,
    "notes": "L'audit montre des manques notables dans les genres de nuages de base (cirrus, cirrocumulus) alors que d'autres (altocumulus, cumulonimbus) sont présents. Les abréviations OACI de temps présent (METAR/TAF) manquaient cruellement, ainsi que les hydrométéores principaux (bruine, grêle, grésil, pluie surfondue) indispensables au PPL(A). Les orages complexes (multicellulaires/supercellulaires) et le givrage fin (givre blanc vs givre clair) font l'objet d'un manque important de couverture."
}

output_path = "/Users/aprunel/.openclaw/workspace/projects/aerolex/data/lots-v1/AUDIT-meteo.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"Audit completed: {len(missing_terms)} missing terms found.")
