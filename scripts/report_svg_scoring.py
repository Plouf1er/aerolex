#!/usr/bin/env python3
"""Genere data/SVG-SCORING.md a partir de data/svg-scoring-gemini.jsonl."""
import json, os, glob, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JL = os.path.join(ROOT, 'data/svg-scoring-gemini.jsonl')
MD = os.path.join(ROOT, 'data/SVG-SCORING.md')

rows = [json.loads(l) for l in open(JL) if l.strip()]
by = {r['slug']: r for r in rows}

# etat reel du corpus
have_svg, flag_schema = set(), set()
for f in glob.glob(os.path.join(ROOT, 'dist/aero/t/*.json')):
    d = json.load(open(f))
    if d.get('schema_svg'):
        have_svg.add(d['slug'])
    if d.get('schema'):
        flag_schema.add(d['slug'])

# les 9 generateurs Python existants et les concepts qu'ils couvrent
GEN_COVER = {
    'svg_piste_seuils_qfu': ['pistes', 'dimensions_piste'],
    'svg_manche_a_air': ['procedures_sol'],
    'svg_rose_des_vents': ['references_magnetiques'],
    'svg_composantes_face_travers': ['vent', 'composantes_vent'],
    'svg_decrabage': ['atterrissages'],
    'svg_tour_de_piste': ['circuit_branches', 'circuit_procedures'],
    'svg_azimut_vrai_magnetique': ['references_magnetiques', 'navigation_caps_et_routes'],
    'svg_remise_des_gaz': ['atterrissages'],
    'svg_distances_piste': ['dimensions_piste'],
}
COVERED_FAM = {f for v in GEN_COVER.values() for f in v}

oui = [r for r in rows if r['svg'] == 'oui']
non = [r for r in rows if r['svg'] == 'non']
b810 = [r for r in rows if r['score'] >= 8]
b57 = [r for r in rows if 5 <= r['score'] <= 7]
b04 = [r for r in rows if r['score'] <= 4]

L = []
L.append('# AeroLex — Scoring SVG des 1300 termes\n')
L.append('> Question posee au modele, terme par terme : **ce terme merite-t-il un schema ?**')
L.append('> Sortie brute : `data/svg-scoring-gemini.jsonl` (1 objet JSON par ligne).\n')
L.append('## Avertissements\n')
L.append('- **Modele reellement utilise : OpenAI `gpt-5-mini`, PAS Gemini.** Aucune credential Google/Gemini')
L.append('  n\'existe sur cette machine (ni cle `AIza*`, ni keychain, ni `~/.gemini`, ni env) : le profil')
L.append('  `google:gemini-29-03-2026` d\'`openclaw.json` est en mode `token` sans secret stocke, et la CLI')
L.append('  `openclaw` est cassee (`Cannot read properties of undefined (reading \'input\')`). Le nom de fichier')
L.append('  `svg-scoring-gemini.jsonl` est conserve car annonce, mais le juge est gpt-5-mini.')
L.append(f'- **Le flag `schema: true` du corpus est menteur** : {len(flag_schema)} fiches le portent dans `dist/`,')
L.append('  et 222 occurrences dans `data/data_glossaire_full.py`, sans jamais dire QUEL schema. Il n\'a pas ete')
L.append(f'  utilise comme signal ici. Seuls **{len(have_svg)} termes ont un `schema_svg` reellement rendu**.')
L.append('- Ce scoring est une **file de travail proposee**, pas une verite : c\'est un avis de modele.\n')

L.append('## Chiffres\n')
L.append(f'| Mesure | Valeur |')
L.append(f'|---|---|')
L.append(f'| Termes scores | **{len(rows)} / 1300** |')
L.append(f'| Lots | 30 (par famille ; familles <25 termes fusionnees, >70 scindees) |')
L.append(f'| `svg: oui` | **{len(oui)}** ({len(oui)*100//len(rows)} %) |')
L.append(f'| `svg: non` | **{len(non)}** ({len(non)*100//len(rows)} %) |')
L.append(f'| Score 8-10 | {len(b810)} |')
L.append(f'| Score 5-7 | {len(b57)} |')
L.append(f'| Score 0-4 | {len(b04)} |')
L.append('')

L.append('### Repartition par type de schema (sur les `oui`)\n')
tc = collections.Counter(r['type_schema'] for r in oui)
L.append('| Type | Nb |')
L.append('|---|---|')
for k, v in tc.most_common():
    L.append(f'| {k} | {v} |')
L.append('')

# controle de sanite
L.append(f'## Controle de sanite — les {len(have_svg)} termes qui ONT DEJA un schema\n')
L.append('Si le modele notait bas des schemas que Louis a juge utiles, le scoring serait douteux.\n')
L.append('| Terme | Score | svg | Type | Voisins |')
L.append('|---|---|---|---|---|')
sc = []
for s in sorted(have_svg):
    r = by.get(s)
    if not r:
        L.append(f'| {s} | *(absent du scoring)* | — | — | — |')
        continue
    sc.append(r['score'])
    L.append(f"| {r['terme']} | **{r['score']}** | {r['svg']} | {r['type_schema'] or '—'} | {len(r['termes_voisins'])} |")
