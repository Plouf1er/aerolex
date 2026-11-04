# -*- coding: utf-8 -*-
"""index_page.py — rendu HTML de dist/aero/index.html (page « Index Sommaire »).

Isolé de build_pages.py pour que la mise en page de l'index évolue sans
toucher au générateur des fiches. build_pages.generate_index() ne fait
qu'appeler render_index() avec son contexte.

Contrat :
  - la liste est rendue côté serveur (fonctionne sans JS, indexable) ;
  - chaque <li> porte data-n = texte de recherche normalisé (terme + développé
    + variantes, sans accents ni casse) pour le filtrage en direct ;
  - l'autocomplétion réutilise le MOTEUR de aerolex-searchbox.js et la donnée
    aerolex-search.json (aucune donnée dupliquée dans la page) ;
  - les lettres sans terme ne sont ni rendues ni affichées (et le JS les
    masque aussi quand le filtre les vide).
"""
import html
import re
import unicodedata
from collections import defaultdict


def norm(s):
    """Même normalisation que _alxNorm (aero.js) : sans accents, minuscule,
    apostrophes -> espace, espaces compactés."""
    s = unicodedata.normalize('NFD', str(s or ''))
    s = ''.join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[\u2019']", ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def _letter(terme):
    c = unicodedata.normalize('NFD', terme[:1] or '#')[:1].upper()
    return c if (c.isalpha() and c.isascii()) else '#'


def _esc(s):
    return html.escape(str(s)) if s else ''


def render_index(glossaire, display, terme_to_slug, families, fam_order, categories_set,
                 family_label, asset_v):
    letters = defaultdict(list)
    for terme in sorted(glossaire.keys(), key=lambda x: norm(x)):
        letters[_letter(terme)].append(terme)
    order = sorted(letters.keys(), key=lambda l: (l == '#', l))   # '#' en dernier

    def gid(l):
        return 'num' if l == '#' else l

    cat_opts = ''.join(f'<option value="{_esc(c)}">{_esc(c)}</option>' for c in sorted(categories_set))
    fam_opts = ''.join(
        f'<option value="{_esc(f)}">{_esc(family_label(f))} ({len(families[f])})</option>'
        for f in fam_order)

    letter_links = ''.join(
        f'<a href="#{gid(l)}" data-l="{gid(l)}" aria-label="Lettre {_esc(l)}">{_esc(l)}</a>' for l in order)

    groups = []
    for l in order:
        rows = []
        for terme in letters[l]:
            d = display[terme]
            g = glossaire[terme]
            slug = terme_to_slug[terme]
            cat, fam = g.get('categorie', ''), g.get('famille', '')
            exp, gloss = d['expansion'], d['gloss']
            if exp:
                dev = exp + (f' ({gloss})' if gloss else '')
            elif d.get('expr'):
                dev = f"({d['expr']})"
            else:
                dev = ''
            var = ' '.join(g.get('variantes') or [])
            n = norm(f"{d['titre']} {terme} {dev} {var}")
            fam_badge = f'<span class="ix-fam">{_esc(family_label(fam))}</span>' if fam else ''
            dev_html = f'<span class="ix-d">{_esc(dev)}</span>' if dev else ''
            rows.append(
                f'<li class="ix-item" data-cat="{_esc(cat)}" data-fam="{_esc(fam)}" data-n="{_esc(n)}">'
                f'<a class="ix-row" href="{_esc(slug)}.html">'
                f'<span class="ix-main"><span class="ix-t">{_esc(d["titre"])}</span>{dev_html}</span>'
                f'{fam_badge}</a></li>')
        groups.append(
            f'<section class="ix-group" id="{gid(l)}" data-l="{gid(l)}">'
            f'<h2 class="ix-letter">{_esc(l)}</h2><ul class="ix-list">{"".join(rows)}</ul></section>')
    body_groups = ''.join(groups)

    v = asset_v
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index du Glossaire Aéronautique — AeroLex</title>
    <meta name="description" content="AeroLex : {len(glossaire)} termes aéronautiques, sigles développés, classés par lettre et par famille.">
    <link rel="stylesheet" href="../aerolex-page.css?v={v}">
    <link rel="stylesheet" href="../aerolex-indexpage.css?v={v}">
</head>
<body class="ix">
    <header class="ix-head">
        <h1>Index <span class="ix-count">{len(glossaire)} termes</span></h1>
        <a href="suggest.html" id="suggest-link" class="ix-suggest">+ Suggérer des termes</a>
    </header>

    <div class="ix-bar" id="ix-bar">
        <div class="ix-search">
            <input type="search" id="search" placeholder="Chercher un terme, un sigle…" autocomplete="off"
                   autocapitalize="off" autocorrect="off" spellcheck="false" enterkeyhint="search"
                   role="combobox" aria-expanded="false" aria-controls="ix-sug" aria-autocomplete="list"
                   aria-label="Rechercher dans le lexique">
            <ul id="ix-sug" class="ix-sug" role="listbox" hidden></ul>
        </div>
        <div class="ix-letters" id="ix-letters" aria-label="Aller à la lettre">{letter_links}</div>
    </div>

    <div class="ix-filters">
        <label class="ix-sel"><span>Catégorie</span><select id="cat-filter"><option value="">Toutes</option>{cat_opts}</select></label>
        <label class="ix-sel"><span>Famille</span><select id="fam-filter"><option value="">Toutes</option>{fam_opts}</select></label>
    </div>
    <p class="ix-status" id="ix-status" role="status" aria-live="polite"></p>

    <main id="index-content">
{body_groups}
    </main>
    <p class="ix-empty" id="ix-empty" hidden>Aucun terme ne correspond. <a href="suggest.html">Suggérer ce terme</a></p>
    <script src="../aerolex-searchbox.js?v={v}"></script>
    <script src="../aerolex-indexpage.js?v={v}" data-search="../aerolex-search.json?v={v}"></script>
</body>
</html>
"""
