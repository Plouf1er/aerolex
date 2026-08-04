import sys
import os
import glob
from collections import defaultdict
import html
from urllib.parse import quote
import re

sys.path.insert(0, 'scripts')
sys.path.insert(0, 'data')
sys.path.insert(0, 'src')

from slugify import build_slug_map
from data_glossaire_full import GLOSSAIRE
from svg_glossaire import SCHEMAS, get_schema

# SOURCE DE VÉRITÉ UNIQUE du contenu d'un terme (2026-08-04).
# Ce module décide seul de ce que contient une fiche ; il alimente
# À LA FOIS ce générateur HTML et scripts/build_terms_json.py (fichiers par
# mot fetchés par la popup). Le HTML ci-dessous n'est plus qu'un RENDU du
# payload : il ne relit jamais GLOSSAIRE pour décider d'un contenu, donc la
# fiche en ligne et la popup ne peuvent pas diverger.
from term_payload import PayloadContext, build_payload

# --- JS de navigation (hors f-string : contient des accolades) ---
NAV_JS_TMPL = """<script>
var CURRENT_SLUG=%%SLUG%%;
/* AeroLex - sur une page de fiche, un mot surligne mene a SA page (pas d'overlay). */
(function(){
  var SLUGS=null;
  fetch('slugmap.json').then(function(r){return r.json();}).then(function(j){SLUGS=j;});
  document.addEventListener('click',function(e){
    var s=e.target.closest?e.target.closest('span.glos'):null;
    if(!s)return;
    var t=s.dataset.term;
    if(!t||!SLUGS)return;
    var sl=SLUGS[t];
    if(!sl||sl===CURRENT_SLUG)return;
    e.preventDefault();
    window.location.href=sl+'.html';
  },true);
})();
</script>"""

def nav_js(slug):
    import json as _j
    return NAV_JS_TMPL.replace('%%SLUG%%', _j.dumps(slug))


# Lu de la base plus tard
# ── Version des assets (cache-busting Cloudflare, max-age=14400) ────────────
# AVANT : constante écrite à la main, à incrémenter manuellement. Oubliée deux
# fois le 03-04/08/2026 → Cloudflare a servi un vieux aerolex.css (HIT).
# MAINTENANT : empreinte sha256 (8 hex) CALCULÉE du contenu réel de
# aerolex.js + aerolex.css + aerolex-svg.js + lexicon.json. Toute modif de code
# ou de réglage client change l'URL automatiquement. Zéro discipline humaine.
from asset_fingerprint import asset_fingerprint, write_build_info  # noqa: E402

ASSET_V = asset_fingerprint()

LEXICON_ID = 'aero'
VISIBILITY = 'public'
EMBED_KEY = None

DIST_DIR = 'dist/aero'
os.makedirs(DIST_DIR, exist_ok=True)

# Build slug map
termes = list(GLOSSAIRE.keys())
terme_to_slug, collisions = build_slug_map(termes)
if collisions:
    print(f"Warning: slug collisions: {collisions}")

slug_to_terme = {v: k for k, v in terme_to_slug.items()}

# Mapping schema — SOURCE UNIQUE dans scripts/schema_map.py (partagé avec
# build_index_js.py et build_schemas_json.py). Ne pas redéclarer ici.
from schema_map import TERM_TO_SCHEMA

# Pre-compute families
families = defaultdict(list)
categories_set = set()
for terme, data in GLOSSAIRE.items():
    fam = data.get('famille')
    if fam:
        families[fam].append(terme)
    cat = data.get('categorie')
    if cat:
        categories_set.add(cat)

for fam in families:
    families[fam].sort(key=lambda t: t.lower())

def escape(s):
    if not s: return ""
    return html.escape(str(s))

# Contexte de payload : calculé UNE fois (slugs, familles, ordre alphabétique),
# partagé par les 1296 rendus.
PAYLOAD_CTX = PayloadContext(GLOSSAIRE)


