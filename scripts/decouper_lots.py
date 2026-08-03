import json
import os
from collections import Counter

def decouper_lots():
    # Définition des chemins
    base_dir = "projects/aerolex"
    audit_file = os.path.join(base_dir, "data/lots-v1/AUDIT-CONSOLIDE.json")
    output_dir = os.path.join(base_dir, "data/lots-v2")
    scripts_dir = os.path.join(base_dir, "scripts")
    
    # Création des dossiers si nécessaire
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(scripts_dir, exist_ok=True)
    
    # Lecture des données d'audit
    with open(audit_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    termes = data.get("termes", [])
    print(f"Chargé {len(termes)} termes depuis {audit_file}")
    
    # Vérification des doublons
    term_counts = Counter(t["terme"].lower().strip() for t in termes)
    doublons = [t for t, count in term_counts.items() if count > 1]
    if doublons:
        print(f"⚠️ DOUBLONS REPÉRÉS dans l'audit consolidé : {doublons}")
    else:
        print("Aucun doublon trouvé dans les termes d'audit.")
        
    # Ordre des domaines pour le regroupement
    dom_order = ["aero-perfs", "aerodrome", "meteo", "nav-radio", "regl-proc"]
    
    # Tri des termes pour grouper par domaine (ordre alphabétique / logique)
    # On trie d'abord par domaine (selon dom_order), puis pour chaque domaine
    # on maintient les termes
    termes_groupes = sorted(termes, key=lambda t: dom_order.index(t["domaine"]))
    
    # Découpage en 6 lots équilibrés : 5 lots de 89, 1 lot de 88
    tailles_lots = [89, 89, 89, 89, 89, 88]
    lots = []
    
    current_idx = 0
    for i, taille in enumerate(tailles_lots):
        lot_num = i + 1
        lot_termes = termes_groupes[current_idx : current_idx + taille]
        current_idx += taille
        
        # Pour chaque lot, on trie : priorité haute d'abord, puis moyenne, puis basse
        prio_order = {"haute": 0, "moyenne": 1, "basse": 2}
        lot_termes_tries = sorted(lot_termes, key=lambda t: prio_order.get(t.get("priorite", "haute"), 0))
        
        # Détermination du domaine principal
        dom_counts = Counter(t["domaine"] for t in lot_termes_tries)
        domaine_principal = dom_counts.most_common(1)[0][0]
        
        lot_data = {
            "lot": lot_num,
            "domaine_principal": domaine_principal,
            "termes": lot_termes_tries
        }
        
        lots.append(lot_data)
        
        # Écriture de LOT-N.json
        out_file = os.path.join(output_dir, f"LOT-{lot_num}.json")
        with open(out_file, "w", encoding="utf-8") as f_out:
            json.dump(lot_data, f_out, indent=2, ensure_ascii=False)
            
        print(f"Écrit Lot {lot_num} : {len(lot_termes_tries)} termes, domaine principal = {domaine_principal}, écrit dans {out_file}")
        
    # Écriture de DECOUPAGE.md
    decoupage_file = os.path.join(output_dir, "DECOUPAGE.md")
    with open(decoupage_file, "w", encoding="utf-8") as f_md:
        f_md.write("# Découpage des lots de rédaction d'AeroLex\n\n")
        f_md.write("| Lot | Domaine principal | Nb termes |\n")
        f_md.write("| :--- | :--- | :--- |\n")
        for lot in lots:
            f_md.write(f"| Lot {lot['lot']} | {lot['domaine_principal']} | {len(lot['termes'])} |\n")
            
    print(f"Écrit {decoupage_file}")

if __name__ == "__main__":
    decouper_lots()
