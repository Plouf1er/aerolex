/*!
 * AeroLex Runtime v1.3.0
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

  /* NFKD ne décompose PAS les ligatures œ/æ (ce sont des lettres, pas des
     lettres accentuées) : `nœud` et `noeud` ne se réduisaient donc pas à la
     même clé. On replie explicitement avant NFKD pour que le `skip` de
     highlight() et la table des homographes traitent les deux graphies
     comme une seule. */
  function stripAccents(s) {
    return String(s)
      .replace(/\u0153/g,'oe').replace(/\u0152/g,'OE')
      .replace(/\u00e6/g,'ae').replace(/\u00c6/g,'AE')
      .normalize('NFKD').replace(/[\u0300-\u036f]/g,'');
  }

  function nbMots(s) {
    var parts = s.split(/[^\w\u00c0-\u024f]+/);
    var n = 0; for (var i=0;i<parts.length;i++) if(parts[i]) n++;
    return n;
  }

  function needsExactCase(surface) {
    if (nbMots(surface) !== 1) return false;
    return /[A-Z]/.test(surface) && HOMOGRAPHES_FR.has(stripAccents(surface.toLowerCase()));
  }

  /* ── SYMBOLES D'UNITÉ ULTRA-COURTS ──────────────────────────────────
     Corollaire du correctif de buildRegex : 1477 surfaces jusque-là inertes
     deviennent cherchables, dont 13 de 1 à 2 caractères (`l`, `m`, `s`, `cc`,
     `co`, `cv`, `cm`, `fl`, `lb`…). En français courant ces formes sont des
     mots-outils ou des élisions : le lookbehind `(?<![\w\-])` ne protège PAS
     `l'aéronef` (l'apostrophe n'est pas un caractère de mot), donc `l` y
     matcherait → lien « litre » sur une élision. Mesuré sur la définition de
     `vitesse` : 2 faux positifs `l -> litre`.
     Un symbole d'unité n'est signifiant qu'accolé à une valeur (« 50 l ») ou
     écrit en capitales (« FL 95 »). On exige donc soit la casse exacte, soit un
     nombre à gauche — dans le moteur PARTAGÉ, pas au cas par cas. */
  function isSymboleCourt(surface) {
    return surface.length <= 2 && !/\s/.test(surface) && !/^[0-9]+$/.test(surface);
  }

  /* ── SIGLES DE 2 LETTRES (v1.3.0, diagnostic 2026-11-04 S2) ──────────
     Le commentaire ci-dessus annonçait « casse exacte » mais le code ne
     l'implémentait pas : Vy, Vx, FL, CG, GS… n'étaient presque jamais liés.
     Règle : un symbole court est accepté si
       1. il est dans csMap (homographe français déclaré en casse exacte), ou
       2. un nombre le précède (« 50 l », « 10 m »), ou
       3. il fait exactement 2 caractères ET
          a. il est tout en MAJUSCULES (CG, FL, AD, TS, °C), ou
          b. il est identique à une forme DÉCLARÉE contenant une majuscule
             (Vy, Vx, Cz, Cm… : maps.exact).
     Toujours refusés : minuscules (« cl », « vy »), 1 lettre sans nombre.
     Garde-fou : un sigle suivi d'un exposant (« GS² ») n'est pas un sigle. */
  function symboleCourtOk(norm, text, index, maps) {
    /* Élision (conformité 2026-11-04) : « l'humidité », « s'applique », « L'altimètre » — un symbole court suivi d'une
       apostrophe est un mot-outil élidé, jamais une unité (« Td = 5, l'humidité » ne doit pas lier « l » → litre). */
    if (/['’]/.test(text.charAt(index + norm.length))) return false;
    if (maps.csMap[norm]) return true;
    if (precedeParNombre(text, index)) return true;
    if (norm.length !== 2) return false;
    var maj = norm === norm.toUpperCase() && norm !== norm.toLowerCase();
    if (!maj && !maps.exact[norm]) return false;
    if (/[\u00b2\u00b3\u2070-\u209f]/.test(text.charAt(index + norm.length))) return false;
    return true;
  }

  /* Vrai si le symbole court est précédé d'une valeur numérique (« 50 l »,
     « 10 m », « 2,5 cm »). Sert de contexte minimal pour les formes minuscules. */
  function precedeParNombre(texte, index) {
    var avant = texte.slice(Math.max(0, index - 12), index);
    return /[0-9][0-9\s,.\u00a0]*$/.test(avant);
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
      var res = pluriels(tete).map(function(p){return p+' '+reste;});
      /* v1.3.0 (S3) : expression nom + adjectif SANS mot-outil (« mille
         nautique », « calage altimétrique ») → TOUS les mots pleins s'accordent
         (« milles nautiques », « calages altimétriques »). Avec un mot-outil
         (« point de rosée »), seule la tête varie : on ne génère pas
         « points de rosées ». */
      var sansOutil = parts.every(function(w){ return !MOTS_OUTILS.has(stripAccents(w.toLowerCase())); });
      if (sansOutil) {
        var tous = parts.map(function(w){
          if (w.length <= 2 || /[0-9]/.test(w)) return w;
          var pw = pluriels(w);
          return pw.length ? pw[0] : w;
        }).join(' ');
        if (tous !== mot && res.indexOf(tous) < 0) res.push(tous);
      }
      return res;
    }
    if (/[sxz]$/.test(mot)) return [];
    if (/al$/.test(mot)) return [mot.slice(0,-2)+'aux'];
    if (/(au|eau|eu)$/.test(mot)) return [mot+'x'];
    return [mot+'s'];
  }

  /* Singuliers automatiques (v1.3.0, S3) : « volets » → « volet », « flaps »
     → « flap », « amers » → « amer », « red lines » → « red line ».
     Condition : tous les mots pleins (hors mots-outils et mots de 3 lettres
     ou moins) finissent en « s » (hors ss/us/is). Rien si majuscule ou
     apostrophe (comme pluriels()). Les mots invariants et les exceptions
     (« indices » ne doit pas devenir « indice » : index ≠ indice) sont exclus. */
  var INVARIANTS_S = new Set([
    'bras','temps','travers','poids','cours','secours','acces','mois','corps',
    'pays','repas','succes','progres','concours','discours','parcours','recours',
    'abus','jus','dos','gaz','tous','plus','moins','sans','vers','fois','lors',
    'puis','alors','hors','dessus','dessous','avis','pardessus','velours'
  ]);
  var SINGULIER_EXCLUS = new Set(['indices']);
  function singuliers(mot) {
    if (!mot || /[A-Z]/.test(mot) || mot.indexOf("'")>=0) return [];
    var base = stripAccents(mot.toLowerCase());
    if (SINGULIER_EXCLUS.has(base)) return [];
    var parts = mot.split(' ');
    var pleins = 0;
    for (var i=0;i<parts.length;i++) {
      var w = parts[i], wl = stripAccents(w.toLowerCase());
      if (MOTS_OUTILS.has(wl) || w.length <= 3) continue;
      if (!/s$/.test(wl) || /(ss|us|is)$/.test(wl) || /[0-9]/.test(wl) || INVARIANTS_S.has(wl)) return [];
      pleins++;
    }
    if (!pleins) return [];
    return [parts.map(function(w){
      var wl = stripAccents(w.toLowerCase());
      return (MOTS_OUTILS.has(wl) || w.length <= 3) ? w : w.slice(0,-1);
    }).join(' ')];
  }

  // ══════════════════════════════════════════════════════════════════════════
  // TABLE DES SURFACES
  // ══════════════════════════════════════════════════════════════════════════
  function buildMaps(termsData) {
    var ciMap = Object.create(null); // lower_surface -> {canon, s, auto?} (casse libre)
    var csMap = Object.create(null); // exact_surface -> {canon, s, auto?} (casse exacte)
    var ctx   = Object.create(null); // canon -> [motifs]   (contexte_requis)
    var hom   = Object.create(null); // canon -> {c, ctx}   (homonyme : aiguillage)
    var cxs   = Object.create(null); // canon -> [motifs]   (contexte exigé pour le singulier AUTOMATIQUE seulement)
    var cxg   = Object.create(null); // canon -> [motifs]   (contexte exigé pour les SIGLES de 2 lettres seulement : « CL = 7 » n'est pas Cl)
    var exact = Object.create(null); // formes courtes déclarées avec majuscule (Vy, Cz…)

    function add(surface, canon, s, auto, forceCs) {
      surface = (surface||'').trim();
      if (!surface) return;
      var lc = surface.toLowerCase();
      // Skip variantes minuscules ambiguës
      if (nbMots(surface)===1 && HOMOGRAPHES_FR.has(stripAccents(lc)) && !/[A-Z]/.test(surface)) return;
      var ent = {canon:canon, s:s};
      if (auto) ent.auto = auto;
      if (forceCs || needsExactCase(surface)) {   // forceCs : champ cs de la fiche (casse_sensible : TORA, TODA…)
        if (!csMap[surface]) csMap[surface] = ent;
      } else {
        if (!ciMap[lc]) ciMap[lc] = ent;
      }
    }

    var canons = Object.keys(termsData);
    function formesDe(canon) {
      var e = termsData[canon];
      var formes = [canon];
      if (e.v) for (var j=0;j<e.v.length;j++) formes.push(e.v[j]);
      return formes;
    }

    /* Phase 1 : formes DÉCLARÉES (clé + variantes) de toutes les fiches.
       Phase 2 : formes AUTOMATIQUES (pluriels, singuliers). Une surface
       déclarée l'emporte donc toujours sur une surface générée, quel que
       soit l'ordre des fiches (v1.3.0). */
    for (var ci=0; ci<canons.length; ci++) {
      var canon = canons[ci], e = termsData[canon], s = e.s||0;
      var fm = formesDe(canon);
      for (var fi=0; fi<fm.length; fi++) {
        add(fm[fi], canon, s, null, !!e.cs);
        if (fm[fi].length <= 2 && !/\s/.test(fm[fi]) && /[A-Z]/.test(fm[fi])) exact[fm[fi]] = true;
      }
      if (e.ctx && e.ctx.length) ctx[canon] = e.ctx;
      if (e.hom) hom[canon] = e.hom;
      if (e.cxs && e.cxs.length) cxs[canon] = e.cxs;
      if (e.cxg && e.cxg.length) cxg[canon] = e.cxg;
    }
    for (var cj=0; cj<canons.length; cj++) {
      var can2 = canons[cj], s2 = termsData[can2].s||0;
      var fm2 = formesDe(can2);
      for (var fj=0; fj<fm2.length; fj++) {
        var pls = pluriels(fm2[fj]);
        for (var pi=0;pi<pls.length;pi++) add(pls[pi], can2, s2, 'pl');
        var sgs = singuliers(fm2[fj]);
        for (var si=0;si<sgs.length;si++) add(sgs[si], can2, s2, 'sg');
      }
    }
    return {ciMap:ciMap, csMap:csMap, ctx:ctx, hom:hom, cxs:cxs, cxg:cxg, exact:exact, terms:termsData};
  }

  // ══════════════════════════════════════════════════════════════════════════
  // REGEX DES SURFACES — tri par (nb mots DESC, longueur DESC)
  // Utilise \w (ASCII) pour la vitesse : les accents de frontière sont une
  // limitation connue du prototype (voir rapport).
  // ══════════════════════════════════════════════════════════════════════════
  function escRx(s) { return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'); }

  /* ── CAUSE RACINE du « nœuds pas surligné » (2026-08-04) ────────────────
     Cette fonction poussait dans la regex `ciMap[lc].canon` — le terme
     CANONIQUE — au lieu de `lc`, la SURFACE effectivement présente dans le
     texte. Conséquence : seules les 1286 formes canoniques entraient dans
     l'alternation, et les 1477 autres surfaces (variantes `v`, pluriels
     automatiques, abréviations) n'étaient JAMAIS cherchées. Le lookup
     csMap/ciMap en aval était donc correct mais inatteignable.
     `nœud/nœuds` (variantes de `kt`) n'était qu'un symptôme visible parmi
     1477 : ce n'était pas un problème de ligature `œ`. Le tri par nb mots
     DESC puis longueur DESC assure le longest-match sur les surfaces réelles
     (avant le correctif il portait sur les canoniques — donc faux). */
  function buildRegex(ciMap, csMap) {
    var surfaces = [];
    for (var lc in ciMap) surfaces.push({t: lc, lc: lc});
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
      if (/^[\w\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u024f]/.test(t)) wParts.push(esc);
      else sParts.push(esc);
    }

    var src = '';
    /* v1.3.0 (S1) : frontières de mot UNICODE. Avant, [\\w] ASCII faisait d'une
       lettre accentuée une frontière (« carte » reconnu dans « écarte »,
       « pos » dans « posé »). Le trait d'union ne bloque à gauche que s'il
       suit une lettre : « -SHRA » (METAR) est reconnu, « anti-carte » non. */
    if (wParts.length) src += '(?<![\\w\\u00c0-\\u00d6\\u00d8-\\u00f6\\u00f8-\\u024f])(?<![\\w\\u00c0-\\u00d6\\u00d8-\\u00f6\\u00f8-\\u024f]-)(' + wParts.join('|') + ')(?![\\w\\-\\u00c0-\\u00d6\\u00d8-\\u00f6\\u00f8-\\u024f])';
    if (sParts.length) {
      if (src) src += '|';
      src += '(' + sParts.join('|') + ')(?![\\w\\-\\u00c0-\\u00d6\\u00d8-\\u00f6\\u00f8-\\u024f])';
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

  /* ── CŒUR DE LA DÉCISION (v1.3.0) ────────────────────────────────────
     UNE seule fonction décide quelles occurrences d'un texte sont des termes :
     utilisée par le surlignage DOM, par resolveSurface (SVG) et par les tests
     (window.AeroLexCore). Retourne [{index, raw, canon, s}] dans l'ordre. */
  function findMatches(text, rx, maps) {
    var out = [];
    rx.lastIndex = 0;
    var m;
    while ((m = rx.exec(text)) !== null) {
      var raw = matchedGroup(m);
      if (!raw) { if (rx.lastIndex === m.index) rx.lastIndex++; continue; }
      var norm = raw.replace(/\s+/g, ' ');
      var lu = maps.csMap[norm] || maps.ciMap[norm.toLowerCase()];
      if (!lu) continue;
      var canon = lu.canon, s = lu.s;
      var end = m.index + raw.length;
      /* Sigle / symbole court : voir symboleCourtOk (majuscules exactes,
         forme déclarée exacte ou nombre à gauche). */
      if (isSymboleCourt(norm) && !symboleCourtOk(norm, text, m.index, maps)) continue;
      /* Sigle de 2 lettres d'une fiche qui exige un contexte pour ses SIGLES
         (champ contexte_sigle) : « CL = 7 » (code OMM) ≠ Cl (coefficient de
         portance) ; « SS PLUS30 » (horaire) ≠ SS (tempête de sable). Les
         formes longues de la même fiche ne sont pas concernées. */
      if (isSymboleCourt(norm) && maps.cxg[canon] && !contexteOk(text, m.index, m.index + raw.length, maps.cxg[canon])) continue;
      // Contexte requis ?
      if (maps.ctx[canon] && !contexteOk(text, m.index, end, maps.ctx[canon])) continue;
      /* Singulier généré automatiquement : contexte exigé si la fiche le
         déclare (« volet » : sens aéro seulement près de flaps, sortis…). */
      if (lu.auto === 'sg' && maps.cxs[canon] && !contexteOk(text, m.index, end, maps.cxs[canon])) continue;
      // Homonyme : aiguillage vers une autre fiche si le contexte le demande
      if (maps.hom[canon]) {
        var h = maps.hom[canon];
        if (contexteOk(text, m.index, end, h.ctx)) {
          canon = h.c;
          s = (maps.terms[canon] || {s: s}).s || 0;
        }
      }
      out.push({index: m.index, raw: raw, canon: canon, s: s});
    }
    return out;
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
    'H1','H2','H3','H4','H5','H6',
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
  function applyGlossaryToTextNode(node, rx, maps, occMap) {
    var text = node.nodeValue;
    if (!text || !text.trim()) return;

    // Collecter les matches dans ce nœud texte (cœur partagé : findMatches)
    var matches = findMatches(text, rx, maps);

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
  function applyGlossaryToDOM(container, rx, maps, occMap) {
    var filter = makeGlossaryFilter(container);
    var tw = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, filter);

    // Passe 1 : collecte (zéro mutation)
    var textNodes = [];
    var tn;
    while ((tn = tw.nextNode()) !== null) textNodes.push(tn);

    // Passe 2 : application (peut muter le DOM)
    for (var i = 0; i < textNodes.length; i++) {
      if (textNodes[i].parentNode) { // nœud encore attaché ?
        applyGlossaryToTextNode(textNodes[i], rx, maps, occMap);
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

    /* ── CACHE-BUST (2026-08-04) ────────────────────────────────────────────
       Bug corrigé : le repli `scriptEl.src.replace(/aerolex\.js([?#].*)?$/,…)`
       SUPPRIMAIT la query string, donc l'index n'était jamais cache-busté même
       quand le script l'était (?v=xxxx). On récupère désormais le `?v=` du
       script et on le PROPAGE à l'index ET aux fichiers par mot (aero/t/*.json).
       Mode test : `?nocache=1` dans l'URL de la page → version aléatoire à
       chaque chargement. Aléatoire UNIQUEMENT dans ce mode : sinon on tuerait
       le cache de tous les lecteurs. */
    var _scriptSrc = (scriptEl && scriptEl.src) || '';
    var _noCache   = /[?&]nocache=1(&|$)/.test(location.search);
    var _vMatch    = _scriptSrc.match(/[?&]v=([^&#]+)/);
    var _ver       = _noCache
                       ? ('nc' + Date.now().toString(36) + Math.random().toString(36).slice(2, 8))
                       : (cfg.version || (_vMatch ? decodeURIComponent(_vMatch[1]) : ''));

    /* Ajoute/écrase ?v= sur une URL sans casser un fragment existant. */
    function withVer(url) {
      if (!url || !_ver) return url;
      var hash = '';
      var iH = url.indexOf('#');
      if (iH >= 0) { hash = url.slice(iH); url = url.slice(0, iH); }
      url = url.replace(/([?&])v=[^&]*(&|$)/, function (m, p1, p2) { return p2 ? p1 : ''; })
               .replace(/[?&]$/, '');
      return url + (url.indexOf('?') >= 0 ? '&' : '?') + 'v=' + encodeURIComponent(_ver) + hash;
    }

    var indexUrl  = cfg.indexUrl ||
                    (scriptEl && scriptEl.dataset && scriptEl.dataset.index) ||
                    (_scriptSrc ? _scriptSrc.replace(/aerolex\.js([?#].*)?$/, 'aerolex-index.json') : null);

    if (!indexUrl) { console.warn('[AeroLex] index URL introuvable.'); return; }

    indexUrl = withVer(indexUrl);

    /* Base des fichiers par mot — CROSS-ORIGIN, UNE SEULE SOURCE
       (décision Louis, 2026-08-04 02h10).
       Le lexique n'est PLUS dupliqué chez les sites clients : il vit à un seul
       endroit et les hôtes le lisent en cross-origin (CORS en liste fermée
       côté serveur, cf. aerolex/serve_cors.py).
       Ordre de priorité, identique à celui de aero.js pour qu'il n'existe
       jamais deux avis sur l'emplacement du lexique :
         1. AeroLexConfig.termsBase
         2. window.AEROLEX_BASE
         3. <script data-aerolex-base="…">
         4. https://aerolex.prunel.net/aero/t/ */
    var TERMS_BASE_DEFAUT = 'https://aerolex.prunel.net/aero/t/';
    var _baseAttrEl = document.querySelector('script[data-aerolex-base]');
    var termsBase   = cfg.termsBase
                    || (typeof window.AEROLEX_BASE === 'string' && window.AEROLEX_BASE
                          ? window.AEROLEX_BASE : '')
                    || (_baseAttrEl ? (_baseAttrEl.getAttribute('data-aerolex-base') || '') : '')
                    || TERMS_BASE_DEFAUT;
    if (termsBase.charAt(termsBase.length - 1) !== '/') termsBase += '/';

    /* Exposé pour aero.js (consommateur de la popup) : il fetche
       termsBase + <sl> + '.json' + ?v=<ver>, en réutilisant NOTRE version. */
    window.AeroLex.indexUrl  = indexUrl;
    window.AeroLex.termsBase = termsBase;
    window.AeroLex.assetVer  = _ver || '';
    window.AeroLex.termUrl   = function (sl) {
      if (!sl) return null;
      return withVer(termsBase + encodeURIComponent(String(sl)) + '.json');
    };

    var container = cfg.container
      ? (typeof cfg.container==='string' ? document.querySelector(cfg.container) : cfg.container)
      : document.body;

    if (!container) { console.warn('[AeroLex] conteneur non trouvé.'); return; }
    if (container.dataset && container.dataset.aerolexDone==='1') return; // idempotence

    fetch(indexUrl)
      .then(function(r){ return r.json(); })
      .then(function(data){
        if (container.dataset && container.dataset.aerolexDone==='1') return; // 2e appel concurrent
        var termsData = data.terms || data;
        /* Expose l'index de SURLIGNAGE. Depuis le 2026-08-04 il ne contient
           plus les définitions : la popup ne lit ici que le slug (routage) et
           l'état rédigé (couleur), puis fetche dist/aero/t/<slug>.json au clic.
           Le bloc "families" a disparu de l'index — les membres d'une famille
           arrivent dans le fichier du mot, déjà triés et résolus en slugs. */
        window.AeroLex.terms = termsData;
        var maps = buildMaps(termsData);
        var rx   = buildRegex(maps.ciMap, maps.csMap);
        if (!rx) { console.warn('[AeroLex] aucun terme.'); return; }

        /* ── API PUBLIQUE DE RE-SURLIGNAGE (2026-08-04, régression 1) ────────
           La popup de aero.js injecte du texte de définition APRÈS l'init : ce
           texte doit lui aussi devenir cliquable (« navigation de terme en
           terme »). Sans point d'entrée public, aero.js n'avait aucun moyen de
           réutiliser le moteur — il ne pouvait ni reconstruire la regex ni
           accéder aux maps, toutes deux locales à init().
           On expose donc une fonction qui applique la MÊME regex et les MÊMES
           maps à une racine arbitraire. `skip` : terme à NE PAS surligner
           (le terme courant de la popup — un mot ne se renvoie pas à lui-même).
           Aucun état partagé muté : occMap est local à l'appel, donc le
           compteur d'occurrences de la page n'est pas pollué. */
        window.AeroLex.highlight = function (root, opts) {
          if (!root || !root.querySelectorAll) return 0;
          opts = opts || {};
          var occLocal = Object.create(null);
          /* Un terme à exclure : on pré-charge occMap au-delà du plafond ?
             Non — le moteur ne connaît pas de plafond ici. On retire donc
             l'entrée des maps le temps de l'appel, puis on la remet. C'est la
             seule façon de ne pas surligner le terme courant sans toucher au
             coeur du moteur. */
          var retires = [];
          if (opts.skip) {
            var nSkip = stripAccents(String(opts.skip)).toLowerCase();
            for (var kci in maps.ciMap) {
              if (kci === nSkip || stripAccents(kci).toLowerCase() === nSkip) {
                retires.push(['ci', kci, maps.ciMap[kci]]);
              }
            }
            for (var kcs in maps.csMap) {
              if (stripAccents(kcs).toLowerCase() === nSkip) {
                retires.push(['cs', kcs, maps.csMap[kcs]]);
              }
            }
            for (var r = 0; r < retires.length; r++) {
              if (retires[r][0] === 'ci') delete maps.ciMap[retires[r][1]];
              else delete maps.csMap[retires[r][1]];
            }
          }
          try {
            applyGlossaryToDOM(root, rx, maps, occLocal);
          } finally {
            for (var q = 0; q < retires.length; q++) {
              if (retires[q][0] === 'ci') maps.ciMap[retires[q][1]] = retires[q][2];
              else maps.csMap[retires[q][1]] = retires[q][2];
            }
          }
          return root.querySelectorAll('.glos').length;
        };

        /* ── RÉSOLUTION DE SURFACE (2026-08-04, libellés de schéma SVG) ─────
           aerolex-svg.js doit décider si un libellé de SVG désigne un terme.
           Il ne peut PAS utiliser highlight() : dans un <svg>, envelopper une
           sous-chaîne d'un <text> dans un <span> casse le positionnement
           (x/y/text-anchor portés par l'élément) — cf. en-tête aerolex-svg.js.
           Il lui faut donc la DÉCISION sans le remplacement DOM.

           On expose la MÊME regex et les MÊMES maps que le surlignage texte :
           pluriels, variantes `v`, homographes `case_sensitive` (csMap) et
           mots-outils sont donc appliqués à l'identique. Zéro second moteur
           de matching — c'était le risque de duplication à éviter.

           Retourne les surfaces trouvées DANS la chaîne (offsets inclus), la
           plus longue d'abord (la regex est déjà triée nb-mots DESC), ce qui
           permet à l'appelant de traiter aussi bien un libellé atomique
           (« vent arrière ») qu'un libellé composite (« rejointe vent
           arrière ») sans réimplémenter la moindre normalisation. */
        window.AeroLex.resolveSurface = function (texte) {
          var s = String(texte == null ? '' : texte).replace(/\u00a0/g, ' ');
          if (!s.trim()) return [];
          var res = [];
          var found = findMatches(s, rx, maps);
          for (var fi = 0; fi < found.length; fi++) {
            var f = found[fi];
            var ent = termsData[f.canon] || {};
            res.push({
              raw: f.raw,
              index: f.index,
              end: f.index + f.raw.length,
              terme: f.canon,
              slug: ent.sl || null,
              s: f.s
            });
          }
          return res;
        };

        var occMap = Object.create(null);

        // Idempotence : portée par container.dataset.aerolexDone (testé en tête
        // d'init). Les spans .glos posés au BUILD (METAR ou glossaire) ne doivent
        // PAS court-circuiter le passage : le TreeWalker rejette déjà les nœuds
        // situés dans .glos (SKIP_CLS_TW), donc pas de double soulignement, et les
        // termes absents du build (ex. « masse à vide », « datum ») sont complétés.

        // ── Stratégie : TreeWalker sur nœuds texte ──────────────────────
        // Passe 1 METAR (div.metar) → passe 2 glossaire (tout le reste).
        // Aucun innerHTML réassigné : zéro destruction d'event listeners,
        // zéro réinitialisation d'état de formulaire/widget.

        // 1. METAR (doit passer en premier : ses spans seront exclus par le
        //    filtre TreeWalker de la passe glossaire via la classe "glos")
        applyMetarToDOM(container, occMap);
        var nMetar = container.querySelectorAll('.glos-metar').length;

        // 2. Glossaire
        applyGlossaryToDOM(container, rx, maps, occMap);

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
  window.AeroLex = { init: init, version: '1.3.0' };
  /* Cœur de décision exposé pour les tests (test_matching.py, mesures sur les
     séances) : aucun effet sur le rendu. */
  window.AeroLexCore = { buildMaps: buildMaps, buildRegex: buildRegex, findMatches: findMatches,
                         pluriels: pluriels, singuliers: singuliers };

  if (document.readyState==='loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
