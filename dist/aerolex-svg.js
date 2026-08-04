/* ============================================================================
   aerolex-svg.js — Surlignage des libellés DANS les schémas SVG
   ----------------------------------------------------------------------------
   Demande Louis (2026-08-04) : les mots du lexique doivent être surlignés et
   cliquables à l'intérieur des schémas (ex. « vent arrière » sur tour_de_piste),
   pas seulement dans le texte courant.

   Pourquoi un module séparé plutôt qu'une modification de svg_glossaire.py :
   src/svg_glossaire.py est INTERDIT en écriture. De toute façon le bon endroit
   est ici : le Python ne connaît pas l'index chargé côté client, et un même SVG
   sert des hôtes dont les lexiques peuvent différer. On travaille donc sur le
   DOM du SVG après insertion.

   Contraintes SVG (≠ HTML) :
     - pas de <span> : on ne peut pas envelopper une sous-chaîne d'un <text>
       sans casser le positionnement (x/y/text-anchor portés par l'élément).
       => on ne surligne QUE les <text>/<tspan> dont le contenu ENTIER
          correspond à un terme du lexique. Pas de découpage partiel : c'est
          exactement le cas d'usage des libellés de schéma, qui sont des
          étiquettes atomiques (« vent arrière », « finale », « QFU »).
     - <a> SVG doit être créé dans le namespace SVG (createElementNS), sinon il
       est inerte. On utilise donc une classe + un handler délégué + le curseur,
       ce qui évite aussi de réécrire l'arbre (zéro perte de listener).

   Comportement du clic :
     - page de fiche  -> navigation vers la page du mot ;
     - dans la popup  -> remplacement du contenu de la popup (comme un clic
       normal sur un mot souligné), via le hook window.AeroLexSvg.onTermClick
       posé par aero.js.
   ========================================================================== */
