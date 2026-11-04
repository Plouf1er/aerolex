#!/usr/bin/env node
/* test_popup.js — reproduit la logique de _renderGlos (popup du site hôte)
   contre l'index réel et vérifie que chaque lien produit cible un fichier
   existant dans dist/aero/. Usage : node scripts/test_popup.js */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const idx = JSON.parse(fs.readFileSync(path.join(ROOT, 'dist/aerolex-index.json'), 'utf8'));
const schemas = JSON.parse(fs.readFileSync(path.join(ROOT, 'dist/aero/schemas.json'), 'utf8'));
const AEROLEX_BASE = process.env.AEROLEX_BASE || 'https://lexique.exemple/aero/';
const DIST = path.join(ROOT, 'dist/aero');

const terms = idx.terms, families = idx.families;
const url = (sl) => AEROLEX_BASE + encodeURIComponent(sl) + '.html';
const entry = (t) => terms[t] || Object.entries(terms).find(([k]) => k.toLowerCase() === t.toLowerCase())?.[1] || null;
const canon = (t) => terms[t] ? t : (Object.keys(terms).find(k => k.toLowerCase() === t.toLowerCase()) || t);

let missing = 0, selfLink = 0;
function fileFor(u) {
  const f = decodeURIComponent(u.slice(AEROLEX_BASE.length));
  const p = path.join(DIST, f);
  if (!fs.existsSync(p)) { missing++; console.log('    ❌ FICHIER MANQUANT ' + f); }
  return fs.existsSync(p);
}

for (const t of ['gouverne', 'tour de piste', 'manuel de vol']) {
  const e = entry(t), c = canon(t);
  console.log(`\n=== ${t} (canon="${c}") ===`);
  // .alx-pop-def
  console.log(`  def    : ${e && e.d ? 'OUI (' + e.d.length + ' car.)' : 'VIDE'}`);
  // .alx-pop-schema
  const svg = e && e.g ? schemas[e.g] : null;
  console.log(`  schema : ${e && e.g ? 'g=' + e.g + ' -> SVG ' + (svg ? svg.length + ' car.' : 'ABSENT DE schemas.json') : 'aucun'}`);
  // .alx-pop-family
  const fam = e && e.f, membres = fam ? (families[fam] || []) : [];
  console.log(`  family : ${fam ? '"' + fam + '" (' + membres.length + ' membres)' : 'aucune'}`);
  for (const m of membres) {
    if (m === c) { console.log(`      [courant, non cliquable] ${m}`); continue; }
    const me = entry(m);
    if (!me || !me.sl) { console.log(`      ⚠️ pas de slug: ${m}`); continue; }
    const u = url(me.sl);
    if (me.sl === (e && e.sl)) { selfLink++; console.log(`      ❌ AUTO-LIEN ${m}`); }
    fileFor(u);
  }
  if (membres.length) console.log(`      ${membres.length - 1} liens vérifiés`);
  // .alx-pop-xrefs
  const xs = (e && e.x) || [];
  const xok = xs.filter(x => x !== c && entry(x) && entry(x).sl);
  console.log(`  xrefs  : ${xs.length} brut -> ${xok.length} liens`);
  xok.forEach(x => fileFor(url(entry(x).sl)));
  // .alx-pop-link
  const link = e && e.sl ? url(e.sl) : AEROLEX_BASE + 'index.html';
  console.log(`  link   : ${link}`);
  fileFor(link);
  const blocs = [e && e.d ? 'def' : null, e && e.g ? 'schema' : null, membres.length >= 2 ? 'family' : null, xok.length ? 'xrefs' : null, 'link'].filter(Boolean);
  console.log(`  BLOCS RENDUS : ${blocs.join(', ')} (${blocs.length}/5)`);
}
console.log(`\nFichiers manquants: ${missing} | auto-liens: ${selfLink}`);
process.exit(missing || selfLink ? 1 : 0);
