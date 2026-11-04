import sys
import os
import json
import glob
import unicodedata
import re
import requests

# Set paths
import os as _os
BASE_DIR = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))   # racine du projet
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
print(f"Loaded v1 glossary: {len(v1_glossary)} terms")

# Extract valid categories and families from v1 glossary
valid_categories = set()
valid_families = set()
for term, entry in v1_glossary.items():
    cat = entry.get('categorie')
    fam = entry.get('famille')
    if cat: valid_categories.add(cat)
    if fam: valid_families.add(fam)

print(f"Valid v1 categories: {len(valid_categories)}")
print(f"Valid v1 families (non-None): {len(valid_families)}")

# 2. Load v2 raw lots
v2_files = sorted(glob.glob(os.path.join(BASE_DIR, "data/lots-v2/REDIGE-LOT-*.json")))
v2_fiches_all = []
for f_path in v2_files:
    with open(f_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
        v2_fiches_all.extend(d.get('fiches', []))

print(f"Loaded v2 fiches from raw lots: {len(v2_fiches_all)}")

# Let's see the 5 duplicates with v1
v1_terms_normalized = {normalize(t): t for t in v1_glossary.keys()}
duplicates_with_v1 = []
for fi in v2_fiches_all:
    term_v2 = fi['terme']
    norm_v2 = normalize(term_v2)
    if norm_v2 in v1_terms_normalized:
        duplicates_with_v1.append((term_v2, v1_terms_normalized[norm_v2], fi))

# Deduplicate duplicates with v1 (only unique ones)
seen_dup = set()
unique_duplicates_with_v1 = []
for term_v2, term_v1, fi in duplicates_with_v1:
    if normalize(term_v2) not in seen_dup:
        seen_dup.add(normalize(term_v2))
        unique_duplicates_with_v1.append((term_v2, term_v1, fi))

print(f"Duplicates with v1: {len(unique_duplicates_with_v1)}")
for d in unique_duplicates_with_v1:
    print(f"  v2: {d[0]} vs v1: {d[1]}")

# 3. Handle duplicates within v2 itself (internal duplicates)
# Let's map normalized term to list of fiches
v2_by_term = {}
for fi in v2_fiches_all:
    term_v2 = fi['terme']
    norm_v2 = normalize(term_v2)
    if norm_v2 not in v2_by_term:
        v2_by_term[norm_v2] = []
    v2_by_term[norm_v2].append(fi)

# Check which ones are duplicates
internal_duplicates = []
for norm_term, f_list in v2_by_term.items():
    if len(f_list) > 1:
        # Check where they come from
        internal_duplicates.append((norm_term, f_list))

print(f"Internal duplicates within v2: {len(internal_duplicates)}")

# Filter out duplicates with v1 first
v2_fiches_filtered = []
seen_terms = set()

# Since REDIGE-LOT-7-COMPLEMENT has the most up-to-date and revised entries, we should prefer fiches from LOT 7 if there's an internal duplicate, or otherwise keep the first one we find.
# Let's sort the occurrences so that REDIGE-LOT-7-COMPLEMENT comes first when resolving duplicates!
def is_complement(fi):
    # We don't have file path here, but wait, we can trace it back or tag them
    pass

# Let's reload v2 fiches and tag them with their source file path
v2_fiches_tagged = []
for f_path in v2_files:
    file_name = os.path.basename(f_path)
    with open(f_path, 'r', encoding='utf-8') as f:
        d = json.load(f)
        for fi in d.get('fiches', []):
            fi_copy = dict(fi)
            fi_copy['_source_file'] = file_name
            v2_fiches_tagged.append(fi_copy)

# Filter out the 5 duplicates with v1
dup_v1_set = {normalize(t) for t in ['portance', 'décrochage', 'aile', 'traînée', 'vitesse propre']}
v2_fiches_no_v1_dup = [f for f in v2_fiches_tagged if normalize(f['terme']) not in dup_v1_set]

print(f"Fiches after removing v1 duplicates: {len(v2_fiches_no_v1_dup)}")

# Deduplicate v2 internal duplicates:
# For each unique term, if it appears multiple times, we prefer REDIGE-LOT-7-COMPLEMENT.json
v2_by_term_unique = {}
for fi in v2_fiches_no_v1_dup:
    norm_t = normalize(fi['terme'])
    if norm_t not in v2_by_term_unique:
        v2_by_term_unique[norm_t] = fi
    else:
        # We already have an entry, let's see which one to keep
        existing = v2_by_term_unique[norm_t]
        if fi['_source_file'] == 'REDIGE-LOT-7-COMPLEMENT.json':
            # Override with COMPLEMENT
            v2_by_term_unique[norm_t] = fi
        elif existing['_source_file'] == 'REDIGE-LOT-7-COMPLEMENT.json':
            # Keep COMPLEMENT
            pass
        else:
            # Keep existing
            pass

final_v2_fiches = list(v2_by_term_unique.values())
print(f"Final unique v2 fiches to import: {len(final_v2_fiches)}")