def generate_term_page(terme, index_list):
    # ── Tout le contenu vient du payload, jamais de GLOSSAIRE en direct ──
    p = build_payload(terme, PAYLOAD_CTX)

    slug = p['slug']
    definition = p['definition']
    categorie = p['categorie']
    famille = p['famille']
    variantes = p['variantes']

    svg_html = p['schema_svg'] or ""
    has_svg = bool(p['schema_svg'])

    # Xrefs déjà filtrées (existence réelle) et résolues en slug par le payload.
    valid_xrefs = p['xrefs']

    # Tableau de famille : membres déjà triés + marqués « courant ».
    family_html = ""
    has_family_table = bool(p['famille_membres'])
    if has_family_table:
        family_html = f"<h3>Famille : {escape(famille)}</h3><ul>"
        for m in p['famille_membres']:
            if m['courant']:
                family_html += f"<li><strong>{escape(m['t'])}</strong></li>"
            else:
                family_html += f'<li><a href="{escape(m["sl"])}.html">{escape(m["t"])}</a></li>'
        family_html += "</ul>"

    prev_link = f'<a href="{escape(p["prev"]["sl"])}.html">&laquo; {escape(p["prev"]["t"])}</a>' if p['prev'] else '<span></span>'
    next_link = f'<a href="{escape(p["next"]["sl"])}.html">{escape(p["next"]["t"])} &raquo;</a>' if p['next'] else '<span></span>'
    
    meta_desc = escape(definition[:152] + '...') if len(definition) > 155 else escape(definition)
    robots = '<meta name="robots" content="noindex">' if VISIBILITY == 'private' else ''
    
    canonical_url = f"https://example.com/aero/{escape(slug)}.html"
    
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(terme)} - Glossaire Aéronautique</title>
    <meta name="description" content="{meta_desc}">
    <link rel="canonical" href="{canonical_url}">
    <meta property="og:title" content="{escape(terme)} - Glossaire Aéronautique">
    <meta property="og:description" content="{meta_desc}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{canonical_url}">
    {robots}
    <link rel="stylesheet" href="../aerolex.css?v={ASSET_V}">
    <link rel="stylesheet" href="../aerolex-page.css?v={ASSET_V}">
    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "DefinedTerm",
      "name": "{escape(terme)}",
      "description": "{meta_desc}"
    }}
    </script>
</head>
<body>
    <nav>
        {prev_link}
        <a href="index.html">Index Sommaire</a>
        {next_link}
    </nav>
    <main>
        <h1>{escape(terme)}</h1>
        <div class="meta">
            {f'Catégorie: <a href="index.html?cat={quote(categorie)}">{escape(categorie)}</a> | ' if categorie else ""}
            {f'Famille: <a href="index.html?fam={quote(famille)}">{escape(famille)}</a>' if famille else ""}
        </div>
        
        <div class="definition">
            <p>{escape(definition)}</p>
        </div>
"""
    if variantes:
        html_content += f"<div><strong>Variantes:</strong> {escape(', '.join(variantes))}</div>"
        
    if svg_html:
        html_content += f'<div class="svg-container">\n{svg_html}\n</div>'
        
    if has_family_table:
        html_content += f'<div class="family-table">{family_html}</div>'
        
    if valid_xrefs:
        html_content += '<div class="xrefs"><strong>Voir aussi :</strong><ul>'
        for xr in valid_xrefs:
            html_content += f'<li><a href="{escape(xr["sl"])}.html">{escape(xr["t"])}</a></li>'
        html_content += '</ul></div>'
        
    html_content += f"""
    </main>
    <script src="../aerolex.js?v={ASSET_V}" data-index="../aerolex-index.json?v={ASSET_V}" data-lexicon="aero" defer></script>
    <!-- Libellés des schémas SVG cliquables (aerolex-svg.js). Sur une page de
         fiche, aucun hook onTermClick n'est posé : le module navigue lui-même
         vers la page du mot. -->
    <script src="../aerolex-svg.js?v={ASSET_V}" defer></script>
    {nav_js(slug)}
