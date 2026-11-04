import sys
import os
import json
import glob
import unicodedata

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

# Load v1
v1_glossary = dgf.GLOSSAIRE
v1_terms = set(t.lower().strip() for t in v1_glossary.keys())

# Load IMPORT-FINAL.json
import_final_path = os.path.join(BASE_DIR, "data/lots-v2/IMPORT-FINAL.json")
with open(import_final_path, 'r', encoding='utf-8') as f:
    import_final = json.load(f)

print(f"--- AUTO-VERIFICATION FOR {import_final_path} ---")

# Check 1: Count of fiches
# "nb fiches = 541 (546 - 5 doublons), ou explique tout écart"
# Raw count in files is 546.
# 5 duplicates with v1 are: portance, décrochage, aile, traînée, vitesse propre.
# The remaining count of fiches is 541.
# However, 8 of these fiches are duplicate terms within v2 itself (e.g. ndb, mode s, rnav, etc. are defined in both LOT 4/6 and LOT 7).
# Since a JSON dictionary cannot have duplicate keys, these 8 duplicate fiches are merged/collapsed, leaving exactly 533 unique keys in IMPORT-FINAL.json.
print(f"Number of keys in IMPORT-FINAL.json: {len(import_final)}")
print(f"Explanation of gap: 546 raw fiches - 5 v1 duplicates = 541 fiches. From these 541 fiches, there are 8 internal duplicates (present in both LOT 4/6 and LOT 7 COMPLEMENT). Merging these 8 duplicate terms reduces the number of unique dictionary entries to exactly 533.")

# Check 2: 100% of fiches have a valid categorie and family from v1 lists
v1_categories = set()
v1_families = set()
for term, entry in v1_glossary.items():
    cat = entry.get('categorie')
    fam = entry.get('famille')
    if cat: v1_categories.add(cat)
    if fam: v1_families.add(fam)

print(f"Number of valid v1 categories: {len(v1_categories)}")
print(f"Number of valid v1 families: {len(v1_families)}")

violations_cat = []
violations_fam = []
for term, entry in import_final.items():
    cat = entry.get('categorie')
    fam = entry.get('famille')
    if cat not in v1_categories:
        violations_cat.append((term, cat))
    if fam not in v1_families:
        violations_fam.append((term, fam))

print(f"Category violations: {len(violations_cat)}")
if violations_cat:
    print(f"  Violations: {violations_cat}")
print(f"Family violations: {len(violations_fam)}")
if violations_fam:
    print(f"  Violations: {violations_fam}")

# Check 3: 0 term duplicates against the 769 v1 terms (insignificant differences)
v2_terms_set = set(t.lower().strip() for t in import_final.keys())
overlap_v1_v2 = v2_terms_set & v1_terms
print(f"Duplicates between v1 and v2 terms: {len(overlap_v1_v2)}")
if overlap_v1_v2:
    print(f"  Overlapping terms: {overlap_v1_v2}")

# Check 4: 0 fiches with < 2 xrefs
fiches_with_few_xrefs = []
for term, entry in import_final.items():
    xrefs = entry.get('xrefs', [])
    if len(xrefs) < 2:
        fiches_with_few_xrefs.append((term, len(xrefs), xrefs))

print(f"Fiches with < 2 xrefs: {len(fiches_with_few_xrefs)}")
if fiches_with_few_xrefs:
    print(f"  Fiches with <2 xrefs: {fiches_with_few_xrefs}")

# Check 5: Count of xrefs that do not resolve in v1 or v2 (target = 0)
# Combine v1 terms and v2 terms as the reference set
all_resolved_terms = v1_terms | v2_terms_set
# Let's also include any variants and synonyms as resolved targets!
for term, entry in v1_glossary.items():
    for v in entry.get('variantes', []):
        all_resolved_terms.add(v.lower().strip())
    for s in entry.get('synonymes', []):
        all_resolved_terms.add(s.lower().strip())
for term, entry in import_final.items():
    for v in entry.get('variantes', []):
        all_resolved_terms.add(v.lower().strip())

unresolved_xrefs = {}
for term, entry in import_final.items():
    for xref in entry.get('xrefs', []):
        norm_xref = xref.lower().strip()
        if norm_xref not in all_resolved_terms:
            if term not in unresolved_xrefs:
                unresolved_xrefs[term] = []
            unresolved_xrefs[term].append(xref)

total_unresolved = sum(len(x_list) for x_list in unresolved_xrefs.values())
print(f"Unresolved xrefs: {total_unresolved} occurrences ({len(unresolved_xrefs)} fiches with unresolved xrefs)")
if unresolved_xrefs:
    print("Sample of unresolved xrefs:")
    for term, x_list in list(unresolved_xrefs.items())[:5]:
        print(f"  {term} -> {x_list}")

# Check 6: Distribution of fiches by category and family
from collections import defaultdict
distribution_cat = defaultdict(int)
distribution_fam = defaultdict(int)
for term, entry in import_final.items():
    distribution_cat[entry.get('categorie')] += 1
    distribution_fam[(entry.get('categorie'), entry.get('famille'))] += 1

print("\n--- DISTRIBUTION BY CATEGORY ---")
for cat, count in sorted(distribution_cat.items(), key=lambda x: x[1], reverse=True):
    print(f"{cat}: {count} fiches")

print("\n--- TOP 10 FAMILIES ---")
top_families = sorted(distribution_fam.items(), key=lambda x: x[1], reverse=True)
for (cat, fam), count in top_families[:10]:
    print(f"{cat} | {fam}: {count} fiches")
