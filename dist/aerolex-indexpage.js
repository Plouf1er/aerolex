/* aerolex-indexpage.js — comportement de dist/aero/index.html
   - filtrage en direct (terme, développé, variantes ; sans accents/casse) + catégorie + famille
   - une lettre sans terme visible disparaît de la barre ET de la liste
   - autocomplétion (moteur partagé aerolex-searchbox.js) : choisir une suggestion ouvre la fiche
   - paramètres d'URL : ?q= ?fam= ?cat=  (liens « Famille » / « Catégorie » des fiches) */
(function () {
  'use strict';
  var $ = function (id) { return document.getElementById(id); };
  var input = $('search'), catSel = $('cat-filter'), famSel = $('fam-filter');
  var status = $('ix-status'), empty = $('ix-empty'), lettersBox = $('ix-letters');
  var groups = Array.prototype.slice.call(document.querySelectorAll('.ix-group'));
  var items = Array.prototype.slice.call(document.querySelectorAll('.ix-item'));
  var letterLinks = {};
  Array.prototype.forEach.call(lettersBox.querySelectorAll('a'), function (a) { letterLinks[a.dataset.l] = a; });
  var norm = window.AeroLexSearch ? window.AeroLexSearch.norm : function (s) { return String(s).toLowerCase(); };
  var total = items.length;

  function filter() {
    var toks = norm(input.value).split(' ').filter(Boolean);
    var c = catSel.value, f = famSel.value, shown = 0;
    items.forEach(function (li) {
      var n = li.dataset.n, ok = (!c || li.dataset.cat === c) && (!f || li.dataset.fam === f);
      for (var i = 0; ok && i < toks.length; i++) ok = n.indexOf(toks[i]) >= 0;
      li.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) {
      var any = !!g.querySelector('.ix-item:not([hidden])');
      g.hidden = !any;
      if (letterLinks[g.dataset.l]) letterLinks[g.dataset.l].hidden = !any;
    });
    empty.hidden = shown > 0;
    var filtered = toks.length || c || f;
    status.textContent = filtered ? shown + ' terme' + (shown > 1 ? 's' : '') + ' sur ' + total : '';
    status.hidden = !filtered;
    lettersBox.hidden = shown === 0;
  }

  input.addEventListener('input', filter);
  catSel.addEventListener('change', filter);
  famSel.addEventListener('change', filter);

  // Liens d'ancre : le filtre actif ne doit pas cacher la lettre visée (elle l'est déjà si le lien est visible).
  if (window.AeroLexSearch) {
    window.AeroLexSearch.mount(input, $('ix-sug'), function (r) {
      window.location.href = r.sl + '.html';
    }, { url: document.currentScript && document.currentScript.dataset.search, max: 8 });
  }

  var p = new URLSearchParams(window.location.search);
  if (p.get('q')) input.value = p.get('q');
  function preset(sel, v) {
    if (!v) return;
    for (var i = 0; i < sel.options.length; i++) if (sel.options[i].value === v) { sel.value = v; return; }
  }
  preset(famSel, p.get('fam')); preset(catSel, p.get('cat'));
  filter();
})();
