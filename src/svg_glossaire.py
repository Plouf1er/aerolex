# -*- coding: utf-8 -*-
"""Schémas SVG légers pour les fiches du glossaire (plan §9quater.1).

Inline, autoportants, viewBox propre, largeur 100 %, aucun texte < 11 px,
lisible mobile, zéro dépendance externe. Préfixe d'id `gg-` pour éviter
les collisions avec les schémas de séance sur la même page.
"""
from __future__ import annotations


def _svg(view: str, body: str, w: int = 640, h: int = 360) -> str:
    return (
        f'<svg class="schema glos-schema" viewBox="0 0 {w} {h}" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'style="max-width:100%;width:100%;height:auto;display:block;margin:10px 0;">'
        f'<rect width="{w}" height="{h}" fill="#e0f2fe" rx="8"/>'
        f"{body}</svg>"
    )


def svg_piste_seuils_qfu() -> str:
    """Piste avec seuils, numérotation QFU 07/25 et marques d'axe."""
    body = """
  <text x="320" y="28" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Piste · seuils · QFU</text>
  <text x="320" y="48" text-anchor="middle" font-size="12" fill="#64748b">QFU = orientation magnétique de l'axe (dizaines de degrés)</text>
  <!-- Bande / strip -->
  <rect x="70" y="95" width="500" height="170" fill="#bbf7d0" stroke="#16a34a" stroke-width="1.5" rx="6" opacity="0.55"/>
  <text x="90" y="115" font-size="12" fill="#166534">bande / strip</text>
  <!-- Piste -->
  <rect x="110" y="130" width="420" height="100" fill="#475569" rx="4"/>
  <!-- Axe -->
  <line x1="140" y1="180" x2="500" y2="180" stroke="#f8fafc" stroke-width="3" stroke-dasharray="14,10"/>
  <!-- Seuils (barres) -->
  <g stroke="#f8fafc" stroke-width="3">
    <line x1="125" y1="145" x2="125" y2="215"/>
    <line x1="133" y1="145" x2="133" y2="215"/>
    <line x1="141" y1="145" x2="141" y2="215"/>
    <line x1="505" y1="145" x2="505" y2="215"/>
    <line x1="513" y1="145" x2="513" y2="215"/>
    <line x1="521" y1="145" x2="521" y2="215"/>
  </g>
  <!-- Numéros QFU -->
  <text x="165" y="188" text-anchor="middle" font-size="28" font-weight="800" fill="#f8fafc">07</text>
  <text x="475" y="188" text-anchor="middle" font-size="28" font-weight="800" fill="#f8fafc">25</text>
  <!-- Flèches QFU -->
  <defs>
    <marker id="gg-arr-g" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#2563eb"/>
    </marker>
  </defs>
  <line x1="200" y1="260" x2="280" y2="260" stroke="#2563eb" stroke-width="2.5" marker-end="url(#gg-arr-g)"/>
  <text x="240" y="282" text-anchor="middle" font-size="12" fill="#1e3a5f">QFU 07 ≈ 070° mag</text>
  <line x1="440" y1="260" x2="360" y2="260" stroke="#7c3aed" stroke-width="2.5" marker-end="url(#gg-arr-g)"/>
  <text x="400" y="282" text-anchor="middle" font-size="12" fill="#1e3a5f">QFU 25 ≈ 250° mag</text>
  <!-- Labels seuils -->
  <text x="135" y="125" text-anchor="middle" font-size="12" font-weight="600" fill="#dc2626">seuil 07</text>
  <text x="515" y="125" text-anchor="middle" font-size="12" font-weight="600" fill="#dc2626">seuil 25</text>
  <text x="320" y="330" text-anchor="middle" font-size="12" fill="#475569">Aire de manœuvre = pistes + voies de circulation (hors parking)</text>
"""
    return _svg("0 0 640 360", body, 640, 360)


