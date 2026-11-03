#!/usr/bin/env python3
"""Scoring 'ce terme merite-t-il un schema ?' sur les 1300 termes AeroLex.

Sortie JSONL incrementale (reprise possible), un objet par terme.
Modele : OpenAI gpt-5-mini (aucune credential Gemini presente sur la machine,
voir RAPPORT). Jugement severe demande : une minorite de 'oui' attendue.

Usage:
  source ~/.gbrain/env.sh && python3 scripts/score_svg_llm.py [--only-failed]
"""
import json, os, sys, time, urllib.request, urllib.error, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOTS = os.path.join(ROOT, 'data/svg-scoring-lots/lots.json')
OUT = os.path.join(ROOT, 'data/svg-scoring-gemini.jsonl')
FAILLOG = os.path.join(ROOT, 'data/svg-scoring-lots/failed.log')
USAGE = os.path.join(ROOT, 'data/svg-scoring-lots/usage.json')
MODEL = os.environ.get('SCORE_MODEL', 'gpt-5-mini')
KEY = os.environ.get('OPENAI_API_KEY')
TYPES = ['geometrie', 'sequence_temporelle', 'vecteurs', 'coupe', 'abaque']

SYS = """Tu es directeur artistique d'un lexique aeronautique francais (AeroLex, 1300 termes, public = eleves pilotes PPL).
Ta tache : decider quels termes MERITENT un schema vectoriel (SVG), et lesquels n'en meritent pas.

SOIS SEVERE. Un lexique ou 900 termes 'meritent un schema' est inutilisable : on ne dessinera qu'une minorite.
Attends-toi a repondre 'non' pour la NETTE MAJORITE des termes d'un lot.

Un schema se justifie UNIQUEMENT si le concept est :
- SPATIAL (une geometrie, une disposition, une trajectoire, une position relative)
- TEMPOREL (une sequence d'actions ou de phases ordonnees)
- VECTORIEL (composition/decomposition de forces, de vents, de vitesses)
- COMPARATIF (deux ou plusieurs grandeurs qui ne se comprennent que cote a cote)

Un schema NE se justifie PAS pour :
- une unite de mesure, un sigle, un acronyme, un code, une frequence
- un document, un formulaire, une obligation administrative, un texte reglementaire
- un organisme, un service, un metier, un titre
- une definition purement lexicale ou terminologique (un synonyme, une denomination)
- un objet trivial qu'une photo remplacerait (on ne fait pas d'illustration decorative)

score : 0-10 = interet reel de dessiner ce terme. 8-10 = schema tres rentable, a faire en premier.
5-7 = utile, second rideau. 0-4 = ne pas dessiner. Si svg vaut "non", score DOIT etre <= 4.

type_schema : exactement un de geometrie | sequence_temporelle | vecteurs | coupe | abaque.
  Si svg vaut "non", mets type_schema a "".

termes_voisins : CRUCIAL. Liste des autres termes qui apparaitraient comme LIBELLES DANS LE DESSIN
  (donc cliquables vers leur fiche). Un dessin qui porte 8 libelles vaut mieux que 3 dessins isoles.
  REGLE ABSOLUE : ne cite QUE des termes presents mot pour mot dans la liste du lot fournie ci-dessous.
  N'invente aucun terme. Copie l'orthographe exacte. Si svg vaut "non", mets [].
  Ne te cite pas toi-meme dans tes propres termes_voisins.

justification : UNE phrase courte (max 20 mots), en francais, qui dit pourquoi oui ou pourquoi non.

Reponds en JSON STRICT, cet objet exact et rien d'autre :
{"resultats":[{"slug":"...","svg":"oui|non","score":0,"type_schema":"","justification":"...","termes_voisins":[]}]}
Un objet par terme fourni, dans le meme ordre, avec le slug EXACT recu."""


def build_user(lot_name, terms):
    liste = "\n".join(f"- {t['terme']}" for t in terms)
    fiches = []
    for t in terms:
        d = t['definition']
        if len(d) > 420:
            d = d[:420] + '...'
        fiches.append(f"slug: {t['slug']}\nterme: {t['terme']}\nfamille: {t['famille'] or '(aucune)'}\ncategorie: {t['categorie']}\ndefinition: {d}")
    return (f"LOT : {lot_name}  ({len(terms)} termes)\n\n"
            f"=== LISTE DES TERMES AUTORISES POUR termes_voisins (n'en cite aucun autre) ===\n{liste}\n\n"
            f"=== FICHES A JUGER ({len(terms)}) ===\n\n" + "\n\n".join(fiches) +
            f"\n\nRends exactement {len(terms)} objets dans resultats, un par slug ci-dessus.")


