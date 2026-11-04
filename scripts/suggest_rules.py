#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suggest_rules.py — règles de QUALITÉ d'un lexique (établies le 2026-11-04), partagées par :
  - suggest_core.py (analyse, relance, contrôle avant « Valider », post-traitement),
  - new_lexicon.py (création d'un lexique, lot de termes source),
  - check_lexicon.py (verdict global).

Règles :
  1. FORME DE BASE : accents (comparés au corpus), singulier, forme française usuelle ; le sigle seulement si c'est l'usage.
  2. VARIANTES D'APPEL générées (pluriel/singulier, sans accent, équivalent anglais, sigle <-> développé, synonymes),
     décochables par le relecteur.
  3. DÉTECTION des fiches existantes : « vario » est une forme d'appel de « variomètre » -> variante, pas nouvelle fiche.
  4. ANTI-RIDICULE : simulation du moteur de soulignement (dist/aerolex.js, dans Node) sur le corpus des séances ;
     aucune variante < 3 lettres en minuscules, aucun mot grammatical, homographe courant => contexte_requis exigé.

Aucune dépendance à suggest_core (pas d'import circulaire) : tout est paramétré par des dicts / chemins.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import unicodedata
from pathlib import Path


# ── normalisation (identique à suggest_core.norm / import_lexique.norm) ─────
def strip_accents(s: str) -> str:
    s = unicodedata.normalize("NFD", s or "")
    return unicodedata.normalize("NFC", "".join(c for c in s if unicodedata.category(c) != "Mn"))


def norm(s: str) -> str:
    s = strip_accents(s).lower()
    s = re.sub(r"[^\w\s/+-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ── mots grammaticaux et homographes courants ───────────────────────────────
GRAMMATICAL = set(norm(w) for w in """a à au aux avec ce ces cet cette ceci cela ça dans de des du elle elles en et eux il ils je la le les leur leurs
lui ma mais me même mêmes mes moi mon ne ni nos notre nous on ou où par pas plus pour qu que quel quelle quels quelles qui sa se ses si son
sont sur ta te tes toi ton tous tout toute toutes tu un une vos votre vous y est été être sera soit sous sans entre vers chez comme donc or
car puis alors aussi très trop peu bien mal déjà encore jamais toujours ici là hors dès lors avant après depuis pendant selon contre
suis es sommes êtes était étaient fut ont ai as avons avez avait aura avoir fait faire peut peuvent doit doivent va vont vas
of the and for to in on at by with is are an not""".split())

# mots français courants qui existent aussi comme termes d'aéro (homographes) : jamais soulignés sans contexte
COMMON_HOMOGRAPHS = set(norm(w) for w in """tour plan air vent point base carte cap mode test bord corde bande vol vitesse temps niveau
poids charge force masse moment ligne piste bout fond haut bas gauche droite arrière milieu centre côté sens
type forme face tête pied main coup tir trou fil fer mer terre ciel nuage eau feu glace neige pluie brume brouillard
vue vie mise prise pose posé porte fin début suite sortie entrée arrêt départ retour trajet
route chemin voie pont mur toit sol pente rampe marche course coin bloc pièce partie part côte plage île
ordre règle loi code note carnet livre feuille page table liste tableau échelle cadran cercle rond
tenue essai rapport décision choix plein vide libre fermé ouvert dur doux clair sombre court long large
calme fort faible lourd léger vif lent rapide pointe pic cime col vallée voile voiles mât bateau""".split())

_FILLER = set(norm(w) for w in """souvent toujours également ensemble partie assez selon comme cette ainsi parfois permet utilisé utilisée peuvent plusieurs autre autres
entre aussi notamment généralement lorsque quand ainsi donc alors toute toutes celui celle ceux celles chaque dont être avoir faire fait faits peut doit
doivent permet permettent sert servent désigne désignent appelle appelée appelés nommé terme mot sens manière façon cas fois leur leurs très plus moins""".split())


def support_words(term: str, definition: str = "", extra=()) -> list:
    """Mots (≥5 lettres, accentués comme dans la définition) qui attestent le sens du lexique : définition + mots fournis (contexte, voir aussi)."""
    tn = set(norm(term).split())
    out, seen = [], set()
    txt = re.sub(r"<[^>]+>", " ", definition or "") + " " + " ".join(extra)
    for w in re.findall(r"[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\-]{4,}", txt):
        n = norm(w)
        if n in seen or n in GRAMMATICAL or n in _FILLER or n in COMMON_HOMOGRAPHS or n in tn or n.startswith("est-a-") or singular_norm(n) in {singular_norm(x) for x in tn}:
            continue
        seen.add(n)
        out.append(w.lower())
    return out[:40]


MIN_LEN_LOWER = 3          # une variante en minuscules de moins de 3 lettres est interdite
MAX_HITS_RISKY = 3         # > 3 soulignements d'une forme à risque sans contexte : bloquant
MAX_FALSE_RATIO = 0.05     # > 5 % de faux probables : bloquant


def is_grammatical(form: str) -> bool:
    """Vrai si la forme n'est faite QUE de mots grammaticaux."""
    ws = [w for w in re.split(r"[\s'’\-]+", norm(form)) if w]
    return bool(ws) and all(w in GRAMMATICAL for w in ws)


def too_short(form: str) -> bool:
    """Moins de 3 caractères (lettres/chiffres) ET écrite sans aucune majuscule : interdit. Une forme de 2 lettres AVEC majuscule
    (FL, Vy, Cd : sigle en casse exacte, que le moteur v1.3.0 ne reconnaît que dans cette casse) et toute forme d'au moins 3 caractères
    (« 7000 ») restent admises."""
    alnum = re.sub(r"[^0-9A-Za-zÀ-ÖØ-öø-ÿ]", "", form.strip())
    if len(alnum) >= MIN_LEN_LOWER:
        return False
    return not (len(alnum) == 2 and any(c.isupper() for c in alnum))


def is_exact_case_sigle(form: str, title: str = "") -> bool:
    """« Va » pour la fiche « VA » : variante de 2 lettres, avec une majuscule mais pas toutes, qui est la forme en casse EXACTE du sigle
    de la fiche (mêmes lettres que le titre en majuscules). Le moteur v1.3.0 ne la lie que dans cette casse (maps.exact) : « Va » (vitesse
    de manœuvre) est lié, « va » (verbe aller) ne l'est jamais. Sans le titre de la fiche on ne distingue pas « Va » de « Si » ou « Ne »
    (mots grammaticaux en début de phrase) : l'exemption exige donc le titre, et check_lexicon vérifie dans le moteur que la forme en
    minuscules n'est pas reconnue."""
    f = (form or "").strip()
    t = (title or "").strip()
    return bool(t) and len(f) == 2 and f.isalpha() and f[0].isupper() and f[1].islower() and t.isupper() and t.upper() == f.upper()


def forbidden_variant(form: str, title: str = "") -> str:
    """Raison de refus d'une variante (ou ''). title : titre de la fiche (admet « Va » pour « VA », cf. is_exact_case_sigle)."""
    f = (form or "").strip()
    if not f:
        return "vide"
    if too_short(f):
        return "moins de 3 lettres en minuscules"
    if is_grammatical(f) and not (len(f) >= 2 and f.isupper()) and not is_exact_case_sigle(f, title):   # « TA », « SI » en MAJUSCULES = sigles
        return "mot grammatical"
    return ""


# ── 1. forme de base : comparaison avec le corpus ──────────────────────────
_TOKEN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ][A-Za-zÀ-ÖØ-öø-ÿ'’\-]*")
_corpus_cache: dict = {}


def corpus_dir(root: Path | None = None, cfg: dict | None = None) -> Path | None:
    """Dossier des séances (corpus de cours) : cfg['corpus'] > $AEROLEX_CORPUS_DIR > ../aero-coach/sessions."""
    if cfg and cfg.get("corpus"):
        p = Path(cfg["corpus"])
        p = p if p.is_absolute() else (root or Path(".")) / p
        return p if p.is_dir() else None
    env = os.environ.get("AEROLEX_CORPUS_DIR")
    if env:
        return Path(env) if Path(env).is_dir() else None
    for c in (Path(__file__).resolve().parent.parent.parent / "aero-coach" / "sessions",
              (root or Path(".")).resolve().parent / "aero-coach" / "sessions",
              Path.home() / ".openclaw" / "workspace" / "projects" / "aero-coach" / "sessions"):
        if c.is_dir():
            return c
    return None


_TAGS = re.compile(r"<(script|style)\b.*?</\1>", re.S | re.I)
_TAG = re.compile(r"<[^>]+>")


def html_text(raw: str) -> str:
    import html as _h
    raw = _TAGS.sub(" ", raw)
    raw = re.sub(r"</(p|div|li|h\d|tr|section|summary|details|ul|ol|table)\s*>|<br\s*/?>", "\n", raw, flags=re.I)
    return re.sub(r"[ \t\r\f\v]+", " ", _h.unescape(_TAG.sub(" ", raw)))


def corpus_texts(cdir: Path | None) -> list:
    """[(nom, texte)] des séances, mis en cache (empreinte = nombre de fichiers + dernière date)."""
    if not cdir or not cdir.is_dir():
        return []
    files = sorted(cdir.glob("*.html"))
    key = (str(cdir), len(files), max((f.stat().st_mtime for f in files), default=0))
    hit = _corpus_cache.get("texts")
    if hit and hit[0] == key:
        return hit[1]
    out = []
    for f in files:
        try:
            out.append((f.name, html_text(f.read_text("utf-8", "ignore"))))
        except OSError:
            continue
    _corpus_cache["texts"] = (key, out)
    return out


def accent_forms(cdir: Path | None, glossaire: dict | None = None) -> dict:
    """{forme sans accent (minuscule) -> {forme réelle: nombre}} sur les séances + les titres/variantes/définitions du lexique."""
    key = (str(cdir), len(glossaire or {}), sum(len(str(m.get("definition") or "")) for m in (glossaire or {}).values()))
    hit = _corpus_cache.get("accents")
    if hit and hit[0] == key:
        return hit[1]
    cnt: dict = {}

    def feed(txt: str, w: int = 1):
        for t in _TOKEN.findall(txt):
            t = t.strip("-'’").lower()
            if len(t) >= 3:
                d = cnt.setdefault(strip_accents(t), {})
                d[t] = d.get(t, 0) + w
    for _n, tx in corpus_texts(cdir):
        feed(tx)
    for term, meta in (glossaire or {}).items():
        feed(term, 3)
        for v in (meta.get("variantes") or []):
            if isinstance(v, str):
                feed(v, 2)
        feed(re.sub(r"<[^>]+>", " ", str(meta.get("definition") or "")))
    _corpus_cache["accents"] = (key, cnt)
    return cnt


def accent_suggestion(term: str, cnt: dict) -> dict | None:
    """Si un mot de `term` est écrit sans accent alors que le corpus l'écrit presque toujours avec -> forme suggérée."""
    out, changed, notes = [], False, []
    for w in re.split(r"(\s+)", term):
        if not w.strip():
            out.append(w)
            continue
        core = w.strip("-'’()")
        low = core.lower()
        if len(low) < 4 or strip_accents(low) != low or (core.isupper() and len(low) <= 5):
            out.append(w)
            continue
        forms = cnt.get(low, {})
        acc = {f: n for f, n in forms.items() if f != low}
        bare = forms.get(low, 0)
        if acc:
            best, n = max(acc.items(), key=lambda kv: kv[1])
            if n >= 2 and n > 2 * bare:
                if core.isupper():
                    rep = best.upper()
                elif core[:1].isupper():
                    rep = best.capitalize()
                else:
                    rep = best
                out.append(w.replace(core, rep))
                changed = True
                notes.append("%s : %d occurrence(s) accentuée(s) « %s » contre %d sans accent" % (low, n, best, bare))
                continue
        out.append(w)
    return {"forme": "".join(out), "details": notes} if changed else None


# ── 2. variantes d'appel ────────────────────────────────────────────────────
TOOL_WORDS = set(norm(w) for w in "de du des d la le les l à au aux en sur sous par pour avec sans et ou dans entre vers chez".split())
INVARIANT = set(norm(w) for w in "arrière avant haut bas debout plus moins non pas très hors".split())
_EXC_AL_S = {"bal", "cal", "carnaval", "festival", "final", "naval", "fatal", "glacial", "idéal", "natal", "banal", "bancal", "chacal", "récital", "régal"}
_EXC_X = {"bijou", "caillou", "chou", "genou", "hibou", "joujou", "pou"}


def plural_word(w: str) -> str:
    lw = w.lower()
    if len(lw) < 3 or lw.endswith(("s", "x", "z")) or (w.isupper() and len(w) >= 2):      # sigle / mot en majuscules : invariable
        return w
    if lw.endswith("al") and lw not in _EXC_AL_S:
        return w[:-2] + "aux"
    if lw in {"travail", "vitrail", "corail", "émail", "soupirail", "bail"}:
        return w[:-3] + "aux"
    if lw.endswith(("au", "eau", "eu")) and lw not in {"pneu", "bleu", "lieu"}:
        return w + "x"
    if lw in _EXC_X:
        return w + "x"
    return w + "s"


_EUX_PLURIELS = {"jeux", "feux", "lieux", "enjeux", "essieux", "cheveux", "pieux", "épieux", "milieux", "vœux", "voeux", "neveux", "aïeux"}


def singular_word(w: str) -> str:
    lw = w.lower()
    if len(lw) <= 3 or (w.isupper() and len(w) >= 2):
        return w
    if lw.endswith("eux"):                       # nuageux, dangereux : invariables ; jeux, lieux : pluriels de -eu
        return w[:-1] if lw in _EUX_PLURIELS else w
    if lw.endswith(("ss", "us", "is")):
        return w
    if lw.endswith(("eaux", "yaux", "uaux")) and len(lw) > 4:       # bateaux -> bateau, tuyaux -> tuyau
        return w[:-1]
    if lw.endswith("aux") and len(lw) > 4:
        return w[:-3] + "al"
    if lw.endswith("eaux") and len(lw) > 4:
        return w[:-1]
    if lw.endswith("s"):
        return w[:-1]
    if lw.endswith("x") and len(lw) > 4:
        return w[:-1]
    return w


def _is_sigle(term: str) -> bool:
    t = term.strip()
    return bool(re.fullmatch(r"[A-Z0-9][A-Z0-9/\-.]{1,7}", t)) and bool(re.search(r"[A-Z]{2}", t))


_NOT_VERBS = {"cahier", "sentier", "pilier", "quartier", "atelier", "escalier", "dossier", "papier", "premier", "dernier", "levier", "clavier", "hangar",
              "calcaire", "mer", "fer", "hiver", "été", "air", "éclair", "cap", "chair", "ver", "enfer", "cuir", "avenir", "souvenir", "plaisir", "loisir",
              "désir", "devoir", "pouvoir", "savoir", "soir", "espoir", "miroir", "couloir", "tiroir", "terroir", "mouchoir", "manoir", "peignoir"}


def looks_verbal(term: str) -> bool:
    """Infinitif probable (« virer de bord », « empanner ») : pas de pluriel généré."""
    w = norm(term.split(" ")[0])
    return len(w) >= 5 and w.endswith(("er", "ir", "oir", "dre")) and w not in {norm(x) for x in _NOT_VERBS}


def _inflect(term: str, fn) -> str | None:
    if _is_sigle(term) or re.search(r"\d", term) or looks_verbal(term):
        return None
    toks = term.split(" ")
    low = [norm(t) for t in toks]
    if len(toks) == 1 or any(t in TOOL_WORDS for t in low[1:]):      # tête seule (« points de rosée »)
        i = 0
        while i < len(toks) and low[i] in TOOL_WORDS:
            i += 1
        if i < len(toks):
            toks[i] = fn(toks[i])
    else:                                                            # nom + adjectif : accord complet (« milles nautiques »)
        toks = [t if (low[k] in INVARIANT or low[k] in TOOL_WORDS) else fn(t) for k, t in enumerate(toks)]
    out = " ".join(toks)
    return out if out != term else None


def plural_form(term: str) -> str | None:
    return _inflect(term, plural_word)


def singular_form(term: str) -> str | None:
    return _inflect(term, singular_word)


TYPES = ("pluriel", "singulier", "sans accent", "anglais", "développé", "sigle", "synonyme", "manuelle")


def known_forms(idx) -> dict:
    """forme normalisée -> fiche propriétaire (termes + variantes + synonymes + développés) ; idx = LexiconIndex."""
    own: dict = {}
    for f, t in idx.exact.items():
        own.setdefault(f, t)
    for f, (t, _n) in idx.alias.items():
        own.setdefault(f, t)
    return own


def exact_key(form: str) -> str:
    """Clé de doublon : casse et espaces seulement (les ACCENTS comptent : « derive » est une variante distincte de « dérive »)."""
    return re.sub(r"\s+", " ", str(form or "")).strip().lower()


def make_variant(form: str, typ: str, me: str, own: dict, seen: set, raison: str = "", term_exact: str = "") -> tuple:
    """-> (variante|None, écartée|None). Applique toutes les interdictions. me = norm(fiche) ; term_exact = exact_key(fiche)."""
    form = re.sub(r"\s+", " ", str(form or "")).strip(" ,;")
    if not form:
        return None, None
    n = norm(form)
    k = exact_key(form)
    if k in seen or k == (term_exact or me):
        return None, None
    seen.add(k)
    why = forbidden_variant(form)
    if not why and (len(form) > 80 or len(form.split()) > 7):
        why = "trop long"
    if not why:
        o = own.get(n) or own.get(singular_norm(n))
        if o and norm(o) != me:
            why = "déjà forme d'appel de « %s »" % o
    if why:
        return None, {"forme": form, "type": typ, "raison": why}
    return {"forme": form, "type": typ, "coche": True, **({"raison": raison} if raison else {})}, None


def build_variants(term: str, d: dict, idx, taken: dict | None = None) -> tuple:
    """-> (variantes proposées [{forme,type,coche,raison?}], écartées [{forme,type,raison}]).
    Générées : pluriel/singulier du terme, sans accent, équivalent anglais, sigle <-> développé, synonymes du modèle.
    Une forme déjà connue d'une AUTRE fiche, trop courte, grammaticale, ou identique au terme est écartée avec sa raison."""
    own = taken if taken is not None else known_forms(idx)
    me, tex = norm(term), exact_key(term)
    keep, drop, seen = [], [], set()

    def add(form, typ, raison=""):
        v, x = make_variant(form, typ, me, own, seen, raison, tex)
        if v:
            keep.append(v)
        if x:
            drop.append(x)

    sigle = _is_sigle(term)
    if not sigle:
        for typ, fn in (("pluriel", plural_form), ("singulier", singular_form)):
            f = fn(term)
            if f:
                add(f, typ)
    sa = strip_accents(term)
    if sa != term:
        add(sa, "sans accent", "écrit sans accent par certains lecteurs")
        if not sigle and (p := plural_form(sa)):
            add(p, "pluriel", "pluriel sans accent")
    eng = d.get("equivalent_anglais") or d.get("anglais")
    for e in ([eng] if isinstance(eng, str) else eng if isinstance(eng, list) else []):
        if isinstance(e, str) and e.strip():
            add(e, "anglais")
    if sigle:
        for dev in (d.get("origine"), d.get("traduction")):
            if isinstance(dev, str) and dev.strip():
                add(dev, "développé")
    else:
        sg = d.get("sigle_equivalent") or d.get("sigle")
        if isinstance(sg, str) and sg.strip():
            add(sg.strip(), "sigle")
        dev = d.get("origine")
        if isinstance(dev, str) and norm(dev) != me and len(dev.split()) >= 2:
            add(dev, "développé")
    for s in d.get("synonymes") or []:
        if isinstance(s, str) and s.strip():
            add(s, "synonyme")
            if not _is_sigle(s) and (pl := plural_form(s)):
                add(pl, "pluriel", "pluriel du synonyme « %s »" % s)
    return keep, drop


def singular_norm(n: str) -> str:
    w = n.split(" ")
    w[-1] = singular_word(w[-1])
    return " ".join(w)


def retained_forms(d: dict) -> list:
    """Formes cochées d'une proposition (variantes d'appel) ; repli : synonymes des anciennes propositions."""
    v = d.get("variantes")
    if isinstance(v, list) and v and isinstance(v[0], dict):
        return [x["forme"] for x in v if x.get("coche", True) and x.get("forme")]
    return [s for s in (d.get("synonymes") or []) if isinstance(s, str)]


# ── 3. détection de fiches existantes ──────────────────────────────────────
def detect_existing(term: str, idx, model_hint: str = "", limit: int = 3) -> list:
    """Fiches dont `term` est (probablement) une forme d'appel : [{fiche, raison, force}] (force: forte|moyenne)."""
    n = norm(term)
    if not n or _is_sigle(term):
        return []
    out: dict = {}
    if model_hint:
        c = idx.canon(model_hint)
        if c and norm(c) != n:
            out[c] = {"fiche": c, "raison": "proposé par le modèle", "force": "moyenne"}
    single = " " not in n
    for t in idx.glossaire:
        tn = norm(t)
        if tn == n or (" " in tn and single):
            continue
        if single and " " not in tn:
            if len(n) >= 5 and tn.startswith(n) and len(n) / len(tn) >= 0.45 and len(tn) - len(n) <= 8:
                out[t] = {"fiche": t, "raison": "« %s » est le début de « %s » (abréviation d'usage)" % (term, t), "force": "forte"}
                continue
            cp = os.path.commonprefix([n, tn])
            if len(cp) >= max(6, int(0.7 * min(len(n), len(tn)))) and len(n) - len(cp) <= 5 and len(tn) - len(cp) <= 5:
                out.setdefault(t, {"fiche": t, "raison": "même radical que « %s » (« %s »)" % (t, cp), "force": "forte"})
        elif not single and n.replace(" ", "") == tn.replace(" ", ""):
            out.setdefault(t, {"fiche": t, "raison": "même graphie à l'espace près", "force": "forte"})
    rank = sorted(out.values(), key=lambda x: (x["force"] != "forte", len(x["fiche"])))
    return rank[:limit]


# ── 4. anti-ridicule : simulation du moteur de soulignement ───────────────
DRIVER = r"""
const fs=require('fs'), vm=require('vm');
const inp=JSON.parse(fs.readFileSync(0,'utf8'));
const win={}, doc={readyState:'loading',addEventListener(){},querySelector(){return null;}};
const ctx=vm.createContext({window:win,document:doc,console,performance:{now:()=>0}});
vm.runInContext(fs.readFileSync(inp.engine,'utf8'),ctx);
const core=win.AeroLexCore;
function run(terms){const m=core.buildMaps(terms), rx=core.buildRegex(m.ciMap,m.csMap);
  if(!rx) return inp.passages.map(()=>[]);
  return inp.passages.map(t=>core.findMatches(t,rx,m).map(x=>[x.raw,x.canon]));}
const out={};
for(const [name,entries] of Object.entries(inp.runs)){
  const t=Object.assign({},inp.base);
  for(const [k,v] of Object.entries(entries)) t[k]=v;
  out[name]=run(t);
}
console.log(JSON.stringify(out));
"""


def engine_paths(lexroot: Path, lex_id: str) -> tuple:
    d = Path(lexroot) / "dist"
    cands = [d / ("aerolex-index.json" if lex_id == "aero" else "aerolex-%s-index.json" % lex_id), d / "aerolex-index.json"]
    return d / "aerolex.js", next((p for p in cands if p.exists()), cands[0])


def corpus_paragraphs(texts: list) -> list:
    """[(séance, paragraphe, paragraphe sans accent en minuscules)] — mis en cache avec le corpus."""
    key = id(texts)
    hit = _corpus_cache.get("paras")
    if hit and hit[0] == key:
        return hit[1]
    out = []
    for name, tx in texts:
        for para in re.split(r"\n+", tx):
            para = para.strip()
            if len(para) >= 3:
                out.append((name, para, strip_accents(para).lower()))
    _corpus_cache["paras"] = (key, out)
    return out


def passages_for(texts: list, needles: list, width: int = 260) -> list:
    """Passages (≈ phrases) du corpus qui contiennent (sans accent, sans casse, pluriel permis) une des formes. [(séance, passage)]"""
    pats = []
    for n in needles:
        nn = norm(n)
        if nn:
            pats.append(re.escape(nn).replace(r"\ ", r"[\s'’\-]+") + r"(?:s|x|es)?")
    if not pats:
        return []
    rx = re.compile(r"(?<![a-z0-9])(?:" + "|".join(pats) + r")(?![a-z0-9])")
    out, seen = [], set()
    for name, para, nrm in corpus_paragraphs(texts):
        if not rx.search(nrm):
            continue
        chunks = [para] if len(para) <= width * 2 else re.split(r"(?<=[.!?])\s+", para)
        for ch in chunks:
            if ch not in seen and rx.search(strip_accents(ch).lower()):
                seen.add(ch)
                out.append((name, ch[:600]))
    return out


def simulate(term: str, forms: list, ctx_words: list, *, lexroot: Path, lex_id: str, cdir: Path | None,
             existing: str | None = None, risky: set | None = None, casse_sensible: bool = False, timeout: int = 90,
             support: list | None = None) -> dict:
    """Simule le moteur sur le corpus. `term` = nouvelle fiche ; si `existing` est donné, seules `forms` s'ajoutent à cette fiche.
    -> {disponible, n, n_sans_contexte, exemples[3], par_forme{}, faux, ratio, volees, risque, formes_risque[]}"""
    eng, idxp = engine_paths(lexroot, lex_id)
    texts = corpus_texts(cdir)
    if not (eng.exists() and idxp.exists() and texts):
        why = "moteur introuvable" if not eng.exists() else "index introuvable" if not idxp.exists() else "corpus des séances introuvable"
        return {"disponible": False, "raison": why, "n": 0}
    base = json.loads(idxp.read_text("utf-8")).get("terms", {})
    canon = existing or term
    surfaces = list(forms) if existing else [term] + list(forms)
    pass_ = passages_for(texts, surfaces)
    if risky is None:
        risky = {f for f in surfaces if norm(f) in COMMON_HOMOGRAPHS or is_grammatical(f)}
    risk_norm = {norm(x) for x in risky}
    ctx_words = [c for c in (ctx_words or []) if c]
    res = {"disponible": True, "n": 0, "n_sans_contexte": 0, "exemples": [], "par_forme": {}, "faux": 0, "ratio": 0.0, "volees": 0,
           "formes_risque": sorted(risky), "passages": len(pass_), "seances": len({p[0] for p in pass_}),
           "faux_sans_contexte": 0, "n_risque_sans_contexte": 0, "ratio_sans_contexte": 0.0, "risque": False}
    if not pass_:
        return res
    cur = dict(base.get(canon) or {})

    def entry(with_ctx: bool) -> dict:
        e = {"s": 1, "v": list(cur.get("v") or []) + [f for f in forms if f not in (cur.get("v") or [])]}
        ctxs = list(cur.get("ctx") or []) + (ctx_words if with_ctx else [])
        if ctxs:
            e["ctx"] = list(dict.fromkeys(ctxs))
        for k in ("cs", "sl", "cxs", "cxg", "hom"):
            if cur.get(k):
                e[k] = cur[k]
        if casse_sensible:
            e["cs"] = True
        return e

    inp = {"engine": str(eng), "base": base, "passages": [p[1] for p in pass_],
           "runs": {"avant": {}, "ctx": {canon: entry(True)}, "brut": {canon: entry(False)}}}
    try:
        p = subprocess.run(["node", "-e", DRIVER], input=json.dumps(inp), capture_output=True, text=True, timeout=timeout)
        if p.returncode != 0:
            raise RuntimeError((p.stderr or p.stdout)[-300:])
        runs = json.loads(p.stdout)
    except Exception as e:
        return {"disponible": False, "raison": "moteur : " + str(e)[:300], "n": 0}
    mine = {norm(f) for f in forms}

    def hits(run, only_new=True):
        base_run = runs["avant"]
        out = []
        for i, ms in enumerate(run):
            before = [(m[0], m[1]) for m in base_run[i]]
            for m in ms:
                if m[1] != canon or (existing and norm(m[0]) not in mine):
                    continue
                if only_new and (m[0], m[1]) in before:
                    continue
                out.append((i, m[0]))
        return out

    def has_ctx(i):
        t = strip_accents(pass_[i][1]).lower()
        return any(strip_accents(c).lower() in t for c in ctx_words)

    h, h_raw = hits(runs["ctx"]), hits(runs["brut"])
    res["n"], res["n_sans_contexte"] = len(h), len(h_raw)
    pf: dict = {}
    for _i, r in h_raw:
        pf[r] = pf.get(r, 0) + 1
    res["par_forme"] = dict(sorted(pf.items(), key=lambda kv: -kv[1]))
    support_n = [norm(w) for w in (support or []) if norm(w)]

    def supported(i):
        t = norm(pass_[i][1])
        return any(w in t for w in support_n)
    massif = set()                  # forme dont la plupart des soulignements tombent hors du sens du lexique (aucun mot de la définition alentour)
    if support_n:
        byf: dict = {}
        for i, r in h_raw:
            byf.setdefault(norm(r), []).append(i)
        for f, ids in byf.items():
            if len(ids) > MAX_HITS_RISKY and f not in risk_norm and sum(1 for i in ids if supported(i)) / len(ids) < 0.2:
                massif.add(f)
    risk_norm |= massif
    res["formes_risque"] = sorted(set(res["formes_risque"]) | {r for _i, r in h_raw if norm(r) in massif})
    res["massif"] = sorted(massif)
    risk_raw = [(i, r) for i, r in h_raw if norm(r) in risk_norm]
    faux_raw = [(i, r) for i, r in risk_raw if not has_ctx(i) and not (norm(r) in massif and supported(i))]
    res["n_risque_sans_contexte"], res["faux_sans_contexte"] = len(risk_raw), len(faux_raw)
    res["ratio_sans_contexte"] = round(len(faux_raw) / len(h_raw), 3) if h_raw else 0.0
    faux = [(i, r) for i, r in h if norm(r) in risk_norm and not has_ctx(i) and not (norm(r) in massif and supported(i))]
    res["faux"], res["ratio"] = len(faux), round(len(faux) / len(h), 3) if h else 0.0
    lost = 0
    for i, ms in enumerate(runs["avant"]):
        after = {(m[0], m[1]) for m in runs["ctx"][i]}
        lost += sum(1 for m in ms if (m[0], m[1]) not in after)
    res["volees"] = lost
    res["risque"] = bool(risk_raw)
    ex = []
    for i, r in (h or h_raw):
        txt = pass_[i][1]
        m = re.search(re.escape(r), txt)
        if m:
            a, b = max(0, m.start() - 55), min(len(txt), m.end() + 55)
            ex.append({"seance": pass_[i][0].replace(".html", ""), "forme": r,
                       "texte": ("…" if a else "") + txt[a:m.start()] + "[" + r + "]" + txt[m.end():b] + ("…" if b < len(txt) else "")})
        if len(ex) >= 3:
            break
    res["exemples"] = ex
    return res


def anti_ridicule_verdict(sim: dict, ctx_words: list) -> dict:
    """-> {statut ok|warn|ko, detail, incontournable, formes_risque}. KO = bloquant non forçable (corriger : contexte ou retrait)."""
    if not sim.get("disponible"):
        return {"statut": "warn", "detail": "non simulé (%s)" % sim.get("raison", "indisponible"), "incontournable": False}
    n = sim["n"]
    ex = " | ".join("%s : %s" % (e["seance"], e["texte"]) for e in sim["exemples"]) or "aucun passage trouvé"
    pf = ", ".join("%s ×%d" % kv for kv in list(sim["par_forme"].items())[:6])
    base = "%d nouveau(x) soulignement(s) simulé(s) dans %d séance(s) (%d passage(s) examiné(s))" % (n, sim.get("seances", 0), sim.get("passages", 0))
    if pf:
        base += " — " + pf
    ex_txt = " Exemples : " + ex
    risk = sim.get("formes_risque") or []
    n_r, ratio_r = sim.get("n_risque_sans_contexte", 0), sim.get("ratio_sans_contexte", 0.0)
    if sim.get("risque") and not ctx_words and (n_r > MAX_HITS_RISKY or ratio_r > MAX_FALSE_RATIO):
        return {"statut": "ko", "incontournable": True, "formes_risque": risk,
                "detail": "%s. Forme(s) à risque d'homographe courant (%s) : %d cas, %d %% de faux probables. Exiger des mots déclencheurs "
                          "(contexte_requis) ou retirer la variante.%s" % (base, ", ".join(risk), n_r, round(ratio_r * 100), ex_txt)}
    if sim.get("faux", 0) and (sim["faux"] > MAX_HITS_RISKY or sim["ratio"] > MAX_FALSE_RATIO):
        return {"statut": "ko", "incontournable": True, "formes_risque": risk,
                "detail": "%s. Même avec le contexte, %d faux probables (%d %%) : affiner contexte_requis ou retirer la variante.%s" % (
                    base, sim["faux"], round(sim["ratio"] * 100), ex_txt)}
    extra = ""
    if ctx_words and sim.get("n_sans_contexte", 0) > n:
        extra += " Le contexte (%s) écarte %d soulignement(s) hors sujet." % (", ".join(ctx_words), sim["n_sans_contexte"] - n)
    if sim.get("volees"):
        extra += " %d soulignement(s) existant(s) remplacé(s) (« plus long gagne »)." % sim["volees"]
    if risk and n and not ctx_words:
        return {"statut": "warn", "incontournable": False, "formes_risque": risk, "detail": base + "." + extra + " Forme(s) à surveiller : " + ", ".join(risk) + "." + ex_txt}
    return {"statut": "ok", "incontournable": False, "formes_risque": risk, "detail": base + "." + extra + (ex_txt if n else "")}