def svg_manche_a_air() -> str:
    """Manche à air (windsock) — lecture grossière de la force."""
    body = """
  <text x="320" y="28" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Manche à air (biroute / windsock)</text>
  <text x="320" y="48" text-anchor="middle" font-size="12" fill="#64748b">Direction = d'où vient le vent · remplissage ≈ force</text>
  <!-- Mât -->
  <line x1="160" y1="80" x2="160" y2="300" stroke="#475569" stroke-width="6"/>
  <circle cx="160" cy="80" r="8" fill="#64748b"/>
  <!-- Socle -->
  <rect x="130" y="300" width="60" height="12" fill="#78716c" rx="2"/>
  <!-- Manche gonflé (vent de gauche) -->
  <path d="M168 80 C 220 70, 280 95, 360 88 C 400 85, 430 95, 450 100
           C 430 115, 400 125, 360 122 C 280 128, 220 110, 168 95 Z"
        fill="#f97316" stroke="#9a3412" stroke-width="2"/>
  <path d="M250 78 L250 120 M320 82 L320 118 M390 88 L390 112"
        stroke="#fff7ed" stroke-width="2" opacity="0.85"/>
  <!-- Flèche vent -->
  <defs>
    <marker id="gg-vent" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
      <path d="M0,0 L9,4.5 L0,9 Z" fill="#2563eb"/>
    </marker>
  </defs>
  <line x1="90" y1="160" x2="150" y2="160" stroke="#2563eb" stroke-width="3" marker-end="url(#gg-vent)"/>
  <text x="120" y="150" text-anchor="middle" font-size="12" font-weight="600" fill="#1d4ed8">VENT</text>
  <!-- Légende force -->
  <g font-size="12" fill="#1e293b">
    <text x="480" y="120" font-weight="700" fill="#1e3a5f">Lecture grossière</text>
    <text x="480" y="145">Mou · pendu ≈ calme</text>
    <text x="480" y="168">1/2 gonflé ≈ 5–10 kt</text>
    <text x="480" y="191">Plein horizontal ≈ ≥ 15 kt</text>
    <text x="480" y="220" fill="#b45309">Les bandes aident à juger</text>
    <text x="480" y="240" fill="#b45309">l'inclinaison / remplissage.</text>
  </g>
  <text x="320" y="340" text-anchor="middle" font-size="12" fill="#475569">Ne remplace pas l'anémomètre ni l'ATIS — c'est un aperçu terrain</text>
"""
    return _svg("0 0 640 360", body, 640, 360)


def svg_rose_des_vents() -> str:
    """Rose des vents avec secteurs et axe QFU."""
    body = """
  <text x="320" y="26" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Rose des vents + axe QFU</text>
  <text x="320" y="46" text-anchor="middle" font-size="12" fill="#64748b">Le vent METAR est en degrés vrais · le QFU est magnétique</text>
  <!-- Cercle -->
  <circle cx="250" cy="200" r="120" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>
  <circle cx="250" cy="200" r="80" fill="none" stroke="#cbd5e1" stroke-width="1"/>
  <!-- Axes cardinaux -->
  <line x1="250" y1="70" x2="250" y2="330" stroke="#94a3b8" stroke-width="1.5"/>
  <line x1="120" y1="200" x2="380" y2="200" stroke="#94a3b8" stroke-width="1.5"/>
  <text x="250" y="64" text-anchor="middle" font-size="14" font-weight="700" fill="#1e3a5f">N</text>
  <text x="250" y="348" text-anchor="middle" font-size="13" font-weight="600" fill="#475569">S</text>
  <text x="108" y="205" text-anchor="middle" font-size="13" font-weight="600" fill="#475569">O</text>
  <text x="392" y="205" text-anchor="middle" font-size="13" font-weight="600" fill="#475569">E</text>
  <!-- Piste 07/25 inclinée ~70° depuis le nord : angle 70° horaire depuis N
       direction piste : 070° → dx=sin70, dy=-cos70 -->
  <g transform="translate(250,200) rotate(70)">
    <rect x="-12" y="-95" width="24" height="190" fill="#475569" rx="3"/>
    <text x="0" y="-70" text-anchor="middle" font-size="13" font-weight="800" fill="#f8fafc" transform="rotate(-70)">07</text>
    <text x="0" y="82" text-anchor="middle" font-size="13" font-weight="800" fill="#f8fafc" transform="rotate(-70)">25</text>
  </g>
  <!-- Vecteur vent exemple 250° -->
  <defs>
    <marker id="gg-rw" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#2563eb"/>
    </marker>
  </defs>
  <!-- 250° : sin250=-0.94, cos250=-0.34 → from outside toward center -->
  <line x1="140" y1="240" x2="210" y2="215" stroke="#2563eb" stroke-width="3" marker-end="url(#gg-rw)"/>
  <text x="130" y="260" font-size="12" font-weight="600" fill="#1d4ed8">vent 250°</text>
  <!-- Légende -->
  <g font-size="12" fill="#1e293b">
    <text x="430" y="120" font-weight="700" fill="#1e3a5f">À lire ensemble</text>
    <text x="430" y="148">1. Direction du vent (d'où)</text>
    <text x="430" y="170">2. Force (kt) + rafales</text>
    <text x="430" y="192">3. QFU en service</text>
    <text x="430" y="214">4. θ = |vent − QFU|</text>
    <text x="430" y="250" fill="#b45309">θ petit → beaucoup de face</text>
    <text x="430" y="272" fill="#b45309">θ ≈ 90° → tout en travers</text>
  </g>
"""
    return _svg("0 0 640 360", body, 640, 360)