def call(messages, max_out=16000):
    body = json.dumps({
        'model': MODEL,
        'messages': messages,
        'response_format': {'type': 'json_object'},
        'max_completion_tokens': max_out,
    }).encode()
    req = urllib.request.Request('https://api.openai.com/v1/chat/completions', data=body,
                                 headers={'Authorization': f'Bearer {KEY}',
                                          'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def clean(rec, allowed_terms, allowed_slugs, self_terme):
    """Normalise + filtre : termes_voisins limites au lexique du lot."""
    slug = str(rec.get('slug', '')).strip()
    if slug not in allowed_slugs:
        return None
    svg = str(rec.get('svg', 'non')).strip().lower()
    svg = 'oui' if svg.startswith('o') else 'non'
    try:
        score = int(round(float(rec.get('score', 0))))
    except Exception:
        score = 0
    score = max(0, min(10, score))
    ts = rec.get('type_schema') or ''
    ts = ts.strip().lower()
    if ts not in TYPES:
        ts = ''
    voisins, seen = [], set()
    for v in (rec.get('termes_voisins') or []):
        v = str(v).strip()
        low = v.lower()
        if low in allowed_terms and low != self_terme.lower() and low not in seen:
            seen.add(low)
            voisins.append(allowed_terms[low])
    just = ' '.join(str(rec.get('justification', '')).split())[:220]
    if svg == 'non':
        score = min(score, 4)
        ts = ''
        voisins = []
    else:
        if not ts:
            ts = 'geometrie'
        score = max(score, 5)
    return {'slug': slug, 'svg': svg, 'score': score, 'type_schema': ts,
            'justification': just, 'termes_voisins': voisins}


def main():
    if not KEY:
        sys.exit('OPENAI_API_KEY absent (source ~/.gbrain/env.sh)')
    lots = json.load(open(LOTS))
    done = set()
    if os.path.exists(OUT):
        for line in open(OUT):
            line = line.strip()
            if line:
                try:
                    done.add(json.loads(line)['slug'])
                except Exception:
                    pass
    print(f'{len(lots)} lots | deja scores : {len(done)}', flush=True)
    usage = collections.Counter()
    failed = []
    fout = open(OUT, 'a')
    for i, lot in enumerate(lots, 1):
        name = lot['lot']
        terms = [t for t in lot['terms'] if t['slug'] not in done]
        if not terms:
            print(f'[{i}/{len(lots)}] {name} : deja complet, skip', flush=True)
            continue
        allowed_terms = {t['terme'].lower(): t['terme'] for t in lot['terms']}
        allowed_slugs = {t['slug'] for t in terms}
        byslug = {t['slug']: t for t in terms}
        msgs = [{'role': 'system', 'content': SYS},
                {'role': 'user', 'content': build_user(name, terms)}]
        got = {}
        for attempt in range(1, 4):
            try:
                r = call(msgs)
                u = r.get('usage', {})
                usage['prompt'] += u.get('prompt_tokens', 0)
                usage['completion'] += u.get('completion_tokens', 0)
                usage['calls'] += 1
                txt = r['choices'][0]['message']['content']
                data = json.loads(txt)
                res = data.get('resultats') or data.get('results') or []
                for rec in res:
                    if not isinstance(rec, dict):
                        continue
                    s = str(rec.get('slug', '')).strip()
                    src = byslug.get(s)
                    if not src:
                        continue
                    c = clean(rec, allowed_terms, allowed_slugs, src['terme'])
                    if c:
                        c['terme'] = src['terme']
                        c['famille'] = src['famille']
                        c['categorie'] = src['categorie']
                        c['lot'] = name
                        got[c['slug']] = c
                miss = [s for s in allowed_slugs if s not in got]
                if not miss:
                    break
                print(f'  [{i}] tentative {attempt}: {len(miss)} manquants, relance ciblee', flush=True)
                sub = [byslug[s] for s in miss]
                msgs = [{'role': 'system', 'content': SYS},
                        {'role': 'user', 'content': build_user(name + ' (reprise)', sub)}]
                allowed_slugs = set(miss)
                time.sleep(2)
            except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
                detail = ''
                if isinstance(e, urllib.error.HTTPError):
                    try:
                        detail = e.read().decode()[:200]
                    except Exception:
                        pass
                print(f'  [{i}] {name} erreur tentative {attempt}: {type(e).__name__} {e} {detail}', flush=True)
                time.sleep(5 * attempt)
        for s in sorted(got):
            fout.write(json.dumps(got[s], ensure_ascii=False) + '\n')
        fout.flush()
        manq = [t['slug'] for t in terms if t['slug'] not in got]
        if manq:
            failed.append({'lot': name, 'manquants': manq})
            print(f'[{i}/{len(lots)}] {name} : {len(got)}/{len(terms)} OK, {len(manq)} ECHEC', flush=True)
        else:
            print(f'[{i}/{len(lots)}] {name} : {len(got)}/{len(terms)} OK', flush=True)
    fout.close()
    if failed:
        with open(FAILLOG, 'w') as f:
            json.dump(failed, f, ensure_ascii=False, indent=1)
    # cout gpt-5-mini : 0.25 $/M in, 2.00 $/M out
    cost = usage['prompt'] / 1e6 * 0.25 + usage['completion'] / 1e6 * 2.00
    json.dump({'model': MODEL, 'calls': usage['calls'], 'prompt_tokens': usage['prompt'],
               'completion_tokens': usage['completion'], 'cost_usd': round(cost, 4),
               'lots_en_echec': len(failed)}, open(USAGE, 'w'), indent=1)
    print(f"\nAPPELS {usage['calls']} | in {usage['prompt']} | out {usage['completion']} | ~${cost:.4f} | lots en echec {len(failed)}")


if __name__ == '__main__':
    main()
