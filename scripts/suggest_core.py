#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
suggest_core.py — « Suggérer des termes » pour AeroLex (et tout lexique déclaré
dans LEXICONS). Aucune dépendance hors bibliothèque standard (+ pypdf/python-docx
OPTIONNELS pour l'upload PDF/DOCX ; pdftotext sinon).

ENTONNOIR (coût croissant, on s'arrête dès que possible) :
  1. parse_terms()      : découpe (virgule, point-virgule, retour ligne), nettoie, dédoublonne
                          par forme normalisée (accents, casse, pluriel)      -> GRATUIT
  2. LexiconIndex.match : comparaison à l'index (termes, variantes, synonymes,
                          développés) -> « déjà présent » / « alias probable »  -> GRATUIT
  3. cache par terme    : un terme déjà analysé n'est JAMAIS repayé              -> GRATUIT
  4. LLM par lots de 20 : seulement pour le reste. Grok 4.3 (xAI) puis Qwopus local
                          en secours ($0). Sortie JSON stricte, validée (validate_item).

Rien n'est publié automatiquement : les résultats pertinents vont dans la file
« propositions » (SQLite data/suggest/suggest.db, non versionné). validate_proposals()
écrit dans la SOURCE des fiches (data/data_glossaire.py) puis relance le pipeline de
build existant (pas de copie).
"""
from __future__ import annotations

import concurrent.futures as cf
import fcntl
import shutil
import importlib.util
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import unicodedata
import urllib.request
import urllib.error
import zipfile
from pathlib import Path

ROOT = Path(os.environ.get("AEROLEX_ROOT", Path(__file__).resolve().parent.parent))
DATA_DIR = Path(os.environ.get("AEROLEX_SUGGEST_DIR", ROOT / "data" / "suggest"))

# ── Configuration ────────────────────────────────────────────────────────────
MAX_TERMS_PER_SUBMISSION = 300
BATCH_SIZE = 20            # termes par appel LLM
PARALLEL_BATCHES = 4       # appels LLM simultanés (job asynchrone)
UNIT_SYNC_MAX = 3          # <= 3 termes à analyser : réponse synchrone
DAILY_USD_CAP = float(os.environ.get("AEROLEX_SUGGEST_DAILY_USD", "2.0"))
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
# Anti-abus de coût (soumission publique, sans jeton). Ne comptent QUE les termes envoyés au LLM :
# l'entonnoir gratuit (index, cache, contrôles déterministes) reste illimité.
LLM_TERMS_PER_IP_HOUR = int(os.environ.get("AEROLEX_SUGGEST_IP_HOUR", "30"))
LLM_TERMS_PER_IP_DAY = int(os.environ.get("AEROLEX_SUGGEST_IP_DAY", "300"))
PARSE_PER_IP_HOUR = 20     # analyses de fichier par IP et par heure (CPU : pdf/docx)
LOW_CONF = 0.6             # confiance < 0,6 : avertissement à la validation
MAX_TERM_LEN = 80
MAX_TERM_WORDS = 6
CANDIDATE_LIMIT = 150      # termes extraits d'un document en prose

PRIMARY_MODEL = os.environ.get("AEROLEX_SUGGEST_MODEL", "grok-4.3")
XAI_URL = "https://api.x.ai/v1/chat/completions"
LOCAL_URL = os.environ.get("AEROLEX_SUGGEST_LOCAL_URL", "http://OMEN-INFERENCE.local:11434/v1/chat/completions")
LOCAL_MODEL = os.environ.get("AEROLEX_SUGGEST_LOCAL_MODEL", "current-llm")
PRICE_IN, PRICE_OUT = 1.25, 2.5          # USD / 1M tokens (grok-4.3, openclaw.json) si le fournisseur ne renvoie pas le coût
LLM_TIMEOUT = 120
# Mesuré (4 nov. 2026, 1 terme) : none 3,5 s / 0,0016 $ ; minimal 11,8 s / 0,0033 $ ; low 14,6 s / 0,0039 $.
REASONING_EFFORT = os.environ.get("AEROLEX_SUGGEST_EFFORT", "none")

try:                                     # libellé lisible d'une famille (term_display + data/familles_labels.json)
    from term_display import family_label as _family_label_default
except Exception:  # pragma: no cover
    _family_label_default = lambda f: f.replace("_", " ").capitalize()  # noqa: E731


def family_label(slug: str, root=None) -> str:
    try:
        d = json.loads(((root or ROOT) / "data" / "familles_labels.json").read_text("utf-8"))
        if isinstance(d, dict) and d.get(slug):
            return d[slug]
    except (OSError, ValueError):
        pass
    return _family_label_default(slug)


LEXICONS = {
    "aero": {
        "label": "Aéronautique (PPL / ULM)",
        "audience": "élève pilote PPL ou ULM",
        "scope": ("vocabulaire du pilotage d'avions légers et d'ULM : aérodynamique, "
                  "instruments, météo aéronautique, navigation, réglementation et espaces aériens, "
                  "radiotéléphonie, performances, masse et centrage, moteur et hélice, "
                  "facteurs humains, procédures et codes (OACI, METAR/TAF, NOTAM…)"),
        "slug_dir": "dist/aero",
        "source": "data/data_glossaire.py",
        "full": "data/data_glossaire_full.py",
        "base_url": "/aero/",
    },
}

# ── Normalisation ────────────────────────────────────────────────────────────
def norm(s: str) -> str:
    """Identique à src/import_lexique.norm (minuscules, sans accents, ponctuation neutralisée)."""
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = s.lower()
    s = re.sub(r"[^\w\s/+-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def singular(n: str) -> str:
    """Pluriel -> singulier (mot par mot sur le DERNIER mot), prudent : mots > 3 lettres."""
    parts = n.split(" ")
    w = parts[-1]
    if len(w) > 3:
        if w.endswith("aux") and len(w) > 4:
            w = w[:-3] + "al"
        elif w.endswith(("s", "x")) and not w.endswith(("ss", "us")):
            w = w[:-1]
    parts[-1] = w
    return " ".join(parts)


def ckey(term: str) -> str:
    """Clé canonique (cache, file) : forme normalisée au singulier."""
    return singular(norm(term))


def keyforms(term: str) -> set:
    n = norm(term)
    out = {n} if n else set()
    if n:
        out.add(singular(n))
    return out


# ── 1. Parsing ───────────────────────────────────────────────────────────────
_SPLIT = re.compile(r"[,;\n\r\t]+")
_BULLET = re.compile(r"^\s*(?:[-*•·▪►]+|\d{1,3}[.)])\s+")


def clean_term(raw: str) -> str:
    t = _BULLET.sub("", raw or "")
    t = t.strip().strip("\"'«»“”‘’()[]{}").strip()
    t = re.sub(r"\s+", " ", t)
    return t.rstrip(" .:")


def parse_terms(text: str, limit: int | None = None) -> dict:
    """Texte libre -> {"terms": [...], "duplicates": n, "rejected": [...]}.
    Dédoublonnage par forme normalisée (accents/casse/pluriel). Garde la 1ère graphie."""
    seen, terms, rejected, dup = set(), [], [], 0
    for raw in _SPLIT.split(text or ""):
        t = clean_term(raw)
        if not t:
            continue
        if len(t) > MAX_TERM_LEN or len(t.split()) > MAX_TERM_WORDS or not re.search(r"\w", t):
            rejected.append(t[:MAX_TERM_LEN])
            continue
        kf = keyforms(t)
        if kf & seen:
            dup += 1
            continue
        seen |= kf
        terms.append(t)
    over = []
    if limit is not None and len(terms) > limit:
        over = terms[limit:]
        terms = terms[:limit]
    return {"terms": terms, "duplicates": dup, "rejected": rejected, "over_limit": over}


# Mots vides FR/EN pour l'extraction de candidats depuis un document en prose
_STOP = set("""a à au aux avec ce ces cet cette dans de des du elle en et eux il ils je la le les leur lui ma mais me même mes moi mon ne nos notre nous on ou où par pas pour qu que qui sa se ses son sur ta te tes toi ton tu un une vos votre vous
est sont être avoir été fait faire peut doit sans sous plus moins très tout tous toute toutes si ainsi alors donc car comme entre vers chez lors puis aussi selon dont après avant pendant lorsque quand cela celui celle ceux the of and to in is for on with as by an at be this that are from or it""".split())
_STOP_N = set(norm(w) for w in _STOP)
_WORD = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9/\-]*")
_CHUNK = re.compile(r"[.;:!?()\[\]«»\u201c\u201d\",\n\r]+")
_STOP |= {"l", "d", "qu", "n", "s", "j", "c", "m", "t"}


def looks_like_list(text: str) -> bool:
    lines = [l for l in re.split(r"[\r\n]+", text) if l.strip()]
    if not lines:
        return False
    avg = sum(len(l) for l in lines) / len(lines)
    return avg < 60 or (len(lines) == 1 and "," in text and len(text) < 3000)


def extract_candidates(text: str, limit: int = CANDIDATE_LIMIT) -> list:
    """Prose -> termes candidats : sigles (2-7 majuscules) + n-grammes 1-3 mots sans mot vide aux bords,
    classés par fréquence puis longueur. Le filtrage domaine/pertinence est fait ensuite par l'entonnoir."""
    counts: dict[str, list] = {}
    def add(phrase: str, w: float):
        k = norm(phrase)
        if not k or k.isdigit():
            return
        e = counts.setdefault(k, [phrase, 0.0])
        e[1] += w
    for chunk in _CHUNK.split(text.replace("'", " ").replace("’", " ")):
        toks = [m.group(0).strip("-/") for m in _WORD.finditer(chunk)]
        toks = [t for t in toks if t]
        for i, t in enumerate(toks):
            low = t.lower()
            if re.fullmatch(r"[A-Z][A-Z0-9/]{1,6}", t) and not t.isdigit():
                add(t, 3)
            for n in (1, 2, 3):
                seg = toks[i:i + n]
                if len(seg) < n:
                    break
                if seg[0].lower() in _STOP or seg[-1].lower() in _STOP:
                    continue
                if n == 1 and (len(t) < 4 or low in _STOP):
                    continue
                add(" ".join(seg) if all(x.isupper() for x in seg) else " ".join(seg).lower(), 1 + 0.3 * (n - 1))
    ranked = sorted(counts.values(), key=lambda e: (-e[1], -len(e[0])))
    # supprime les n-grammes dont un sous-terme de même fréquence est déjà mieux classé
    out, seen = [], set()
    for phrase, _ in ranked:
        kf = keyforms(phrase)
        if kf & seen:
            continue
        seen |= kf
        out.append(phrase)
        if len(out) >= limit:
            break
    return out


def extract_text(filename: str, data: bytes) -> str:
    ext = (filename or "").lower().rsplit(".", 1)[-1] if "." in (filename or "") else "txt"
    if ext == "pdf":
        try:
            import pypdf  # type: ignore
            r = pypdf.PdfReader(io.BytesIO(data))
            return "\n".join((p.extract_text() or "") for p in r.pages)
        except ImportError:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".pdf") as f:
                f.write(data); f.flush()
                return subprocess.run(["pdftotext", "-layout", f.name, "-"], capture_output=True, timeout=60).stdout.decode("utf-8", "replace")
    if ext == "docx":
        try:
            import docx  # type: ignore
            d = docx.Document(io.BytesIO(data))
            parts = [p.text for p in d.paragraphs]
            for t in d.tables:
                for row in t.rows:
                    parts.append(", ".join(c.text for c in row.cells))
            return "\n".join(parts)
        except ImportError:
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                xml = z.read("word/document.xml").decode("utf-8", "replace")
            return re.sub(r"<[^>]+>", " ", xml.replace("</w:p>", "\n"))
    if ext in ("txt", "csv", "md", "tsv", "text", ""):
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                continue
    raise ValueError("format non pris en charge : ." + ext)


