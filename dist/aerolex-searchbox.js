/* ============================================================================
   aerolex-searchbox.js — MOTEUR DE RECHERCHE PARTAGÉ d'AeroLex (autocomplétion)
   ----------------------------------------------------------------------------
   Copie autonome du moteur _alxMountSearch de la popup de référence du site hôte (aero.js)
   (même normalisation, même barème de score), pour les pages AeroLex qui
   n'embarquent pas aero.js (index du lexique). La DONNÉE n'est pas copiée : on
   lit le même aerolex-search.json, chargé au premier focus.

   Format d'une ligne de aerolex-search.json : [titre, slug, clé, développé, alias séparés par |]
   Recherche sur : terme, variantes (alias), développé de sigle ; insensible
   aux accents et à la casse.

   API :  AeroLexSearch.mount(input, ul, onPick, { url, max, clearOnPick })
          AeroLexSearch.norm(texte)
   Clavier : ↓ ↑ Entrée Échap. Tactile : tap sur une suggestion.
   Si vous corrigez le barème ici, répercutez-le dans aero.js (et inversement).
   ========================================================================== */
(function (root) {
  'use strict';
  function norm(x) {
    return String(x || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .toLowerCase().replace(/[\u2019']/g, ' ').replace(/\s+/g, ' ').trim();
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  var cache = {};                       // url -> Promise<lignes> (une seule lecture par page)
  function loadData(url) {
    if (!url) return Promise.resolve([]);
    if (cache[url]) return cache[url];
    cache[url] = fetch(url).then(function (r) { return r.json(); }).then(function (j) {
      return (j.d || []).map(function (r) {
        return { t: r[0], sl: r[1], k: r[2], e: r[3] || '', a: r[4] || '',
                 nt: norm(r[0] + ' ' + r[2]), ne: norm(r[3]), na: norm(r[4]) };
      });
    }).catch(function () { delete cache[url]; return []; });
    return cache[url];
  }

  function score(r, n) {
    var s = 0;
    if (r.nt === n) s = 100;
    else if (r.nt.indexOf(n) === 0) s = 80;
    else if (r.nt.split(' ').some(function (w) { return w.indexOf(n) === 0; })) s = 60;
    else if (r.na.split('|').some(function (a) { return a === n; })) s = 70;
    else if (r.na.split('|').some(function (a) { return a.indexOf(n) === 0 || (' ' + a).indexOf(' ' + n) >= 0; })) s = 50;
    else if (r.ne.indexOf(n) === 0 || (' ' + r.ne).indexOf(' ' + n) >= 0) s = 45;
    else if (r.nt.indexOf(n) >= 0 || r.ne.indexOf(n) >= 0 || r.na.indexOf(n) >= 0) s = 20;
    return s ? s - Math.min(r.t.length, 40) / 100 : 0;
  }

  /* Variante (alias) qui correspond à la requête, si le titre lui-même ne
     correspond pas : affichée « aussi : … » pour expliquer la suggestion. */
  function matchedAlias(r, n) {
    if (r.nt.indexOf(n) >= 0) return '';
    var raw = r.a.split('|'), nor = r.na.split('|');
    for (var i = 0; i < nor.length; i++) if (nor[i].indexOf(n) >= 0) return raw[i] || '';
    return '';
  }

  function mount(q, ul, onPick, opts) {
    opts = opts || {};
    var max = opts.max || 8, items = [], cur = -1, lastN = '';
    var seq = 0;
    function load() { return loadData(opts.url); }
    function close() {
      ul.hidden = true; q.setAttribute('aria-expanded', 'false'); cur = -1;
      q.removeAttribute('aria-activedescendant');
    }
    function render() {
      ul.innerHTML = '';
      items.forEach(function (x, i) {
        var r = x.r, li = document.createElement('li');
        li.id = ul.id + '-opt-' + i; li.setAttribute('role', 'option');
        var al = x.alias ? '<span class="alx-s-a">aussi\u00a0: ' + esc(x.alias) + '</span>' : '';
        li.innerHTML = '<span class="alx-s-t">' + esc(r.t) + '</span>' +
          (r.e ? '<span class="alx-s-e">' + esc(r.e) + '</span>' : '') + al;
        li.addEventListener('mousedown', function (ev) { ev.preventDefault(); });   // garde le focus (pas de blur avant le tap)
        li.addEventListener('click', function () { choose(i); });
        ul.appendChild(li);
      });
      ul.hidden = !items.length;
      q.setAttribute('aria-expanded', items.length ? 'true' : 'false');
    }
    function mark() {
      Array.prototype.forEach.call(ul.children, function (li, i) {
        li.setAttribute('aria-selected', i === cur ? 'true' : 'false');
        li.classList.toggle('alx-active', i === cur);
      });
      if (cur >= 0) {
        q.setAttribute('aria-activedescendant', ul.id + '-opt-' + cur);
        var el = ul.children[cur]; if (el && el.scrollIntoView) el.scrollIntoView({ block: 'nearest' });
      }
    }
    function choose(i) {
      var x = items[i]; if (!x) return;
      close();
      if (opts.clearOnPick) { q.value = ''; q.blur(); }
      onPick(x.r);
    }
    function search() {
      var n = norm(q.value); lastN = n;
      if (!n) { items = []; render(); return; }
      var my = ++seq;
      load().then(function (d) {
        if (my !== seq || norm(q.value) !== n) return;
        items = d.map(function (r) { return { r: r, s: score(r, n) }; })
          .filter(function (x) { return x.s > 0; })
          .sort(function (a, b) { return b.s - a.s; }).slice(0, max)
          .map(function (x) { return { r: x.r, alias: matchedAlias(x.r, n) }; });
        cur = items.length ? 0 : -1; render(); mark();
      });
    }
    q.addEventListener('focus', function () { load(); if (items.length && norm(q.value) === lastN) { ul.hidden = false; q.setAttribute('aria-expanded', 'true'); } });
    q.addEventListener('input', search);
    q.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); if (items.length) { if (ul.hidden) { ul.hidden = false; q.setAttribute('aria-expanded', 'true'); } cur = (cur + 1) % items.length; mark(); } }
      else if (e.key === 'ArrowUp') { e.preventDefault(); if (items.length) { cur = (cur - 1 + items.length) % items.length; mark(); } }
      else if (e.key === 'Enter') { if (!ul.hidden && cur >= 0) { e.preventDefault(); choose(cur); } }
      else if (e.key === 'Escape') { if (!ul.hidden) { e.stopPropagation(); close(); } else if (q.value) { q.value = ''; q.dispatchEvent(new Event('input')); } }
    });
    q.addEventListener('blur', function () { setTimeout(close, 150); });
    return { close: close };
  }

  root.AeroLexSearch = { mount: mount, norm: norm };
})(window);