def svg_composantes_face_travers() -> str:
    """Triangle de composantes : vent → face + travers."""
    body = """
  <text x="320" y="26" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Composantes face / travers</text>
  <text x="320" y="46" text-anchor="middle" font-size="12" fill="#64748b">face = V · cos θ ··· travers = V · sin θ</text>
  <!-- Piste horizontale -->
  <rect x="80" y="200" width="360" height="36" fill="#475569" rx="3"/>
  <text x="100" y="224" font-size="14" font-weight="700" fill="#f8fafc">07</text>
  <text x="400" y="224" font-size="14" font-weight="700" fill="#f8fafc">25</text>
  <text x="260" y="255" text-anchor="middle" font-size="12" fill="#475569">axe de piste (QFU)</text>
  <!-- Origine O sur le seuil gauche-ish -->
  <circle cx="200" cy="218" r="5" fill="#0f172a"/>
  <text x="200" y="275" text-anchor="middle" font-size="12" fill="#0f172a">O</text>
  <defs>
    <marker id="gg-cf" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#059669"/>
    </marker>
    <marker id="gg-ct" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#dc2626"/>
    </marker>
    <marker id="gg-cv" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#2563eb"/>
    </marker>
  </defs>
  <!-- Face (le long de la piste, vers la droite = vent de face pour QFU 07 si vent vient d'avant) 
       Convention pédagogique : vecteur vent dessiné VERS la piste (d'où il vient → impact)
       Vent vient du 040° pour QFU 070 → θ=30°. On dessine V oblique. -->
  <!-- Vecteur V (vent) -->
  <line x1="200" y1="218" x2="360" y2="100" stroke="#2563eb" stroke-width="3.5" marker-end="url(#gg-cv)"/>
  <text x="370" y="95" font-size="13" font-weight="700" fill="#1d4ed8">V vent</text>
  <!-- Face (projection sur axe) -->
  <line x1="200" y1="218" x2="340" y2="218" stroke="#059669" stroke-width="3.5" marker-end="url(#gg-cf)"/>
  <text x="270" y="205" text-anchor="middle" font-size="13" font-weight="700" fill="#047857">face</text>
  <!-- Travers (perpendiculaire) -->
  <line x1="340" y1="218" x2="340" y2="100" stroke="#dc2626" stroke-width="3.5" marker-end="url(#gg-ct)"/>
  <text x="355" y="160" font-size="13" font-weight="700" fill="#b91c1c">travers</text>
  <!-- Angle theta arc -->
  <path d="M250 218 A50 50 0 0 0 245 175" fill="none" stroke="#7c3aed" stroke-width="2"/>
  <text x="255" y="185" font-size="13" font-weight="700" fill="#6d28d9">θ</text>
  <!-- Formules -->
  <g font-size="13" fill="#1e293b">
    <text x="460" y="130" font-weight="700" fill="#1e3a5f">Formules</text>
    <text x="460" y="158" fill="#047857">face = V × cos θ</text>
    <text x="460" y="182" fill="#b91c1c">travers = V × sin θ</text>
    <text x="460" y="215">θ = |direction vent − QFU|</text>
    <text x="460" y="245" fill="#b45309">Règle 30/45/60 :</text>
    <text x="460" y="268" fill="#b45309">30°→½ · 45°→0,7 · 60°→0,9</text>
  </g>
"""
    return _svg("0 0 640 360", body, 640, 360)