def parse_upload(filename: str, data: bytes, limit: int = MAX_TERMS_PER_SUBMISSION) -> dict:
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError("fichier trop gros (max 5 Mo)")
    text = extract_text(filename, data)
    ext = (filename or "").lower().rsplit(".", 1)[-1]
    if ext in ("pdf", "docx") and not looks_like_list(text):
        mode, terms_text = "candidats", "\n".join(extract_candidates(text))
    elif looks_like_list(text):
        mode, terms_text = "liste", text
    else:
        mode, terms_text = "candidats", "\n".join(extract_candidates(text))
    r = parse_terms(terms_text, limit)
    r["mode"] = mode
    r["chars"] = len(text)
    return r


def edit_distance(a: str, b: str, cap: int = 3) -> int:
    """Levenshtein avec coupe (retourne cap+1 dès que dépassé)."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        if min(cur) > cap:
            return cap + 1
        prev = cur
    return prev[-1]


# Contrôles déterministes gratuits AVANT le LLM : écartent ce qui n'a manifestement pas sa place.
# Mots courants sans AUCUN sens aéronautique spécifique. Volontairement PAS : vent, vol, piste, avion, hélice,
# pilote, nuage… (sens aéro précis possible -> décision laissée au LLM dans le doute).
GENERIC_WORDS = set(norm(w) for w in """chose choses truc trucs machin bidule exemple exemples problème problèmes question questions
cas fois partie parties article articles page pages chapitre chapitres manière façon sorte genre personne personnes gens monde
oui non ok bonjour merci bonsoir salut voilà etc suite début fin liste tableau figure schéma texte mot mots phrase
maison voiture chien chat table chaise pain fromage""".split())
UNITS = set(norm(w) for w in """mètre mètres metre metres kilomètre kilomètres kilogramme kilogrammes gramme grammes litre litres seconde secondes
minute minutes heure heures jour jours degré degrés pourcent pourcentage m km kg g s h min l cm mm °c °f %""".split())
_NUM = re.compile(r"^[\d\s.,:/+\-°%]+$")
_NUM_UNIT = re.compile(r"^\d+(?:[.,]\d+)?\s*[a-zA-Z°%]{1,10}$")
_VERBISH = set("est sont doit doivent peut peuvent fait font faut ont il elle ils elles je tu nous vous on qui que ne pas sera seront était serait avez avons".split())


def free_discard(term: str, idx: "LexiconIndex"):
    """Écarte sans LLM. -> None | {motif, raison[, terme_proche, lien]}"""
    n = norm(term)
    words = n.split()
    if not n or _NUM.match(term.strip()):
        return {"motif": "nombre", "raison": "Un nombre ou une valeur seule n'est pas un terme de lexique."}
    if _NUM_UNIT.match(term.strip()):
        return {"motif": "valeur_chiffree", "raison": "Une valeur chiffrée avec unité n'est pas un terme de lexique."}
    if n in UNITS:
        return {"motif": "unite", "raison": "Unité courante du système international, déjà connue de tous (pas de fiche dédiée)."}
    if len(words) == 1 and (n in _STOP or n in GENERIC_WORDS):
        return {"motif": "mot_courant", "raison": "Mot courant de la langue, sans sens aéronautique spécifique."}
    if len(words) > 5 or (len(words) >= 3 and any(w in _VERBISH for w in words)):
        return {"motif": "fragment_phrase", "raison": "Fragment de phrase plutôt qu'un terme (trop long ou verbe conjugué)."}
    near = idx.typo_match(term)
    if near:
        return {"motif": "faute_de_frappe", "raison": "Alias probable / faute de frappe de « %s » (fiche existante)." % near,
                "terme_proche": near, "lien": idx.link(near)}
    return None


# ── 2. Index du lexique (gratuit) ────────────────────────────────────────────
def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class LexiconIndex:
    def __init__(self, lex_id: str):
        self.id = lex_id
        cfg = LEXICONS[lex_id]
        self.cfg = cfg
        full = ROOT / cfg["full"]
        self._mtime = full.stat().st_mtime
        sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "data")]
        try:
            gl = dict(_load_module(full, "glossaire_full_" + lex_id + str(int(self._mtime))).GLOSSAIRE)
        finally:
            del sys.path[:2]
        self.glossaire = gl
        slugmap = {}
        sm = ROOT / cfg["slug_dir"] / "slugmap.json"
        if sm.exists():
            slugmap = json.loads(sm.read_text("utf-8"))
        self.slugmap = slugmap
        self.exact: dict[str, str] = {}      # forme normalisée -> terme (terme lui-même ou variante)
        self.alias: dict[str, tuple] = {}    # synonymes/développés -> (terme, nature)
        for term, meta in gl.items():
            for f in keyforms(term):
                self.exact.setdefault(f, term)
        for term, meta in gl.items():
            for v in meta.get("variantes") or []:
                for f in keyforms(v):
                    self.exact.setdefault(f, term)
            for s in meta.get("synonymes") or []:
                for f in keyforms(s):
                    self.alias.setdefault(f, (term, "synonyme"))
        try:
            sys.path.insert(0, str(ROOT / "scripts"))
            from term_expansions import EXPANSIONS  # type: ignore
            for term, tup in EXPANSIONS.items():
                if term not in gl:
                    continue
                for e in tup[:2]:
                    if e:
                        for f in keyforms(re.split(r"\s+[—-]\s+", e)[-1]):
                            self.alias.setdefault(f, (term, "développé"))
                        for f in keyforms(e):
                            self.alias.setdefault(f, (term, "développé"))
        except Exception:
            pass
        finally:
            if sys.path and sys.path[0] == str(ROOT / "scripts"):
                sys.path.pop(0)
        self.words: dict[str, list] = {}     # mot normalisé -> termes (multi-mots) qui le contiennent
        for term in gl:
            n = norm(term)
            if " " in n:
                for w in set(n.split(" ")):
                    if len(w) > 3:
                        self.words.setdefault(w, []).append(term)
        fams: dict[str, int] = {}
        for meta in gl.values():
            if meta.get("famille"):
                fams[meta["famille"]] = fams.get(meta["famille"], 0) + 1
        self.families = dict(sorted(fams.items(), key=lambda kv: (-kv[1], kv[0])))
        self.family_labels = {f: family_label(f, ROOT) for f in self.families}
        self.no_family = sorted(t for t, m in gl.items() if not m.get("famille"))

    def family_info(self, examples: int = 3) -> list:
        """[{slug, label, n, exemples[<=3]}] — catalogue complet des familles existantes (pour le prompt et l'audit)."""
        mem: dict[str, list] = {}
        for t, m in self.glossaire.items():
            if m.get("famille"):
                mem.setdefault(m["famille"], []).append(t)
        return [{"slug": f, "label": self.family_labels.get(f, f), "n": n, "exemples": sorted(mem.get(f, []), key=lambda x: (len(x), x))[:examples]}
                for f, n in self.families.items()]

    def canon(self, raw: str):
        """Nom exact d'une fiche existante (terme, variante) ou None."""
        for f in keyforms(raw or ""):
            t = self.exact.get(f)
            if t and t in self.glossaire:
                return t
        return None

    # ── fiches voisines : TF-IDF local (pas d'index d'embeddings dans le projet) ──
    def _toks(self, s: str) -> list:
        out = []
        for w in norm(re.sub(r"<[^>]+>", " ", s or "")).split():
            if len(w) > 2 and w not in _STOP_N:
                out.append(singular(w))
        return out

    def _build_vecs(self):
        import math
        from collections import Counter
        docs, df = {}, Counter()
        for t, m in self.glossaire.items():
            c = Counter()
            for w in self._toks(t):
                c[w] += 3
            for v in m.get("variantes") or []:
                for w in self._toks(v):
                    c[w] += 2
            for w in self._toks(m.get("definition", "")):
                c[w] += 1
            for x in m.get("xrefs") or []:
                for w in self._toks(x if isinstance(x, str) else ""):
                    c[w] += 1
            docs[t] = c
            df.update(c.keys())
        n = len(docs)
        self._idf = {w: math.log((n + 1) / (d + 1)) + 1 for w, d in df.items()}
        self._vecs = {t: self._vec(c) for t, c in docs.items()}
        self._ndef = {t: " " + " ".join(self._toks(m.get("definition", ""))) + " " for t, m in self.glossaire.items()}

    def _vec(self, counter) -> dict:
        import math
        v = {w: (1 + math.log(c)) * self._idf.get(w, 1.0) for w, c in counter.items()}
        nrm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        return {w: x / nrm for w, x in v.items()}

    def similar(self, term: str, text: str = "", k: int = 12, exclude=()) -> list:
        """Les k fiches existantes les plus proches du terme (et de `text` : définition, commentaire…).
        Lexical (mots du terme, variantes, définitions, voir aussi) + similarité TF-IDF + fiches nommées dans `text`
        + 'retour de pertinence' (voisins des meilleurs résultats) quand on n'a pas de définition."""
        from collections import Counter
        if not hasattr(self, "_vecs"):
            self._build_vecs()
        own = {norm(term)}
        skip = {norm(x) for x in exclude} | own
        q = Counter()
        for w in self._toks(term):
            q[w] += 3
        for w in self._toks(text):
            q[w] += 1
        qv = self._vec(q)
        dot = lambda a, b: sum(x * b.get(w, 0.0) for w, x in a.items())
        tw = set(self._toks(term))
        forced = []
        if text:                                    # fiches explicitement nommées (ex. commentaire « comme bord d'attaque »)
            toks = norm(text).split()
            for n_ in (4, 3, 2, 1):
                for i in range(len(toks) - n_ + 1):
                    g = " ".join(toks[i:i + n_])
                    if len(g) >= 4 and g not in _STOP and g in self.exact and self.exact[g] in self.glossaire and norm(self.exact[g]) not in skip:
                        if self.exact[g] not in forced:
                            forced.append(self.exact[g])
        score = {}
        for t in self.glossaire:
            if norm(t) in skip:
                continue
            s = dot(qv, self._vecs[t])
            if tw and any(w in self._ndef[t] for w in tw if len(w) > 4):
                s += 0.5                            # le terme est mentionné dans la définition de la fiche
            score[t] = s
        if not text:                                # retour de pertinence : on élargit autour des 3 meilleurs
            top = sorted(score, key=score.get, reverse=True)[:3]
            top = [t for t in top if score[t] > 0]
            if top:
                cen = Counter()
                for t in top:
                    for w, x in self._vecs[t].items():
                        cen[w] += x
                import math
                nrm = math.sqrt(sum(x * x for x in cen.values())) or 1.0
                cv = {w: x / nrm for w, x in cen.items()}
                for t in score:
                    score[t] += 0.7 * dot(cv, self._vecs[t])
        ranked = forced[:k] + [t for t in sorted(score, key=lambda x: (-score[x], x)) if t not in forced and score[t] > 0.02]
        return ranked[:k]

    def neighbour_card(self, t: str) -> dict:
        m = self.glossaire[t]
        return {"terme": t, "lien": self.link(t), "famille": m.get("famille", "")}

    def link(self, term: str) -> str:
        slug = self.slugmap.get(term)
        return (self.cfg["base_url"] + slug + ".html") if slug else ""

    def neighbours(self, raw: str, limit: int = 3) -> list:
        """Termes existants (multi-mots) qui contiennent ce mot : indice gratuit, ne remplace pas l'analyse."""
        n = norm(raw)
        if " " in n or len(n) <= 3:
            return []
        out = []
        for f in {n, singular(n)}:
            for t in self.words.get(f, []):
                if t not in out:
                    out.append(t)
        return [{"terme": t, "lien": self.link(t)} for t in out[:limit]]

    def typo_match(self, raw: str):
        """Terme existant à distance d'édition <= 2 (<= 1 si 5-6 lettres ; jamais < 5 lettres, sigles exclus)
        -> terme | None. Les formes présentes (match exact) sont traitées avant."""
        n = norm(raw)
        if len(n) < 5 or (raw.strip().isupper() and len(n) < 7):
            return None
        maxd = 2 if len(n) >= 7 else 1
        if not hasattr(self, "_bylen"):
            self._bylen = {}
            for f, t in self.exact.items():
                self._bylen.setdefault(len(f), []).append((f, t))
        best = None
        for L in range(len(n) - maxd, len(n) + maxd + 1):
            for f, t in self._bylen.get(L, ()):
                d = edit_distance(n, f, maxd)
                if 1 <= d <= maxd and (best is None or d < best[0]):
                    best = (d, t)
        return best[1] if best else None

    def match(self, raw: str):
        """-> None | {"statut": "present"|"alias", "terme", "lien", "nature"}"""
        for f in keyforms(raw):
            t = self.exact.get(f)
            if t:
                return {"statut": "present", "terme": t, "lien": self.link(t), "nature": "terme/variante"}
        for f in keyforms(raw):
            a = self.alias.get(f)
            if a:
                return {"statut": "alias", "terme": a[0], "lien": self.link(a[0]), "nature": a[1]}
        return None


_idx_cache: dict = {}
_idx_lock = threading.Lock()


def get_index(lex_id: str) -> LexiconIndex:
    if lex_id not in LEXICONS:
        raise KeyError("lexique inconnu : " + lex_id)
    full = ROOT / LEXICONS[lex_id]["full"]
    mt = full.stat().st_mtime
    with _idx_lock:
        cur = _idx_cache.get(lex_id)
        if cur is None or cur._mtime != mt:
            cur = LexiconIndex(lex_id)
            _idx_cache[lex_id] = cur
        return cur


# ── Stockage SQLite ──────────────────────────────────────────────────────────
_db_lock = threading.RLock()


def db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DATA_DIR / "suggest.db"), timeout=30)
    con.row_factory = sqlite3.Row
    con.executescript("""
    CREATE TABLE IF NOT EXISTS cache(domain TEXT, key TEXT, data TEXT, model TEXT, ts REAL, PRIMARY KEY(domain,key));
    CREATE TABLE IF NOT EXISTS proposals(id INTEGER PRIMARY KEY AUTOINCREMENT, domain TEXT, key TEXT, term TEXT,
        status TEXT, data TEXT, job TEXT, ts REAL, upd REAL, UNIQUE(domain,key,status));
    CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, domain TEXT, state TEXT, total INTEGER, done INTEGER,
        results TEXT, info TEXT, ts REAL, upd REAL);
    CREATE TABLE IF NOT EXISTS ratelimit(ip TEXT, kind TEXT, ts REAL, n INTEGER);
    CREATE INDEX IF NOT EXISTS ratelimit_ip ON ratelimit(ip, kind, ts);
    CREATE TABLE IF NOT EXISTS proposal_versions(proposal_id INTEGER, v INTEGER, data TEXT, comment TEXT, model TEXT, ts REAL,
        PRIMARY KEY(proposal_id, v));
    CREATE TABLE IF NOT EXISTS costlog(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, job TEXT, model TEXT,
        n_terms INTEGER, tok_in INTEGER, tok_out INTEGER, usd REAL, secs REAL, ok INTEGER);
    """)
    return con


