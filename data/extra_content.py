# -*- coding: utf-8 -*-
"""Contenu additionnel injecte dans certaines fiches, par slug.

Sert au contenu tabulaire/pedagogique qui appartient a UNE page precise et
qu'il serait absurde d'eclater en fiches de glossaire (ex: les 26 lettres de
l'alphabet OACI : creer 26 entrees surlignables n'aurait aucun interet).

Regle : ce HTML est du CONTENU DE PAGE, pas des termes. Aucun <span class="glos">
la-dedans, donc rien n'est surligne ni transforme en lien par le JS.
"""

# Alphabet phonetique OACI : lettre, mot, prononciation recommandee OACI.
ALPHABET_OACI = [
    ("A", "Alpha",    "AL-FAH"),      ("N", "November", "NO-VEMM-BER"),
    ("B", "Bravo",    "BRA-VO"),      ("O", "Oscar",    "OSS-KAR"),
    ("C", "Charlie",  "TCHAR-LI"),    ("P", "Papa",     "PA-PAH"),
    ("D", "Delta",    "DELL-TAH"),    ("Q", "Quebec",   "KE-BECK"),
    ("E", "Echo",     "EK-O"),        ("R", "Romeo",    "RO-MI-O"),
    ("F", "Foxtrot",  "FOX-TROTT"),   ("S", "Sierra",   "SI-AIR-RAH"),
    ("G", "Golf",     "GOLF"),        ("T", "Tango",    "TANG-GO"),
    ("H", "Hotel",    "HO-TELL"),     ("U", "Uniform",  "YOU-NI-FORM"),
    ("I", "India",    "IN-DI-AH"),    ("V", "Victor",   "VIK-TAR"),
    ("J", "Juliett",  "DJOU-LI-ETT"), ("W", "Whiskey",  "WISS-KI"),
    ("K", "Kilo",     "KI-LO"),       ("X", "X-ray",    "EKSS-RE"),
    ("L", "Lima",     "LI-MAH"),      ("Y", "Yankee",   "YANG-KI"),
    ("M", "Mike",     "MAIK"),        ("Z", "Zulu",     "ZOU-LOU"),
]

CHIFFRES_OACI = [
    ("0", "Zero", "ZI-RO"), ("1", "Unaone", "OU-NA-OUANN"),
    ("2", "Bissotwo", "BIS-SO-TOU"), ("3", "Terrathree", "TE-RA-TRI"),
    ("4", "Kartefour", "KAR-TE-FOR"), ("5", "Pantafive", "PANN-TA-FAIV"),
    ("6", "Soxisix", "SOK-SI-SIKS"), ("7", "Setteseven", "SET-TE-SEVEN"),
    ("8", "Oktoeight", "OK-TO-EIT"), ("9", "Novenine", "NO-VE-NAIN"),
    ("100", "Hundred", "HANN-DRED"), ("1000", "Thousand", "TAOU-ZEND"),
]


def _table_alphabet():
    # Deux colonnes cote a cote : A-M et N-Z (l'ordre de la liste alterne deja).
    rows = ""
    for i in range(0, len(ALPHABET_OACI), 2):
        g, d = ALPHABET_OACI[i], ALPHABET_OACI[i + 1]
        rows += (
            "<tr>"
            f"<td class='alx-l'>{g[0]}</td><td class='alx-m'>{g[1]}</td><td class='alx-p'>{g[2]}</td>"
            f"<td class='alx-l'>{d[0]}</td><td class='alx-m'>{d[1]}</td><td class='alx-p'>{d[2]}</td>"
            "</tr>"
        )
    chif = ""
    for c, mot, pron in CHIFFRES_OACI:
        chif += f"<tr><td class='alx-l'>{c}</td><td class='alx-m'>{mot}</td><td class='alx-p'>{pron}</td></tr>"

    return f"""<div class="alx-content" data-alx-content="alphabet-oaci">
<h3>L'alphabet phonétique OACI</h3>
<p class="alx-note">Les 26 lettres. La colonne de droite donne la prononciation
recommandée par l'OACI (l'accent tonique est sur la syllabe soulignée dans le
document original ; ici en majuscules).</p>
<table class="alx-table alx-alphabet">
<thead><tr>
<th>Lettre</th><th>Mot</th><th>Prononciation</th>
<th>Lettre</th><th>Mot</th><th>Prononciation</th>
</tr></thead>
<tbody>{rows}</tbody>
</table>
<h3>Les chiffres</h3>
<p class="alx-note">À la radio, les chiffres s'énoncent un par un. Les formes
longues (Unaone, Bissotwo…) sont réservées aux liaisons difficiles ; en pratique
courante on dit « un, deux, trois » en français, ou « wun, too, tree » en anglais.</p>
<table class="alx-table alx-alphabet">
<thead><tr><th>Chiffre</th><th>Mot</th><th>Prononciation</th></tr></thead>
<tbody>{chif}</tbody>
</table>
<p class="alx-note"><strong>Exemple.</strong> L'immatriculation F-GJKL s'épelle
« Foxtrot – Golf – Juliett – Kilo – Lima ». En vol on n'utilise souvent que les
trois dernières lettres après le premier contact : « Juliett Kilo Lima ».</p>
</div>"""


# slug -> HTML additionnel, insere avant le tableau de famille.
EXTRA_CONTENT = {
    "alphabet-oaci": _table_alphabet,
    "alphabet-aviation": _table_alphabet,
}


def get_extra_content(slug):
    fn = EXTRA_CONTENT.get(slug)
    return fn() if fn else ""