def svg_decrabage() -> str:
    """Crabe en finale puis décrabage au toucher."""
    body = """
  <text x="320" y="26" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Crabe puis décrabage</text>
  <text x="320" y="46" text-anchor="middle" font-size="12" fill="#64748b">Nez au vent en finale · alignement fuselage juste avant / au toucher</text>
  <!-- Piste -->
  <rect x="60" y="250" width="520" height="40" fill="#475569" rx="3"/>
  <line x1="80" y1="270" x2="560" y2="270" stroke="#f8fafc" stroke-width="2" stroke-dasharray="12,8"/>
  <text x="90" y="278" font-size="13" font-weight="700" fill="#f8fafc">07</text>
  <!-- Vent -->
  <defs>
    <marker id="gg-dcv" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#2563eb"/>
    </marker>
  </defs>
  <line x1="120" y1="90" x2="200" y2="90" stroke="#2563eb" stroke-width="3" marker-end="url(#gg-dcv)"/>
  <text x="160" y="78" text-anchor="middle" font-size="12" font-weight="600" fill="#1d4ed8">vent traversier</text>
  <!-- Avion en crabe (vue dessus, fuselage tourné) -->
  <g transform="translate(250,160) rotate(-28)">
    <ellipse cx="0" cy="0" rx="34" ry="10" fill="#1e3a5f"/>
    <rect x="-6" y="-28" width="12" height="56" fill="#334155" rx="2"/>
    <path d="M20 -6 L40 0 L20 6 Z" fill="#f59e0b"/>
    <text x="0" y="4" text-anchor="middle" font-size="11" fill="#f8fafc">nez</text>
  </g>
  <text x="250" y="210" text-anchor="middle" font-size="12" font-weight="600" fill="#7c3aed">1. Crabe : route sol sur l'axe</text>
  <!-- Flèche décrabage -->
  <path d="M320 150 Q380 150 420 200" fill="none" stroke="#dc2626" stroke-width="2.5" stroke-dasharray="6,4"/>
  <text x="400" y="140" font-size="12" font-weight="700" fill="#b91c1c">2. Décrabage</text>
  <!-- Avion aligné au sol -->
  <g transform="translate(480,230)">
    <ellipse cx="0" cy="0" rx="34" ry="10" fill="#059669"/>
    <rect x="-6" y="-28" width="12" height="56" fill="#047857" rx="2"/>
    <path d="M20 -6 L40 0 L20 6 Z" fill="#f59e0b"/>
  </g>
  <text x="480" y="310" text-anchor="middle" font-size="12" font-weight="600" fill="#047857">3. Fuselage // piste au toucher</text>
  <text x="320" y="345" text-anchor="middle" font-size="12" fill="#475569">Sans décrabage : charge latérale train + sortie d'axe</text>
"""
    return _svg("0 0 640 360", body, 640, 360)


# Géométrie du circuit (doit rester synchro avec svg_tour_de_piste).
# Chaque branche : segment (x1,y1,x2,y2) à surligner + point de pastille.
_TDP_BRANCHES = {
    "montée initiale":  (240, 140, 400, 140, 320, 152),
    "vent traversier":  (400, 140, 400,  80, 412, 112),
    "vent arrière":     (400,  80, 240,  80, 320,  62),
    "étape de base":    (240,  80, 240, 140, 214, 112),
    "dernier virage":   (240, 140, 232, 168, 214, 150),
    "longue finale":    (150, 174, 200, 174, 175, 196),
    "courte finale":    (200, 174, 230, 174, 215, 196),
    "arrondi":          (228, 174, 250, 174, 250, 200),
}


def _tdp_highlight(actif: str | None) -> str:
    """Calque de surbrillance dessiné SOUS le circuit (halo ambre + pastille)."""
    if not actif:
        return ""
    g = _TDP_BRANCHES.get(actif)
    if not g:
        return ""
    x1, y1, x2, y2, lx, ly = g
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#fbbf24" '
        f'stroke-width="13" stroke-linecap="round" opacity="0.55"/>'
        f'<circle cx="{lx}" cy="{ly}" r="5" fill="#b45309"/>'
        f'<text x="320" y="346" text-anchor="middle" font-size="12.5" '
        f'font-weight="700" fill="#b45309">Sur cette fiche : {actif}</text>'
    )