</body>
</html>
"""
    with open(os.path.join(DIST_DIR, f"{slug}.html"), 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    return has_svg, has_family_table, not bool(famille)

def generate_index():
    if VISIBILITY == 'private':
        return
        
    letters = defaultdict(list)
    for terme in sorted(GLOSSAIRE.keys(), key=lambda x: x.lower()):
        letter = terme[0].upper()
        if not letter.isalpha():
            letter = '#'
        letters[letter].append(terme)
        
    cat_opts = "".join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in sorted(categories_set))
    fam_opts = "".join(f'<option value="{escape(f)}">{escape(f)} ({len(families[f])})</option>' for f in sorted(families.keys()))
    
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index du Glossaire Aéronautique</title>
    <link rel="stylesheet" href="../aerolex.css?v={ASSET_V}">
    <link rel="stylesheet" href="../aerolex-page.css?v={ASSET_V}">
    <style>
        .letter-group {{ margin-bottom: 2rem; }}
        .letter-nav a {{ margin-right: 0.5rem; text-decoration: none; }}
        .term-list {{ list-style-type: none; padding: 0; }}
        .term-list li {{ margin-bottom: 0.5rem; }}
    </style>
</head>
<body>
    <h1>Index Sommaire ( {len(GLOSSAIRE)} termes, {len(categories_set)} catégories, {len(families)} familles )</h1>
    
    <div>
        <input type="text" id="search" placeholder="Recherche rapide..." style="width: 100%; padding: 0.5rem; margin-bottom: 1rem;">
        <select id="cat-filter"><option value="">Toutes les catégories</option>{cat_opts}</select>
        <select id="fam-filter"><option value="">Toutes les familles</option>{fam_opts}</select>
    </div>
    
    <div class="letter-nav">
        {"".join(f'<a href="#{escape(l)}">{escape(l)}</a>' for l in sorted(letters.keys()))}
    </div>
    
    <div id="index-content">
"""
    for letter in sorted(letters.keys()):
        html_content += f'<div class="letter-group" id="{escape(letter)}"><h2>{escape(letter)}</h2><ul class="term-list">'
        for terme in letters[letter]:
            slug = terme_to_slug[terme]
            cat = GLOSSAIRE[terme].get('categorie', '')
            fam = GLOSSAIRE[terme].get('famille', '')
            html_content += f'<li data-cat="{escape(cat)}" data-fam="{escape(fam)}"><a href="{escape(slug)}.html">{escape(terme)}</a></li>'
        html_content += '</ul></div>'
        
    html_content += """
    </div>
    <script src="../aerolex.js?v={ASSET_V}" data-index="../aerolex-index.json?v={ASSET_V}" data-lexicon="aero" defer></script>
    <script src="../aerolex-svg.js?v={ASSET_V}" defer></script>
    <script>
/* AeroLex — sur une page de fiche, un mot surligné mène à SA page (pas d'overlay). */
(function(){
  var SLUGS = null;
  fetch('slugmap.json').then(function(r){return r.json()}).then(function(j){SLUGS=j;});
  document.addEventListener('click', function(e){
    var s = e.target.closest && e.target.closest('span.glos');
    if(!s) return;
    var t = s.dataset.term; if(!t || !SLUGS) return;
    var slug = SLUGS[t]; if(!slug) return;
    if(slug === CURRENT_SLUG) return;
    e.preventDefault(); window.location.href = slug + '.html';
  }, true);
})();
</script>
    <script>
        const searchInput = document.getElementById('search');
        const catFilter = document.getElementById('cat-filter');
        const famFilter = document.getElementById('fam-filter');
        const lis = document.querySelectorAll('.term-list li');
        
        function filter() {
            const q = searchInput.value.toLowerCase();
            const c = catFilter.value;
            const f = famFilter.value;
            lis.forEach(li => {
                const text = li.textContent.toLowerCase();
                const cat = li.getAttribute('data-cat');
                const fam = li.getAttribute('data-fam');
                const matchQ = text.includes(q);
                const matchC = !c || cat === c;
                const matchF = !f || fam === f;
                li.style.display = matchQ && matchC && matchF ? '' : 'none';
            });
        }
        
        searchInput.addEventListener('input', filter);
        catFilter.addEventListener('change', filter);
        famFilter.addEventListener('change', filter);
    </script>
</body>
</html>
"""
    with open(os.path.join(DIST_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    sorted_termes = sorted(GLOSSAIRE.keys(), key=lambda x: x.lower())
    
    total_svg = 0
    total_fam = 0
    total_no_fam = 0
    
    for terme in sorted_termes:
        s, f, nf = generate_term_page(terme, sorted_termes)
        if s: total_svg += 1
        if f: total_fam += 1
        if nf: total_no_fam += 1
        
    generate_index()
    
    files = glob.glob(os.path.join(DIST_DIR, '*.html'))
    num_files = len(files)
    total_size = sum(os.path.getsize(f) for f in files)
    avg_size = total_size / num_files if num_files else 0
    
    dead_links = 0
    valid_targets = {os.path.basename(f) for f in files}
    valid_targets.add('index.html')
    
    href_re = re.compile(r'href="([^"]+)"')
    for f in files:
        with open(f, 'r', encoding='utf-8') as fp:
            content = fp.read()
            for href in href_re.findall(content):
                if href.startswith('http') or href.startswith('#') or href.startswith('mailto:') or href.startswith('../'):
                    continue
                # Strip fragment ET query string : index.html?fam=Gouvernes est
                # un lien VALIDE vers index.html (filtre de famille). Sans le
                # split('?') le compteur remontait 2453 faux morts (04/08/2026).
                target_file = href.split('#')[0].split('?')[0]
                if target_file and target_file not in valid_targets:
                    dead_links += 1
                    
    def check_page(t):
        if t not in terme_to_slug: return f"Missing '{t}'"
        slug = terme_to_slug[t]
        p = os.path.join(DIST_DIR, f"{slug}.html")
        if not os.path.exists(p): return f"Missing file {p}"
        return f"OK ({os.path.getsize(p)} bytes)"
        
    p1 = check_page('gouverne')
    p2 = check_page('tour de piste')
    p3 = check_page('manuel de vol')
    
    print(f"Pages écrites: {num_files} | Poids total: {total_size/1024:.1f} KB | Poids moyen: {avg_size:.1f} bytes")
    print(f"Pages avec SVG: {total_svg} | Pages avec tableau de famille: {total_fam} | Pages sans famille: {total_no_fam}")
    # Empreinte + métadonnées de build, consultables en public d'un simple curl
    # (/aero/build-info.json) pour diagnostiquer un cache CDN périmé.
    info = write_build_info(len(GLOSSAIRE))

    print(f"Liens morts: {dead_links}")
    print(f"Empreinte assets: {info['empreinte']} (build-info.json écrit)")
    print(f"Vérif gouverne: {p1}")
    print(f"Vérif tour de piste: {p2}")
    print(f"Vérif manuel de vol: {p3}")

if __name__ == '__main__':
    main()
