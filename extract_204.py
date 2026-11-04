import sys
import json
from data.data_glossaire_full import GLOSSAIRE
import os
sys.path.insert(0, os.environ.get('AEROLEX_HOST_PROJECT', '.'))   # dossier du projet hôte qui porte data_glossaire._LOCAL_OVERLAY (facultatif)
try:
    from data_glossaire import _LOCAL_OVERLAY
except ImportError:
    _LOCAL_OVERLAY = {}

inherited = []
for k, v in GLOSSAIRE.items():
    if v.get("schema") is True:
        if k in _LOCAL_OVERLAY and isinstance(_LOCAL_OVERLAY[k].get("schema"), str):
            continue
        inherited.append({
            "terme": k,
            "categorie": v.get("categorie", ""),
            "famille": v.get("famille", "")
        })

with open("data/schemas-candidats-heritage.json", "w", encoding="utf-8") as f:
    json.dump(inherited, f, indent=2, ensure_ascii=False)