def _ipkey(ip: str) -> str:
    import hashlib
    return hashlib.sha256(("aerolex|" + ip).encode()).hexdigest()[:16]     # pas d'IP en clair en base


def rate_used(ip: str, kind: str, window: float) -> int:
    with _db_lock, db() as con:
        return int(con.execute("SELECT COALESCE(SUM(n),0) FROM ratelimit WHERE ip=? AND kind=? AND ts>?",
                               (_ipkey(ip), kind, time.time() - window)).fetchone()[0])


def rate_record(ip: str, kind: str, n: int = 1):
    with _db_lock, db() as con:
        con.execute("INSERT INTO ratelimit(ip,kind,ts,n) VALUES(?,?,?,?)", (_ipkey(ip), kind, time.time(), n))
        con.execute("DELETE FROM ratelimit WHERE ts<?", (time.time() - 2 * 86400,))


def llm_quota_remaining(ip: str) -> int:
    return max(0, min(LLM_TERMS_PER_IP_HOUR - rate_used(ip, "llm", 3600), LLM_TERMS_PER_IP_DAY - rate_used(ip, "llm", 86400)))


def cost_today() -> float:
    start = time.time() - 86400
    with _db_lock, db() as con:
        r = con.execute("SELECT COALESCE(SUM(usd),0) FROM costlog WHERE ts>?", (start,)).fetchone()
    return float(r[0])


# ── 4. LLM ───────────────────────────────────────────────────────────────────
def _xai_key() -> str | None:
    k = os.environ.get("XAI_API_KEY")
    if k:
        return k
    for p in (Path.home() / ".openclaw" / ".env",):
        try:
            for line in p.read_text("utf-8").splitlines():
                if line.startswith("XAI_API_KEY="):
                    return line.split("=", 1)[1].strip().strip("\"'")
        except OSError:
            pass
    return None


NEIGH_PER_TERM = 12        # fiches voisines passées au modèle (8 si le lot dépasse 4 termes : prompt borné)
MAX_VOIR_AUSSI = 8         # « voir aussi » proposés par version
MAX_VERSIONS = 10          # versions max d'une proposition (relances commentées)


def neighbours_ctx(lex_id: str, terms: list, texts: dict | None = None) -> dict:
    """{terme: [fiches voisines existantes]} — récupérées AVANT l'appel LLM (lexical + TF-IDF + voir aussi)."""
    idx = get_index(lex_id)
    k = NEIGH_PER_TERM if len(terms) <= 4 else 8
    return {t: idx.similar(t, (texts or {}).get(t, ""), k) for t in terms}


def _fiche_line(idx: "LexiconIndex", t: str) -> str:
    m = idx.glossaire[t]
    xr = [x for x in (m.get("xrefs") or []) if isinstance(x, str)][:4]
    return "  · %s | famille : %s | %s%s" % (t, m.get("famille") or "(aucune)", _plain(m.get("definition", ""), 150),
                                            (" | voir aussi : " + ", ".join(xr)) if xr else "")


def _item_json(it: dict) -> str:
    keep = ("definition", "famille", "famille_nouvelle", "famille_nouvelle_label", "famille_justification", "rattachements",
            "voir_aussi", "synonymes", "origine", "traduction", "confiance")
    return json.dumps({k: it.get(k) for k in keep if k in it}, ensure_ascii=False)


