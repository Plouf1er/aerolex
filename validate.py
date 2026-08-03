import json
import glob
import sys
import re

def load_all_valid_terms():
    valid = set()
    for p in glob.glob("projects/aerolex/data/lots-v2/LOT-*.json"):
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            for t in data["termes"]:
                valid.add(t["terme"].lower().strip())
    return valid

def validate_lot2(output_path):
    with open("projects/aerolex/data/lots-v2/LOT-2.json", "r", encoding="utf-8") as f:
        lot2_in = json.load(f)
    
    in_terms = {t["terme"].lower().strip(): t for t in lot2_in["termes"]}
    all_valid_terms = load_all_valid_terms()
    
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            out_data = json.load(f)
    except Exception as e:
        print(f"Error loading output file: {e}")
        return False
        
    if not isinstance(out_data, dict):
        print("Output must be a dict containing 'lot' and 'fiches'")
        return False
        
    if out_data.get("lot") != 2:
        print("Output 'lot' must be 2")
        return False
        
    fiches = out_data.get("fiches", [])
    if not isinstance(fiches, list):
        print("Output 'fiches' must be a list")
        return False
        
    if len(fiches) != len(in_terms):
        print(f"Number of fiches is {len(fiches)}, expected {len(in_terms)}")
        return False
        
    errors = []
    seen_terms = set()
    
    for idx, fiche in enumerate(fiches):
        terme = fiche.get("terme")
        if not terme:
            errors.append(f"Fiche {idx} is missing 'terme'")
            continue
            
        terme_key = terme.lower().strip()
        if terme_key not in in_terms:
            errors.append(f"Term '{terme}' is not in LOT-2.json")
            continue
            
        if terme_key in seen_terms:
            errors.append(f"Duplicate term '{terme}'")
        seen_terms.add(terme_key)
        
        # Check domain
        expected_domain = in_terms[terme_key]["domaine"]
        if fiche.get("domaine") != expected_domain:
            errors.append(f"[{terme}] expected domain '{expected_domain}', got '{fiche.get('domaine')}'")
            
        # Check definition
        defn = fiche.get("definition", "")
        words = defn.split()
        word_count = len(words)
        if word_count < 20 or word_count > 45:
            errors.append(f"[{terme}] definition length is {word_count} words (must be between 20 and 45)")
            
        # Check xrefs
        xrefs = fiche.get("xrefs", [])
        if not isinstance(xrefs, list):
            errors.append(f"[{terme}] 'xrefs' must be a list")
        elif len(xrefs) < 2:
            errors.append(f"[{terme}] has {len(xrefs)} xrefs (must be >= 2)")
        else:
            for xr in xrefs:
                xr_key = xr.lower().strip()
                if xr_key not in all_valid_terms:
                    errors.append(f"[{terme}] xref '{xr}' is not a valid term in the lexicon")
                    
        # Check HTML tags and entities
        if re.search(r"<[^>]+>", defn) or re.search(r"&[a-zA-Z0-9#]+;", defn):
            errors.append(f"[{terme}] definition contains HTML or HTML entity: {defn}")
            
        # Check specific numbers/aircraft models
        # (Aquila AT01, specific masses/speeds)
        # Let's search for common patterns like numbers followed by kt, kg, ft, hPa, etc.
        # But wait! General numbers (like 1.3 or 1013.25 or 1000 ft) are allowed if generic.
        # Let's check for specific models like "Aquila", "AT01", "C152", "DR400", "Boeing", "Airbus".
        for model in ["aquila", "at01", "c152", "dr400", "boeing", "airbus", "cessna", "robin"]:
            if model in defn.lower():
                errors.append(f"[{terme}] contains aircraft model '{model}': {defn}")
                
    if errors:
        print(f"Validation FAILED with {len(errors)} errors:")
        for err in errors[:20]:
            print(" -", err)
        if len(errors) > 20:
            print(f" ... and {len(errors) - 20} more errors")
        return False
        
    print("Validation PASSED!")
    # Print stats
    lens = [len(f["definition"].split()) for f in fiches]
    print(f"Count: {len(fiches)}")
    print(f"Min length: {min(lens)}")
    print(f"Max length: {max(lens)}")
    print(f"Avg length: {sum(lens)/len(lens):.2f}")
    print(f"Fiches with >=2 xrefs: {sum(1 for f in fiches if len(f.get('xrefs', [])) >= 2)}")
    return True

if __name__ == "__main__":
    if len(sys.argv) > 1:
        validate_lot2(sys.argv[1])
    else:
        print("Usage: python validate.py <output_path>")
