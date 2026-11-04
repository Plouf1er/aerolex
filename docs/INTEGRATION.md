# Intégrer AeroLex dans un site

## 1. Une balise

```html
<link rel="stylesheet" href="/lexique/aerolex.css">
<script src="/lexique/aerolex.js" defer data-lexicon="mon-lexique" data-src="/lexique/aerolex-mon-lexique-index.json"></script>
```

Le moteur lit l'index (JSON statique) puis souligne les termes de la page. Il n'appelle **aucun serveur** pour décider d'un soulignement. Chaque
soulignement est un `<span class="glos" data-term="…" data-occ="1|n">` (feuille `aerolex.css`).

## 2. Ce que contient l'index

```json
{ "meta": {"format": 2, "lexicon": "mon-lexique", "terms_base": "mon-lexique/t/",
           "display": {"skip_selectors": [".cookie-banner"], "metar": false},
           "rules": {"exact_case": ["ais"], "singular_exclude": ["indices"]}},
  "terms": {"voile": {"s": 1, "v": ["voiles"], "ctx": ["bateau", "mât"], "sl": "voile"}, "AIS": {"s": 1, "cs": 1, "sl": "ais"}} }
```

`terms` : règles par fiche (variantes `v`, `contexte_requis` `ctx`, homonymes `hom`, casse exacte `cs`, contextes de sigle et de singulier `cxs` `cxg`).
`meta` : règles et options du lexique (voir README « Configurer un lexique »). Un index sans `meta` (ancien format) reste lu.

## 3. Zones à ignorer

Par défaut : `script style code pre textarea input select option noscript svg canvas iframe a summary button h1…h6`, les éléments `contenteditable`, ceux
qui portent `data-aerolex-skip` ou la classe `aerolex-skip`, et les éléments posés par le moteur (`.glos`, `[class^="glos-"]`). À ajouter :

- côté intégrateur : `data-skip-selectors=".bandeau, #menu"` ou `window.AeroLexConfig = {skipSelectors: [".bandeau"]}` ;
- côté lexique : `display.skip_selectors` de `data/lexicon.json` (publié avec l'index) — c'est là que notre installation déclare les classes de son site hôte ;
- `data-skip-tags="script,style,pre"` remplace la liste de balises par défaut. Un sélecteur invalide est ignoré avec un avertissement console.

## 4. Fiche au clic

La popup de définition est celle du site hôte (le moteur expose `window.AeroLex.termUrl(slug)` → `…/t/<slug>.json`, et `termsBase`). `termsBase` suit
`AeroLexConfig.termsBase` > `window.AEROLEX_BASE` > `data-aerolex-base` > `meta.terms_base` (URL absolue, ou relative à l'index) > `<dossier de l'index>/<data-lexicon>/t/`.

## 5. Hébergement

Si le site hôte héberge lui-même `dist/`, tout est same-origin. Sinon, le serveur du lexique doit répondre en CORS pour l'index, `<lexique>/t/*` et
`<lexique>/lexicon.json` : `serve_cors.py` le fait pour les origines listées dans `aerolex.config.json` (`serve.cors_origins`) ou `$AEROLEX_CORS_ORIGINS`.
