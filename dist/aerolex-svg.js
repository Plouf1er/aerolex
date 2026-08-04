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

  /* ── RÉSOLUTION : déléguée au moteur de surlignage ────────────────────────
     AVANT (v1.0.0) : ce fichier reconstruisait sa propre table
     « libellé normalisé -> terme » avec un norm() maison (minuscules + trim).
     Trois divergences avec le moteur texte, donc trois familles de ratés :
       1. pas de stripAccents (NFKD)  -> « décollage » vs « decollage » ;
       2. pas de pluriels automatiques -> « volets » ne trouvait pas « volet » ;
       3. pas de règle case_sensitive  -> les sigles courts homographes
          (« S », « A »…) pouvaient matcher un mot français quelconque.
     Et surtout : match sur le libellé ENTIER uniquement, donc un libellé
     composite (« rejointe vent arrière », « remise · montée ») ne résolvait
     rien alors qu'il contient un terme.

     MAINTENANT : window.AeroLex.resolveSurface() — même regex, mêmes maps
     ciMap/csMap, mêmes pluriels/variantes/homographes que le texte courant.
     Un seul moteur de matching dans tout le projet. */
  function resolveSurfaces(txt) {
    var f = window.AeroLex && window.AeroLex.resolveSurface;
    if (typeof f !== 'function') return [];
    try { return f(txt) || []; } catch (e) { return []; }
  }

  /* Terme de la fiche courante : on ne se renvoie jamais à soi-même.
     Sur une page de fiche, CURRENT_SLUG est posé par build_pages.py ; dans la
     popup, aero.js publie le slug affiché via AeroLexSvg.currentSlug. */
  function currentSlug() {
    if (window.AeroLexSvg && window.AeroLexSvg.currentSlug) return window.AeroLexSvg.currentSlug;
    if (typeof window.CURRENT_SLUG === 'string') return window.CURRENT_SLUG;
    return null;
  }

  /** Cible d'un libellé pris comme un tout, ou null (libellé atomique). */
  function resolveLabel(txt) {
    var hits = resolveSurfaces(txt);
    if (!hits.length) return null;
    var s = String(txt == null ? '' : txt).replace(/\u00a0/g, ' ').trim();
    for (var i = 0; i < hits.length; i++) {
      // Couvre tout le libellé (aux espaces/ponctuation légère près) ?
      if (hits[i].raw.trim().length >= s.replace(/^[(\[«"'\s]+|[)\]»"':;,.!?\s]+$/g, '').length) {
        return hits[i];
      }
    }
    return hits[0];
  }

  /* Marque un élément SVG textuel comme terme cliquable.
     On ne touche ni x/y ni text-anchor : le rendu ne bouge pas d'un pixel.
     Le soulignement discret vient du CSS (.alx-svg-term), pas d'un attribut. */
  function markElement(el, rec) {
    if (!el || el.getAttribute('data-alx-term')) return false;
    // Le terme de la fiche courante reste inerte (pas d'auto-référence).
    if (rec.slug && rec.slug === currentSlug()) return false;
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
      if (recT && markElement(t, recT)) { n++; continue; }
      /* Rien au niveau du libellé entier : tenter le libellé composite
         (un terme noyé dans une phrase d'étiquette). */
      n += splitCompositeText(t);
    }
    svg.setAttribute('data-alx-svg-done', '1');
    return n;
  }

  /* Libellé COMPOSITE (« rejointe vent arrière », « remise · montée ») : le
     terme n'est qu'une partie du <text>. On ne peut pas y poser un <span>
     (interdit en SVG), MAIS on peut découper le <text> en <tspan> : un <tspan>
     sans x/y hérite du flux de son parent, donc le rendu est identique au
     pixel tant qu'on ne réordonne rien. C'est ce qui débloque les schémas dont
     les étiquettes sont des phrases (cas « remise des gaz »).
     Prérequis : le <text> ne contient QUE du texte (aucun tspan positionné),
     sinon on s'abstient plutôt que de risquer un déplacement. */
  function splitCompositeText(t) {
    if (t.querySelector('tspan')) return 0;
    var s = t.textContent;
    if (!s || !s.trim()) return 0;
    var hits = resolveSurfaces(s);
    if (!hits.length) return 0;

    // Garder des surfaces disjointes, les plus longues d'abord (regex déjà triée).
    hits.sort(function (a, b) { return a.index - b.index || b.end - a.end; });
    var keep = [], last = -1, cur = currentSlug();
    for (var i = 0; i < hits.length; i++) {
      var h = hits[i];
      if (h.index < last) continue;             // chevauchement
      if (!h.slug || h.slug === cur) continue;  // inerte / auto-référence
      keep.push(h); last = h.end;
    }
    if (!keep.length) return 0;
    // Surface unique couvrant tout le libellé : markElement suffit, pas de découpe.
    if (keep.length === 1 && keep[0].raw.trim().length === s.trim().length) return 0;

    var frag = document.createDocumentFragment();
    var pos = 0, n = 0;
    function plain(txt) {
      if (!txt) return;
      var sp = document.createElementNS(SVG_NS, 'tspan');
      sp.textContent = txt;
      frag.appendChild(sp);
    }
    for (var k = 0; k < keep.length; k++) {
      var h2 = keep[k];
      plain(s.slice(pos, h2.index));
      var sp2 = document.createElementNS(SVG_NS, 'tspan');
      sp2.textContent = s.slice(h2.index, h2.end);
      frag.appendChild(sp2);
      if (markElement(sp2, h2)) n++;
      pos = h2.end;
    }
    plain(s.slice(pos));
    if (!n) return 0;
    while (t.firstChild) t.removeChild(t.firstChild);
    t.appendChild(frag);
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
