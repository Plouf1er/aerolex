# Méthode de génération des schémas SVG

## L'Outil et la méthode
Le système existant n'utilise **aucun outil externe ni fichier SVG brut**. Tous les schémas sont écrits en **Python pur**, directement sous forme de chaînes de caractères (templates string interpolés).
- **Emplacement :** `src/svg_glossaire.py` (dans aerolex) et une dizaine de fichiers `svg_schemas_XXX.py` (dans aero-coach).
- **Générateurs identifiés :** `src/svg_glossaire.py` contient actuellement 9 générateurs (ex: `svg_piste_seuils_qfu`, `svg_tour_de_piste`, `svg_decrabage`).
- **Signature standard :** `def svg_nom_schema() -> str:`
- **Utilisation par les données :** Le glossaire utilise la clé `"schema": "nom_du_schema"`. Un dictionnaire `SCHEMAS` mappe ce nom vers la fonction Python.

## Caractéristiques Techniques
- **Inline et autoportant :** Aucun fichier `.svg` sur disque, le code SVG complet est retourné par la fonction et injecté dans le HTML (`<svg ...>...</svg>`).
- **ViewBox et Responsive :** Utilisation systématique de `viewBox="0 0 640 360"` avec `style="max-width:100%; height:auto;"`.
- **Zéro dépendance :** Pas de bibliothèque externe. Formes vectorielles simples (`rect`, `circle`, `line`, `path`, `text`).
- **Style visuel :** Très épuré, pédagogique. Palette de couleurs style Tailwind (`#f8fafc`, `#1e3a5f`, `#2563eb`, `#dc2626`). Les textes sont inclus dans le SVG via `<text>` (jamais de texte inférieur à 11px pour la lisibilité mobile).
- **Interaction :** Certaines fonctions (comme le tour de piste) acceptent un paramètre `actif: str | None = None` permettant de mettre en évidence (halo jaune) la partie spécifique abordée par la fiche du glossaire.

## Rôle de l'IA
**Aucun prompt LLM n'a été retrouvé.** Les SVG existants ont été codés en dur ou générés de manière itérative mais sans laisser de script "d'appel LLM" ni de prompt persistant dans le repository.

## Exemple complet généré (`svg_composantes_face_travers`)
```python
def svg_composantes_face_travers() -> str:
    """Triangle de composantes : vent → face + travers."""
    body = """
  <text x="320" y="26" text-anchor="middle" font-size="15" font-weight="700" fill="#1e3a5f">Composantes face / travers</text>
  <text x="320" y="46" text-anchor="middle" font-size="12" fill="#64748b">face = V · cos θ ··· travers = V · sin θ</text>
  <!-- Piste horizontale -->
  <rect x="80" y="200" width="360" height="36" fill="#475569" rx="3"/>
  <text x="100" y="224" font-size="14" font-weight="700" fill="#f8fafc">07</text>
  <text x="400" y="224" font-size="14" font-weight="700" fill="#f8fafc">25</text>
  <text x="260" y="255" text-anchor="middle" font-size="12" fill="#475569">axe de piste (QFU)</text>
  <!-- Origine O sur le seuil gauche-ish -->
  <circle cx="200" cy="218" r="5" fill="#0f172a"/>
  <!-- ... autres éléments (flèches avec marker-end, arcs) ... -->
"""
    return (
        f'<svg class="schema glos-schema" viewBox="0 0 640 360" '
        f'xmlns="http://www.w3.org/2000/svg" role="img" '
        f'style="max-width:100%;width:100%;height:auto;display:block;margin:10px 0;">'
        f'<rect width="640" height="360" fill="#e0f2fe" rx="8"/>'
        f"{body}</svg>"
    )
```