def svg_tour_de_piste(actif: str | None = None) -> str:
    """Circuit rectangulaire. `actif` met une branche en évidence (halo + pastille)."""
    hl = _tdp_highlight(actif)
    body = hl + """
  <text x="320" y="24" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Tour de piste (circuit)</text>
  <text x="320" y="44" text-anchor="middle" font-size="12" fill="#64748b">Branches : vent arrière · étape de base · finale · montée initiale</text>
  <!-- Piste -->
  <rect x="220" y="160" width="200" height="28" fill="#475569" rx="3"/>
  <text x="235" y="180" font-size="12" font-weight="700" fill="#f8fafc">07</text>
  <text x="390" y="180" font-size="12" font-weight="700" fill="#f8fafc">25</text>
  <!-- Circuit main gauche pour 07 : rectangle autour -->
  <defs>
    <marker id="gg-tp" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#2563eb"/>
    </marker>
  </defs>
  <!-- Montée / vent debout (upwind) le long piste vers 25 puis crosswind -->
  <polyline points="240,140 400,140 400,80 240,80 240,140"
            fill="none" stroke="#2563eb" stroke-width="3" stroke-linejoin="round"/>
  <!-- flèches sur chaque branche -->
  <line x1="280" y1="140" x2="340" y2="140" stroke="#2563eb" stroke-width="3" marker-end="url(#gg-tp)"/>
  <line x1="400" y1="120" x2="400" y2="100" stroke="#2563eb" stroke-width="3" marker-end="url(#gg-tp)"/>
  <line x1="360" y1="80" x2="300" y2="80" stroke="#2563eb" stroke-width="3" marker-end="url(#gg-tp)"/>
  <line x1="240" y1="100" x2="240" y2="120" stroke="#2563eb" stroke-width="3" marker-end="url(#gg-tp)"/>
  <!-- Labels branches (positions aérées, pas de chevauchement) -->
  <text x="320" y="155" text-anchor="middle" font-size="11" font-weight="700" fill="#1d4ed8">montée initiale</text>
  <text x="470" y="110" font-size="11" font-weight="700" fill="#7c3aed">vent traversier</text>
  <text x="470" y="124" font-size="10" fill="#7c3aed">(crosswind)</text>
  <text x="320" y="64" text-anchor="middle" font-size="12" font-weight="700" fill="#b45309">vent arrière</text>
  <text x="320" y="78" text-anchor="middle" font-size="10" fill="#b45309">(downwind)</text>
  <text x="130" y="105" text-anchor="middle" font-size="11" font-weight="700" fill="#dc2626">étape de base</text>
  <text x="130" y="120" text-anchor="middle" font-size="10" fill="#dc2626">(base)</text>
  <!-- Finale flèche vers seuil -->
  <line x1="200" y1="174" x2="230" y2="174" stroke="#059669" stroke-width="3.5" marker-end="url(#gg-tp)"/>
  <text x="145" y="168" font-size="12" font-weight="700" fill="#047857">finale</text>
  <!-- Remise des gaz path — libellé déporté sous la piste -->
  <path d="M300 174 Q340 145 380 100" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="6,4"/>
  <text x="400" y="210" font-size="11" font-weight="700" fill="#b91c1c">remise des gaz</text>
  <text x="400" y="224" font-size="10" fill="#b91c1c">→ rejoint vent arrière</text>
  <text x="320" y="240" text-anchor="middle" font-size="12" fill="#475569">Sens du circuit : imposé par la VAC (main gauche / main droite)</text>
  <text x="320" y="262" text-anchor="middle" font-size="12" fill="#475569">Altitude de circuit : souvent 1000 ft AAL — lire la carte VAC</text>
  <g font-size="12" fill="#1e293b">
    <text x="80" y="300" font-weight="700" fill="#1e3a5f">Branche = segment nommé du circuit</text>
    <text x="80" y="322">Ne confonds pas « tour de piste » (manœuvre) et « tour de contrôle » (organisme ATS).</text>
  </g>
"""
    return _svg("0 0 640 360", body, 640, 360)


