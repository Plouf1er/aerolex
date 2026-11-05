#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
term_expansions.py — développés OFFICIELS des sigles/abréviations AeroLex.

Règle de Louis (2026-11-03/04) : tout acronyme/abréviation est développé juste
sous le titre de la fiche (et entre parenthèses dans l'index) :
    « EAS — Equivalent Airspeed (vitesse équivalente) »
    « OACI — Organisation de l'aviation civile internationale (ICAO — ...) »
Forme d'origine (anglaise ou française) + traduction française entre
parenthèses quand l'original est anglais.

Consommé par term_display.compute_entry() (donc HTML + popup + index + recherche).
Le sens retenu est celui de la DÉFINITION de la fiche (ex. AD = aérodrome ; en contexte
entretien / navigabilité, le moteur aiguille AD vers « consignes de navigabilité » : champ homonyme).

Format : clé GLOSSAIRE -> (développement, équivalent FR | None, flags)
flags : "U" = titre en MAJUSCULES, "N" = ne pas insérer le développement dans
le texte des autres définitions (Q-codes, unités, codes météo…).
"""
from __future__ import annotations

import re

EXPANSIONS = {
    # ── Organismes / espaces / publications ────────────────────────────────
    "ACC":   ("Area Control Centre", "centre de contrôle régional", ""),
    "AD":    ("Aerodrome", "aérodrome", ""),
    "AIC":   ("Aeronautical Information Circular", "circulaire d'information aéronautique", ""),
    "APP":   ("Approach Control", "contrôle d'approche", ""),
    "AWY":   ("Airway", "voie aérienne", ""),
    # Documents de bord : sens confirmé par la séance 017 (« CDN (certificat de navigabilité) »,
    # « CEN (certificat d'examen de navigabilité) », ARC = ex-CEN) — 2026-11-04.
    "CDN":   ("Certificat de navigabilité", "CofA — Certificate of Airworthiness", ""),
    "CEN":   ("Certificat d'examen de navigabilité", "équivalent français de l'ARC — Airworthiness Review Certificate", ""),
    "TWR":   ("Aerodrome Control Tower", "tour de contrôle d'aérodrome", ""),
    "siv":   ("Service d'information de vol", "Flight Information Service", "U"),
    "SAR":   ("Search and Rescue", "recherche et sauvetage", ""),
    "SSLIA": ("Service de sauvetage et de lutte contre l'incendie des aéronefs",
              "RFFS — Rescue and Firefighting Services", ""),
    "oaci":  ("Organisation de l'aviation civile internationale",
              "ICAO — International Civil Aviation Organization", "U"),
    "ALERFA":   ("Alert phase", "phase d'alerte (mot de code OACI)", ""),
    "INCERFA":  ("Uncertainty phase", "phase d'incertitude (mot de code OACI)", ""),
    "DETRESFA": ("Distress phase", "phase de détresse (mot de code OACI)", ""),
    "LAPL":  ("Light Aircraft Pilot Licence", "licence de pilote d'aéronef léger", ""),
    "volmet": ("Meteorological information for aircraft in flight",
               "informations météorologiques pour aéronefs en vol", "U"),
    "sigmet": ("Significant Meteorological Information",
               "information météorologique significative", "U"),
    "airmet": ("Airmen's Meteorological Information",
               "information météorologique pour les aéronefs à basse altitude", "U"),
    "gamet":  ("Area forecast for low-level flights",
               "prévision de zone pour les vols à basse altitude", "U"),
    "temsi":  ("Temps significatif", "Significant Weather Chart", "U"),
    "wintem": ("WINd and TEMperature", "vent et température en altitude", "U"),
    "metar/taf": ("METeorological Aerodrome Report / Terminal Aerodrome Forecast",
                  "observation / prévision d'aérodrome", "U"),
    "utc":   ("Coordinated Universal Time", "temps universel coordonné", "U"),
    "rnav":  ("Area Navigation", "navigation de surface", "U"),
    "rvr":   ("Runway Visual Range", "portée visuelle de piste", "U"),
    "VASIS":   ("Visual Approach Slope Indicator System", "indicateur visuel de pente d'approche", ""),
    "T-VASIS": ("T Visual Approach Slope Indicator System",
                "indicateur visuel de pente d'approche en T", ""),
    "100LL": ("100 octane Low Lead", "essence aviation à faible teneur en plomb", ""),
    "ul91":  ("Unleaded 91 (octane)", "essence aviation sans plomb 91 octanes", "U"),
    "DODAR": ("Diagnosis, Options, Decision, Assign, Review",
              "diagnostic, options, décision, attribution, revue", ""),
    "imsafe": ("Illness, Medication, Stress, Alcohol, Fatigue, Emotion",
               "maladie, médicaments, stress, alcool, fatigue, émotion", "U"),
    "cg":    ("Centre of Gravity", "centre de gravité", "U"),
    "mtom":  ("Maximum Take-Off Mass", "masse maximale au décollage", "U"),
    "MTOW":  ("Maximum Take-Off Weight", "masse maximale au décollage", ""),
    "pax":   ("Passengers", "passagers", "U"),
    "alt":   ("Altitude", "ou mode ALT du transpondeur (transmission de l'altitude)", "U"),
    "mag":   ("Magnetic", "magnétique", "U"),
    "com":   ("Communication", "radiocommunication", "U"),
    "nav":   ("Navigation", "navigation", "U"),
    "prop":  ("Propeller", "hélice", ""),
    "prob":  ("Probability", "probabilité", "U"),
    "t/o":   ("Take-Off", "décollage", "U"),
    # ── Coefficients aérodynamiques (symboles) ────────────────────────────
    "Cd": ("Section Drag Coefficient", "coefficient de traînée de profil", ""),
    "Cl": ("Section Lift Coefficient", "coefficient de portance de profil", ""),
    "Cx": ("Coefficient de traînée", "Drag Coefficient", ""),
    "Cz": ("Coefficient de portance", "Lift Coefficient", ""),
    # ── Vitesses caractéristiques ─────────────────────────────────────────
    "VA":    ("Maneuvering Speed", "vitesse de manœuvre", ""),
    "Vapp":  ("Approach Speed", "vitesse d'approche finale", ""),
    "VBG":   ("Best Glide Speed", "vitesse de meilleure finesse", ""),
    "VG":    ("Best Glide Speed", "vitesse de meilleur plané", ""),
    "VLO":   ("Maximum Landing Gear Operating Speed", "vitesse maximale de manœuvre du train", ""),
    "vle":   ("Maximum Landing Gear Extended Speed", "vitesse maximale train sorti", "U"),
    "Vlof":  ("Lift-Off Speed", "vitesse de décollage (envol)", ""),
    "VRA":   ("Rough Air Speed", "vitesse en air turbulent", ""),
    "vr":    ("Rotation Speed", "vitesse de rotation", "U"),
    "Vref":  ("Reference Landing Speed", "vitesse de référence à l'atterrissage", ""),
    "Vtoss": ("Take-Off Safety Speed", "vitesse de sécurité au décollage", ""),
    "Vx":    ("Best Angle of Climb Speed", "vitesse du meilleur angle de montée", ""),
    "Vy":    ("Best Rate of Climb Speed", "vitesse du meilleur taux de montée", ""),
    "VFE":   ("Maximum Flap Extended Speed", "vitesse maximale volets sortis", ""),
    "VNE":   ("Never Exceed Speed", "vitesse à ne jamais dépasser", ""),
    "VNO":   ("Maximum Structural Cruising Speed", "vitesse maximale de croisière structurale", ""),
    "VS0":   ("Stall Speed in Landing Configuration",
              "vitesse de décrochage en configuration d'atterrissage", ""),
    "VS1":   ("Stall Speed in Clean Configuration",
              "vitesse de décrochage en configuration lisse", ""),
    # ── Q-codes (codes, pas des acronymes : sens du code) ─────────────────
    "QNH": ("Q-code — altimeter setting to sea level",
            "calage altimétrique sur la pression ramenée au niveau de la mer", "N"),
    "QNE": ("Q-code — standard altimeter setting (1013.25 hPa)",
            "calage altimétrique standard", "N"),
    "QFE": ("Q-code — aerodrome-elevation pressure setting",
            "calage altimétrique sur la pression de l'aérodrome", "N"),
    "QFU": ("Q-code — magnetic orientation of the runway",
            "orientation magnétique de la piste", "N"),
    "qdm": ("Q-code — magnetic heading to the station (zero wind)",
            "cap magnétique pour rejoindre la station", "UN"),
    "qdr": ("Q-code — magnetic bearing from the station",
            "relèvement magnétique depuis la station", "UN"),
    "QTE": ("Q-code — true bearing from the station",
            "relèvement vrai depuis la station", "N"),
    "QUJ": ("Q-code — true track to the station",
            "route vraie pour rejoindre la station", "N"),
    # ── Unités ────────────────────────────────────────────────────────────
    "ft":     ("Foot (feet)", "pied", "N"),
    "ft/min": ("Feet per minute", "pieds par minute", "N"),
    "kt":     ("Knot", "nœud", "N"),
    "kg":     ("Kilogram", "kilogramme", "N"),
    "kg/l":   ("Kilograms per litre", "kilogramme par litre", "N"),
    "km":     ("Kilometre", "kilomètre", "N"),
    "km/h":   ("Kilometres per hour", "kilomètres par heure", "N"),
    "l/h":    ("Litres per hour", "litres par heure", "N"),
    "m/s":    ("Metres per second", "mètres par seconde", "N"),
    "inHg":   ("Inches of mercury", "pouces de mercure", "N"),
    "°C":     ("Degrees Celsius", "degrés Celsius", "N"),
    # ── Codes météo METAR/TAF ─────────────────────────────────────────────
    "bkn":  ("Broken", "nuages fragmentés (5 à 7 octas)", "UN"),
    "few":  ("Few", "quelques nuages (1 à 2 octas)", "UN"),
    "ovc":  ("Overcast", "ciel couvert (8 octas)", "UN"),
    "sct":  ("Scattered", "nuages épars (3 à 4 octas)", "UN"),
    "br":   ("Mist", "brume", "UN"),
    "cu":   ("Cumulus", None, "UN"),
    "ds":   ("Duststorm", "tempête de poussière", "UN"),
    "dz":   ("Drizzle", "bruine", "UN"),
    "fg":   ("Fog", "brouillard", "UN"),
    "fu":   ("Smoke", "fumée", "UN"),
    "fz":   ("Freezing", "se congelant (verglaçant)", "UN"),
    "gr":   ("Hail", "grêle", "UN"),
    "hz":   ("Haze", "brume sèche", "UN"),
    "po":   ("Dust/Sand Whirls (Dust Devils)", "tourbillons de poussière ou de sable", "UN"),
    "ra":   ("Rain", "pluie", "UN"),
    "sh":   ("Showers", "averses", "UN"),
    "shra": ("Shower Rain", "averses de pluie", "UN"),
    "sn":   ("Snow", "neige", "UN"),
    "sq":   ("Squall", "grain", "UN"),
    "ss":   ("Sandstorm", "tempête de sable", "UN"),
    "ts":   ("Thunderstorm", "orage", "UN"),
    "vc":   ("In the Vicinity", "au voisinage de l'aérodrome", "UN"),
    "vrb":  ("Variable", "direction de vent variable", "UN"),
    # ajoutés par validate_batch (titres à trait d'union : développé non calculable automatiquement)
    "CS-VLA": ("Certification Specifications for Very Light Aeroplanes", "spécifications de certification des avions très légers", ""),
    "Part-NCO": ("Non-Commercial Operations with other-than-complex motor-powered aircraft", "exploitation non commerciale d'aéronefs à moteur non complexes", ""),
    "Part-MED": ("Medical requirements", "exigences médicales", ""),
    "Part-FCL": ("Flight Crew Licensing", "licences des équipages de conduite", ""),
}

# Compléments FR pour des développés déjà calculés depuis les données mais
# affichés sans traduction (clé -> (développement corrigé | None, équivalent)).
# Le développement n'est remplacé que s'il est donné (1er élément non None).
GLOSS_FIX = {
    "AAL": (None, "hauteur au-dessus du niveau de l'aérodrome"),
    "adf": (None, "radiocompas"),
    "afis": (None, "service d'information de vol d'aérodrome"),
    "agl": (None, "hauteur au-dessus du sol"),
    "AIP": (None, "publication d'information aéronautique"),
    "AIRAC": (None, "régulation et contrôle de l'information aéronautique"),
    "AMSL": (None, "altitude au-dessus du niveau moyen de la mer"),
    "ASDA": (None, "distance d'accélération-arrêt utilisable"),
    "asi": (None, "anémomètre (badin)"),
    "atc": (None, "contrôle de la circulation aérienne"),
    "ATIS": (None, "service automatique d'information de région terminale"),
    "ats": (None, "services de la circulation aérienne"),
    "atz": (None, "zone de trafic d'aérodrome"),
    "BECMG": (None, "devenant"),
    "cas": ("Calibrated Airspeed", "vitesse conventionnelle (corrigée)"),
    "cat": (None, "turbulence en air clair"),
    "CAVOK": (None, "plafond et visibilité OK"),
    "cht": (None, "température de culasse"),
    "crm": (None, "gestion des ressources de l'équipage"),
    "dalr": (None, "gradient adiabatique sec"),
    "DME": (None, "équipement de mesure de distance"),
    "easa": (None, "Agence de l'Union européenne pour la sécurité aérienne"),
    "eet": (None, "durée estimée de vol"),
    "elr": (None, "gradient thermique ambiant"),
    "eta": (None, "heure estimée d'arrivée"),
    "EOBT": (None, "heure estimée de départ bloc"),
    "fc": ("Funnel Cloud", "nuage en entonnoir (tuba)"),
    "fi": (None, "instructeur de vol"),
    "fir": (None, "région d'information de vol"),
    "fpl": (None, "plan de vol"),
    "gnss": (None, "système mondial de navigation par satellite"),
    "gps": (None, "système mondial de positionnement"),
    "iac": (None, "carte d'approche aux instruments"),
    "IMC": (None, "conditions météorologiques de vol aux instruments"),
    "ils": (None, "système d'atterrissage aux instruments"),
    "ktas": (None, "nœuds en vitesse propre"),
    "LDA": (None, "distance d'atterrissage utilisable"),
    "ldg": ("Landing", "atterrissage"),
    "MEF": (None, "altitude maximale des obstacles de la case"),
    "METAR": ("Meteorological Aerodrome Report", "message d'observation météorologique d'aérodrome"),
    "MORA": (None, "altitude minimale hors route"),
    "ndb": (None, "radiophare non directionnel"),
    "NOSIG": (None, "pas de changement significatif"),
    "NOTAM": (None, "avis aux navigants"),
    "NSW": (None, "pas de phénomène météo significatif"),
    "oat": (None, "température extérieure de l'air"),
    "PAPI": (None, "indicateur de trajectoire d'approche de précision"),
    "PCL": (None, "balisage lumineux commandé par le pilote"),
    "PCN": (None, "numéro de classification de chaussée"),
    "POH": ("Pilot's Operating Handbook", "manuel d'utilisation du pilote (manuel de vol)"),
    "ppl": ("Private Pilot Licence", "licence de pilote privé"),
    "PROB30": (None, "probabilité de 30 %"),
    "PROB40": (None, "probabilité de 40 %"),
    "psi": (None, "livres par pouce carré"),
    "RESA": (None, "aire de sécurité d'extrémité de piste"),
    "RFFS": (None, "service de sauvetage et de lutte contre l'incendie (SSLIA)"),
    "rmz": (None, "zone à utilisation obligatoire de la radio"),
    "rpm": (None, "tours par minute"),
    "sep": (None, "monomoteur à pistons"),
    "SPECI": (None, "message d'observation spéciale"),
    "tcds": (None, "fiche de données du certificat de type"),
    "tem": (None, "gestion des menaces et des erreurs"),
    "TL": (None, "niveau de transition"),
    "tmz": (None, "zone à utilisation obligatoire du transpondeur"),
    "tod": (None, "point de début de descente"),
    "TODA": (None, "distance de décollage utilisable"),
    "TORA": (None, "distance de roulement utilisable au décollage"),
    "uir": (None, "région supérieure d'information de vol"),
    "VAC": (None, "carte d'approche à vue"),
    "VMC": (None, "conditions météorologiques de vol à vue"),
    "vor": ("VHF Omnidirectional Range", "radiophare omnidirectionnel VHF"),
    "wca": (None, "angle de correction de dérive"),
    "WILCO": ("Will comply", "je me conformerai"),
    "ETD": (None, None),
    "NDB": (None, "radiophare non directionnel"),
    "EOBT": (None, "heure estimée de départ bloc"),
    "PROB30": (None, "probabilité de 30 %"),
    "dgac": (None, None),
}

# Sigles/abréviations SANS fiche propre mais cités dans des libellés ou alias
# (ex. alias « KIAS » de la fiche IAS) : développé + équivalent FR. Même format
# que EXPANSIONS ; consommé par term_display.extra_info() (HTML + popup).
EXTRA_ABBREVIATIONS = {
    "KIAS": ("Knots Indicated Airspeed", "vitesse indiquée en nœuds", ""),
    # ajoutés via « Suggérer des termes » (développé vérifié : initiales = sigle)
    "VHF": ("Very High Frequency", "très haute fréquence", ""),
    "UHF": ("Ultra High Frequency", "Ultra haute fréquence", ""),
    "FAA": ("Federal Aviation Administration", "autorité de l'aviation civile américaine", ""),
    "NSC": ("No Significant Cloud", "pas de nuage significatif", ""),
    "NCD": ("No Cloud Detected", "aucun nuage détecté", ""),
    "OBS": ("Omni Bearing Selector", "sélecteur de radial", ""),
    "CDI": ("Course Deviation Indicator", "indicateur d'écart de route", ""),
    "ULM": ("Ultra Léger Motorisé", None, ""),
    "BEA": ("Bureau d'Enquêtes et d'Analyses pour la sécurité de l'aviation civile", None, ""),
    "AVGAS": ("Aviation Gasoline", "essence aviation", ""),
    "OMM": ("Organisation météorologique mondiale", None, ""),
    "ATA": ("Actual Time of Arrival", "heure d'arrivée réelle", ""),
    "ATO": ("Approved Training Organisation", "organisme de formation agréé", ""),
    "DTO": ("Declared Training Organisation", "organisme de formation déclaré", ""),
    "MAC": ("Mean Aerodynamic Chord", "corde aérodynamique moyenne", ""),
    "UE": ("Union européenne", None, ""),
    "POB": ("Persons On Board", "personnes à bord", ""),
    "CS": ("Certification Specifications", "spécifications de certification", ""),
    "AIRPROX": ("Aircraft Proximity", "rapprochement dangereux", ""),
    "TUC": ("Time of Useful Consciousness", "temps utile de conscience", ""),
    "SERA": ("Standardised European Rules of the Air", "règles de l'air européennes standardisées", ""),
    "ASFC": ("Above Surface", "au-dessus de la surface", ""),
}

# Mots/phrases dont le calcul automatique tire un « développement » qui n'en est
# pas un (mot ordinaire, répétition du titre, junk) : on n'affiche rien.
NOT_ACRONYMS = {
    "CLEARED", "STANDBY", "flaps", "holding", "idle", "ignition", "pump",
    "dorsale", "harnais", "jauge",
}

# Entrées ressemblant à des sigles mais DONT LE SENS EST DOUTEUX dans les
# données : volontairement non développées (à valider par Louis).
# Les mots de code radio (AFFIRM…) ne sont pas des acronymes.
UNRESOLVED = {
    "APRS":  "définition : « autorisation spéciale » en zone réglementée/dangereuse ; sigle absent des séances et du POH, sens non confirmé (hypothèse : Approbation pour remise en service / CRS, à valider par Louis)",
    "7000 (VFR)": "code transpondeur, pas un acronyme (contient VFR)",
}
CODEWORDS = {"AFFIRM", "NEGATIVE", "HOLD SHORT", "LINE UP", "PAN PAN", "GO/NO GO", "no-go"}

_ICAO = re.compile(r"^Code OACI de (?:la |l'|le |les )?(.+?)\.\s", re.S)
_ICAO_KEY = re.compile(r"^lf[a-z]{2}$", re.I)


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:]


def icao_expansion(key: str, definition: str):
    """'lfpn' + « Code OACI de l'aérodrome de Toussus-le-Noble. » ->
    ('Aérodrome de Toussus-le-Noble', 'code OACI'). None si pas un code OACI."""
    if not _ICAO_KEY.match(key or ""):
        return None
    m = _ICAO.match((definition or "").strip() + " ")
    if not m:
        return None
    return _cap(m.group(1).strip()), "code OACI d'aérodrome"


def lookup(key: str, meta: dict):
    """-> (expansion, gloss, upper, inline) ou None si pas de développé curaté."""
    e = EXPANSIONS.get(key)
    if e:
        exp, gloss, flags = e
        return exp, gloss, ("U" in flags), ("N" not in flags)
    ic = icao_expansion(key, (meta or {}).get("definition") or "")
    if ic:
        return ic[0], ic[1], True, False
    return None
