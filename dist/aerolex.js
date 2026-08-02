/*!
 * AeroLex Runtime v1.2.0
 * Surlignage des termes aéronautiques (vanilla JS, zéro dépendance)
 *
 * Usage :
 *   <link rel="stylesheet" href=".../aerolex.css">
 *   <script src=".../aerolex.js" defer data-index=".../aerolex-index.json"></script>
 *
 * Config optionnelle (window.AeroLexConfig) :
 *   { indexUrl: '...', container: 'body', onDone: fn }
 *
 * Approche DOM : TreeWalker sur nœuds texte (nodeType 3), deux passes.
 * Passe 1 (METAR) : div.metar → tokenise chaque nœud texte, remplace par
 *   DocumentFragment (texte brut + <span class="glos glos-metar">).
 * Passe 2 (Glossaire) : TreeWalker global, collecte d'abord la liste complète
 *   des nœuds texte candidats (sans mutation), puis remplace chaque nœud par
 *   un DocumentFragment sans jamais toucher aux éléments parents.
 * Garantie : aucun event listener détruit, aucune référence DOM invalidée,
 *   compatible widget distribué sur sites tiers interactifs.
 */
(function () {
  'use strict';

  // ══════════════════════════════════════════════════════════════════════════
  // METAR — classifieur de tokens (port de data_metar_codes.py:classify_token)
  // ══════════════════════════════════════════════════════════════════════════
  var METAR_EXACT = {
    'METAR':'METAR','SPECI':'SPECI','TAF':'TAF',
    'CAVOK':'CAVOK','NOSIG':'NOSIG','BECMG':'BECMG',
    'TEMPO':'TEMPO','PROB30':'PROB30','PROB40':'PROB40',
    'RMK':'RMK','FOEHN':'FOEHN','FOHN':'FOHN',
    'AUTO':'AUTO','COR':'COR','NSC':'NSC',
    'NCD':'NCD','VRB':'VRB','9999':'9999',
  };
  var RE_H  = /^\d{6}Z$/;
  var RE_FT = /^\d{4}\/\d{4}$/;
  var RE_V  = /^(?:VRB|\d{3})\d{2,3}(?:G\d{2,3})?(?:KT|MPS)$/;
  var RE_SE = /^\d{3}V\d{3}$/;
  var RE_NU = /^(FEW|SCT|BKN|OVC|VV)(\d{3}|\/\/\/)?(CB|TCU)?$/;
  var RE_T  = /^M?\d{2}\/M?\d{2}$/;
  var RE_Q  = /^Q\d{3,4}$/;
  var RE_A  = /^A\d{4}$/;
  var RE_VI = /^\d{4}$/;
  var RE_PR = /^PROB\d{2}$/;
  var RE_FM = /^FM\d{4,6}$/;
  var RE_OA = /^[A-Z]{4}$/;
  var OACI1 = 'ABCDEFGKLIMNOPRSVY';

  function classifyMetar(tok) {
    if (!tok || /^\s*$/.test(tok)) return null;
    if (METAR_EXACT[tok]) return METAR_EXACT[tok];
    if (RE_H.test(tok))  return 'groupe-horaire';
    if (RE_FT.test(tok)) return 'fenetre-taf';
    if (RE_V.test(tok))  return 'groupe-vent';
    if (RE_SE.test(tok)) return 'secteur-variable';
    var mn = RE_NU.exec(tok); if (mn) return mn[1];
    if (RE_T.test(tok))  return 'groupe-temp';
    if (RE_Q.test(tok) || RE_A.test(tok)) return 'groupe-qnh';
    if (RE_PR.test(tok)) return tok.endsWith('30') ? 'PROB30' : 'PROB40';
    if (RE_FM.test(tok)) return 'FM';
    if (RE_VI.test(tok)) return 'visibilite-metar';
    if (RE_OA.test(tok) && !METAR_EXACT[tok] && OACI1.indexOf(tok[0]) >= 0)
      return 'station-oaci';
    return null;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // CASSE — homographes français
  // ══════════════════════════════════════════════════════════════════════════
  var HOMOGRAPHES_FR = new Set([
    'a','ai','aie','ait','as','au','aux','ay','bien','bon',
    'ca','car','cas','ce','ces','cet','ceux','chez','ci',
    'dans','de','des','dit','do','doit','don','donc','dont','du',
    'elle','en','es','est','et','eu','eux','fa','fait','fit','fois','ha','hier',
    'ici','il','ils','je','la','le','les','leur','lors','lu','lui',
    'ma','mais','mes','met','mets','mien','moi','moins','mon',
    'ne','ni','nm','non','nos','nous','nu','nul',
    'on','ont','or','ou','ou','oui',
    'par','pas','peu','plus','pour','pu','puis',
    'que','qui','quoi','re','rien',
    'sa','sait','sans','sauf','se','ses','seul','si','sien','soi',
    'son','sont','sou','sous','su','suis','sur',
    'ta','tan','tas','te','tel','tes','toi','ton','tous','tout','trop','tu',
    'un','une','va','vais','vas','vers','veut','vis','vit','vos','vous','vs','vu','vue',
    'y',
  ]);

  var MOTS_OUTILS = new Set([
    'a','au','aux','d','de','des','du','en','l','la','le','les',
    'par','pour','sans','sous','sur','un','une','et','ou','ni','que','qui',
    'vers','chez','dans','avec',
  ]);

  function stripAccents(s) { return s.normalize('NFKD').replace(/[\u0300-\u036f]/g,''); }

  function nbMots(s) {
    var parts = s.split(/[^\w\u00c0-\u024f]+/);
    var n = 0; for (var i=0;i<parts.length;i++) if(parts[i]) n++;
    return n;
  }

  function needsExactCase(surface) {
    if (nbMots(surface) !== 1) return false;
    return /[A-Z]/.test(surface) && HOMOGRAPHES_FR.has(stripAccents(surface.toLowerCase()));
  }

  // ══════════════════════════════════════════════════════════════════════════
  // PLURIELS AUTOMATIQUES — port de _pluriels_auto
  // ══════════════════════════════════════════════════════════════════════════
  function pluriels(mot) {
    if (!mot || /[A-Z]/.test(mot) || mot.indexOf("'")>=0) return [];
    if (mot.indexOf(' ')>=0) {
      var parts = mot.split(' ');
      var tete = parts[0], reste = parts.slice(1).join(' ');
      if (MOTS_OUTILS.has(stripAccents(tete.toLowerCase()))) return [];
      return pluriels(tete).map(function(p){return p+' '+reste;});
    }
    if (/[sxz]$/.test(mot)) return [];
    if (/al$/.test(mot)) return [mot.slice(0,-2)+'aux'];
    if (/(au|eau|eu)$/.test(mot)) return [mot+'x'];
    return [mot+'s'];
  }

  // ══════════════════════════════════════════════════════════════════════════
  // TABLE DES SURFACES
  // ══════════════════════════════════════════════════════════════════════════
  function buildMaps(termsData) {
    var ciMap = Object.create(null); // lower_surface -> {canon, s}
    var csMap = Object.create(null); // exact_surface -> {canon, s} (case-sensitive)
    var ctx   = Object.create(null); // canon -> [motifs]
    var hom   = Object.create(null); // canon -> {c, ctx}

    function add(surface, canon, s) {
      surface = (surface||'').trim();
      if (!surface) return;
      var lc = surface.toLowerCase();
      // Skip variantes minuscules ambiguës
      if (nbMots(surface)===1 && HOMOGRAPHES_FR.has(stripAccents(lc)) && !/[A-Z]/.test(surface)) return;
      if (needsExactCase(surface)) {
        if (!csMap[surface]) csMap[surface] = {canon:canon, s:s};
      } else {
        if (!ciMap[lc]) ciMap[lc] = {canon:canon, s:s};
      }
    }

    for (var canon in termsData) {
      var e = termsData[canon];
      var s = e.s||0;
      var formes = [canon];
      if (e.v) for (var j=0;j<e.v.length;j++) formes.push(e.v[j]);
      for (var fi=0;fi<formes.length;fi++) {
        add(formes[fi], canon, s);
        var pls = pluriels(formes[fi]);
        for (var pi=0;pi<pls.length;pi++) add(pls[pi], canon, s);
      }
      if (e.ctx && e.ctx.length) ctx[canon] = e.ctx;
      if (e.hom) hom[canon] = e.hom;
    }
    return {ciMap:ciMap, csMap:csMap, ctx:ctx, hom:hom};
  }

  // ══════════════════════════════════════════════════════════════════════════
  // REGEX DES SURFACES — tri par (nb mots DESC, longueur DESC)
  // Utilise \w (ASCII) pour la vitesse : les accents de frontière sont une
  // limitation connue du prototype (voir rapport).
  // ══════════════════════════════════════════════════════════════════════════
  function escRx(s) { return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }

  function buildRegex(ciMap, csMap) {
    var surfaces = [];
    for (var lc in ciMap) surfaces.push({t: ciMap[lc].canon||lc, lc:lc});
    for (var cs in csMap) surfaces.push({t: cs, lc: cs.toLowerCase(), csSurf: cs});

    surfaces.sort(function(a,b){
      var wA=nbMots(a.t), wB=nbMots(b.t);
      if (wB!==wA) return wB-wA;
      return b.t.length - a.t.length;
    });

    // Deux listes : termes commençant par un alphanum (besoin de lookbehind)
    // et symboles (pas de lookbehind, seulement lookahead)
    var wParts=[], sParts=[];
    for (var i=0;i<surfaces.length;i++) {
      var t = surfaces[i].t;
      if (!t) continue;
      var esc = escRx(t).replace(/(?:\\ |\s)+/g,'\\s+');
      if (/^\w/.test(t)) wParts.push(esc);
      else sParts.push(esc);
    }

    var src = '';
    if (wParts.length) src += '(?<![\\w\\-])(' + wParts.join('|') + ')(?![\\w\\-])';
    if (sParts.length) {
      if (src) src += '|';
      src += '(' + sParts.join('|') + ')(?![\\w\\-])';
    }
    if (!src) return null;
    return new RegExp(src, 'gi');
  }

  function matchedGroup(m) {
    for (var i=1;i<m.length;i++) if (m[i]!==undefined) return m[i];
    return null;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // CONTEXTE (contexte_requis / homonyme)
  // ══════════════════════════════════════════════════════════════════════════
  var FENETRE = 70;

  function contexteOk(text, start, end, motifs) {
    var avant = text.slice(Math.max(0,start-FENETRE), start).toLowerCase();
    var apres = text.slice(end, end+FENETRE).toLowerCase();
    var f = (avant+' '+apres).replace(/\s+/g,' ');
    for (var i=0;i<motifs.length;i++) {
      var m = motifs[i].toLowerCase().replace(/\s+/g,' ').trim();
      if (m && f.indexOf(m)>=0) return true;
    }
    return false;
  }

  // ══════════════════════════════════════════════════════════════════════════
  // BANDEAU
  // ══════════════════════════════════════════════════════════════════════════
  function updateBanner(nTotal, nVide, nMetar, ms) {
    var el = document.getElementById('aerolex-banner');
    if (!el) return;
    el.textContent = 'AeroLex Runtime JS — '+nTotal+' termes posés ('+nVide+' à rédiger, '+nMetar+' METAR) — '+ms.toFixed(1)+' ms';
  }

  // ══════════════════════════════════════════════════════════════════════════
  // FILTRE TREEWALKER — éléments à ne jamais traverser
  // ══════════════════════════════════════════════════════════════════════════
  // Tags dont on rejette tout le sous-arbre texte :
  var SKIP_TAGS_TW = new Set([
    'SCRIPT','STYLE','CODE','PRE','TEXTAREA','INPUT','SELECT','OPTION',
    'NOSCRIPT','SVG','CANVAS','IFRAME','A','SUMMARY','BUTTON',
  ]);

  // Classes d'éléments racine à exclure complètement (mêmes zones que PARK_RE) :
  var SKIP_CLS_TW = ['glos','barre-score','qcm-options','aerolex-skip'];

  // Retourne un NodeFilter pour le TreeWalker.
  // Vérifie les ancêtres du nœud texte jusqu'au container (stopEl) :
  //   — tag interdit (SKIP_TAGS_TW)
  //   — contenteditable
  //   — classe glos/glos-metar/glos-vide (idempotence), aerolex-skip,
  //     barre-score, qcm-options
  //   — attribut data-aerolex-skip
  function makeGlossaryFilter(stopEl) {
    return {
      acceptNode: function (node) {
        var el = node.parentNode;
        while (el && el !== stopEl) {
          if (el.nodeType !== 1) { el = el.parentNode; continue; }
          // Tag interdit ?
          if (SKIP_TAGS_TW.has(el.tagName)) return NodeFilter.FILTER_REJECT;
          // contenteditable ?
          if (el.contentEditable === 'true') return NodeFilter.FILTER_REJECT;
          // Classe protégée ?
          var cls = typeof el.className === 'string'
            ? el.className
            : (el.className && el.className.baseVal) || '';
          for (var ci = 0; ci < SKIP_CLS_TW.length; ci++) {
            if (cls.indexOf(SKIP_CLS_TW[ci]) >= 0) return NodeFilter.FILTER_REJECT;
          }
          // Attribut data-aerolex-skip ?
          if (el.hasAttribute && el.hasAttribute('data-aerolex-skip')) return NodeFilter.FILTER_REJECT;
          el = el.parentNode;
        }
        return NodeFilter.FILTER_ACCEPT;
      }
    };
  }

  // ══════════════════════════════════════════════════════════════════════════
  // COUCHE METAR (Passe 1) — via DOM, sans innerHTML
  // Trouve les div.metar, parcourt leurs nœuds texte, remplace chaque nœud
  // par un DocumentFragment (texte brut + spans glos-metar).
  // ══════════════════════════════════════════════════════════════════════════
  var RE_TOK = /\S+|\s+/g;

  function applyMetarToDOM(container, occMap) {
    var metarDivs = container.querySelectorAll('div.metar');
    for (var d = 0; d < metarDivs.length; d++) {
      var div = metarDivs[d];
      // Idempotence : déjà wrappé ?
      if (div.querySelector('.glos-metar')) continue;

      // Collecte des nœuds texte (ne pas muter pendant l'itération)
      var tw = document.createTreeWalker(div, NodeFilter.SHOW_TEXT, null);
      var textNodes = [];
      var tn;
      while ((tn = tw.nextNode()) !== null) textNodes.push(tn);

      // Application des remplacements
      for (var i = 0; i < textNodes.length; i++) {
        var node = textNodes[i];
        if (!node.parentNode) continue; // nœud détaché
        var text = node.nodeValue;
        if (!text || !text.trim()) continue;

        // Tokeniser : conserver les espaces
        RE_TOK.lastIndex = 0;
        var toks = text.match(RE_TOK) || [];
        var hasMetar = false;
        for (var k = 0; k < toks.length; k++) {
          if (!/^\s+$/.test(toks[k]) && classifyMetar(toks[k])) { hasMetar = true; break; }
        }
        if (!hasMetar) continue;

        var frag = document.createDocumentFragment();
        for (var j = 0; j < toks.length; j++) {
          var tok = toks[j];
          if (/^\s+$/.test(tok)) {
            frag.appendChild(document.createTextNode(tok));
            continue;
          }
          var key = classifyMetar(tok);
          if (!key) {
            frag.appendChild(document.createTextNode(tok));
            continue;
          }
          var prev = occMap[key] || 0;
          occMap[key] = prev + 1;
          var occ = prev === 0 ? '1' : 'n';
          var span = document.createElement('span');
          span.className = 'glos glos-metar';
          span.dataset.occ = occ;
          span.dataset.term = key;
          span.textContent = tok;
          frag.appendChild(span);
        }
        node.parentNode.replaceChild(frag, node);
      }
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // APPLICATION GLOSSAIRE SUR UN NŒUD TEXTE — retourne le nb de remplacements
  // ══════════════════════════════════════════════════════════════════════════
  function applyGlossaryToTextNode(node, rx, ciMap, csMap, ctxMap, homMap, occMap) {
    var text = node.nodeValue;
    if (!text || !text.trim()) return;

    // Collecter les matches dans ce nœud texte
    rx.lastIndex = 0;
    var matches = [];
    var m;
    while ((m = rx.exec(text)) !== null) {
      var raw = matchedGroup(m);
      if (!raw) continue;
      var norm = raw.replace(/\s+/g, ' ');
      var lu = csMap[norm] || ciMap[norm.toLowerCase()];
      if (!lu) continue;
      var canon = lu.canon, s = lu.s;
      // Contexte requis ?
      if (ctxMap[canon] && !contexteOk(text, m.index, m.index + raw.length, ctxMap[canon])) continue;
      // Homonyme ?
      if (homMap[canon]) {
        var h = homMap[canon];
        if (contexteOk(text, m.index, m.index + raw.length, h.ctx)) {
          canon = h.c;
          s = (ciMap[canon] || csMap[canon] || {s: s}).s;
        }
      }
      matches.push({index: m.index, raw: raw, canon: canon, s: s});
    }

    if (!matches.length) return;

    // Construire le DocumentFragment de remplacement
    var frag = document.createDocumentFragment();
    var lastIdx = 0;
    for (var i = 0; i < matches.length; i++) {
      var match = matches[i];
      if (match.index > lastIdx) {
        frag.appendChild(document.createTextNode(text.slice(lastIdx, match.index)));
      }
      var prev = occMap[match.canon] || 0;
      occMap[match.canon] = prev + 1;
      var occ = prev === 0 ? '1' : 'n';
      var cls = 'glos' + (match.s === 0 ? ' glos-vide' : '');
      var span = document.createElement('span');
      span.className = cls;
      span.dataset.occ = occ;
      span.dataset.term = match.canon;
      if (match.s === 0) span.dataset.todo = '1';
      span.textContent = match.raw;
      frag.appendChild(span);
      lastIdx = match.index + match.raw.length;
    }
    if (lastIdx < text.length) {
      frag.appendChild(document.createTextNode(text.slice(lastIdx)));
    }

    // Remplacement chirurgical : UNIQUEMENT ce nœud texte, jamais le parent
    node.parentNode.replaceChild(frag, node);
  }

  // ══════════════════════════════════════════════════════════════════════════
  // COUCHE GLOSSAIRE (Passe 2) — TreeWalker global
  // 1. Collecte tous les nœuds texte candidats (sans mutation).
  // 2. Applique les remplacements (peut modifier le DOM, mais les refs
  //    collectées à l'étape 1 ne bougent pas).
  // ══════════════════════════════════════════════════════════════════════════
  function applyGlossaryToDOM(container, rx, ciMap, csMap, ctxMap, homMap, occMap) {
    var filter = makeGlossaryFilter(container);
    var tw = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, filter);

    // Passe 1 : collecte (zéro mutation)
    var textNodes = [];
    var tn;
    while ((tn = tw.nextNode()) !== null) textNodes.push(tn);

    // Passe 2 : application (peut muter le DOM)
    for (var i = 0; i < textNodes.length; i++) {
      if (textNodes[i].parentNode) { // nœud encore attaché ?
        applyGlossaryToTextNode(textNodes[i], rx, ciMap, csMap, ctxMap, homMap, occMap);
      }
    }
  }

  // ══════════════════════════════════════════════════════════════════════════
  // POINT D'ENTRÉE
  // ══════════════════════════════════════════════════════════════════════════
  function init() {
    var t0 = performance.now();

    var cfg       = window.AeroLexConfig || {};
    var scriptEl  = document.currentScript || document.querySelector('script[src*="aerolex"]');
    var indexUrl  = cfg.indexUrl ||
                    (scriptEl && scriptEl.dataset && scriptEl.dataset.index) ||
                    (scriptEl ? scriptEl.src.replace(/aerolex\.js([?#].*)?$/, 'aerolex-index.json') : null);

    if (!indexUrl) { console.warn('[AeroLex] index URL introuvable.'); return; }

    var container = cfg.container
      ? (typeof cfg.container==='string' ? document.querySelector(cfg.container) : cfg.container)
      : document.body;

    if (!container) { console.warn('[AeroLex] conteneur non trouvé.'); return; }
    if (container.dataset && container.dataset.aerolexDone==='1') return; // idempotence

    fetch(indexUrl)
      .then(function(r){ return r.json(); })
      .then(function(data){
        var termsData = data.terms || data;
        var maps = buildMaps(termsData);
        var rx   = buildRegex(maps.ciMap, maps.csMap);
        if (!rx) { console.warn('[AeroLex] aucun terme.'); return; }

        var occMap = Object.create(null);

        // Idempotence : si des spans glos existent déjà, ne pas re-traiter
        if (container.querySelector('.glos')) {
          if (container.dataset) container.dataset.aerolexDone = '1';
          return;
        }

        // ── Stratégie : TreeWalker sur nœuds texte ──────────────────────
        // Passe 1 METAR (div.metar) → passe 2 glossaire (tout le reste).
        // Aucun innerHTML réassigné : zéro destruction d'event listeners,
        // zéro réinitialisation d'état de formulaire/widget.

        // 1. METAR (doit passer en premier : ses spans seront exclus par le
        //    filtre TreeWalker de la passe glossaire via la classe "glos")
        applyMetarToDOM(container, occMap);
        var nMetar = container.querySelectorAll('.glos-metar').length;

        // 2. Glossaire
        applyGlossaryToDOM(container, rx, maps.ciMap, maps.csMap, maps.ctx, maps.hom, occMap);

        // 3. Comptages
        var nTotal = container.querySelectorAll('.glos').length;
        var nVide  = container.querySelectorAll('.glos-vide').length;
        var ms = performance.now() - t0;

        if (container.dataset) container.dataset.aerolexDone = '1';

        updateBanner(nTotal, nVide, nMetar, ms);
        console.info('[AeroLex] '+nTotal+' termes ('+nVide+' vide, '+nMetar+' METAR) en '+ms.toFixed(1)+' ms');

        if (typeof cfg.onDone==='function') cfg.onDone({nTotal:nTotal, nVide:nVide, nMetar:nMetar, ms:ms});
      })
      .catch(function(err){ console.error('[AeroLex] index load error:', err); });
  }

  // ══════════════════════════════════════════════════════════════════════════
  // EXPOSITION + AUTO-INIT
  // ══════════════════════════════════════════════════════════════════════════
  window.AeroLex = { init: init, version: '1.2.0' };

  if (document.readyState==='loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
