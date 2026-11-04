#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
new_lexicon.py — crée un NOUVEAU lexique AeroLex qui applique d'office toutes les règles de qualité (README « Règles de qualité d'un lexique »).

    python3 scripts/new_lexicon.py --slug voile --label "Voile" [--source termes.txt] [--famille slug=Libellé ...]
                                   [--audience "…"] [--scope "…"] [--analysis items.json] [--no-llm]
                                   [--corpus DOSSIER | --corpus-sitemap URL | --corpus-urls URL,URL… | (aucun)]
                                   [--public-url https://mon.site] [--skip-selectors ".menu,.bandeau"] [--base DOSSIER] [--db-dir DOSSIER]

Crée lexicons/<slug>/ (racine propre du lexique ; la chaîne de build y tourne avec AEROLEX_LEXICON=<slug>) :
  data/        data_glossaire.py + data_glossaire_full.py (vides), familles_labels.json (catalogue de familles ; « Divers » d'office),
               lexicon.json (CONFIGURATION du lexique : identité, corpus facultatif, options d'affichage, règles — voir README),
               extra_content.py, lexique-filtre.txt
  dist/        moteur v1.4.0 + feuilles (copiés de dist/ du projet), dist/<slug>/ : index (lettres vides masquées, autocomplétion, popups mis en page),
               suggest.html/js/css (page « Suggérer »), slugmap.json, lexicon.json, build-info.json (cache-bust par empreinte), t/, search/index JSON
  scripts/ src/ build_index_js.py   liens vers ceux du projet (une seule chaîne de build)
et déclare le lexique dans lexicons/registry.json (lu par suggest_core : redémarrer le service qui sert l'API de suggestion pour l'activer).

Corpus (facultatif) du contrôle anti-ridicule : dossier local (--corpus), sitemap du site hôte (--corpus-sitemap), liste d'URL (--corpus-urls) ou
aucun (défaut : la simulation est alors générique — définitions du lexique, homographes français, règles de casse et d'unités ; un échantillon de
textes peut être téléversé plus tard depuis la page « Suggérer »).

Avec --source (fichier .txt/.csv/.md/.pdf/.docx : liste de termes), les termes passent par le MÊME pipeline que « Suggérer des termes »
(entonnoir gratuit, analyse par le modèle, forme de base accentuée, variantes d'appel, famille obligatoire ou Divers, sigles développés,
contrôle anti-ridicule sur le corpus) EN LOT, puis sont déposés dans la file « À valider » : rien n'est publié.
--analysis items.json : analyses déjà faites (liste d'items au contrat du modèle) au lieu d'appeler le modèle ; --no-llm : pas de modèle
(définitions à rédiger, famille Divers).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE_DEFAULT = HERE.parent
sys.path.insert(0, str(HERE))
import lexicon_env  # noqa: E402
RESERVED = {"index", "dist", "data", "scripts", "src", "lexicons", "suggest", "api", "t", "svg", "schemas", "slugmap", "build-info",
            "lexicon", "search", "backups", "docs", "deploy", "test", "tests", "admin"}
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
ASSETS = ["aerolex.js", "aerolex.css", "aerolex-page.css", "aerolex-svg.js", "aerolex-indexpage.css", "aerolex-indexpage.js", "aerolex-searchbox.js"]
# Premier build : lexicon.json (réglages client, inclus dans l'empreinte de cache) AVANT les pages, sinon l'empreinte écrite dans les pages
# serait celle d'un lexicon.json encore absent. Les builds suivants (core.REBUILD_STEPS) gardent l'ordre officiel : le fichier existe déjà.
REBUILD = [["python3", "src/import_lexique.py", "--write", "--root", "{root}", "--backup-dir", "{bk}"], ["python3", "scripts/build_terms_json.py"],
           ["python3", "scripts/build_pages.py"], ["python3", "scripts/build_search_json.py"], ["python3", "build_index_js.py"]]

GLOSS_HEAD = '''# -*- coding: utf-8 -*-
"""Lexique « %(label)s » (%(slug)s) — %(what)s

Chaque entrée : "terme": {"definition": "…", "categorie": "…", "famille": "<slug de famille ou divers>", "variantes": [...], ...}
Règle : TOUT terme a une famille (« divers » si aucune ne convient). Aucune variante de moins de 3 lettres en minuscules, aucun mot grammatical.
Créé le %(date)s par scripts/new_lexicon.py.
"""
GLOSSAIRE = {
}
'''


def check_slug(slug: str, base: Path | None = None) -> None:
    if not SLUG_RE.fullmatch(slug or "") or not (3 <= len(slug) <= 40):
        raise SystemExit("slug invalide « %s » : minuscules, chiffres et tirets, 3 à 40 caractères (ex. voile, demo-voile)" % slug)
    main_id = lexicon_env.meta(str(base or BASE_DEFAULT)).get("id")       # le lexique de la racine occupe dist/<id>/
    if slug in RESERVED or slug == main_id:
        raise SystemExit("slug réservé : « %s »" % slug)


def _write(p: Path, txt: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(txt, "utf-8")


def corpus_spec(corpus=None, sitemap: str = "", urls: str = "") -> dict:
    """Configuration du corpus (clé « corpus » de data/lexicon.json) : dossier local, sitemap, liste d'URL, ou aucun."""
    if isinstance(corpus, dict):
        return corpus
    if corpus:
        return {"type": "dir", "path": str(Path(corpus).resolve()), "unit": "page"}
    if sitemap:
        return {"type": "sitemap", "url": sitemap, "unit": "page"}
    if urls:
        return {"type": "urls", "urls": [u.strip() for u in urls.split(",") if u.strip()], "unit": "page"}
    return {"type": "none"}


def create_lexicon(slug: str, label: str, base: Path = BASE_DEFAULT, audience: str = "", scope: str = "", corpus="",
                   familles: dict | None = None, out=print, public_url: str = "", skip_selectors: str = "") -> Path:
    """Crée la racine du lexique, la déclare au registre et construit une première fois (index vide mais complet). -> racine."""
    base = Path(base).resolve()
    check_slug(slug, base)
    root = base / "lexicons" / slug
    if root.exists():
        raise SystemExit("le lexique existe déjà : %s" % root)
    if not (base / "dist" / "aerolex.js").exists():
        raise SystemExit("moteur introuvable : %s" % (base / "dist" / "aerolex.js"))
    engine = (base / "dist" / "aerolex.js").read_text("utf-8")
    m = re.search(r"AeroLex Runtime v(\d+\.\d+\.\d+)", engine)
    ver = m.group(1) if m else "?"
    if tuple(int(x) for x in ver.split(".")) < (1, 4, 0) if m else True:
        raise SystemExit("moteur trop ancien (%s) : il faut >= 1.4.0 (frontières Unicode, sigles de 2 lettres, pluriel/singulier, contexte_requis)" % ver)
    main_id = lexicon_env.meta(str(base)).get("id") or ""
    fams = dict(familles or {})
    fams.pop("divers", None)
    # 1. data/
    _write(root / "data" / "data_glossaire.py", GLOSS_HEAD % {"label": label, "slug": slug, "date": time.strftime("%Y-%m-%d"),
                                                             "what": "entrées validées via « Suggérer des termes » (origine=suggest), entrée de l'import."})
    _write(root / "data" / "data_glossaire_full.py", GLOSS_HEAD % {"label": label, "slug": slug, "date": time.strftime("%Y-%m-%d"),
                                                                  "what": "STOCK CANONIQUE des fiches (écrit par src/import_lexique.py)."})
    _write(root / "data" / "familles_labels.json", json.dumps(fams, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    _write(root / "data" / "lexique-filtre.txt", "")
    _write(root / "data" / "extra_content.py", '# -*- coding: utf-8 -*-\n"""Contenus additionnels par fiche (aucun pour ce lexique)."""\n\n\ndef get_extra_content(slug):\n    return ""\n')
    meta = {"id": slug, "label": label, "audience": audience or "lecteur du domaine « %s »" % label, "scope": scope or "vocabulaire du domaine « %s »" % label,
            "corpus": corpus if isinstance(corpus, dict) else corpus_spec(corpus),
            "display": {"skip_selectors": [x.strip() for x in skip_selectors.split(",") if x.strip()]} if skip_selectors else {},
            "rules": {}, "moteur": ver, "cree": time.strftime("%Y-%m-%d")}
    pub = (public_url or os.environ.get("AEROLEX_PUBLIC_URL") or "").rstrip("/")
    if pub:          # URL publique des fiches ; absente : le moteur la déduit de l'emplacement de l'index (relative)
        meta["base_url"] = "%s/%s/" % (pub, slug)
    _write(root / "data" / "lexicon.json", json.dumps(meta, ensure_ascii=False, indent=1) + "\n")
    # 2. dist/ : moteur + feuilles + pages de service du lexique
    for a in ASSETS:
        if (base / "dist" / a).exists():
            (root / "dist").mkdir(parents=True, exist_ok=True)
            shutil.copy2(base / "dist" / a, root / "dist" / a)
    dd = root / "dist" / slug
    dd.mkdir(parents=True, exist_ok=True)
    tpl = base / "dist" / main_id                      # gabarit de la page « Suggérer » : celle du lexique de la racine
    if not (tpl / "suggest.html").exists():
        tpl = next((p.parent for p in sorted((base / "dist").glob("*/suggest.html"))), tpl)
    for f in ("suggest.js", "suggest.css"):
        shutil.copy2(tpl / f, dd / f)
    html = (tpl / "suggest.html").read_text("utf-8")
    html = html.replace("— AeroLex</title>", "— %s — AeroLex</title>" % label).replace('<script src="suggest.js?v=', '<script data-lexicon="%s" src="suggest.js?v=' % slug)
    _write(dd / "suggest.html", html)
    # 3. liens vers la chaîne de build du projet
    for name in ("scripts", "src", "build_index_js.py"):
        link = root / name
        if not link.exists() and not link.is_symlink():
            link.symlink_to(os.path.relpath(base / name, root), target_is_directory=(base / name).is_dir())
    # 4. registre
    reg_p = base / "lexicons" / "registry.json"
    try:
        reg = json.loads(reg_p.read_text("utf-8"))
    except (OSError, ValueError):
        reg = {"lexicons": {}}
    reg.setdefault("lexicons", {})[slug] = {
        "label": label, "audience": meta["audience"], "scope": meta["scope"], "root": "lexicons/" + slug, "slug_dir": "dist/" + slug,
        "source": "data/data_glossaire.py", "full": "data/data_glossaire_full.py", "base_url": "/%s/" % slug, "catalog_seed": True}
    _write(reg_p, json.dumps(reg, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    out("✓ structure créée : %s (moteur v%s)" % (root, ver))
    build(slug, root, out=out)
    return root


def build(slug: str, root: Path, out=print) -> None:
    """Chaîne officielle : import --write -> build_pages -> build_terms_json -> build_search_json -> build_index_js."""
    env = dict(os.environ, AEROLEX_LEXICON=slug, AEROLEX_LEXROOT=str(root))
    bk = root / "backups"
    for cmd in REBUILD:
        cmd = [c.replace("{bk}", str(bk)).replace("{root}", str(root)) for c in cmd]
        p = subprocess.run(cmd, cwd=str(root), env=env, capture_output=True, text=True, timeout=600)
        if p.returncode != 0:
            raise SystemExit("build échoué : %s\n%s" % (" ".join(cmd), (p.stdout + p.stderr)[-800:]))
    publish_links(slug, root, out)
    out("✓ build : import, pages (index + fiches), JSON des fiches, recherche, index du moteur, slugmap, empreinte de cache")


def publish_links(slug: str, root: Path, out=print) -> None:
    """Le service sert <base>/dist : on y relie dist/<slug>/ et les JSON partagés du lexique (liens relatifs, idempotent)."""
    base = root.parent.parent
    for rel in (Path(slug), Path("aerolex-%s-index.json" % slug), Path("aerolex-%s-search.json" % slug)):
        src, link = root / "dist" / rel, base / "dist" / rel
        if not src.exists() or not (base / "dist").is_dir():
            continue
        if link.is_symlink() or link.exists():
            if link.is_symlink() and link.resolve() == src.resolve():
                continue
            out("⚠ %s existe déjà : non remplacé" % link)
            continue
        link.symlink_to(os.path.relpath(src, link.parent), target_is_directory=src.is_dir())
        out("✓ servi : dist/%s → %s" % (rel, os.path.relpath(src, base)))


def seed(slug: str, base: Path, terms: list, analysis_file: str = "", llm: bool = True, out=print) -> dict:
    """Lot de termes source -> file « À valider » via le pipeline de suggest_core (rien n'est publié)."""
    os.environ["AEROLEX_ROOT"] = str(Path(base).resolve())
    sys.path.insert(0, str(HERE))
    import suggest_core as core  # noqa: E402
    core._load_registry()
    if slug not in core.LEXICONS:
        raise SystemExit("lexique non déclaré : %s" % slug)
    analysis = None
    if analysis_file:
        raw = json.loads(Path(analysis_file).read_text("utf-8"))
        items = raw.get("items") if isinstance(raw, dict) else raw
        analysis = {str(i.get("terme")): i for i in items if isinstance(i, dict) and i.get("terme")}
    job = "seed-" + time.strftime("%Y%m%d-%H%M%S")
    rep = core.seed_terms(slug, terms, analysis=analysis, llm=llm, job=job)
    out("✓ %d terme(s) analysé(s) : %d en file « À valider », %d déjà présent(s), %d écarté(s)%s" % (
        len(terms), rep["en_file"], len(rep["deja_presents"]), len(rep["ecartes"]), (" — erreurs : " + "; ".join(rep["erreurs"])[:200]) if rep["erreurs"] else ""))
    for pid, notes in rep["corriges"].items():
        for n in notes:
            out("   · #%s %s" % (pid, n))
    return rep


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--slug", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--source", help="fichier de termes (.txt .csv .md .pdf .docx)")
    ap.add_argument("--famille", action="append", default=[], help="catalogue de familles de départ : slug=Libellé (répétable ; « divers » existe d'office)")
    ap.add_argument("--audience", default="")
    ap.add_argument("--scope", default="")
    ap.add_argument("--corpus", default="", help="dossier local de pages (.html .txt .md) servant au contrôle anti-ridicule (facultatif)")
    ap.add_argument("--corpus-sitemap", default="", help="sitemap.xml du site hôte : pages récupérées puis mises en cache (facultatif)")
    ap.add_argument("--corpus-urls", default="", help="liste d'URL séparées par des virgules (facultatif)")
    ap.add_argument("--public-url", default="", help="URL publique du site qui sert dist/ (défaut : $AEROLEX_PUBLIC_URL, sinon relative)")
    ap.add_argument("--skip-selectors", default="", help="sélecteurs CSS des zones à ne pas souligner, publiés avec l'index (ex. « .menu,.bandeau »)")
    ap.add_argument("--analysis", default="", help="analyses déjà faites (JSON, contrat du modèle) au lieu d'appeler le modèle")
    ap.add_argument("--no-llm", action="store_true", help="aucun appel au modèle (définitions à rédiger)")
    ap.add_argument("--base", default=str(BASE_DEFAULT), help="racine du projet (tests : copie dans /tmp)")
    ap.add_argument("--db-dir", default="", help="dossier de la base de propositions (tests : dossier temporaire)")
    a = ap.parse_args(argv)
    if a.db_dir:
        os.environ["AEROLEX_SUGGEST_DIR"] = a.db_dir
    fams = {}
    for f in a.famille:
        k, _, v = f.partition("=")
        if not re.fullmatch(r"[a-z0-9_]+", k.strip()) or not v.strip():
            raise SystemExit("--famille attend slug=Libellé (reçu %r)" % f)
        fams[k.strip()] = v.strip()
    base = Path(a.base).resolve()
    root = create_lexicon(a.slug, a.label, base, a.audience, a.scope, corpus_spec(a.corpus, a.corpus_sitemap, a.corpus_urls), fams,
                          public_url=a.public_url, skip_selectors=a.skip_selectors)
    if a.source:
        sys.path.insert(0, str(HERE))
        os.environ["AEROLEX_ROOT"] = str(base)
        import suggest_core as core  # noqa: E402
        p = Path(a.source)
        terms = core.parse_upload(p.name, p.read_bytes())["terms"]
        if not terms:
            raise SystemExit("aucun terme exploitable dans %s" % a.source)
        rep = seed(a.slug, base, terms, a.analysis, llm=not a.no_llm)
        (root / "data" / "lot-source.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), "utf-8")
    print("\nSuite : relire la file « À valider » sur /%s/suggest.html (espace relecteur) ; vérifier avec  python3 scripts/check_lexicon.py %s" % (a.slug, a.slug))
    print("Activation côté service : redémarrer le service qui sert l'API de suggestion (suggest_api, via serve_cors.py)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
