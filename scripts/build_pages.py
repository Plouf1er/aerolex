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

from slugify import build_slug_map, build_redirects
from data_glossaire_full import GLOSSAIRE
from svg_glossaire import SCHEMAS, get_schema
from extra_content import get_extra_content

# SOURCE DE VÉRITÉ UNIQUE du contenu d'un terme (2026-08-04).
# Ce module décide seul de ce que contient une fiche ; il alimente
# À LA FOIS ce générateur HTML et scripts/build_terms_json.py (fichiers par
# mot fetchés par la popup). Le HTML ci-dessous n'est plus qu'un RENDU du
# payload : il ne relit jamais GLOSSAIRE pour décider d'un contenu, donc la
# fiche en ligne et la popup ne peuvent pas diverger.
from term_payload import PayloadContext, build_payload
from term_display import family_label, family_sort_key

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

from lexicon_env import LEX_ID as LEXICON_ID, index_name as _INDEX_NAME, search_name as _SEARCH_NAME, meta as _lex_meta  # noqa: E402
VISIBILITY = 'public'
EMBED_KEY = None

DIST_DIR = 'dist/' + LEXICON_ID
os.makedirs(DIST_DIR, exist_ok=True)

# Build slug map
termes = list(GLOSSAIRE.keys())
terme_to_slug, collisions = build_slug_map(termes, GLOSSAIRE)
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


def _dev_span(m):
    """Développé à côté d'un libellé de liste : sigle -> '— développé (FR)',
    expression contenant un sigle -> '(développé du sigle — FR)'."""
    if m.get('dev'):
        return f' <span class="dev">— {escape(m["dev"])}</span>'
    if m.get('expr'):
        return f' <span class="dev">({escape(m["expr"])})</span>'
    return ''


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
        family_html = f"<h3>Famille : {escape(p['famille_label'])}</h3><ul>"
        for m in p['famille_membres']:
            dev = _dev_span(m)
            if m['courant']:
                family_html += f"<li><strong>{escape(m['titre'])}</strong>{dev}</li>"
            else:
                family_html += f'<li><a href="{escape(m["sl"])}.html">{escape(m["titre"])}</a>{dev}</li>'
        family_html += "</ul>"

    prev_link = f'<a href="{escape(p["prev"]["sl"])}.html">&laquo; {escape(p["prev"]["titre"])}</a>' if p['prev'] else '<span></span>'
    next_link = f'<a href="{escape(p["next"]["sl"])}.html">{escape(p["next"]["titre"])} &raquo;</a>' if p['next'] else '<span></span>'
    
    meta_desc = escape(definition[:152] + '...') if len(definition) > 155 else escape(definition)
    robots = '<meta name="robots" content="noindex">' if VISIBILITY == 'private' else ''
    
    canonical_url = f"https://example.com/{LEXICON_ID}/{escape(slug)}.html"
    
    fam_label_esc = escape(p['famille_label'])
    fam_meta = (f'<span class="chip aerolex-skip">Famille: <a href="index.html?fam={quote(famille)}">{fam_label_esc}</a></span>' if famille else "")
    sg = p['sigle']
    sigle_html = ''
    if sg:
        sigle_html = (f'<p class="sigle"><strong>{escape(p["titre"])}</strong> — {escape(sg["developpement"])}'
                      + (f' ({escape(sg["equivalent"])})' if sg.get('equivalent') else '') + '</p>')
    if not sigle_html and p['sigles_expr']:
        sigle_html = '<p class="sigle">' + ' ; '.join(
            f'<strong>{escape(x["s"])}</strong> — {escape(x["dev"])}' for x in p['sigles_expr']) + '</p>'
    html_content = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(p['titre'])} - Glossaire Aéronautique</title>
    <meta name="description" content="{meta_desc}">
    <link rel="canonical" href="{canonical_url}">
    <meta property="og:title" content="{escape(p['titre'])} - Glossaire Aéronautique">
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
    <nav class="crumb">
        {prev_link}
        <a href="index.html">Index Sommaire</a>
        {next_link}
    </nav>
    <main>
        <header class="fiche-head">
            <h1>{escape(p['titre'])}</h1>
            {sigle_html}
            <div class="meta">
                {f'<span class="chip cat aerolex-skip">Catégorie: <a href="index.html?cat={quote(categorie)}">{escape(categorie)}</a></span>' if categorie else ""}
                {fam_meta}
            </div>
        </header>
        
        <div class="definition">
            <p>{escape(definition)}</p>
        </div>