(function () {
  'use strict';

  var SVG_NS = 'http://www.w3.org/2000/svg';
  var CLS = 'alx-svg-term';

  /** Normalise pour comparer : minuscules, espaces/NBSP compactés, trim. */
  function norm(s) {
    return String(s == null ? '' : s)
      .replace(/\u00a0/g, ' ')
      .replace(/\s+/g, ' ')
      .trim()
      .toLowerCase();
  }

  /* Table de correspondance « libellé normalisé -> {terme canonique, slug} ».
     Construite depuis l'index de surlignage (window.AeroLex.terms), variantes
     incluses : un schéma peut porter « vent arrière » quand la clé canonique
     est « vent arrière (branche) ». Mémoïsée, mais invalidée si l'index change
     de taille (chargement tardif). */
  var _lookup = null;
  var _lookupSize = -1;

  function buildLookup() {
    var terms = (window.AeroLex && window.AeroLex.terms) || {};
    var keys = Object.keys(terms);
    if (_lookup && _lookupSize === keys.length) return _lookup;

    var map = Object.create(null);
    for (var i = 0; i < keys.length; i++) {
      var canon = keys[i];
      var e = terms[canon] || {};
      var rec = { terme: canon, slug: e.sl || null, s: e.s };
      var n = norm(canon);
      if (n && !map[n]) map[n] = rec;
      var vs = e.v || [];
      for (var j = 0; j < vs.length; j++) {
        var nv = norm(vs[j]);
        // Une variante ne doit jamais écraser une clé canonique.
        if (nv && !map[nv]) map[nv] = rec;
      }
    }
    _lookup = map;
    _lookupSize = keys.length;
    return map;
  }

  /** Cible d'un libellé, ou null. Tolère un libellé ponctué (« finale : »). */
  function resolveLabel(txt) {
    var map = buildLookup();
    var n = norm(txt);
    if (!n) return null;
    if (map[n]) return map[n];
    // Retire une ponctuation terminale/initiale légère et les parenthèses.
    var cleaned = n.replace(/^[(\[«"'\s]+|[)\]»"':;,.!?\s]+$/g, '');
    if (cleaned && cleaned !== n && map[cleaned]) return map[cleaned];
    return null;
  }

  /* Marque un élément SVG textuel comme terme cliquable.
     On ne touche ni x/y ni text-anchor : le rendu ne bouge pas d'un pixel.
     Le soulignement discret vient du CSS (.alx-svg-term), pas d'un attribut. */
  function markElement(el, rec) {
    if (!el || el.getAttribute('data-alx-term')) return false;
    el.setAttribute('data-alx-term', rec.terme);
    if (rec.slug) el.setAttribute('data-alx-slug', rec.slug);
    if (!rec.s) el.setAttribute('data-alx-todo', '1');
    var cur = el.getAttribute('class') || '';
    el.setAttribute('class', (cur ? cur + ' ' : '') + CLS);
    // Accessibilité : un libellé cliquable doit être atteignable et annoncé.
    el.setAttribute('role', 'link');
    el.setAttribute('tabindex', '0');
    var t = el.getAttribute('data-alx-term');
    el.setAttribute('aria-label', t + ' — ouvrir la définition');
    if (!el.querySelector || !el.querySelector('title')) {
      try {
        var ti = document.createElementNS(SVG_NS, 'title');
        ti.textContent = t + ' — ouvrir la définition';
        el.appendChild(ti);
      } catch (e) { /* title optionnel */ }
    }
    return true;
  }

  /* Traite un <svg> : renvoie le nombre de libellés rendus cliquables.
     Stratégie : on privilégie les <tspan> quand il y en a (un <text> découpé en
     lignes), sinon le <text> entier. Un <text> dont les tspans ont matché n'est
     pas marqué en plus — sinon double zone cliquable imbriquée. */
  function processSvg(svg) {
    if (!svg || svg.getAttribute('data-alx-svg-done') === '1') return 0;
    var n = 0;
    var texts = svg.querySelectorAll('text');
    for (var i = 0; i < texts.length; i++) {
      var t = texts[i];
      var tspans = t.querySelectorAll('tspan');
      var hitInner = 0;
      for (var j = 0; j < tspans.length; j++) {
        var rec = resolveLabel(tspans[j].textContent);
        if (rec && markElement(tspans[j], rec)) { hitInner++; n++; }
      }
      if (hitInner) continue;               // déjà traité au niveau tspan
      var recT = resolveLabel(t.textContent);
      if (recT && markElement(t, recT)) n++;
    }
    svg.setAttribute('data-alx-svg-done', '1');
    return n;
  }

  /** Traite tous les <svg> d'une racine (document, ou la popup). */
  function process(root) {
    root = root || document;
    if (!root.querySelectorAll) return 0;
    var svgs = root.querySelectorAll('svg');
    var total = 0;
    for (var i = 0; i < svgs.length; i++) total += processSvg(svgs[i]);
    return total;
  }

  /* Handler délégué unique, posé sur document en capture : fonctionne pour les
     SVG déjà présents ET pour ceux injectés plus tard dans la popup, sans
     jamais réattacher quoi que ce soit. */
  function onActivate(e) {
    var el = e.target;
    // closest() n'existe pas sur les éléments SVG des vieux moteurs : remontée
    // manuelle jusqu'au porteur de data-alx-term.
    var hit = null;
    while (el && el !== document) {
      if (el.getAttribute && el.getAttribute('data-alx-term')) { hit = el; break; }
      el = el.parentNode;
    }
    if (!hit) return;
    if (e.type === 'keydown' && e.key !== 'Enter' && e.key !== ' ') return;
    if (e.type === 'click' && (e.metaKey || e.ctrlKey || e.shiftKey)) return;

    var terme = hit.getAttribute('data-alx-term');
    var slug = hit.getAttribute('data-alx-slug');
    e.preventDefault();
    e.stopPropagation();

    /* Aiguillage : si un hôte a fourni un hook (aero.js dans les séances), on
       lui passe la main -> le clic remplace le contenu de la popup. Sinon on
       est sur une page de fiche -> navigation vers la page du mot. */
    var hook = window.AeroLexSvg && window.AeroLexSvg.onTermClick;
    if (typeof hook === 'function') { hook(terme, slug, hit); return; }
    if (slug) {
      var base = (window.AEROLEX_PAGE_BASE || '');
      window.location.href = base + slug + '.html';
    }
  }

  document.addEventListener('click', onActivate, true);
  document.addEventListener('keydown', onActivate, true);

  /* Auto-traitement au chargement + à chaque SVG injecté (popup).
     MutationObserver plutôt qu'un timer : coût nul quand rien ne bouge. */
  function autorun() {
    var n = process(document);
    if (n) console.info('[AeroLex/SVG] ' + n + ' libellé(s) de schéma rendus cliquables');
    if (window.MutationObserver) {
      new MutationObserver(function (muts) {
        for (var i = 0; i < muts.length; i++) {
          var added = muts[i].addedNodes || [];
          for (var j = 0; j < added.length; j++) {
            var node = added[j];
            if (node.nodeType !== 1) continue;
            if (node.tagName && node.tagName.toLowerCase() === 'svg') processSvg(node);
            else if (node.querySelectorAll) process(node);
          }
        }
      }).observe(document.documentElement, { childList: true, subtree: true });
    }
  }

  window.AeroLexSvg = window.AeroLexSvg || {};
  window.AeroLexSvg.process = process;
  window.AeroLexSvg.resolveLabel = resolveLabel;
  window.AeroLexSvg.version = '1.0.0';

  /* L'index peut arriver après nous (aerolex.js fetche en asynchrone). On
     retente donc une fois l'index disponible : sans lui, resolveLabel() ne
     matcherait rien et tous les libellés resteraient inertes. */
  function waitIndexThenRun(tries) {
    var terms = (window.AeroLex && window.AeroLex.terms);
    if (terms && Object.keys(terms).length) { autorun(); return; }
    if (tries <= 0) return;
    setTimeout(function () { waitIndexThenRun(tries - 1); }, 120);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () { waitIndexThenRun(60); });
  } else {
    waitIndexThenRun(60);
  }
})();