def build_prompt(lex_id: str, terms: list, families: dict, ctx: dict | None = None, previous: dict | None = None,
                 comment: str = "") -> list:
    cfg = LEXICONS[lex_id]
    idx = get_index(lex_id)
    if ctx is None:
        ctx = neighbours_ctx(lex_id, terms)
    fam_cat = "\n".join("  %s — %s (%d fiches) : %s" % (f["slug"], f["label"], f["n"], ", ".join(f["exemples"])) for f in idx.family_info())
    no_fam = ", ".join(idx.no_family)
    system = (
        "Tu es rédacteur de lexique pour AeroLex (" + cfg["label"] + "). Public : " + cfg["audience"] + ".\n"
        "Domaine couvert : " + cfg["scope"] + ".\n"
        "Pour CHAQUE terme fourni, renvoie un objet. Réponds UNIQUEMENT par un objet JSON "
        '{"items":[...]} avec exactement un item par terme, dans le même ordre, champs :\n'
        '  "terme": le terme tel que fourni,\n'
        '  "domaine": true/false (appartient au domaine ci-dessus),\n'
        '  "raison_domaine": 1 phrase courte,\n'
        '  "pertinent": true/false (mérite une fiche pour ce public ; faux si trop générique, trop rare, nom propre/ville, immatriculation),\n'
        '  "raison_pertinent": 1 phrase courte,\n'
        '  "origine": si sigle/abréviation, forme développée d\'origine (langue d\'origine), sinon "",\n'
        '  "traduction": si l\'origine est étrangère, traduction française du développé, sinon "",\n'
        '  "definition": 2 à 4 phrases claires, exactes, niveau ' + cfg["audience"] + ' (vide "" si domaine=false),\n'
        '  "famille": le SLUG d\'UNE famille existante (liste ci-dessous) dès qu\'elle convient, sinon "" ;\n'
        '  "famille_nouvelle": slug snake_case d\'une nouvelle famille UNIQUEMENT si aucune famille existante ne convient, sinon "" ;\n'
        '  "famille_nouvelle_label": libellé lisible en français de cette nouvelle famille (ex. « Structure de l\'aile », jamais un slug), sinon "" ;\n'
        '  "famille_justification": 1 à 2 phrases : pourquoi cette famille existante convient, ou pourquoi aucune ne convient et que cette nouvelle famille se justifie,\n'
        '  "rattachements": fiches EXISTANTES SANS FAMILLE (liste ci-dessous, noms exacts) qui devraient rejoindre la famille choisie/proposée (vide si aucune),\n'
        '  "voir_aussi": jusqu\'à 8 fiches EXISTANTES (noms exacts, voisines ou liste du lexique) à relier en « voir aussi »,\n'
        '  "synonymes": variantes, synonymes, alias, formes courantes (peut être vide),\n'
        '  "confiance": nombre 0..1 (ta certitude sur la définition).\n'
        "RÈGLES DE FAMILLE : regarde d'abord les fiches voisines fournies avec chaque terme et le catalogue des familles ; choisis une famille "
        "EXISTANTE dès qu'elle convient. Ne crée une nouvelle famille que si aucune ne convient ; dans ce cas, propose les fiches existantes sans famille "
        "qui devraient la rejoindre (ex. pour « emplanture » : bord d'attaque, bord de fuite, longeron, nervure, corde, profil). "
        "Les noms de fiches (voir_aussi, rattachements) doivent exister dans le lexique : n'invente rien.\n"
        "Pas de HTML, pas de markdown, pas de commentaire hors JSON. Sois exact : si tu ne connais pas un terme, "
        "mets confiance basse et définition vide plutôt que d'inventer.\n"
        "Familles existantes (slug — libellé (nombre de fiches) : 3 exemples) :\n" + fam_cat + "\n"
        "Fiches existantes SANS famille (" + str(len(idx.no_family)) + ") : " + no_fam
    )
    blocks = []
    for t in terms:
        near = [n for n in ctx.get(t, []) if n in idx.glossaire]
        blocks.append("- " + t + ("\n  Fiches voisines (terme | famille | début de définition | voir aussi) :\n" + "\n".join(_fiche_line(idx, n) for n in near)
                                  if near else "\n  Fiches voisines : aucune trouvée."))
    user = "Termes :\n" + "\n".join(blocks)
    if previous is not None:
        user += ("\n\nTa proposition précédente pour ce terme (JSON) :\n" + _item_json(previous) +
                 "\n\nCommentaire du relecteur : " + comment.strip()[:1500] +
                 "\n\nRéponds par une NOUVELLE version complète (même format, un seul item) qui tient compte du commentaire, "
                 "en restant exacte ; ne change que ce que le commentaire ou les fiches voisines justifient.")
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _post_json(url: str, body: dict, headers: dict, timeout: int) -> dict:
    req = urllib.request.Request(url, json.dumps(body).encode("utf-8"), headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def _call_provider(name: str, messages: list, n_terms: int) -> tuple:
    """-> (content, usage_dict, model, usd)"""
    if name == "xai":
        key = _xai_key()
        if not key:
            raise RuntimeError("XAI_API_KEY absente")
        body = {"model": PRIMARY_MODEL, "messages": messages, "temperature": 0.2,
                "response_format": {"type": "json_object"}, "reasoning_effort": REASONING_EFFORT}
        r = _post_json(XAI_URL, body, {"Authorization": "Bearer " + key, "Content-Type": "application/json"}, LLM_TIMEOUT)
        u = r.get("usage") or {}
        tin = int(u.get("prompt_tokens", 0))
        tout = int(u.get("completion_tokens", 0)) + int((u.get("completion_tokens_details") or {}).get("reasoning_tokens", 0))
        usd = (u.get("cost_in_usd_ticks") or 0) / 1e10 or (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
        return r["choices"][0]["message"]["content"], {"in": tin, "out": tout}, PRIMARY_MODEL, usd
    body = {"model": LOCAL_MODEL, "messages": messages, "temperature": 0.2,
            "response_format": {"type": "json_object"}, "max_tokens": 6000}
    r = _post_json(LOCAL_URL, body, {"Content-Type": "application/json"}, 300)
    u = r.get("usage") or {}
    return r["choices"][0]["message"]["content"], {"in": int(u.get("prompt_tokens", 0)), "out": int(u.get("completion_tokens", 0))}, LOCAL_MODEL + "@local", 0.0


def _strip_json(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s)
    if not s.startswith("{"):
        a, b = s.find("{"), s.rfind("}")
        if a >= 0 and b > a:
            s = s[a:b + 1]
    return s


def _b(v) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("true", "oui", "vrai", "yes", "1")
    return bool(v)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm(s)).strip("_")[:50]


def _names(v, idx, own: str, limit: int, no_family_only: bool = False) -> list:
    """Liste de noms de fiches -> noms EXACTS de fiches existantes (inconnues et doublons écartés)."""
    if isinstance(v, str):
        v = re.split(r"[,;]", v)
    out = []
    for x in v if isinstance(v, list) else []:
        t = idx.canon(x) if idx and isinstance(x, str) else None
        if not t or norm(t) == norm(own) or t in out:
            continue
        if no_family_only and idx.glossaire[t].get("famille"):
            continue
        out.append(t)
    return out[:limit]


def validate_item(it: dict, asked: str, families: dict, idx: "LexiconIndex | None" = None) -> dict:
    """Contrat de sortie LLM -> item normalisé ; lève ValueError si inutilisable."""
    if not isinstance(it, dict):
        raise ValueError("item non-objet")
    conf = it.get("confiance", 0)
    try:
        conf = max(0.0, min(1.0, float(conf)))
    except (TypeError, ValueError):
        conf = 0.0
    fam = (it.get("famille") or "").strip()
    fam_new = (it.get("famille_nouvelle") or "").strip()
    fam_label = str(it.get("famille_nouvelle_label") or "").strip()[:80]
    if fam and fam not in families:
        # famille inventée : on la rétrograde en proposition de nouvelle famille
        fam_new, fam = fam_new or fam, ""
    if fam_new:
        if not re.fullmatch(r"[a-z0-9_]+", fam_new):          # libellé lisible donné à la place du slug
            fam_label = fam_label or fam_new
            fam_new = _slug(fam_new)
        if fam_new in families:                                # la « nouvelle » famille existe déjà
            fam, fam_new, fam_label = fam or fam_new, "", ""
    if not fam_new:
        fam_label = ""
    elif not fam_label:
        fam_label = family_label(fam_new)
    syn = it.get("synonymes") or []
    if isinstance(syn, str):
        syn = [s for s in re.split(r"[,;]", syn)]
    syn = [clean_term(s) for s in syn if isinstance(s, str) and clean_term(s)]
    out = {
        "terme": asked,
        "domaine": _b(it.get("domaine")),
        "raison_domaine": str(it.get("raison_domaine") or "")[:300],
        "pertinent": _b(it.get("pertinent")),
        "raison_pertinent": str(it.get("raison_pertinent") or "")[:300],
        "origine": str(it.get("origine") or "").strip()[:200],
        "traduction": str(it.get("traduction") or "").strip()[:200],
        "definition": re.sub(r"<[^>]+>", "", str(it.get("definition") or "")).strip(),
        "famille": fam,
        "famille_nouvelle": fam_new[:60],
        "famille_nouvelle_label": fam_label,
        "famille_justification": str(it.get("famille_justification") or "").strip()[:400],
        "rattachements": _names(it.get("rattachements"), idx, asked, 15, True),
        "voir_aussi": _names(it.get("voir_aussi"), idx, asked, MAX_VOIR_AUSSI),
        "synonymes": list(dict.fromkeys(syn))[:10],
        "confiance": round(conf, 2),
    }
    if out["domaine"] and out["pertinent"] and len(out["definition"]) < 20:
        out["pertinent"] = False
        out["raison_pertinent"] = (out["raison_pertinent"] + " (définition manquante : à rédiger)").strip()
    return out


def parse_llm(content: str, asked: list, families: dict, idx: "LexiconIndex | None" = None) -> dict:
    """-> {terme_demandé: item validé}. Associe par ordre, repli par forme normalisée."""
    obj = json.loads(_strip_json(content))
    items = obj.get("items") if isinstance(obj, dict) else obj
    if not isinstance(items, list):
        if isinstance(obj, dict) and obj.get("definition") is not None and len(asked) == 1:
            items = [obj]                     # un seul item renvoyé sans enveloppe
        else:
            raise ValueError("clé items absente")
    by_norm = {}
    for it in items:
        if isinstance(it, dict) and it.get("terme"):
            by_norm[norm(str(it["terme"]))] = it
    out = {}
    for i, t in enumerate(asked):
        it = by_norm.get(norm(t)) or (items[i] if i < len(items) and len(items) == len(asked) else None)
        if it is None:
            continue
        try:
            out[t] = validate_item(it, t, families, idx)
        except ValueError:
            continue
    return out


def llm_batch(lex_id: str, terms: list, families: dict, job: str = "", build=None) -> tuple:
    """Un appel LLM pour <= BATCH_SIZE termes. Repli : retry -> Qwopus local.
    `build(terms, ctx) -> messages` : prompt personnalisé (relance commentée). Par défaut build_prompt + fiches voisines.
    -> (résultats {terme: item}, [erreurs], coût_usd)"""
    idx = get_index(lex_id)
    build = build or (lambda ts, cx: build_prompt(lex_id, ts, families, cx))
    ctx = neighbours_ctx(lex_id, terms)
    messages = build(terms, ctx)
    errors, total_usd = [], 0.0
    plan = ["xai", "xai", "local"]
    results: dict = {}
    for prov in plan:
        if cost_today() >= DAILY_USD_CAP and prov == "xai":
            errors.append("plafond quotidien atteint (%.2f USD)" % DAILY_USD_CAP)
            continue
        t0 = time.time()
        try:
            content, usage, model, usd = _call_provider(prov, messages, len(terms))
            got = parse_llm(content, terms, families, idx)
            ok = len(got) > 0
            with _db_lock, db() as con:
                con.execute("INSERT INTO costlog(ts,job,model,n_terms,tok_in,tok_out,usd,secs,ok) VALUES(?,?,?,?,?,?,?,?,?)",
                            (time.time(), job, model, len(terms), usage["in"], usage["out"], usd, time.time() - t0, int(ok)))
            total_usd += usd
            for k, v in got.items():
                v["modele"] = model
                v["voisins_consultes"] = [idx.neighbour_card(n) for n in ctx.get(k, []) if n in idx.glossaire]
                results[k] = v
            missing = [x for x in terms if x not in results]
            if not missing:
                return results, errors, total_usd
            terms = missing                     # on ne redemande que les manquants
            ctx = neighbours_ctx(lex_id, terms)
            messages = build(terms, ctx)
            errors.append("%d terme(s) manquant(s) dans la réponse de %s" % (len(missing), model))
        except Exception as e:  # réseau, HTTP, JSON invalide…
            errors.append("%s: %s" % (prov, str(e)[:160]))
    return results, errors, total_usd


# ── Pipeline complet (entonnoir) ─────────────────────────────────────────────
def cache_get(lex_id: str, key: str):
    with _db_lock, db() as con:
        r = con.execute("SELECT data FROM cache WHERE domain=? AND key=?", (lex_id, key)).fetchone()
    return json.loads(r[0]) if r else None


def cache_put(lex_id: str, key: str, item: dict):
    with _db_lock, db() as con:
        con.execute("INSERT OR REPLACE INTO cache(domain,key,data,model,ts) VALUES(?,?,?,?,?)",
                    (lex_id, key, json.dumps(item, ensure_ascii=False), item.get("modele", ""), time.time()))


def funnel_free(lex_id: str, terms: list, skip_checks: bool = False) -> tuple:
    """Étapes 2 et 3 (gratuites) + contrôles déterministes. -> (résultats par terme, à_envoyer_au_LLM)"""
    idx = get_index(lex_id)
    res, todo = {}, []
    for t in terms:
        m = idx.match(t)
        if m:
            res[t] = {"terme": t, **m}
            continue
        if not skip_checks:
            dsc = free_discard(t, idx)
            if dsc:
                res[t] = {"terme": t, "statut": "ecarte", "verdict": "ecarte", **dsc}
                continue
        c = cache_get(lex_id, ckey(t))
        if c:
            res[t] = {"terme": t, "statut": "analyse", "cache": True, **{k: v for k, v in c.items() if k != "terme"}}
            nb = idx.neighbours(t)
            if nb:
                res[t]["voisins"] = nb
            continue
        res[t] = {"terme": t, "statut": "attente"}
        nb = idx.neighbours(t)
        if nb:
            res[t]["voisins"] = nb
        todo.append(t)
    return res, todo


def classify(item: dict) -> str:
    if not item.get("domaine"):
        return "hors_domaine"
    if not item.get("pertinent"):
        return "non_pertinent"
    return "a_valider"


NOT_DATA = ("statut", "cache", "terme", "verdict", "voisins")


def store_outcomes(lex_id: str, res: dict, job: str):
    """Verdicts -> file : à valider (pending) ; écartés automatiquement (discarded, repêchables)."""
    for t, r in res.items():
        if r.get("statut") == "analyse":
            r["verdict"] = classify(r)
            enqueue_proposal(lex_id, t, {k: v for k, v in r.items() if k not in NOT_DATA}, job,
                             "pending" if r["verdict"] == "a_valider" else "discarded")
        elif r.get("statut") == "ecarte":
            enqueue_proposal(lex_id, t, {k: v for k, v in r.items() if k not in NOT_DATA}, job, "discarded")


def apply_llm_results(lex_id: str, res: dict, got: dict, job: str):
    for t, item in got.items():
        cache_put(lex_id, ckey(t), item)
        nb = res.get(t, {}).get("voisins")
        res[t] = {"terme": t, "statut": "analyse", "cache": False, **{k: v for k, v in item.items() if k != "terme"}}
        if nb:
            res[t]["voisins"] = nb
    store_outcomes(lex_id, res, job)


def enqueue_proposal(lex_id: str, term: str, data: dict, job: str, status: str = "pending"):
    key = ckey(term)
    now = time.time()
    with _db_lock, db() as con:
        if con.execute("SELECT 1 FROM proposals WHERE domain=? AND key=? AND status='pending'", (lex_id, key)).fetchone():
            return
        if status == "pending":
            con.execute("DELETE FROM proposals WHERE domain=? AND key=? AND status='discarded'", (lex_id, key))
        con.execute("INSERT OR REPLACE INTO proposals(domain,key,term,status,data,job,ts,upd) VALUES(?,?,?,?,?,?,?,?)",
                    (lex_id, key, term, status, json.dumps(data, ensure_ascii=False), job, now, now))


QUOTA_MSG = ("Limite d'analyses atteinte pour cette connexion (%d termes/heure, %d/jour) : "
             "réessayez plus tard. Les termes déjà connus ne comptent pas." % (LLM_TERMS_PER_IP_HOUR, LLM_TERMS_PER_IP_DAY))


def new_job(lex_id: str, terms: list, info: dict, ip: str | None = None) -> str:
    jid = secrets.token_hex(8)
    res, todo = funnel_free(lex_id, terms)
    if ip and todo:                       # quota LLM par IP (soumission publique)
        rem = llm_quota_remaining(ip)
        for t in todo[rem:]:
            res[t] = {"terme": t, "statut": "limite", "raison": QUOTA_MSG}
        if len(todo) > rem:
            info = dict(info, limite_atteinte=True)
        todo = todo[:rem]
        if todo:
            rate_record(ip, "llm", len(todo))
    store_outcomes(lex_id, res, jid)
    info = dict(info, todo=todo, free=len(terms) - len(todo))
    now = time.time()
    with _db_lock, db() as con:
        con.execute("INSERT INTO jobs(id,domain,state,total,done,results,info,ts,upd) VALUES(?,?,?,?,?,?,?,?,?)",
                    (jid, lex_id, "running" if todo else "done", len(terms), len(terms) - len(todo),
                     json.dumps(res, ensure_ascii=False), json.dumps(info, ensure_ascii=False), now, now))
    return jid


def batch_size(n: int) -> int:
    """Latence vs coût : un appel de 20 termes dure ~25 s (sortie longue). En dessous de
    PARALLEL_BATCHES*BATCH_SIZE termes on découpe en PARALLEL_BATCHES appels simultanés ;
    au-delà, lots pleins de BATCH_SIZE (le prompt système est mis en cache côté xAI)."""
    if n >= PARALLEL_BATCHES * BATCH_SIZE:
        return BATCH_SIZE
    return max(2, -(-n // PARALLEL_BATCHES))


def run_job(jid: str):
    """Traite les termes à envoyer au LLM, par lots, en parallèle ; progression persistée."""
    with _db_lock, db() as con:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    lex_id = row["domain"]
    res = json.loads(row["results"])
    info = json.loads(row["info"])
    todo = info.get("todo", [])
    families = get_index(lex_id).families
    size = batch_size(len(todo))
    batches = [todo[i:i + size] for i in range(0, len(todo), size)]
    lock = threading.Lock()
    t0 = time.time()

    def work(b):
        got, errs, usd = llm_batch(lex_id, b, families, jid)
        with lock:
            apply_llm_results(lex_id, res, got, jid)
            info["usd"] = round(info.get("usd", 0.0) + usd, 6)
            info.setdefault("errors", []).extend(errs)
            for t in b:
                if res[t].get("statut") == "attente":
                    res[t]["statut"] = "erreur"
                    res[t]["erreur"] = "Analyse momentanément indisponible (service saturé ou plafond de coût atteint) : réessayez plus tard."
                    res[t]["detail"] = "; ".join(errs)[:200] or "pas de réponse"
            done = sum(1 for r in res.values() if r.get("statut") != "attente")
            with _db_lock, db() as con:
                con.execute("UPDATE jobs SET done=?,results=?,info=?,upd=? WHERE id=?",
                            (done, json.dumps(res, ensure_ascii=False), json.dumps(info, ensure_ascii=False), time.time(), jid))

    try:
        with cf.ThreadPoolExecutor(PARALLEL_BATCHES) as ex:
            list(ex.map(work, batches))
    finally:
        info["secs"] = round(time.time() - t0, 1)
        n_llm = len(todo)
        info["usd_par_terme"] = round(info.get("usd", 0.0) / n_llm, 6) if n_llm else 0
        with _db_lock, db() as con:
            con.execute("UPDATE jobs SET state='done',info=?,upd=? WHERE id=?", (json.dumps(info, ensure_ascii=False), time.time(), jid))


def job_view(jid: str, full: bool = True):
    with _db_lock, db() as con:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not row:
        return None
    info = json.loads(row["info"])
    info.pop("todo", None)
    if not full:                          # visiteur anonyme : pas de détail technique ni de coût
        info["errors"] = len(info.get("errors") or [])
        info.pop("usd", None); info.pop("usd_par_terme", None)
    res = json.loads(row["results"])
    return {"id": row["id"], "domaine": row["domain"], "etat": row["state"], "total": row["total"], "fait": row["done"],
            "info": info, "resultats": list(res.values())}


def submit(lex_id: str, text: str = "", terms: list | None = None, background: bool = True, ip: str | None = None, full: bool = True) -> dict:
    """Point d'entrée unique (unitaire ET lot). -> vue du job (terminée si ≤ UNIT_SYNC_MAX à analyser)."""
    if lex_id not in LEXICONS:
        raise KeyError("lexique inconnu : " + lex_id)
    if terms is None:
        p = parse_terms(text, MAX_TERMS_PER_SUBMISSION)
    else:
        p = parse_terms(", ".join(terms), MAX_TERMS_PER_SUBMISSION)
    if not p["terms"]:
        raise ValueError("aucun terme exploitable")
    info = {"doublons": p["duplicates"], "rejetes": p["rejected"], "au_dela_limite": len(p["over_limit"])}
    jid = new_job(lex_id, p["terms"], info, ip)
    v = job_view(jid, full)
    with _db_lock, db() as con:
        n_todo = len(json.loads(con.execute("SELECT info FROM jobs WHERE id=?", (jid,)).fetchone()["info"]).get("todo", []))
    if n_todo == 0:
        return v
    if n_todo <= UNIT_SYNC_MAX or not background:
        run_job(jid)
        return job_view(jid, full)
    threading.Thread(target=run_job, args=(jid,), daemon=True, name="suggest-" + jid).start()
    return v


# ── 3. File de propositions + validation ─────────────────────────────────────
def list_proposals(lex_id: str | None, status: str = "pending") -> list:
    q, a = "SELECT * FROM proposals WHERE status=?", [status]
    if lex_id:
        q += " AND domain=?"; a.append(lex_id)
    with _db_lock, db() as con:
        rows = con.execute(q + " ORDER BY ts DESC", a).fetchall()
        vers = {}
        for v in con.execute("SELECT proposal_id,v,comment,model,ts FROM proposal_versions ORDER BY proposal_id, v"):
            vers.setdefault(v["proposal_id"], []).append({"v": v["v"], "commentaire": v["comment"], "modele": v["model"], "ts": v["ts"]})
    out = []
    for r in rows:
        d = json.loads(r["data"])
        liens = {}
        if r["domain"] in LEXICONS and status == "pending":      # liens vers les fiches citées (voir aussi, rattachements)
            idx = get_index(r["domain"])
            for n in list(d.get("voir_aussi") or []) + list(d.get("rattachements") or []):
                if n in idx.glossaire:
                    liens[n] = idx.link(n)
        out.append({"id": r["id"], "domaine": r["domain"], "terme": r["term"], "statut": r["status"], "data": d, "job": r["job"],
                    "ts": r["ts"], "versions": vers.get(r["id"], []), "liens": liens})
    return out


def edit_proposal(pid: int, term: str | None, data: dict) -> dict:
    allowed = {"definition", "famille", "famille_nouvelle", "famille_nouvelle_label", "famille_justification", "synonymes",
               "origine", "traduction", "voir_aussi", "rattachements_retenus"}
    with _db_lock, db() as con:
        r = con.execute("SELECT * FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
        if not r:
            raise KeyError("proposition introuvable")
        cur = json.loads(r["data"])
        idx = get_index(r["domain"])
        for k, v in data.items():
            if k in allowed:
                cur[k] = v
        if isinstance(cur.get("synonymes"), str):
            cur["synonymes"] = [clean_term(s) for s in cur["synonymes"].split(",") if clean_term(s)]
        if "voir_aussi" in data:
            cur["voir_aussi"] = _names(cur.get("voir_aussi"), idx, r["term"], MAX_VOIR_AUSSI)
        if "rattachements_retenus" in data:      # uniquement des fiches existantes sans famille
            cur["rattachements_retenus"] = _names(cur.get("rattachements_retenus"), idx, r["term"], 15, True)
        con.execute("UPDATE proposals SET data=?, term=?, upd=? WHERE id=?",
                    (json.dumps(cur, ensure_ascii=False), clean_term(term) if term else r["term"], time.time(), pid))
        cv = cur.get("version")
        if cv:                                   # la version courante suit les modifications manuelles
            con.execute("UPDATE proposal_versions SET data=? WHERE proposal_id=? AND v=?", (json.dumps(cur, ensure_ascii=False), pid, cv))
    return {"ok": True}


# ── Relance commentée + historique des versions ─────────────────────────────
def _ensure_v1(con, r) -> dict:
    """Garantit que la proposition courante est enregistrée comme version (v1 au premier appel)."""
    cur = json.loads(r["data"])
    if not cur.get("version"):
        cur["version"] = 1
        con.execute("INSERT OR REPLACE INTO proposal_versions(proposal_id,v,data,comment,model,ts) VALUES(?,?,?,?,?,?)",
                    (r["id"], 1, json.dumps(cur, ensure_ascii=False), "", cur.get("modele", ""), r["ts"]))
        con.execute("UPDATE proposals SET data=? WHERE id=?", (json.dumps(cur, ensure_ascii=False), r["id"]))
    return cur


def relaunch_proposal(pid: int, comment: str) -> dict:
    """Le modèle reçoit sa proposition précédente + le commentaire + les fiches voisines et renvoie une nouvelle version
    (v2, v3…). N'utilise pas le cache et le remplace ; soumise au plafond de coût (llm_batch) ; session relecteur exigée par l'API."""
    comment = (comment or "").strip()
    if len(comment) < 3:
        raise ValueError("commentaire vide : écrivez ce que le modèle doit corriger")
    with _db_lock, db() as con:
        r = con.execute("SELECT * FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
        if not r:
            raise KeyError("proposition introuvable")
        cur = _ensure_v1(con, r)
        nmax = con.execute("SELECT MAX(v) FROM proposal_versions WHERE proposal_id=?", (pid,)).fetchone()[0] or 1
    if nmax >= MAX_VERSIONS:
        raise ValueError("nombre maximal de versions atteint (%d) : modifiez la fiche à la main" % MAX_VERSIONS)
    term, dom = r["term"], r["domain"]
    idx = get_index(dom)
    text = " ".join([cur.get("definition", ""), comment])

    used: dict = {}

    def build(ts, _cx):                          # voisins recalculés avec la définition précédente + le commentaire
        cx = {x: idx.similar(x, text, NEIGH_PER_TERM) for x in ts}
        used.update(cx)
        return build_prompt(dom, ts, idx.families, cx, previous=cur, comment=comment)

    got, errs, usd = llm_batch(dom, [term], idx.families, "relance:%d" % pid, build=build)
    if term not in got:
        raise ValueError("relance impossible : " + ("; ".join(errs)[:200] or "pas de réponse"))
    item = {k: v for k, v in got[term].items() if k not in NOT_DATA}
    for k in ("repeche", "erreur_validation"):
        item.pop(k, None)
    item["rattachements_retenus"] = list(item.get("rattachements") or [])
    item["voisins_consultes"] = [idx.neighbour_card(n) for n in used.get(term, []) if n in idx.glossaire]    # ceux réellement passés au modèle
    with _db_lock, db() as con:
        nv = (con.execute("SELECT MAX(v) FROM proposal_versions WHERE proposal_id=?", (pid,)).fetchone()[0] or 1) + 1
        item["version"] = nv
        con.execute("INSERT INTO proposal_versions(proposal_id,v,data,comment,model,ts) VALUES(?,?,?,?,?,?)",
                    (pid, nv, json.dumps(item, ensure_ascii=False), comment, item.get("modele", ""), time.time()))
        con.execute("UPDATE proposals SET data=?, upd=? WHERE id=?", (json.dumps(item, ensure_ascii=False), time.time(), pid))
        con.execute("DELETE FROM cache WHERE domain=? AND key=?", (dom, r["key"]))      # cache de ce terme invalidé
    return {"ok": True, "version": nv, "usd": usd}


def revert_proposal(pid: int, v: int) -> dict:
    with _db_lock, db() as con:
        r = con.execute("SELECT * FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
        if not r:
            raise KeyError("proposition introuvable")
        row = con.execute("SELECT data FROM proposal_versions WHERE proposal_id=? AND v=?", (pid, int(v))).fetchone()
        if not row:
            raise KeyError("version introuvable")
        d = json.loads(row["data"])
        d["version"] = int(v)
        con.execute("UPDATE proposals SET data=?, upd=? WHERE id=?", (json.dumps(d, ensure_ascii=False), time.time(), pid))
    return {"ok": True, "version": int(v)}


def reject_proposal(pid: int) -> dict:
    with _db_lock, db() as con:
        # statut rejected unique par (domain,key) : on remplace une éventuelle ancienne ligne
        r = con.execute("SELECT domain,key FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
        if not r:
            raise KeyError("proposition introuvable")
        con.execute("DELETE FROM proposals WHERE domain=? AND key=? AND status='rejected'", (r["domain"], r["key"]))
        con.execute("UPDATE proposals SET status='rejected', upd=? WHERE id=?", (time.time(), pid))
    return {"ok": True}


def rescue_proposal(pid: int) -> dict:
    """Repêche un terme écarté automatiquement -> file « À valider ».
    Écarté par le LLM : on réutilise son analyse. Écarté par un contrôle gratuit : analyse LLM forcée."""
    with _db_lock, db() as con:
        r = con.execute("SELECT * FROM proposals WHERE id=? AND status='discarded'", (pid,)).fetchone()
    if not r:
        raise KeyError("terme écarté introuvable")
    d = json.loads(r["data"])
    if "definition" not in d:             # écarté sans LLM : on l'analyse maintenant (relecteur authentifié)
        got, errs, usd = llm_batch(r["domain"], [r["term"]], get_index(r["domain"]).families, "rescue")
        if r["term"] not in got:
            raise ValueError("analyse impossible : " + "; ".join(errs)[:200])
        d = {k: v for k, v in got[r["term"]].items() if k not in NOT_DATA}
        cache_put(r["domain"], r["key"], got[r["term"]])
    d["repeche"] = True
    now = time.time()
    with _db_lock, db() as con:
        con.execute("DELETE FROM proposals WHERE domain=? AND key=? AND status='pending'", (r["domain"], r["key"]))
        con.execute("UPDATE proposals SET status='pending', data=?, upd=? WHERE id=?", (json.dumps(d, ensure_ascii=False), now, pid))
    return {"ok": True}


# ── Contrôle de cohérence AVANT écriture (clic « Valider ») ─────────────────
_DEV_STOP = set(norm(w) for w in "of the and for to in on at de du des la le les à a au aux et en pour sur d l un une by with".split())
_ABBREV = re.compile(r"\b(env|ex|etc|cf|fig|max|min|ft|kt|nm|hpa|qnh|approx|vs|resp|c-à-d|càd)\.", re.I)


def count_sentences(text: str) -> int:
    t = re.sub(r"<[^>]+>", "", text or "")
    t = _ABBREV.sub(lambda m: m.group(1), t)
    t = re.sub(r"(\d)\.(\d)", r"\1\2", t)
    return len([x for x in re.split(r"[.!?…]+(?:\s+|$)", t.strip()) if len(x.strip()) > 2])


def _subseq(sub: str, word: str) -> bool:
    it = iter(word)
    return all(c in it for c in sub)


def acronym_matches(sig: str, dev: str) -> bool:
    """Initiales du développé = lettres du sigle (mots vides facultatifs ; un mot peut fournir 1-3 lettres
    (la 1re = son initiale) : NOTAM = NOtice To AirMen). Vrai pour le développé anglais OU français."""
    a = re.sub(r"[^a-z0-9]", "", norm(sig))
    dev = re.sub(r"\([^)]*\)", " ", dev or "")
    words = [w for w in re.split(r"[\s\-/]+", norm(dev)) if w]
    if not a or not words:
        return False
    from functools import lru_cache

    @lru_cache(None)
    def dp(i, j):
        if i == len(words):
            return j == len(a)
        w = words[i]
        if w in _DEV_STOP and dp(i + 1, j):
            return True
        for k in range(1, min(3, len(w)) + 1):
            seg = a[j:j + k]
            if len(seg) == k and seg[0] == w[0] and _subseq(seg[1:], w[1:]) and dp(i + 1, j + k):
                return True
        return False
    return dp(0, 0)


def related_fiches(idx: "LexiconIndex", term: str, d: dict, limit: int = 3) -> list:
    """Fiches existantes les plus proches : termes voisins, quasi-homonyme, fiches citées dans la définition/le développé."""
    out = [n["terme"] for n in idx.neighbours(term, 3)]
    near = idx.typo_match(term)
    if near:
        out.append(near)
    text = norm(" ".join([d.get("definition", ""), d.get("origine", ""), d.get("traduction", "")]))
    toks = text.split()
    for n in (3, 2, 1):
        for i in range(len(toks) - n + 1):
            g = " ".join(toks[i:i + n])
            if len(g) >= 4 and g not in _STOP and g in idx.exact:
                out.append(idx.exact[g])
    for e in (d.get("origine"), d.get("traduction")):
        if e:
            for f in keyforms(e):
                a = idx.alias.get(f)
                if a:
                    out.append(a[0])
    seen, res = {norm(term)}, []
    for t in out:
        if norm(t) in seen or t not in idx.glossaire:
            continue
        seen.add(norm(t)); res.append(t)
    return res[:limit]


def _plain(s: str, n: int = 450) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s or "")).strip()[:n]


def coherence_llm(messages: list) -> dict:
    """Appel court : grok-4.3 (reasoning none) puis Qwopus local. -> dict JSON ; lève si tout échoue."""
    last = None
    for prov in ("xai", "local"):
        if prov == "xai" and cost_today() >= DAILY_USD_CAP:
            continue
        t0 = time.time()
        try:
            content, usage, model, usd = _call_provider(prov, messages, 1)
            with _db_lock, db() as con:
                con.execute("INSERT INTO costlog(ts,job,model,n_terms,tok_in,tok_out,usd,secs,ok) VALUES(?,?,?,?,?,?,?,?,?)",
                            (time.time(), "coherence", model, 1, usage["in"], usage["out"], usd, time.time() - t0, 1))
            return json.loads(_strip_json(content))
        except Exception as e:
            last = e
    raise RuntimeError("contrôle de cohérence indisponible : %s" % (str(last)[:120] if last else "plafond atteint"))


def check_proposal(row, run_llm: bool = True) -> dict:
    """Contrôle de cohérence d'une proposition AVANT écriture. -> {ok, controles:[{nom,statut ok|warn|ko,detail}], bloquants, avertissements, fiches_liees}"""
    dom, term, d = row["domain"], row["term"], json.loads(row["data"])
    idx = get_index(dom)
    ctl = []

    def add(nom, statut, detail=""):
        ctl.append({"nom": nom, "statut": statut, "detail": detail})

    m = idx.match(term)                                    # re-vérifié contre l'index COURANT, alias compris
    if m:
        add("Terme inexistant", "ko", "« %s » existe déjà (%s : %s)." % (term, "alias" if m["statut"] == "alias" else "fiche", m["terme"]))
    else:
        near = idx.typo_match(term)
        add("Terme inexistant", "warn" if near else "ok", ("très proche de « %s » (faute de frappe ?)" % near) if near else "")
    fam, fam_new = d.get("famille") or "", d.get("famille_nouvelle") or ""
    raw_att = d.get("rattachements_retenus") or []
    att = _names(raw_att, idx, term, 15, True)
    if fam and fam in idx.families:
        add("Famille", "ok", "%s (%s)" % (idx.family_labels.get(fam, fam), fam))
    elif fam_new:
        lab = d.get("famille_nouvelle_label") or family_label(fam_new)
        just = (d.get("famille_justification") or "").strip()
        if att and just:
            add("Famille", "ok", "nouvelle famille « %s » — %s" % (lab, just))
        elif att:
            add("Famille", "warn", "nouvelle famille « %s » sans justification écrite (%d fiche(s) rattachée(s))." % (lab, len(att)))
        else:
            add("Famille", "warn", "nouvelle famille « %s » proposée : à justifier (aucune fiche existante à rattacher)." % lab)
    else:
        add("Famille", "ko", "aucune famille (ni existante, ni nouvelle justifiée).")
    if att:
        add("Rattachements", "ok", "%d fiche(s) sans famille rejoindront la famille : %s" % (len(att), ", ".join(att)))
    if len(att) < len(raw_att):
        add("Rattachements", "warn", "%d fiche(s) cochée(s) ignorée(s) (inconnue ou déjà dans une famille)." % (len(raw_att) - len(att)))
    definition = (d.get("definition") or "").strip()
    if not definition:
        add("Définition", "ko", "définition vide.")
    else:
        ns = count_sentences(definition)
        words = [w for w in norm(definition).split() if len(w) > 3 and w not in _STOP and w not in set(norm(term).split())]
        if ns < 2 or ns > 4:
            add("Définition", "ko", "%d phrase(s) : il en faut 2 à 4." % ns)
        elif len(set(words)) < 4 or norm(definition).startswith(norm(term) + " est " + norm(term)):
            add("Définition", "ko", "circulaire : le terme sert seul d'explication.")
        else:
            add("Définition", "ok", "%d phrases." % ns)
    t0 = term.strip()
    if re.fullmatch(r"[A-Z0-9][A-Z0-9/\-]{1,7}", t0) and re.search(r"[A-Z]{2}", t0):
        devs = [x for x in (d.get("origine"), d.get("traduction")) if x]
        if not devs:
            add("Développé du sigle", "warn", "sigle sans développé.")
        elif any(acronym_matches(t0, x) for x in devs):
            add("Développé du sigle", "ok", " / ".join(devs))
        else:
            add("Développé du sigle", "ko", "les initiales de « %s » ne correspondent pas au sigle %s." % (" / ".join(devs), t0))
    rel = related_fiches(idx, term, d)
    if not run_llm:
        add("Cohérence avec les fiches liées", "warn", "non vérifiée.")
    elif not definition:
        pass
    elif not rel:
        add("Cohérence avec les fiches liées", "ok", "aucune fiche voisine à comparer.")
    else:
        fich = "\n".join("- %s : %s" % (t, _plain(idx.glossaire[t].get("definition", ""))) for t in rel)
        msgs = [{"role": "system", "content": (
            "Tu relis une proposition de fiche de lexique d'aéronautique (élève pilote). On te donne la proposition et des fiches "
            "existantes liées. Réponds UNIQUEMENT par un JSON {\"coherent\": true|false, \"raison\": \"1 phrase\"}. "
            "coherent=false si la proposition CONTREDIT une fiche existante (sigle développé autrement, sens, grandeur ou unité "
            "différents) ou est manifestement fausse au regard d'elles ; true sinon (une simple différence de formulation ou "
            "un complément n'est pas une contradiction).")},
            {"role": "user", "content": "Proposition : %s\nDéveloppé : %s %s\nDéfinition : %s\n\nFiches existantes :\n%s" % (
                term, d.get("origine", ""), d.get("traduction", ""), _plain(definition, 700), fich)}]
        try:
            j = coherence_llm(msgs)
            if _b(j.get("coherent", True)):
                add("Cohérence avec les fiches liées", "ok", "cohérent avec : " + ", ".join(rel))
            else:
                add("Cohérence avec les fiches liées", "ko", "contradiction avec %s : %s" % (", ".join(rel), str(j.get("raison", ""))[:300]))
        except Exception as e:
            add("Cohérence avec les fiches liées", "warn", str(e)[:200])
    conf = float(d.get("confiance") or 0)
    if conf < LOW_CONF:
        add("Confiance", "warn", "confiance du modèle %d %% (< %d %%) : relire avec attention." % (round(conf * 100), round(LOW_CONF * 100)))
    return {"ok": not any(c["statut"] == "ko" for c in ctl), "controles": ctl,
            "bloquants": [c["nom"] + " : " + c["detail"] for c in ctl if c["statut"] == "ko"],
            "avertissements": [c["nom"] + " : " + c["detail"] for c in ctl if c["statut"] == "warn"],
            "fiches_liees": rel, "confiance": conf}


def check_proposal_id(pid: int, run_llm: bool = True) -> dict:
    with _db_lock, db() as con:
        r = con.execute("SELECT * FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
    if not r:
        raise KeyError("proposition introuvable")
    return check_proposal(r, run_llm)


def _py(s) -> str:
    return json.dumps(s, ensure_ascii=False)


def render_entry(term: str, d: dict, categorie: str = "À classer") -> str:
    """Entrée au format de data/data_glossaire.py (même style que les fiches existantes)."""
    definition = d.get("definition", "").strip()
    if d.get("origine"):
        pre = "<em>%s</em>" % d["origine"]
        if d.get("traduction"):
            pre += " — « %s »" % d["traduction"]
        definition = pre + ". " + definition
    lines = ["    %s: {" % _py(term),
             "        \"definition\": %s," % _py(definition),
             "        \"categorie\": %s," % _py(categorie)]
    if d.get("famille"):
        lines.append("        \"famille\": %s," % _py(d["famille"]))
    syn = [s for s in d.get("synonymes", []) if norm(s) != norm(term)]
    if syn:
        lines.append("        \"variantes\": %s," % _py(syn))
    xr = [x for x in (d.get("voir_aussi") or []) if isinstance(x, str) and norm(x) != norm(term)]
    if xr:
        lines.append("        \"xrefs\": %s," % _py(xr))
    lines.append("        \"origine\": \"suggest\",")
    lines.append("    },")
    return "\n".join(lines) + "\n"


def insert_into_source(src: Path, entries: str) -> None:
    """Insère les entrées avant l'accolade fermante du dict GLOSSAIRE (1ère ligne '}' après 'GLOSSAIRE = {')."""
    lines = src.read_text("utf-8").splitlines(keepends=True)
    start = next(i for i, l in enumerate(lines) if l.startswith("GLOSSAIRE = {"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("}"))
    lines[end:end] = ["    # ---------------- Suggestions validées (suggest) ----------------\n" if not any(
        "Suggestions validées" in l for l in lines) else "", entries]
    src.write_text("".join(lines), "utf-8")


def set_families_in_full(full: Path, assign: dict) -> tuple:
    """Rattache des fiches EXISTANTES (sans famille) à une famille, en modifiant uniquement ces entrées de data_glossaire_full.py
    (insertion d'une ligne 'famille' ou remplissage d'une valeur vide ; le reste du fichier est conservé octet pour octet).
    Vérifie ensuite que le fichier se relit avec les mêmes clés. -> (appliquées [(terme, famille)], ignorées [(terme, raison)])
    Toute incohérence lève une exception (la validation restaure alors le site)."""
    import ast
    raw = full.read_text("utf-8")
    tree = ast.parse(raw)

    def glossaire(tr):
        return next(n for n in tr.body if isinstance(n, ast.Assign) and any(isinstance(x, ast.Name) and x.id == "GLOSSAIRE" for x in n.targets))

    node = glossaire(tree)
    lines = raw.splitlines(keepends=True)
    applied, skipped, ops = [], [], []
    keys_before = [k.value for k in node.value.keys if isinstance(k, ast.Constant)]
    for k, v in zip(node.value.keys, node.value.values):
        if not (isinstance(k, ast.Constant) and k.value in assign):
            continue
        term, fam = k.value, assign[k.value]
        if not isinstance(v, ast.Dict):
            skipped.append((term, "entrée illisible")); continue
        fk = next((i for i, kk in enumerate(v.keys) if isinstance(kk, ast.Constant) and kk.value == "famille"), None)
        if fk is not None:
            fv = v.values[fk]
            if not (isinstance(fv, ast.Constant) and not fv.value):
                skipped.append((term, "a déjà une famille")); continue
            if fv.lineno != fv.end_lineno:
                skipped.append((term, "valeur multi-ligne")); continue
            ops.append((fv.lineno, "set", fv, fam))
        else:
            if v.lineno != k.lineno or not v.keys or v.keys[0].lineno <= v.lineno:
                skipped.append((term, "format d'entrée inattendu")); continue
            ops.append((v.lineno, "ins", v, fam))
        applied.append((term, fam))
    for lineno, kind, nd, fam in sorted(ops, key=lambda o: -o[0]):
        if kind == "ins":
            indent = " " * nd.keys[0].col_offset
            lines.insert(lineno, "%s'famille': %s,\n" % (indent, repr(fam)))
        else:
            b = lines[lineno - 1].encode("utf-8")
            lines[lineno - 1] = (b[:nd.col_offset] + repr(fam).encode("utf-8") + b[nd.end_col_offset:]).decode("utf-8")
    out = "".join(lines)
    node2 = glossaire(ast.parse(out))
    if [k.value for k in node2.value.keys if isinstance(k, ast.Constant)] != keys_before:
        raise RuntimeError("rattachement de familles : les clés du glossaire ont changé (annulé)")
    got = {k.value: {kk.value: vv.value for kk, vv in zip(v.keys, v.values) if isinstance(kk, ast.Constant) and kk.value == "famille" and isinstance(vv, ast.Constant)}
           for k, v in zip(node2.value.keys, node2.value.values) if isinstance(k, ast.Constant) and k.value in assign and isinstance(v, ast.Dict)}
    for term, fam in applied:
        if got.get(term, {}).get("famille") != fam:
            raise RuntimeError("rattachement de familles : %r non appliqué (annulé)" % term)
    full.write_text(out, "utf-8")
    return applied, skipped


def register_family_label(root: Path, slug: str, label: str) -> None:
    p = root / "data" / "familles_labels.json"
    try:
        d = json.loads(p.read_text("utf-8"))
    except (OSError, ValueError):
        d = {}
    d[slug] = label
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1, sort_keys=True) + "\n", "utf-8")


REBUILD_STEPS = [
    ["python3", "src/import_lexique.py", "--write"],
    ["python3", "scripts/build_pages.py"],
    ["python3", "scripts/build_terms_json.py"],
    ["python3", "scripts/build_search_json.py"],
    ["python3", "build_index_js.py"],
]
_build_lock = threading.Lock()


def rebuild(steps=None) -> list:
    log = []
    with _build_lock:
        for cmd in (steps if steps is not None else REBUILD_STEPS):
            p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
            log.append({"cmd": " ".join(cmd), "rc": p.returncode, "tail": (p.stdout + p.stderr)[-300:]})
            if p.returncode != 0:
                raise RuntimeError("build échoué : %s\n%s" % (" ".join(cmd), (p.stdout + p.stderr)[-500:]))
    return log


BACKUP_ROOT = Path(os.environ.get("AEROLEX_BACKUP_DIR", Path.home() / "Backups" / "aerolex"))
LINKS_TEST = ["python3", "scripts/test_links_resolve.py"]
_SKIP_DATA = shutil.ignore_patterns("suggest")      # data/suggest = base SQLite vivante (propositions, sessions) : jamais restaurée


class ValidationError(RuntimeError):
    """Validation annulée ; data/ et dist/aero/ ont été restaurés."""


def _count_cards() -> int:
    return len(list((ROOT / "dist" / "aero" / "t").glob("*.json")))


def backup_site() -> Path:
    """Sauvegarde horodatée de data/ et dist/aero/ -> ~/Backups/aerolex/<AAAAmmjj-HHMMSS>-validate/."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    dest, n = BACKUP_ROOT / (stamp + "-validate"), 1
    while dest.exists():
        n += 1
        dest = BACKUP_ROOT / ("%s-%d-validate" % (stamp, n))
    dest.mkdir(parents=True)
    shutil.copytree(ROOT / "data", dest / "data", symlinks=True, ignore=_SKIP_DATA)
    shutil.copytree(ROOT / "dist" / "aero", dest / "dist_aero", symlinks=True)
    try:                                   # ne garder que les 20 dernières sauvegardes automatiques (jamais les manuelles)
        _load_module(ROOT / "src" / "import_lexique.py", "import_lexique_prune").prune_backups(BACKUP_ROOT)
    except Exception as e:
        sys.stderr.write("rotation des sauvegardes: %r\n" % (e,))
    return dest


def restore_site(bk: Path) -> None:
    for live, saved, ign in ((ROOT / "data", bk / "data", _SKIP_DATA), (ROOT / "dist" / "aero", bk / "dist_aero", None)):
        tmp = live.with_name(live.name + ".restore-tmp")
        shutil.rmtree(tmp, ignore_errors=True)
        if ign:      # on garde data/suggest en place
            for item in live.iterdir():
                if item.name != "suggest":
                    shutil.rmtree(item) if item.is_dir() and not item.is_symlink() else item.unlink()
            for item in saved.iterdir():
                (shutil.copytree(item, live / item.name, symlinks=True) if item.is_dir() else shutil.copy2(item, live / item.name))
        else:
            shutil.rmtree(live)
            shutil.copytree(saved, live, symlinks=True)


def _run(cmd) -> None:
    p = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        raise RuntimeError("échec de %s : %s" % (" ".join(cmd), (p.stdout + p.stderr)[-400:].strip()))


def validate_proposals(ids: list, do_rebuild: bool = True, steps=None, force: bool = False, run_llm: bool = True,
                       links_cmd=None) -> dict:
    with _db_lock, db() as con:
        rows = [con.execute("SELECT * FROM proposals WHERE id=? AND status='pending'", (i,)).fetchone() for i in ids]
    rows = [r for r in rows if r]
    if not rows:
        raise KeyError("aucune proposition en attente parmi les ids")
    done, skipped, chunks, refused = [], [], [], []
    by_dom: dict = {}
    for r in rows:
        by_dom.setdefault(r["domain"], []).append(r)
    for dom, rs in by_dom.items():
        idx = get_index(dom)
        for r in rs:
            m = idx.match(r["term"])
            if m and m["statut"] == "present":
                skipped.append({"terme": r["term"], "raison": "déjà présent (%s)" % m["terme"]})
                continue
            rep_ = check_proposal(r, run_llm)
            if not rep_["ok"] and not force:       # contrôle bloquant : rien n'est écrit pour ce terme
                refused.append({"id": r["id"], "terme": r["term"], **rep_})
                continue
            d = json.loads(r["data"])
            if not d.get("famille") and d.get("famille_nouvelle"):      # nouvelle famille retenue : la fiche en prend le slug
                d["famille"] = d["famille_nouvelle"]
            d["voir_aussi"] = _names(d.get("voir_aussi"), idx, r["term"], MAX_VOIR_AUSSI)
            att = _names(d.get("rattachements_retenus"), idx, r["term"], 15, True) if d.get("famille") else []
            chunks.append((dom, r, render_entry(r["term"], d), d, att))
    if not chunks:
        return {"valides": [], "ignores": skipped, "refuses": refused, "build": [], "force": bool(force)}

    attached: list = []
    skipped_att: list = []

    def write_sources():
        for dom in by_dom:
            if any(c[0] == dom for c in chunks):
                insert_into_source(ROOT / LEXICONS[dom]["source"], "".join(c[2] for c in chunks if c[0] == dom))
                assign, labels = {}, {}
                for c in chunks:                 # rattachements + libellé d'une nouvelle famille : même opération sûre
                    if c[0] != dom:
                        continue
                    d_, att_ = c[3], c[4]
                    if d_.get("famille_nouvelle") and d_.get("famille") == d_["famille_nouvelle"] and d_["famille"] not in get_index(dom).families:
                        labels[d_["famille"]] = d_.get("famille_nouvelle_label") or family_label(d_["famille"])
                    for t_ in att_:
                        assign.setdefault(t_, d_["famille"])
                for slug, lab in labels.items():
                    register_family_label(ROOT, slug, lab)
                if assign:
                    a_, s_ = set_families_in_full(ROOT / LEXICONS[dom]["full"], assign)
                    attached.extend(a_); skipped_att.extend(s_)

    def mark_validated():
        with _db_lock, db() as con:
            for dom, r, *_ in chunks:
                con.execute("DELETE FROM proposals WHERE domain=? AND key=? AND status='validated'", (dom, r["key"]))
                con.execute("UPDATE proposals SET status='validated', upd=? WHERE id=?", (time.time(), r["id"]))
                done.append(r["term"])

    if not do_rebuild:
        write_sources()
        mark_validated()
        return {"valides": done, "ignores": skipped, "refuses": refused, "build": [], "force": bool(force),
                "rattaches": attached, "rattachements_ignores": skipped_att}

    # ── chemin sûr : un seul à la fois, sauvegarde, reconstruction, contrôles, restauration auto ──
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    lock = open(DATA_DIR / "validate.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        lock.close()
        raise ValueError("une validation est déjà en cours, réessayez dans un instant")
    try:
        bk = backup_site()
        before = _count_cards()
        try:
            write_sources()
            log = rebuild(steps)
            _run(links_cmd if links_cmd is not None else LINKS_TEST)
            after = _count_cards()
            if after < before:
                raise RuntimeError("le nombre de fiches a baissé (%d -> %d)" % (before, after))
        except Exception as e:
            restore_site(bk)
            msg = str(e)[:600]
            with _db_lock, db() as con:     # la proposition reste « à valider », avec le message d'erreur
                for dom, r, *_ in chunks:
                    d = json.loads(r["data"])
                    d["erreur_validation"] = msg
                    con.execute("UPDATE proposals SET data=?, upd=? WHERE id=?", (json.dumps(d, ensure_ascii=False), time.time(), r["id"]))
            _idx_cache.clear()
            raise ValidationError("validation annulée, site restauré (sauvegarde %s) : %s" % (bk, msg))
        mark_validated()
        return {"valides": done, "ignores": skipped, "refuses": refused, "build": log, "force": bool(force),
                "fiches": [before, after], "sauvegarde": str(bk),
                "rattaches": attached, "rattachements_ignores": skipped_att}
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


def stats() -> dict:
    with _db_lock, db() as con:
        c = con.execute("SELECT COUNT(*), COALESCE(SUM(usd),0), COALESCE(SUM(n_terms),0) FROM costlog").fetchone()
        t = con.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        p = con.execute("SELECT status, COUNT(*) FROM proposals GROUP BY status").fetchall()
    return {"appels_llm": c[0], "usd_total": round(c[1], 5), "termes_factures": c[2], "usd_24h": round(cost_today(), 5),
            "plafond_usd_24h": DAILY_USD_CAP, "termes_en_cache": t, "propositions": {r[0]: r[1] for r in p}}


# ── Mot de passe relecteur + session (cookie HttpOnly) ──────────────────────
import hashlib
import hmac

PASSWORD_FILE = Path(os.environ.get("AEROLEX_SUGGEST_PASSWORD_FILE", Path.home() / ".aerolex-suggest-password"))
SESSION_DAYS = 30
COOKIE_NAME = "aerolex_session"
LOGIN_MAX_FAILS = 5
LOGIN_BLOCK_SECS = 15 * 60
_SCRYPT = dict(n=2 ** 14, r=8, p=1, dklen=32)
_pw_ref = None      # (sel, hash scrypt) gardé en mémoire ; le mot de passe en clair n'est jamais conservé


def _kdf(pw: str, salt: bytes) -> bytes:
    """scrypt ; repli PBKDF2-HMAC-SHA256 600 000 itérations si l'interpréteur n'a pas scrypt (python3 système macOS / LibreSSL)."""
    if hasattr(hashlib, "scrypt"):
        return hashlib.scrypt(pw.encode("utf-8"), salt=salt, **_SCRYPT)
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt, 600_000)


def load_password(path=None):
    """Lit le fichier (une ligne), n'en garde que sel + hash scrypt. -> True si un mot de passe est défini."""
    global _pw_ref
    _pw_ref = None
    try:
        pw = Path(path or PASSWORD_FILE).read_text("utf-8").strip()
    except OSError:
        return False
    if pw:
        salt = secrets.token_bytes(16)
        _pw_ref = (salt, _kdf(pw, salt))
    return _pw_ref is not None


load_password()


def check_password(given: str) -> bool:
    if _pw_ref is None or not given:
        return False
    salt, ref = _pw_ref
    return hmac.compare_digest(_kdf(given, salt), ref)


def login_blocked(ip: str) -> int:
    """-> secondes restantes de blocage (0 si libre)."""
    with _db_lock, db() as con:
        rows = con.execute("SELECT ts FROM ratelimit WHERE ip=? AND kind='loginfail' AND ts>? ORDER BY ts",
                           (_ipkey(ip), time.time() - LOGIN_BLOCK_SECS)).fetchall()
    if len(rows) >= LOGIN_MAX_FAILS:
        return int(rows[-1][0] + LOGIN_BLOCK_SECS - time.time()) + 1
    return 0


def login(password: str, ip: str):
    """-> (ok, cookie_value|None, retry_after). 5 échecs par IP -> blocage 15 min."""
    wait = login_blocked(ip)
    if wait:
        return False, None, wait
    if not check_password(password):
        rate_record(ip, "loginfail")
        return False, None, login_blocked(ip)
    with _db_lock, db() as con:
        con.execute("DELETE FROM ratelimit WHERE ip=? AND kind='loginfail'", (_ipkey(ip),))
        con.execute("CREATE TABLE IF NOT EXISTS sessions(h TEXT PRIMARY KEY, exp REAL)")
        con.execute("DELETE FROM sessions WHERE exp<?", (time.time(),))
        sid = secrets.token_urlsafe(32)
        con.execute("INSERT INTO sessions(h,exp) VALUES(?,?)", (hashlib.sha256(sid.encode()).hexdigest(), time.time() + SESSION_DAYS * 86400))
    return True, sid, 0


def _sid_from(headers) -> str:
    c = headers.get("Cookie") or ""
    m = re.search(r"(?:^|;\s*)" + COOKIE_NAME + r"=([A-Za-z0-9_\-]+)", c)
    return m.group(1) if m else ""


def check_session(headers) -> bool:
    sid = _sid_from(headers)
    if not sid:
        return False
    with _db_lock, db() as con:
        con.execute("CREATE TABLE IF NOT EXISTS sessions(h TEXT PRIMARY KEY, exp REAL)")
        r = con.execute("SELECT exp FROM sessions WHERE h=?", (hashlib.sha256(sid.encode()).hexdigest(),)).fetchone()
    return bool(r) and r[0] > time.time()


def logout(headers) -> None:
    sid = _sid_from(headers)
    if sid:
        with _db_lock, db() as con:
            con.execute("DELETE FROM sessions WHERE h=?", (hashlib.sha256(sid.encode()).hexdigest(),))
