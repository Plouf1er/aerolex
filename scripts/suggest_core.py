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
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
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
        raise ValueError("fichier trop gros (max 8 Mo)")
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
    CREATE TABLE IF NOT EXISTS costlog(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL, job TEXT, model TEXT,
        n_terms INTEGER, tok_in INTEGER, tok_out INTEGER, usd REAL, secs REAL, ok INTEGER);
    """)
    return con


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


def build_prompt(lex_id: str, terms: list, families: dict) -> list:
    cfg = LEXICONS[lex_id]
    fam_list = ", ".join(families.keys())
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
        '  "famille": UNE valeur choisie dans la liste des familles existantes si l\'une convient, sinon "" ;\n'
        '  "famille_nouvelle": proposition courte (snake_case) UNIQUEMENT si aucune famille existante ne convient, sinon "",\n'
        '  "synonymes": liste de synonymes/alias/formes courantes (peut être vide),\n'
        '  "confiance": nombre 0..1 (ta certitude sur la définition).\n'
        "Pas de HTML, pas de markdown, pas de commentaire hors JSON. Sois exact : si tu ne connais pas un terme, "
        "mets confiance basse et définition vide plutôt que d'inventer.\n"
        "Familles existantes : " + fam_list
    )
    user = "Termes :\n" + "\n".join("- " + t for t in terms)
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


def validate_item(it: dict, asked: str, families: dict) -> dict:
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
    if fam and fam not in families:
        # famille inventée : on la rétrograde en proposition de nouvelle famille
        fam_new, fam = fam_new or fam, ""
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
        "synonymes": list(dict.fromkeys(syn))[:10],
        "confiance": round(conf, 2),
    }
    if out["domaine"] and out["pertinent"] and len(out["definition"]) < 20:
        out["pertinent"] = False
        out["raison_pertinent"] = (out["raison_pertinent"] + " (définition manquante : à rédiger)").strip()
    return out


def parse_llm(content: str, asked: list, families: dict) -> dict:
    """-> {terme_demandé: item validé}. Associe par ordre, repli par forme normalisée."""
    obj = json.loads(_strip_json(content))
    items = obj.get("items") if isinstance(obj, dict) else obj
    if not isinstance(items, list):
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
            out[t] = validate_item(it, t, families)
        except ValueError:
            continue
    return out


def llm_batch(lex_id: str, terms: list, families: dict, job: str = "") -> tuple:
    """Un appel LLM pour <= BATCH_SIZE termes. Repli : retry -> Qwopus local.
    -> (résultats {terme: item}, [erreurs], coût_usd)"""
    messages = build_prompt(lex_id, terms, families)
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
            got = parse_llm(content, terms, families)
            ok = len(got) > 0
            with _db_lock, db() as con:
                con.execute("INSERT INTO costlog(ts,job,model,n_terms,tok_in,tok_out,usd,secs,ok) VALUES(?,?,?,?,?,?,?,?,?)",
                            (time.time(), job, model, len(terms), usage["in"], usage["out"], usd, time.time() - t0, int(ok)))
            total_usd += usd
            for k, v in got.items():
                v["modele"] = model
                results[k] = v
            missing = [t for t in terms if t not in results]
            if not missing:
                return results, errors, total_usd
            terms = missing                     # on ne redemande que les manquants
            messages = build_prompt(lex_id, terms, families)
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


def funnel_free(lex_id: str, terms: list) -> tuple:
    """Étapes 2 et 3 (gratuites). -> (résultats par terme (dict ordonné), à_envoyer_au_LLM)"""
    idx = get_index(lex_id)
    res, todo = {}, []
    for t in terms:
        m = idx.match(t)
        if m:
            res[t] = {"terme": t, **m}
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


def apply_llm_results(lex_id: str, res: dict, got: dict, job: str):
    for t, item in got.items():
        cache_put(lex_id, ckey(t), item)
        nb = res.get(t, {}).get("voisins")
        res[t] = {"terme": t, "statut": "analyse", "cache": False, **{k: v for k, v in item.items() if k != "terme"}}
        if nb:
            res[t]["voisins"] = nb
    for t, r in res.items():
        if r.get("statut") == "analyse":
            r["verdict"] = classify(r)
            if r["verdict"] == "a_valider":
                enqueue_proposal(lex_id, t, {k: v for k, v in r.items() if k not in ("statut", "cache", "terme", "verdict", "voisins")}, job)


def enqueue_proposal(lex_id: str, term: str, data: dict, job: str):
    key = ckey(term)
    now = time.time()
    with _db_lock, db() as con:
        if con.execute("SELECT 1 FROM proposals WHERE domain=? AND key=? AND status='pending'", (lex_id, key)).fetchone():
            return
        con.execute("INSERT OR REPLACE INTO proposals(domain,key,term,status,data,job,ts,upd) VALUES(?,?,?,?,?,?,?,?)",
                    (lex_id, key, term, "pending", json.dumps(data, ensure_ascii=False), job, now, now))


def new_job(lex_id: str, terms: list, info: dict) -> str:
    jid = secrets.token_hex(8)
    res, todo = funnel_free(lex_id, terms)
    # termes déjà analysés (cache) qui n'ont pas de proposition : on (ré)alimente la file
    for t, r in res.items():
        if r.get("statut") == "analyse":
            r["verdict"] = classify(r)
            if r["verdict"] == "a_valider":
                enqueue_proposal(lex_id, t, {k: v for k, v in r.items() if k not in ("statut", "cache", "terme", "verdict", "voisins")}, jid)
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
                    res[t]["erreur"] = "; ".join(errs)[:200] or "pas de réponse"
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


def job_view(jid: str):
    with _db_lock, db() as con:
        row = con.execute("SELECT * FROM jobs WHERE id=?", (jid,)).fetchone()
    if not row:
        return None
    info = json.loads(row["info"])
    info.pop("todo", None)
    res = json.loads(row["results"])
    return {"id": row["id"], "domaine": row["domain"], "etat": row["state"], "total": row["total"], "fait": row["done"],
            "info": info, "resultats": list(res.values())}


def submit(lex_id: str, text: str = "", terms: list | None = None, background: bool = True) -> dict:
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
    jid = new_job(lex_id, p["terms"], info)
    v = job_view(jid)
    with _db_lock, db() as con:
        n_todo = len(json.loads(con.execute("SELECT info FROM jobs WHERE id=?", (jid,)).fetchone()["info"]).get("todo", []))
    if n_todo == 0:
        return v
    if n_todo <= UNIT_SYNC_MAX or not background:
        run_job(jid)
        return job_view(jid)
    threading.Thread(target=run_job, args=(jid,), daemon=True, name="suggest-" + jid).start()
    return v


# ── 3. File de propositions + validation ─────────────────────────────────────
def list_proposals(lex_id: str | None, status: str = "pending") -> list:
    q, a = "SELECT * FROM proposals WHERE status=?", [status]
    if lex_id:
        q += " AND domain=?"; a.append(lex_id)
    with _db_lock, db() as con:
        rows = con.execute(q + " ORDER BY ts DESC", a).fetchall()
    return [{"id": r["id"], "domaine": r["domain"], "terme": r["term"], "statut": r["status"],
             "data": json.loads(r["data"]), "job": r["job"], "ts": r["ts"]} for r in rows]


def edit_proposal(pid: int, term: str | None, data: dict) -> dict:
    allowed = {"definition", "famille", "famille_nouvelle", "synonymes", "origine", "traduction"}
    with _db_lock, db() as con:
        r = con.execute("SELECT * FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
        if not r:
            raise KeyError("proposition introuvable")
        cur = json.loads(r["data"])
        for k, v in data.items():
            if k in allowed:
                cur[k] = v
        if isinstance(cur.get("synonymes"), str):
            cur["synonymes"] = [clean_term(s) for s in cur["synonymes"].split(",") if clean_term(s)]
        con.execute("UPDATE proposals SET data=?, term=?, upd=? WHERE id=?",
                    (json.dumps(cur, ensure_ascii=False), clean_term(term) if term else r["term"], time.time(), pid))
    return {"ok": True}


def reject_proposal(pid: int) -> dict:
    with _db_lock, db() as con:
        # statut rejected unique par (domain,key) : on remplace une éventuelle ancienne ligne
        r = con.execute("SELECT domain,key FROM proposals WHERE id=? AND status='pending'", (pid,)).fetchone()
        if not r:
            raise KeyError("proposition introuvable")
        con.execute("DELETE FROM proposals WHERE domain=? AND key=? AND status='rejected'", (r["domain"], r["key"]))
        con.execute("UPDATE proposals SET status='rejected', upd=? WHERE id=?", (time.time(), pid))
    return {"ok": True}


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


REBUILD_STEPS = [
    ["python3", "src/import_lexique.py"],
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


def validate_proposals(ids: list, do_rebuild: bool = True, steps=None) -> dict:
    with _db_lock, db() as con:
        rows = [con.execute("SELECT * FROM proposals WHERE id=? AND status='pending'", (i,)).fetchone() for i in ids]
    rows = [r for r in rows if r]
    if not rows:
        raise KeyError("aucune proposition en attente parmi les ids")
    done, skipped, chunks = [], [], []
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
            d = json.loads(r["data"])
            fam = d.get("famille") or ""
            chunks.append((dom, r, render_entry(r["term"], d)))
        if any(c[0] == dom for c in chunks):
            insert_into_source(ROOT / LEXICONS[dom]["source"], "".join(c[2] for c in chunks if c[0] == dom))
    with _db_lock, db() as con:
        for dom, r, _ in chunks:
            con.execute("DELETE FROM proposals WHERE domain=? AND key=? AND status='validated'", (dom, r["key"]))
            con.execute("UPDATE proposals SET status='validated', upd=? WHERE id=?", (time.time(), r["id"]))
            done.append(r["term"])
    log = rebuild(steps) if (do_rebuild and done) else []
    return {"valides": done, "ignores": skipped, "build": log}


def stats() -> dict:
    with _db_lock, db() as con:
        c = con.execute("SELECT COUNT(*), COALESCE(SUM(usd),0), COALESCE(SUM(n_terms),0) FROM costlog").fetchone()
        t = con.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        p = con.execute("SELECT status, COUNT(*) FROM proposals GROUP BY status").fetchall()
    return {"appels_llm": c[0], "usd_total": round(c[1], 5), "termes_factures": c[2], "usd_24h": round(cost_today(), 5),
            "plafond_usd_24h": DAILY_USD_CAP, "termes_en_cache": t, "propositions": {r[0]: r[1] for r in p}}


# ── Jeton ────────────────────────────────────────────────────────────────────
TOKEN_FILE = Path(os.environ.get("AEROLEX_SUGGEST_TOKEN_FILE", Path.home() / ".aerolex-suggest-token"))


def get_token() -> str:
    t = os.environ.get("AEROLEX_SUGGEST_TOKEN")
    if t:
        return t
    try:
        return TOKEN_FILE.read_text("utf-8").strip()
    except OSError:
        t = secrets.token_urlsafe(24)
        TOKEN_FILE.write_text(t + "\n", "utf-8")
        os.chmod(TOKEN_FILE, 0o600)
        return t


def check_token(given: str | None) -> bool:
    return bool(given) and secrets.compare_digest(given, get_token())