"""
    if variantes:
        html_content += f"<div class=\"aliases\"><strong>Aussi appelé :</strong> {escape(', '.join(variantes))}</div>" if not (p['variantes_dev'] or p['variantes_expr']) else (
            '<div class="aliases"><strong>Aussi appelé :</strong> ' + '; '.join(
                escape(a) + (f' <span class="dev">— {escape(p["variantes_dev"][a])}</span>' if a in p['variantes_dev']
                             else f' <span class="dev">({escape(p["variantes_expr"][a])})</span>' if a in p['variantes_expr'] else '')
                for a in variantes) + '</div>')
        
    if svg_html:
        html_content += f'<div class="svg-container">\n{svg_html}\n</div>'
        
    extra_html = get_extra_content(slug)
    if extra_html:
        html_content += extra_html

    if has_family_table:
        html_content += f'<div class="family-table">{family_html}</div>'
        
    if valid_xrefs:
        html_content += '<div class="xrefs"><strong>Voir aussi :</strong><ul>'
        for xr in valid_xrefs:
            dev = _dev_span(xr)
            html_content += f'<li><a href="{escape(xr["sl"])}.html">{escape(xr["titre"])}</a>{dev}</li>'
        html_content += '</ul></div>'
        
    html_content += f"""
    </main>
    <script src="../aerolex.js?v={ASSET_V}" data-index="../{_INDEX_NAME()}?v={ASSET_V}" data-lexicon="{LEXICON_ID}" defer></script>
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
    # Rendu isolé dans scripts/index_page.py (mise en page, recherche, lettres vides masquées).
    from index_page import render_index
    # Familles triées ici (Divers en dernier : test_familles.py cherche ce tri dans ce fichier).
    fam_order = sorted(families.keys(), key=family_sort_key)
    html_content = render_index(
        GLOSSAIRE, PAYLOAD_CTX.display, terme_to_slug, families, fam_order, categories_set,
        family_label, ASSET_V, search_name=_SEARCH_NAME(),
        title=('Index du Glossaire Aéronautique — AeroLex' if LEXICON_ID == 'aero' else 'Index — ' + (_lex_meta(os.getcwd()).get('label') or LEXICON_ID) + ' — AeroLex'))
    with open(os.path.join(DIST_DIR, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(html_content)

def write_slugmap():
    """dist/aero/slugmap.json : terme canonique -> slug. Lu par le JS de clic
    des fiches ET de l'index. Il était écrit une fois à la main (4 août) et
    jamais régénéré : tout terme ajouté depuis n'avait plus de cible."""
    import json as _json
    redirects = build_redirects(terme_to_slug)
    out = dict(sorted(terme_to_slug.items()))
    if redirects:
        out['_redirects'] = redirects     # ancien slug -> slug actuel (liens existants conserves)
    with open(os.path.join(DIST_DIR, 'slugmap.json'), 'w', encoding='utf-8') as f:
        _json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
    write_redirect_pages(redirects)


REDIRECT_MARK = '<!-- aerolex-redirect -->'


def write_redirect_pages(redirects):
    """Une page HTML de renvoi par ancien slug (meta refresh + canonical + JS). Les anciennes pages de renvoi
    perimees (marqueur) sont supprimees d'abord."""
    for f in glob.glob(os.path.join(DIST_DIR, '*.html')):
        with open(f, 'r', encoding='utf-8') as fp:
            if REDIRECT_MARK in fp.read(400):
                os.remove(f)
    for old, new in redirects.items():
        page = (f'{REDIRECT_MARK}<!doctype html><html lang="fr"><head><meta charset="utf-8">'
                f'<meta http-equiv="refresh" content="0; url={new}.html">'
                f'<link rel="canonical" href="{new}.html"><meta name="robots" content="noindex">'
                f'<title>Redirection</title></head><body>'
                f'<p>Cette fiche a changé d’adresse : <a href="{new}.html">{new}.html</a></p>'
                f'<script>location.replace("{new}.html"+location.search+location.hash);</script></body></html>')
        with open(os.path.join(DIST_DIR, f'{old}.html'), 'w', encoding='utf-8') as fp:
            fp.write(page)


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
    write_slugmap()
    
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
    if total_no_fam:
        print(f"AVERTISSEMENT : {total_no_fam} fiche(s) sans famille. Regle AeroLex : tout terme a une famille "
              f"(divers si aucune ne convient). Non bloquant tant que le classement existant n'est pas applique ; "
              f"les NOUVEAUX ajouts sans famille sont refuses par src/import_lexique.py --write.")
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
