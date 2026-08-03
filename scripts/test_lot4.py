# -*- coding: utf-8 -*-
import json
import os
import re

BASE_DIR = "/Users/aprunel/.openclaw/workspace/projects/aerolex"
LOT4_PATH = os.path.join(BASE_DIR, "data/lots-v2/LOT-4.json")
VALID_TERMS_PATH = os.path.join(BASE_DIR, "data/lots-v2/all_valid_terms.json")
REDIGE4_PATH = os.path.join(BASE_DIR, "data/lots-v2/REDIGE-LOT-4.json")

def run_verification():
    with open(LOT4_PATH, "r", encoding="utf-8") as f:
        lot_in = json.load(f)
    
    with open(REDIGE4_PATH, "r", encoding="utf-8") as f:
        lot_out = json.load(f)
        
    with open(VALID_TERMS_PATH, "r", encoding="utf-8") as f:
        all_valid_list = json.load(f)
    all_valid_set = set(t.lower().strip() for t in all_valid_list)
    
    in_terms = {t["terme"].lower().strip(): t for t in lot_in["termes"]}
    fiches = lot_out.get("fiches", [])
    
    errors = []
    seen_terms = set()
    lengths = []
    domains_count = {}
    
    # Global checks
    if lot_out.get("lot") != 4:
        errors.append(f"Expected lot number 4, got {lot_out.get('lot')}")
        
    if len(fiches) != len(lot_in["termes"]):
        errors.append(f"Expected {len(lot_in['termes'])} fiches, got {len(fiches)}")
        
    for idx, fiche in enumerate(fiches):
        terme = fiche.get("terme")
        if not terme:
            errors.append(f"Fiche {idx} is missing 'terme'")
            continue
            
        terme_key = terme.lower().strip()
        if terme_key not in in_terms:
            errors.append(f"Term '{terme}' is not in LOT-4.json")
            continue
            
        if terme_key in seen_terms:
            errors.append(f"Duplicate term '{terme}'")
        seen_terms.add(terme_key)
        
        # Check domain
        expected_domain = in_terms[terme_key]["domaine"]
        actual_domain = fiche.get("domaine")
        if actual_domain != expected_domain:
            errors.append(f"[{terme}] expected domain '{expected_domain}', got '{actual_domain}'")
        else:
            domains_count[actual_domain] = domains_count.get(actual_domain, 0) + 1
            
        # Check definition word count
        defn = fiche.get("definition", "")
        words = defn.split()
        word_count = len(words)
        lengths.append(word_count)
        if word_count < 20 or word_count > 45:
            errors.append(f"[{terme}] definition length is {word_count} words (must be 20-45)")
            
        # Check xrefs
        xrefs = fiche.get("xrefs", [])
        if not isinstance(xrefs, list):
            errors.append(f"[{terme}] 'xrefs' must be a list")
        elif len(xrefs) < 2:
            errors.append(f"[{terme}] has {len(xrefs)} xrefs (must be >= 2)")
        else:
            for xr in xrefs:
                xr_key = xr.lower().strip()
                if xr_key not in all_valid_set:
                    errors.append(f"[{terme}] xref '{xr}' is not a valid term in the lexicon")
                    
        # Check HTML tags and entities
        if re.search(r"<[^>]+>", defn) or re.search(r"&[a-zA-Z0-9#]+;", defn):
            errors.append(f"[{terme}] definition contains HTML or HTML entity: {defn}")
            
        # Check specific numbers/aircraft models
        for model in ["aquila", "at01", "c152", "dr400", "boeing", "airbus", "cessna", "robin"]:
            if model in defn.lower():
                errors.append(f"[{terme}] contains aircraft model '{model}': {defn}")
                
    if errors:
        print(f"FAILED with {len(errors)} errors:")
        for err in errors[:20]:
            print(" -", err)
        if len(errors) > 20:
            print(f" ... and {len(errors) - 20} more errors")
    else:
        print("ALL CONSTRAINTS PASSED PERFECTLY!")
        print(f"Count: {len(fiches)}")
        print(f"Min length: {min(lengths)} words")
        print(f"Max length: {max(lengths)} words")
        print(f"Avg length: {sum(lengths)/len(lengths):.2f} words")
        print(f"Fiches with >= 2 xrefs: {sum(1 for f in fiches if len(f.get('xrefs', [])) >= 2)}")
        print(f"Domains distribution: {domains_count}")

if __name__ == "__main__":
    run_verification()