def svg_azimut_vrai_magnetique() -> str:
    """Nord vrai vs nord magnétique et déclinaison."""
    body = """
  <text x="320" y="26" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Azimut vrai · magnétique · compas</text>
  <text x="320" y="46" text-anchor="middle" font-size="12" fill="#64748b">Déclinaison : angle entre nord géographique et nord magnétique</text>
  <!-- Roses -->
  <circle cx="220" cy="200" r="110" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>
  <!-- Nord vrai -->
  <line x1="220" y1="200" x2="220" y2="95" stroke="#059669" stroke-width="3.5"/>
  <polygon points="220,88 212,108 228,108" fill="#059669"/>
  <text x="235" y="105" font-size="13" font-weight="700" fill="#047857">Nv (vrai)</text>
  <!-- Nord magnétique décalé ~15° vers l'est pour lisibilité pédagogique -->
  <g transform="translate(220,200) rotate(15)">
    <line x1="0" y1="0" x2="0" y2="-105" stroke="#2563eb" stroke-width="3.5"/>
    <polygon points="0,-112 -8,-92 8,-92" fill="#2563eb"/>
  </g>
  <text x="275" y="120" font-size="13" font-weight="700" fill="#1d4ed8">Nm (mag)</text>
  <!-- Arc déclinaison -->
  <path d="M220 120 A80 80 0 0 1 248 125" fill="none" stroke="#7c3aed" stroke-width="2.5"/>
  <text x="250" y="155" font-size="13" font-weight="700" fill="#6d28d9">var / déclinaison</text>
  <!-- Cap exemple -->
  <g transform="translate(220,200) rotate(55)">
    <line x1="0" y1="0" x2="0" y2="-70" stroke="#dc2626" stroke-width="2.5" stroke-dasharray="5,3"/>
  </g>
  <text x="290" y="250" font-size="12" fill="#b91c1c">exemple de cap</text>
  <!-- Formules -->
  <g font-size="13" fill="#1e293b">
    <text x="380" y="110" font-weight="700" fill="#1e3a5f">Conversions</text>
    <text x="380" y="140">CM = CV − Est  (+ Ouest)</text>
    <text x="380" y="165">CV = CM + Est  (− Ouest)</text>
    <text x="380" y="200" fill="#b45309">East is least · West is best</text>
    <text x="380" y="225">(Est : on retranche · Ouest : on ajoute</text>
    <text x="380" y="245">pour passer du vrai au magnétique)</text>
    <text x="380" y="280" font-weight="700" fill="#1e3a5f">Compas</text>
    <text x="380" y="305">Cc = CM − déviation (carte de compas)</text>
  </g>
  <text x="320" y="340" text-anchor="middle" font-size="12" fill="#475569">METAR = degrés vrais · QFU / compas de bord = magnétique</text>
"""
    return _svg("0 0 640 360", body, 640, 360)


def svg_remise_des_gaz() -> str:
    """Trajectoire de remise des gaz depuis la courte finale."""
    body = """
  <text x="320" y="26" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Remise des gaz (go-around)</text>
  <text x="320" y="46" text-anchor="middle" font-size="12" fill="#64748b">Décision franche · puissance · assiette · configuration · rejointe circuit</text>
  <!-- Sol / piste -->
  <rect x="40" y="280" width="560" height="40" fill="#86efac"/>
  <rect x="180" y="288" width="300" height="24" fill="#475569" rx="2"/>
  <text x="200" y="305" font-size="12" font-weight="700" fill="#f8fafc">seuil</text>
  <!-- Trajectoire approche puis remise -->
  <defs>
    <marker id="gg-rg" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#dc2626"/>
    </marker>
  </defs>
  <path d="M80 120 Q160 200 220 260" fill="none" stroke="#64748b" stroke-width="3" stroke-dasharray="8,5"/>
  <text x="90" y="150" font-size="12" fill="#475569">finale instable</text>
  <path d="M220 260 Q280 180 360 120 Q420 90 520 80" fill="none" stroke="#dc2626" stroke-width="3.5" marker-end="url(#gg-rg)"/>
  <text x="300" y="170" font-size="13" font-weight="700" fill="#b91c1c">remise · montée</text>
  <text x="430" y="75" font-size="12" font-weight="600" fill="#b91c1c">rejointe vent arrière</text>
  <g font-size="12" fill="#1e293b">
    <text x="60" y="70" font-weight="700" fill="#1e3a5f">Ordre mental type</text>
    <text x="60" y="92">1. Puissance max / hélices</text>
    <text x="60" y="112">2. Assiette de montée</text>
    <text x="60" y="132">3. Volets selon manuel de vol</text>
    <text x="60" y="152">4. Train haut si applicable</text>
  </g>
"""
    return _svg("0 0 640 360", body, 640, 360)