if sc:
    ok = sum(1 for x in sc if x >= 8)
    L.append('')
    L.append(f'**Moyenne : {sum(sc)/len(sc):.1f}/10** — {ok}/{len(sc)} notes 8+, '
             f'{sum(1 for x in sc if x >= 5)}/{len(sc)} avec `svg: oui`. '
             f'Min {min(sc)}, max {max(sc)}.')
L.append('')

L.append('## Top 60 recommandations\n')
L.append('| # | Score | Terme | Type | Voisins | Famille | Justification |')
L.append('|---|---|---|---|---|---|---|')
top = sorted(oui, key=lambda r: (-r['score'], -len(r['termes_voisins']), r['terme']))
for i, r in enumerate(top[:60], 1):
    deja = ' ✅' if r['slug'] in have_svg else ''
    L.append(f"| {i} | {r['score']} | **{r['terme']}**{deja} | {r['type_schema']} | "
             f"{len(r['termes_voisins'])} | {r['famille'] or '—'} | {r['justification']} |")
L.append('')
L.append('✅ = schema deja existant.\n')

L.append('## Agregats par famille\n')
fam = collections.defaultdict(lambda: {'n': 0, 'oui': 0, 'sc': [], 'vois': 0})
for r in rows:
    k = r['famille'] or f"(sans famille — {r['categorie']})"
    fam[k]['n'] += 1
    if r['svg'] == 'oui':
        fam[k]['oui'] += 1
        fam[k]['sc'].append(r['score'])
        fam[k]['vois'] += len(r['termes_voisins'])
L.append('| Famille | Termes | `oui` | Score moy. des `oui` | Libelles cliquables cumules |')
L.append('|---|---|---|---|---|')
for k in sorted(fam, key=lambda x: (-fam[x]['oui'], x)):
    v = fam[k]
    moy = f"{sum(v['sc'])/len(v['sc']):.1f}" if v['sc'] else '—'
    L.append(f"| {k} | {v['n']} | {v['oui']} | {moy} | {v['vois']} |")
L.append('')

L.append('## Couverture par les 9 generateurs Python existants\n')
cov = [r for r in oui if r['famille'] in COVERED_FAM]
new = [r for r in oui if r['famille'] not in COVERED_FAM]
L.append(f'- Familles deja outillees par `src/svg_glossaire.py` : {", ".join(sorted(COVERED_FAM))}')
L.append(f'- Recommandations `oui` dans ces familles (generateur adaptable) : **{len(cov)}**')
L.append(f'- Recommandations `oui` hors de ces familles (nouveau generateur requis) : **{len(new)}**')
L.append('')
L.append('Estimation par famille, hors perimetre actuel, triee par volume :\n')
nf = collections.Counter(r['famille'] or f"(sans famille — {r['categorie']})" for r in new)
L.append('| Famille a outiller | `oui` |')
L.append('|---|---|')
for k, v in nf.most_common(20):
    L.append(f'| {k} | {v} |')
L.append('')

L.append('## Les termes les plus "porteurs" (le plus de libelles cliquables)\n')
L.append('Un dessin qui porte 8 libelles vaut mieux que 3 dessins isoles.\n')
L.append('| Terme | Score | Voisins | Liste |')
L.append('|---|---|---|---|')
for r in sorted(oui, key=lambda r: -len(r['termes_voisins']))[:25]:
    L.append(f"| {r['terme']} | {r['score']} | {len(r['termes_voisins'])} | {', '.join(r['termes_voisins'][:8])} |")
L.append('')
tot_v = sum(len(r['termes_voisins']) for r in oui)
L.append(f"**Total libelles cliquables potentiels sur les {len(oui)} `oui` : {tot_v}** "
         f"(moyenne {tot_v/max(1,len(oui)):.1f} par schema).")

u = os.path.join(ROOT, 'data/svg-scoring-lots/usage.json')
if os.path.exists(u):
    d = json.load(open(u))
    L.append('')
    L.append('## Cout API reel\n')
    L.append(f"- Modele : `{d['model']}` | appels : {d['calls']} | lots en echec : {d['lots_en_echec']}")
    L.append(f"- Tokens : {d['prompt_tokens']} in / {d['completion_tokens']} out")
    L.append(f"- **Cout : ${d['cost_usd']}** (tarif gpt-5-mini 0,25 $/M in, 2,00 $/M out)")

open(MD, 'w').write('\n'.join(L) + '\n')
print(f'ecrit {MD} ({len(L)} lignes)')
print(f'rows={len(rows)} oui={len(oui)} non={len(non)} 8-10={len(b810)} 5-7={len(b57)} 0-4={len(b04)}')
