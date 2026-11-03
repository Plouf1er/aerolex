import sys
import os
import json
import glob
import unicodedata
import re

# Set paths
BASE_DIR = "/Users/aprunel/.openclaw/workspace/projects/aerolex"
sys.path.insert(0, os.path.join(BASE_DIR, "data"))
import data_glossaire_full as dgf

def normalize(text):
    if not text: return ''
    text = text.lower().strip()
    text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
    return text

def clean_term_key(text):
    return text.strip()

# 1. Load v1 glossary
v1_glossary = dgf.GLOSSAIRE
v1_terms_set = {t.lower().strip(): t for t in v1_glossary.keys()}

# Extract valid categories and families from v1 glossary
valid_categories = set()
valid_families = set()
for term, entry in v1_glossary.items():
    cat = entry.get('categorie')
    fam = entry.get('famille')
    if cat: valid_categories.add(cat)
    if fam: valid_families.add(fam)

# 2. Load all v2 fiches and tag them with their source file
v2_files = sorted(glob.glob(os.path.join(BASE_DIR, "data/lots-v2/REDIGE-LOT-*.json")))
v2_fiches_raw = []
for f_path in v2_files:
    file_name = os.path.basename(f_path)
    with open(f_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
        for fi in d.get('fiches', []):
            fi_copy = dict(fi)
            fi_copy['_source_file'] = file_name
            v2_fiches_raw.append(fi_copy)

print(f"Loaded {len(v2_fiches_raw)} raw fiches from v2 files")

# Identify the 5 duplicates with v1 (based on normalized term)
v1_duplicates_terms = {t.lower().strip() for t in ['portance', 'décrochage', 'aile', 'traînée', 'vitesse propre']}
v1_duplicates_fiches = [f for f in v2_fiches_raw if f['terme'].lower().strip() in v1_duplicates_terms]
print(f"Found {len(v1_duplicates_fiches)} occurrences of v1 duplicates in v2 raw data")

# Filter out v1 duplicates
v2_fiches_no_v1_dup = [f for f in v2_fiches_raw if f['terme'].lower().strip() not in v1_duplicates_terms]
print(f"Fiches remaining after removing v1 duplicates: {len(v2_fiches_no_v1_dup)}")

# 3. Deduplicate v2 internal duplicates
# Group by term to see occurrences
v2_by_term = {}
for fi in v2_fiches_no_v1_dup:
    norm_t = fi['terme'].lower().strip()
    if norm_t not in v2_by_term:
        v2_by_term[norm_t] = []
    v2_by_term[norm_t].append(fi)

v2_fiches_dedup = []
internal_duplicates_info = []

for norm_t, occurrences in sorted(v2_by_term.items()):
    if len(occurrences) > 1:
        # Resolve internal duplicate: prefer REDIGE-LOT-7-COMPLEMENT.json
        chosen = None
        for fi in occurrences:
            if fi['_source_file'] == 'REDIGE-LOT-7-COMPLEMENT.json':
                chosen = fi
                break
        if not chosen:
            chosen = occurrences[0]
        v2_fiches_dedup.append(chosen)
        internal_duplicates_info.append({
            "term": chosen['terme'],
            "all_sources": [o['_source_file'] for o in occurrences],
            "chosen_source": chosen['_source_file'],
            "occurrences": len(occurrences)
        })
    else:
        v2_fiches_dedup.append(occurrences[0])

print(f"Unique v2 fiches to import: {len(v2_fiches_dedup)}")

# 4. Load taxonomy categories and invalid families from the AUDIT files
audit_mapping = {}
for p in ['projects/aerolex/data/lots-v1/AUDIT-aero-perfs.json',
          'projects/aerolex/data/lots-v1/AUDIT-aerodrome.json',
          'projects/aerolex/data/lots-v1/AUDIT-meteo.json',
          'projects/aerolex/data/lots-v1/AUDIT-nav-radio.json',
          'projects/aerolex/data/lots-v1/AUDIT-regl-proc.json']:
    with open(p, 'r', encoding='utf-8') as f:
        d = json.load(f)
        for m in d.get('manquants', []):
            term = m['terme'].lower().strip()
            audit_mapping[term] = {
                "categorie": m.get('categorie'),
                "famille_audit": m.get('famille')
            }

print(f"Loaded audit taxonomy mappings for {len(audit_mapping)} terms")

# 5. Define taxonomy fallback/mapping from AUDIT (category, invalid_famille) to valid v1 families
MANUAL_FAM_MAP = {
    # Altimétrie
    ('Altimétrie', 'altimetrie_references'): 'altitudes',
    ('Altimétrie', 'references_pression'): 'calages_altimetriques',
    ('Altimétrie', 'references_verticales'): 'references_verticales',
    
    # Aérodrome & cartes
    ('Aérodrome & cartes', 'aire_signaux'): 'procedures_sol',
    ('Aérodrome & cartes', 'cartes_aeronautiques'): 'cartes_aeronautiques',
    ('Aérodrome & cartes', 'circuit_procedures'): 'circuit_procedures',
    ('Aérodrome & cartes', 'dimensions_piste'): 'dimensions_piste',
    ('Aérodrome & cartes', 'feux_balisage'): 'pistes',
    ('Aérodrome & cartes', 'marquages_sol'): 'pistes',
    
    # Aérodynamique
    ('Aérodynamique', 'aerodynamique_fluides'): 'trainee',
    ('Aérodynamique', 'angles_aerodynamiques'): 'assiettes',
    ('Aérodynamique', 'couplage_aerodynamique'): 'virages',
    ('Aérodynamique', 'decrochages'): 'decrochages',
    ('Aérodynamique', 'ecoulement_air'): 'trainee',
    ('Aérodynamique', 'forces_vol'): 'trainee',
    ('Aérodynamique', 'geometrie_aile'): 'hypersustentateurs',
    ('Aérodynamique', 'points_aerodynamiques'): 'assiettes',
    ('Aérodynamique', 'polaire_finesse'): 'trainee',
    ('Aérodynamique', 'profil_aile'): 'hypersustentateurs',
    ('Aérodynamique', 'stabilite_vol'): 'virages',
    ('Aérodynamique', 'structure_limites'): 'decrochages',
    ('Aérodynamique', 'trainee'): 'trainee',
    
    # Instruments
    ('Instruments', 'codes_transpondeur'): 'instruments_radionavigation',
    ('Instruments', 'compas_et_magnetisme'): 'references_magnetiques',
    ('Instruments', 'instruments_gyroscopiques'): 'instruments_gyroscopiques',
    ('Instruments', 'instruments_mesure'): 'instruments_radionavigation',
    ('Instruments', 'instruments_pression'): 'instruments_anemobarometriques',
    ('Instruments', 'instruments_radionavigation'): 'instruments_radionavigation',
    
    # Masse & centrage
    ('Masse & centrage', 'limites_de_centrage'): 'limites_de_centrage',
    ('Masse & centrage', 'masses'): 'masses',
    
    # Moteur & hélice
    ('Moteur & hélice', 'carburation'): 'commandes_cockpit',
    ('Moteur & hélice', 'circuit_allumage'): 'magnetos',
    ('Moteur & hélice', 'circuit_carburant'): 'parametres_moteur',
    ('Moteur & hélice', 'circuit_electrique'): 'parametres_moteur',
    ('Moteur & hélice', 'helice'): 'helice',
    ('Moteur & hélice', 'moteur_cycle'): 'parametres_moteur',
    ('Moteur & hélice', 'moteur_helice'): 'helice',
    ('Moteur & hélice', 'pannes_moteur'): 'pannes_moteur',
    ('Moteur & hélice', 'refroidissement_moteur'): 'parametres_moteur',
    ('Moteur & hélice', 'systemes_degivrage'): 'givrage',
    
    # Météo
    ('Météo', 'brouillards_types'): 'conditions_visibilite',
    ('Météo', 'cartes_meteo'): 'messages_meteo_types',
    ('Météo', 'codes_meteo_etat'): 'codes_meteo_etat',
    ('Météo', 'couches_atmosphere'): 'couches_atmospheriques',
    ('Météo', 'force_vent'): 'effets_vent_relief',
    ('Météo', 'fronts_meteorologiques'): 'fronts_meteorologiques',
    ('Météo', 'generalites_atmosphere'): 'stabilite_atmospherique',
    ('Météo', 'generalites_meteo'): 'codes_meteo_etat',
    ('Météo', 'givrage'): 'givrage',
    ('Météo', 'gradients_thermiques'): 'isothermes_temperatures',
    ('Météo', 'isobares_pression'): 'stabilite_atmospherique',
    ('Météo', 'messages_meteo_types'): 'messages_meteo_types',
    ('Météo', 'mouvements_verticaux'): 'stabilite_atmospherique',
    ('Météo', 'nuages_especes'): 'nuages_especes',
    ('Météo', 'nuages_etages'): 'nuages_couverture',
    ('Météo', 'nuages_genres'): 'nuages_genres',
    ('Météo', 'phenomenes_dangereux'): 'stabilite_atmospherique',
    ('Météo', 'precipitations'): 'codes_meteo_etat',
    ('Météo', 'systemes_pression'): 'stabilite_atmospherique',
    ('Météo', 'thermodynamique'): 'stabilite_atmospherique',
    ('Météo', 'turbulences'): 'turbulences',
    ('Météo', 'visibilite_phenomenes'): 'conditions_visibilite',
    
    # Navigation
    ('Navigation', 'compas_et_magnetisme'): 'references_magnetiques',
    ('Navigation', 'heures_estimations'): 'heures_estimations',
    ('Navigation', 'navigation_caps_et_routes'): 'navigation_caps_et_routes',
    ('Navigation', 'navigation_termes'): 'navigation_caps_et_routes',
    ('Navigation', 'points_navigation'): 'navigation_caps_et_routes',
    
    # Procédures
    ('Procédures', 'briefings'): 'briefings',
    ('Procédures', 'essais_moteur'): 'procedures_sol',
    ('Procédures', 'pannes_moteur'): 'pannes_moteur',
    ('Procédures', 'phases_vol'): 'phases_vol',
    
    # Radio & phraséologie
    ('Radio & phraséologie', 'alphabet_oaci'): 'alphabet_oaci',
    ('Radio & phraséologie', 'codes_transpondeur'): 'radio_phraseologie',
    ('Radio & phraséologie', 'info_trafic'): 'radio_phraseologie',
    ('Radio & phraséologie', 'radio_communications'): 'radio_phraseologie',
    ('Radio & phraséologie', 'radio_phraséologie'): 'radio_phraseologie',
    
    # Réglementation & docs
    ('Réglementation & docs', 'altitudes_survol'): 'altitudes',
    ('Réglementation & docs', 'documents_bord'): 'documents_bord',
    ('Réglementation & docs', 'documents_licences'): 'documents_bord',
    ('Réglementation & docs', 'espaces_controles'): 'espaces_controles',
    ('Réglementation & docs', 'espaces_reglementes'): 'espaces_reglementes',
    ('Réglementation & docs', 'interception'): 'regles_vol',
    ('Réglementation & docs', 'maintenance'): 'documents_bord',
    ('Réglementation & docs', 'masses'): 'documents_bord',
    ('Réglementation & docs', 'niveaux_vol'): 'altitudes',
    ('Réglementation & docs', 'phases_urgence'): 'regles_vol',
    ('Réglementation & docs', 'plan_de_vol'): 'documents_bord',
    ('Réglementation & docs', 'recherche_sauvetage'): 'regles_vol',
    ('Réglementation & docs', 'regle_semi_circulaire'): 'regles_vol',
    ('Réglementation & docs', 'regles_anticollision'): 'regles_vol',
    ('Réglementation & docs', 'regles_vol'): 'regles_vol',
    ('Réglementation & docs', 'services_atc'): 'regles_vol',
    ('Réglementation & docs', 'services_organismes'): 'espaces_controles',
    ('Réglementation & docs', 'vfr_ifr'): 'regles_vol',
    
    # Structure & cellule
    ('Structure & cellule', 'categories_aeronefs'): 'commandes_cockpit',
    ('Structure & cellule', 'structure_element'): 'gouvernes_primaires',
    ('Structure & cellule', 'train_atterrissage'): 'commandes_cockpit',
    
    # Sécurité & facteurs humains
    ('Sécurité & facteurs humains', 'equipements_secu'): 'facteurs_humains_physiologie',
    ('Sécurité & facteurs humains', 'facteurs_humains_physiologie'): 'facteurs_humains_physiologie',
    ('Sécurité & facteurs humains', 'fh_illusions_sensorielles'): 'physiologie',
    ('Sécurité & facteurs humains', 'fh_modeles_et_biais'): 'fh_modeles_et_biais',
    ('Sécurité & facteurs humains', 'fh_prise_de_decision'): 'fh_prise_de_decision',
    ('Sécurité & facteurs humains', 'procedures_urgence'): 'fh_prise_de_decision',
    
    # Unités
    ('Unités', 'unites'): 'unites_moteur_temps', # modified in code below
    
    # Vent
    ('Vent', 'brises'): 'brises',
    ('Vent', 'effets_vent_relief'): 'effets_vent_relief',
    ('Vent', 'turbulences'): 'turbulences',
    
    # Vitesses & performances
    ('Vitesses & performances', 'distances_performances'): 'distances_performances',
    ('Vitesses & performances', 'erreurs_mesures'): 'vitesses_mesurees',
    ('Vitesses & performances', 'facteurs_performances'): 'distances_performances',
    ('Vitesses & performances', 'plafonds_vol'): 'performances_verticales',
    ('Vitesses & performances', 'vitesses_limites'): 'vitesses_limites',
    ('Vitesses & performances', 'vitesses_mesurees'): 'vitesses_mesurees',
    ('Vitesses & performances', 'vitesses_operationnelles'): 'vitesses_operationnelles',
}

# 6. Apply processing rules
import_final_dict = {}
variants_removed_list = []
xrefs_added_list = []

for fi in v2_fiches_dedup:
    term_v2 = fi['terme']
    norm_t = term_v2.lower().strip()
    
    # A. Get category and family from AUDIT files
    audit_info = audit_mapping.get(norm_t)
    if not audit_info:
        print(f"Warning: term not found in AUDIT files: {term_v2}")
        # Default fallback
        cat = "Procédures"
        fam_audit = "phases_vol"
    else:
        cat = audit_info['categorie']
        fam_audit = audit_info['famille_audit']
    
    # B. Map family to a valid v1 family
    mapped_fam = MANUAL_FAM_MAP.get((cat, fam_audit))
    if not mapped_fam:
        # Check if fam_audit is already a valid family in v1
        if fam_audit in valid_families:
            mapped_fam = fam_audit
        else:
            mapped_fam = list(valid_families)[0] # extreme fallback
            print(f"Warning: no family map for ({cat}, {fam_audit}) - fallback to {mapped_fam}")
    
    # Special refinement for Unités
    if cat == "Unités" and fam_audit == "unites":
        # Refine based on term
        term_lower = term_v2.lower()
        if any(w in term_lower for w in ["noeud", "kt", "vitesse", "km/h"]):
            mapped_fam = "unites_vitesse"
        elif any(w in term_lower for w in ["masse", "carburant", "kg", "gallon", "litre", "kilogramme", "livre"]):
            mapped_fam = "unites_masse_carburant"
        elif any(w in term_lower for w in ["altitude", "pression", "pied", "mètre", "ft", "hpa", "inhg", "millibar"]):
            mapped_fam = "unites_altitude_pression"
        else:
            mapped_fam = "unites_moteur_temps"
            
    # C. Handle Variant Conflicts
    # des `variantes` de fiches v2 sont des TERMES PRINCIPAUX en v1.
    # DÉCISION : RETIRER la variante côté v2, et à la place AJOUTER une xref v2 vers ce terme v1 (si pas déjà présente).
    variantes_v2 = fi.get('variantes', [])
    xrefs_v2 = list(fi.get('xrefs', []))
    
    clean_variantes = []
    for var in variantes_v2:
        norm_var = var.lower().strip()
        if norm_var in v1_terms_set:
            # Conflict! Remove from v2 variantes, add corresponding v1 term to xrefs
            v1_term_exact = v1_terms_set[norm_var]
            variants_removed_list.append({
                "v2_term": term_v2,
                "variant": var,
                "v1_term": v1_term_exact
            })
            if v1_term_exact not in xrefs_v2:
                xrefs_v2.append(v1_term_exact)
                xrefs_added_list.append({
                    "v2_term": term_v2,
                    "added_xref": v1_term_exact,
                    "reason": f"From conflict variant '{var}'"
                })
        else:
            clean_variantes.append(var)
            
    # D. Format according to v1 schema
    # Fields: definition, categorie, famille, variantes, xrefs, statut, origine, schema
    import_final_dict[term_v2] = {
        "definition": fi['definition'],
        "categorie": cat,
        "famille": mapped_fam,
        "variantes": clean_variantes,
        "xrefs": xrefs_v2,
        "statut": "redigee",  # convention canonique du projet (deux e)
        "origine": "v2-audit-ppl",
        "schema": False
    }

print(f"Processed fiches: {len(import_final_dict)}")
print(f"Variants removed: {len(variants_removed_list)}")
print(f"Xrefs added from variant conflicts: {len(xrefs_added_list)}")

# 7. Write data/lots-v2/IMPORT-FINAL.json
output_json_path = os.path.join(BASE_DIR, "data/lots-v2/IMPORT-FINAL.json")
os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
with open(output_json_path, 'w', encoding='utf-8') as f:
    json.dump(import_final_dict, f, ensure_ascii=False, indent=2)

print(f"Successfully wrote final JSON to {output_json_path}")