def svg_distances_piste() -> str:
    """Les quatre distances declarees, en bandes superposees."""
    body = """
  <text x="320" y="24" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Les distances d\u00e9clar\u00e9es d'une piste</text>
  <text x="320" y="44" text-anchor="middle" font-size="12" fill="#64748b">Longueurs publi\u00e9es par terrain et par sens \u2014 \u00e0 lire sur la carte VAC</text>
  <rect x="90" y="70" width="330" height="30" fill="#475569" rx="2"/>
  <rect x="420" y="76" width="70" height="18" fill="#94a3b8" rx="2"/>
  <rect x="490" y="79" width="70" height="12" fill="#cbd5e1" rx="2"/>
  <text x="255" y="90" text-anchor="middle" font-size="12" font-weight="700" fill="#f8fafc">piste rev\u00eatue</text>
  <text x="455" y="89" text-anchor="middle" font-size="10" fill="#1e293b">prol. arr\u00eat</text>
  <text x="525" y="88" text-anchor="middle" font-size="10" fill="#475569">prol. d\u00e9gag\u00e9</text>
  <line x1="150" y1="64" x2="150" y2="106" stroke="#dc2626" stroke-width="2.5"/>
  <text x="150" y="58" text-anchor="middle" font-size="11" font-weight="700" fill="#b91c1c">seuil d\u00e9cal\u00e9</text>
  <defs>
    <marker id="dp-a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 Z" fill="#1d4ed8"/>
    </marker>
    <marker id="dp-b" markerWidth="8" markerHeight="8" refX="1" refY="4" orient="auto">
      <path d="M8,0 L0,4 L8,8 Z" fill="#1d4ed8"/>
    </marker>
  </defs>
  <g stroke="#1d4ed8" stroke-width="2.5" marker-start="url(#dp-b)" marker-end="url(#dp-a)">
    <line x1="90" y1="140" x2="420" y2="140"/>
    <line x1="90" y1="180" x2="560" y2="180"/>
    <line x1="90" y1="220" x2="490" y2="220"/>
    <line x1="150" y1="260" x2="420" y2="260"/>
  </g>
  <g font-size="12" font-weight="700" fill="#1d4ed8">
    <text x="80" y="144" text-anchor="end">TORA</text>
    <text x="80" y="184" text-anchor="end">TODA</text>
    <text x="80" y="224" text-anchor="end">ASDA</text>
    <text x="140" y="264" text-anchor="end">LDA</text>
  </g>
  <g font-size="11" fill="#475569">
    <text x="255" y="132" text-anchor="middle">roulement au d\u00e9collage</text>
    <text x="325" y="172" text-anchor="middle">= TORA + prolongement d\u00e9gag\u00e9</text>
    <text x="290" y="212" text-anchor="middle">= TORA + prolongement d'arr\u00eat</text>
    <text x="285" y="252" text-anchor="middle">du seuil au bout de piste</text>
  </g>
  <line x1="60" y1="286" x2="580" y2="286" stroke="#e2e8f0" stroke-width="1"/>
  <g font-size="12" fill="#1e293b">
    <text x="60" y="308" font-weight="700" fill="#1e3a5f">Un seuil d\u00e9cal\u00e9 raccourcit la LDA, pas la TORA.</text>
    <text x="60" y="330">La partie avant le seuil reste utilisable au d\u00e9collage \u2014 pas \u00e0 l'atterrissage.</text>
  </g>
"""
    return _svg("0 0 640 360", body, 640, 360)


# Catalogue nom → générateur (pour data_glossaire["schema"] = "piste_seuils_qfu")
SCHEMAS = {
    "piste_seuils_qfu": svg_piste_seuils_qfu,
    "manche_a_air": svg_manche_a_air,
    "rose_des_vents": svg_rose_des_vents,
    "composantes_face_travers": svg_composantes_face_travers,
    "decrabage": svg_decrabage,
    "tour_de_piste": svg_tour_de_piste,
    "distances_piste": svg_distances_piste,
    "azimut_vrai_magnetique": svg_azimut_vrai_magnetique,
    "remise_des_gaz": svg_remise_des_gaz,
}


def get_schema(name: str, terme: str | None = None) -> str:
    """SVG inline pour une clé de schéma, ou '' si inconnu.

    `terme` (optionnel) met en évidence la partie traitée par la fiche
    courante, pour les schémas qui le supportent (demande Louis 02/08).
    """
    fn = SCHEMAS.get(name)
    if not fn:
        return ""
    try:
        return fn(terme) if terme is not None else fn()
    except TypeError:
        return fn()
