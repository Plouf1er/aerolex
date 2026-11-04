import os
import xml.dom.minidom
import subprocess

import os
out_dir = os.path.dirname(os.path.abspath(__file__))

svgs = {
    "virage-forces.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE L'ARRI&#200;RE &#183; Virage &#224; gauche</text>
  
  <g transform="translate(320, 250) rotate(-30)">
    <!-- Avion (fuselage + ailes) -->
    <ellipse cx="0" cy="0" rx="20" ry="30" fill="#94a3b8"/>
    <rect x="-120" y="-5" width="240" height="10" fill="#94a3b8"/>
    <text x="0" y="25" font-family="Arial" font-size="12" fill="#1e3a5f" text-anchor="middle">Avion inclin&#233;</text>
    
    <!-- Portance totale (perpendiculaire aux ailes) -->
    <line x1="0" y1="-15" x2="0" y2="-170" stroke="#2563eb" stroke-width="4" marker-end="url(#arrow-blue)"/>
    <text x="-10" y="-175" font-family="Arial" font-size="14" fill="#2563eb" text-anchor="end" class="aerolex-terme" data-slug="portance">Portance totale</text>
  </g>

  <!-- Poids (vertical vers le bas) -->
  <line x1="320" y1="250" x2="320" y2="385" stroke="#dc2626" stroke-width="4" marker-end="url(#arrow-red)"/>
  <text x="330" y="380" font-family="Arial" font-size="14" fill="#dc2626" class="aerolex-terme" data-slug="poids">Poids</text>

  <!-- Composante verticale de la portance (&#233;gale au poids en longueur = 135) -->
  <line x1="320" y1="250" x2="320" y2="115" stroke="#2563eb" stroke-width="3" stroke-dasharray="5,5" marker-end="url(#arrow-blue)"/>
  <text x="330" y="110" font-family="Arial" font-size="14" fill="#2563eb">Comp. verticale (&#233;quilibre le poids)</text>

  <!-- Composante horizontale (Force centrip&#232;te) -->
  <line x1="320" y1="115" x2="242" y2="115" stroke="#2563eb" stroke-width="3" stroke-dasharray="5,5" marker-end="url(#arrow-blue)"/>
  <text x="230" y="110" font-family="Arial" font-size="14" fill="#2563eb" text-anchor="end">Comp. horizontale (fait tourner)</text>
  
  <line x1="242" y1="115" x2="320" y2="250" stroke="#94a3b8" stroke-width="1" stroke-dasharray="2,2"/>

  <defs>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2563eb"/></marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#dc2626"/></marker>
  </defs>
</svg>""",

    "incidence-vent-relatif.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE PROFIL &#183; Profil d'aile en vol</text>
  
  <!-- Trajectoire et horizon -->
  <line x1="50" y1="200" x2="590" y2="200" stroke="#94a3b8" stroke-width="2" stroke-dasharray="10,5"/>
  <text x="590" y="195" font-family="Arial" font-size="14" fill="#94a3b8" text-anchor="end" class="aerolex-terme" data-slug="trajectoire">Trajectoire (ici = Horizon)</text>
  
  <g transform="translate(250, 200)">
    <!-- Profil d'aile cabr&#233; de 15 degres -->
    <g transform="rotate(-15)">
      <path d="M-100,0 C-100,-30 50,-20 120,0 C50,10 -100,20 -100,0 Z" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/>
      <line x1="-100" y1="0" x2="120" y2="0" stroke="#1e3a5f" stroke-width="2"/>
      <text x="130" y="-5" font-family="Arial" font-size="14" fill="#1e3a5f" class="aerolex-terme" data-slug="corde">Corde</text>
    </g>
    
    <!-- Vent relatif -->
    <line x1="200" y1="0" x2="-200" y2="0" stroke="#38bdf8" stroke-width="3" marker-end="url(#arrow-cyan)"/>
    <text x="-210" y="-10" font-family="Arial" font-size="14" fill="#0284c7" text-anchor="end" class="aerolex-terme" data-slug="vent-relatif">Vent Relatif (oppos&#233; trajectoire)</text>
    
    <!-- Angle d'incidence -->
    <path d="M-50,0 A50,50 0 0,1 -48.3,-12.9" fill="none" stroke="#dc2626" stroke-width="2"/>
    <text x="-35" y="-15" font-family="Arial" font-size="14" fill="#dc2626" font-weight="bold" class="aerolex-terme" data-slug="incidence">Incidence</text>
  </g>

  <defs>
    <marker id="arrow-cyan" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#38bdf8"/></marker>
  </defs>
</svg>""",

    "forces-vol-palier.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE PROFIL &#183; Vol en palier stabilis&#233;</text>
  
  <g transform="translate(320, 200)">
    <!-- Avion stylis&#233; -->
    <rect x="-60" y="-15" width="120" height="30" rx="15" fill="#94a3b8"/>
    <ellipse cx="0" cy="-15" rx="30" ry="10" fill="#cbd5e1"/>
    
    <!-- Portance (up) -->
    <line x1="0" y1="-15" x2="0" y2="-135" stroke="#2563eb" stroke-width="4" marker-end="url(#arrow-blue)"/>
    <text x="10" y="-120" font-family="Arial" font-size="14" fill="#2563eb" class="aerolex-terme" data-slug="portance">Portance</text>
    
    <!-- Poids (down) -->
    <line x1="0" y1="15" x2="0" y2="135" stroke="#dc2626" stroke-width="4" marker-end="url(#arrow-red)"/>
    <text x="10" y="130" font-family="Arial" font-size="14" fill="#dc2626" class="aerolex-terme" data-slug="poids">Poids</text>
    
    <!-- Traction (forward/left) -->
    <line x1="-60" y1="0" x2="-200" y2="0" stroke="#16a34a" stroke-width="4" marker-end="url(#arrow-green)"/>
    <text x="-190" y="-10" font-family="Arial" font-size="14" fill="#16a34a" text-anchor="end" class="aerolex-terme" data-slug="traction">Traction</text>
    
    <!-- Tra&#238;n&#233;e (backward/right) -->
    <line x1="60" y1="0" x2="200" y2="0" stroke="#b45309" stroke-width="4" marker-end="url(#arrow-brown)"/>
    <text x="190" y="-10" font-family="Arial" font-size="14" fill="#b45309" class="aerolex-terme" data-slug="trainee">Tra&#238;n&#233;e</text>
  </g>
  
  <text x="320" y="370" font-family="Arial" font-size="14" fill="#1e3a5f" font-style="italic" text-anchor="middle">En palier stabilis&#233; : Portance = Poids, et Traction = Tra&#238;n&#233;e (longueurs de fl&#232;ches &#233;gales)</text>

  <defs>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2563eb"/></marker>
    <marker id="arrow-red" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#dc2626"/></marker>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#16a34a"/></marker>
    <marker id="arrow-brown" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#b45309"/></marker>
  </defs>
</svg>""",

    "gouvernes-3-axes.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE DESSUS &#183; Les 3 gouvernes primaires</text>
  
  <!-- Silhouette avion -->
  <g transform="translate(320, 200)">
    <!-- Ailes -->
    <rect x="-150" y="-30" width="300" height="40" fill="#cbd5e1" stroke="#94a3b8"/>
    <!-- Empennage horizontal -->
    <rect x="-60" y="100" width="120" height="20" fill="#cbd5e1" stroke="#94a3b8"/>
    <!-- Fuselage -->
    <rect x="-20" y="-120" width="40" height="260" rx="20" fill="#94a3b8"/>
    
    <!-- Ailerons (Roulis) -->
    <rect x="-140" y="10" width="50" height="10" fill="#f59e0b" stroke="#b45309" stroke-width="2"/>
    <rect x="90" y="10" width="50" height="10" fill="#f59e0b" stroke="#b45309" stroke-width="2"/>
    <text x="-160" y="35" font-family="Arial" font-size="14" fill="#b45309" font-weight="bold" text-anchor="end" class="aerolex-terme" data-slug="aileron">Ailerons (Roulis)</text>
    
    <!-- Gouverne de profondeur (Tangage) -->
    <rect x="-50" y="120" width="100" height="15" fill="#10b981" stroke="#047857" stroke-width="2"/>
    <text x="-70" y="130" font-family="Arial" font-size="14" fill="#047857" font-weight="bold" text-anchor="end" class="aerolex-terme" data-slug="gouverne">Profondeur (Tangage)</text>
    
    <!-- Gouverne de direction (Lacet) - repr&#233;sent&#233;e d&#233;pli&#233;e ou &#224; l'arri&#232;re -->
    <rect x="-5" y="135" width="10" height="40" fill="#3b82f6" stroke="#1d4ed8" stroke-width="2"/>
    <text x="15" y="160" font-family="Arial" font-size="14" fill="#1d4ed8" font-weight="bold" class="aerolex-terme" data-slug="gouverne">Direction (Lacet)</text>
  </g>
</svg>""",

    "repere-3-axes.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE EN PERSPECTIVE &#183; Les 3 axes de rotation</text>
  
  <g transform="translate(320, 220)">
    <!-- Centre de gravit&#233; -->
    <circle cx="0" cy="0" r="5" fill="#000"/>
    <text x="10" y="20" font-family="Arial" font-size="12" fill="#000" class="aerolex-terme" data-slug="centre-de-gravite">CG</text>
    
    <!-- Axe de Roulis (Longitudinal) -->
    <line x1="-150" y1="50" x2="150" y2="-50" stroke="#f59e0b" stroke-width="3" stroke-dasharray="8,4" marker-end="url(#arrow-orange)"/>
    <text x="-160" y="65" font-family="Arial" font-size="14" fill="#b45309" font-weight="bold" class="aerolex-terme" data-slug="roulis">Axe de Roulis (Longitudinal)</text>
    
    <!-- Axe de Tangage (Transversal) -->
    <line x1="-200" y1="-20" x2="200" y2="20" stroke="#10b981" stroke-width="3" stroke-dasharray="8,4" marker-end="url(#arrow-emerald)"/>
    <text x="-210" y="-30" font-family="Arial" font-size="14" fill="#047857" font-weight="bold" class="aerolex-terme" data-slug="tangage">Axe de Tangage (Transversal)</text>
    
    <!-- Axe de Lacet (Vertical) -->
    <line x1="0" y1="120" x2="0" y2="-150" stroke="#3b82f6" stroke-width="3" stroke-dasharray="8,4" marker-end="url(#arrow-blue)"/>
    <text x="10" y="-140" font-family="Arial" font-size="14" fill="#1d4ed8" font-weight="bold" class="aerolex-terme" data-slug="lacet">Axe de Lacet (Vertical)</text>
    
    <!-- Indicateurs de rotation -->
    <path d="M-80,-20 A30,30 0 0,1 -60,0" fill="none" stroke="#f59e0b" stroke-width="2" marker-end="url(#arrow-orange)"/>
    <path d="M-100,-10 A30,30 0 0,1 -120,-30" fill="none" stroke="#10b981" stroke-width="2" marker-end="url(#arrow-emerald)"/>
    <path d="M20,-60 A30,30 0 0,1 -20,-60" fill="none" stroke="#3b82f6" stroke-width="2" marker-end="url(#arrow-blue)"/>
  </g>

  <defs>
    <marker id="arrow-orange" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#f59e0b"/></marker>
    <marker id="arrow-emerald" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#10b981"/></marker>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#3b82f6"/></marker>
  </defs>
</svg>""",

    "lacet-adverse-conjugaison.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE DESSUS + ENCART ARRI&#200;RE &#183; Lacet adverse</text>
  
  <!-- Encart arri&#232;re pour voir les ailerons -->
  <g transform="translate(100, 100)">
    <rect x="-60" y="-40" width="120" height="80" fill="#e2e8f0" stroke="#94a3b8"/>
    <text x="0" y="-20" font-family="Arial" font-size="12" fill="#1e3a5f" text-anchor="middle">Vue arri&#232;re</text>
    <line x1="-50" y1="10" x2="50" y2="10" stroke="#cbd5e1" stroke-width="10"/>
    <rect x="-50" y="0" width="20" height="10" fill="#dc2626"/> <!-- Aileron gauche lev&#233; -->
    <rect x="30" y="10" width="20" height="10" fill="#16a34a"/> <!-- Aileron droit baiss&#233; -->
    <text x="-40" y="30" font-family="Arial" font-size="10" fill="#dc2626" text-anchor="middle">Lev&#233;</text>
    <text x="40" y="30" font-family="Arial" font-size="10" fill="#16a34a" text-anchor="middle">Baiss&#233;</text>
  </g>

  <g transform="translate(380, 200)">
    <!-- Silhouette avion top view inclin&#233; -->
    <g transform="rotate(-15)">
      <rect x="-100" y="-15" width="200" height="30" fill="#cbd5e1" stroke="#94a3b8"/>
      <rect x="-15" y="-80" width="30" height="160" rx="15" fill="#94a3b8"/>
      
      <!-- Tra&#238;n&#233;e aileron gauche (faible) -->
      <line x1="-80" y1="15" x2="-80" y2="45" stroke="#b45309" stroke-width="2" marker-end="url(#arrow-brown)"/>
      
      <!-- Tra&#238;n&#233;e aileron droit (forte) -->
      <line x1="80" y1="15" x2="80" y2="95" stroke="#b45309" stroke-width="5" marker-end="url(#arrow-brown)"/>
      <text x="90" y="85" font-family="Arial" font-size="14" fill="#b45309" class="aerolex-terme" data-slug="trainee">Forte Tra&#238;n&#233;e</text>
      
      <!-- Effet de lacet adverse -->
      <path d="M0,-100 A100,100 0 0,1 60,-80" fill="none" stroke="#1d4ed8" stroke-width="3" marker-end="url(#arrow-blue)"/>
      <text x="70" y="-80" font-family="Arial" font-size="14" fill="#1d4ed8" font-weight="bold" class="aerolex-terme" data-slug="lacet-adverse">Lacet adverse (nez &#224; droite)</text>
    </g>
  </g>

  <text x="320" y="360" font-family="Arial" font-size="14" fill="#1e3a5f" text-anchor="middle">L'aileron baiss&#233; (pour monter l'aile) cr&#233;e plus de tra&#238;n&#233;e, tirant le nez du c&#244;t&#233; oppos&#233; au virage.</text>
  <text x="320" y="380" font-family="Arial" font-size="14" fill="#16a34a" font-weight="bold" text-anchor="middle" class="aerolex-terme" data-slug="conjugaison">On compense au palonnier : c'est la conjugaison.</text>

  <defs>
    <marker id="arrow-brown" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#b45309"/></marker>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1d4ed8"/></marker>
  </defs>
</svg>""",

    "volets-hypersustentation.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE PROFIL &#183; Effet des volets (Hypersustentation)</text>
  
  <g transform="translate(150, 180)">
    <text x="0" y="-60" font-family="Arial" font-size="14" fill="#1e3a5f" font-weight="bold" text-anchor="middle">Profil Lisse (sans volets)</text>
    <path d="M-80,0 C-80,-20 30,-15 100,0 C30,5 -80,10 -80,0 Z" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/>
    <line x1="10" y1="0" x2="10" y2="-80" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow-blue)"/>
    <text x="15" y="-70" font-family="Arial" font-size="12" fill="#2563eb">Portance mod&#233;r&#233;e</text>
    <line x1="30" y1="0" x2="70" y2="0" stroke="#b45309" stroke-width="2" marker-end="url(#arrow-brown)"/>
    <text x="75" y="15" font-family="Arial" font-size="12" fill="#b45309">Tra&#238;n&#233;e faible</text>
  </g>

  <g transform="translate(450, 180)">
    <text x="0" y="-60" font-family="Arial" font-size="14" fill="#1e3a5f" font-weight="bold" text-anchor="middle">Avec Volets Sortis</text>
    <path d="M-80,0 C-80,-20 30,-15 70,-5 C30,0 -80,10 -80,0 Z" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/>
    <!-- Volet d&#233;ploy&#233; vers le bas -->
    <path d="M70,-5 C85,5 95,20 100,30 L80,25 C75,15 70,-5 70,-5 Z" fill="#94a3b8" stroke="#475569" stroke-width="2"/>
    
    <!-- Portance massive -->
    <line x1="10" y1="0" x2="10" y2="-130" stroke="#2563eb" stroke-width="5" marker-end="url(#arrow-blue)"/>
    <text x="15" y="-120" font-family="Arial" font-size="14" fill="#2563eb" font-weight="bold" class="aerolex-terme" data-slug="hypersustentation">Grosse Portance (+)</text>
    
    <!-- Tra&#238;n&#233;e massive -->
    <line x1="30" y1="0" x2="130" y2="0" stroke="#b45309" stroke-width="5" marker-end="url(#arrow-brown)"/>
    <text x="80" y="-10" font-family="Arial" font-size="14" fill="#b45309" font-weight="bold">Grosse Tra&#238;n&#233;e (+)</text>
  </g>

  <defs>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2563eb"/></marker>
    <marker id="arrow-brown" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#b45309"/></marker>
  </defs>
</svg>""",

    "aerofrein-effet.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE PROFIL &#183; Effet de l'a&#233;rofrein (Destructeur de portance)</text>
  
  <g transform="translate(320, 200)">
    <!-- Profil avec A&#233;rofrein sur l'extrados -->
    <path d="M-150,0 C-150,-30 50,-20 150,0 C50,10 -150,20 -150,0 Z" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/>
    <!-- A&#233;rofrein (lame lev&#233;e au-dessus de l'aile) -->
    <rect x="-20" y="-40" width="5" height="30" fill="#475569" stroke="#0f172a" stroke-width="2"/>
    <text x="-15" y="-50" font-family="Arial" font-size="14" fill="#0f172a" font-weight="bold" class="aerolex-terme" data-slug="aerofrein">A&#233;rofrein sorti</text>
    
    <!-- D&#233;collement des filets d'air (tourbillons) -->
    <path d="M-150,-10 C-50,-25 -25,-40 -20,-60" fill="none" stroke="#38bdf8" stroke-width="2" stroke-dasharray="5,3"/>
    <circle cx="10" cy="-20" r="10" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="2,2"/>
    <circle cx="40" cy="-15" r="15" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="2,2"/>
    <circle cx="80" cy="-10" r="20" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="2,2"/>
    <text x="40" y="-40" font-family="Arial" font-size="12" fill="#64748b">D&#233;collement (Portance d&#233;truite)</text>
    
    <!-- Portance r&#233;duite -->
    <line x1="-50" y1="0" x2="-50" y2="-40" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow-blue)"/>
    <text x="-55" y="-20" font-family="Arial" font-size="14" fill="#2563eb" text-anchor="end">Portance r&#233;duite (-)</text>
    
    <!-- Tra&#238;n&#233;e massive -->
    <line x1="20" y1="0" x2="200" y2="0" stroke="#b45309" stroke-width="6" marker-end="url(#arrow-brown)"/>
    <text x="100" y="20" font-family="Arial" font-size="14" fill="#b45309" font-weight="bold" class="aerolex-terme" data-slug="trainee">Grosse Tra&#238;n&#233;e (+)</text>
  </g>
  
  <text x="320" y="360" font-family="Arial" font-size="14" fill="#1e3a5f" text-anchor="middle">Contrairement au volet (qui ajoute de la portance), l'a&#233;rofrein d&#233;truit la portance</text>
  <text x="320" y="380" font-family="Arial" font-size="14" fill="#1e3a5f" text-anchor="middle">et cr&#233;e de la tra&#238;n&#233;e pour descendre sans acc&#233;l&#233;rer.</text>

  <defs>
    <marker id="arrow-blue" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#2563eb"/></marker>
    <marker id="arrow-brown" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#b45309"/></marker>
  </defs>
</svg>""",

    "profil-aile-geometrie.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">VUE DE PROFIL &#183; G&#233;om&#233;trie de l'aile</text>
  
  <g transform="translate(320, 200)">
    <!-- Profil d'aile : Bord d'attaque ARRONDI (-200), bord de fuite EFFIL&#201; (200) -->
    <path d="M-200,0 C-200,-80 50,-60 200,0 C50,20 -200,30 -200,0 Z" fill="#cbd5e1" stroke="#64748b" stroke-width="2"/>
    
    <!-- Corde -->
    <line x1="-200" y1="0" x2="200" y2="0" stroke="#1e3a5f" stroke-width="2" stroke-dasharray="5,5"/>
    <text x="0" y="15" font-family="Arial" font-size="14" fill="#1e3a5f" class="aerolex-terme" data-slug="corde">Corde</text>
    
    <!-- &#201;paisseur maximale -->
    <line x1="-50" y1="-43" x2="-50" y2="12" stroke="#dc2626" stroke-width="2"/>
    <line x1="-60" y1="-43" x2="-40" y2="-43" stroke="#dc2626" stroke-width="2"/>
    <line x1="-60" y1="12" x2="-40" y2="12" stroke="#dc2626" stroke-width="2"/>
    <text x="-40" y="-10" font-family="Arial" font-size="14" fill="#dc2626" class="aerolex-terme" data-slug="epaisseur">&#201;paisseur</text>
    
    <!-- Extrados -->
    <text x="0" y="-60" font-family="Arial" font-size="14" fill="#0284c7" font-weight="bold" class="aerolex-terme" data-slug="extrados">Extrados (Dessus)</text>
    
    <!-- Intrados -->
    <text x="0" y="40" font-family="Arial" font-size="14" fill="#0284c7" font-weight="bold" class="aerolex-terme" data-slug="intrados">Intrados (Dessous)</text>
    
    <!-- Bord d'attaque -->
    <circle cx="-200" cy="0" r="5" fill="#f59e0b"/>
    <text x="-210" y="-20" font-family="Arial" font-size="14" fill="#b45309" font-weight="bold" text-anchor="end" class="aerolex-terme" data-slug="bord-d-attaque">Bord d'attaque (Arrondi)</text>
    
    <!-- Bord de fuite -->
    <circle cx="200" cy="0" r="5" fill="#f59e0b"/>
    <text x="210" y="-20" font-family="Arial" font-size="14" fill="#b45309" font-weight="bold" class="aerolex-terme" data-slug="bord-de-fuite">Bord de fuite (Effil&#233;)</text>
  </g>
</svg>""",

    "polaire-cz-cx.svg": """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 400">
  <rect width="640" height="400" fill="#e0f2fe"/>
  <rect x="10" y="10" width="620" height="380" fill="#f8fafc" stroke="#94a3b8" stroke-width="2"/>
  <text x="320" y="40" font-family="Arial" font-size="18" fill="#1e3a5f" font-weight="bold" text-anchor="middle">GRAPHIQUE &#183; Polaire de l'aile (Cz en fonction de Cx)</text>
  
  <g transform="translate(150, 320)">
    <!-- Axes -->
    <line x1="0" y1="0" x2="400" y2="0" stroke="#1e3a5f" stroke-width="2" marker-end="url(#arrow-axis)"/>
    <text x="390" y="20" font-family="Arial" font-size="14" fill="#1e3a5f" class="aerolex-terme" data-slug="coefficient-de-trainee">Cx (Coef. Tra&#238;n&#233;e)</text>
    
    <line x1="0" y1="0" x2="0" y2="-250" stroke="#1e3a5f" stroke-width="2" marker-end="url(#arrow-axis)"/>
    <text x="-10" y="-240" font-family="Arial" font-size="14" fill="#1e3a5f" text-anchor="end" class="aerolex-terme" data-slug="coefficient-de-portance">Cz (Coef. Portance)</text>
    
    <!-- Courbe polaire -->
    <path d="M 20,-20 Q 30,-150 150,-200 Q 250,-220 300,-150 Q 330,-100 350,-50" fill="none" stroke="#2563eb" stroke-width="3"/>
    
    <!-- Point de Finesse Max (Tangente depuis l'origine) -->
    <line x1="0" y1="0" x2="160" y2="-213.3" stroke="#10b981" stroke-width="2" stroke-dasharray="4,4"/>
    <circle cx="125" cy="-166" r="5" fill="#10b981"/>
    <text x="140" y="-166" font-family="Arial" font-size="14" fill="#047857" font-weight="bold" class="aerolex-terme" data-slug="finesse">Finesse max</text>
    
    <!-- Cz max et D&#233;crochage -->
    <circle cx="205" cy="-210" r="5" fill="#dc2626"/>
    <text x="215" y="-215" font-family="Arial" font-size="14" fill="#dc2626" font-weight="bold">Cz Max</text>
    
    <text x="320" y="-150" font-family="Arial" font-size="14" fill="#dc2626" font-weight="bold" class="aerolex-terme" data-slug="decrochage">D&#233;crochage</text>
  </g>

  <defs>
    <marker id="arrow-axis" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#1e3a5f"/></marker>
  </defs>
</svg>"""
}

def validate_svg(filename, content):
    try:
        xml.dom.minidom.parseString(content)
        return True
    except Exception as e:
        print(f"XML Validation failed for {filename}: {e}")
        return False

for filename, content in svgs.items():
    filepath = os.path.join(out_dir, filename)
    with open(filepath, "w") as f:
        f.write(content)
    
    if validate_svg(filename, content):
        print(f"Generated and validated {filename}")
        
        # Phase 2 prep: convert to PNG
        png_filename = filename.replace(".svg", ".png")
        png_filepath = os.path.join(out_dir, png_filename)
        try:
            subprocess.run(["rsvg-convert", "-w", "1280", "-b", "white", filepath, "-o", "png_filepath"], check=True, stderr=subprocess.PIPE)
            # Actually need to pass the real png_filepath, fixed in Popen below
            subprocess.run(f"rsvg-convert -w 1280 -b white '{filepath}' -o '{png_filepath}'", shell=True, check=True)
            print(f"Converted {filename} to PNG.")
        except Exception as e:
            print(f"Failed to convert {filename} to PNG: {e}")
            
print("All tasks completed.")
