# Déploiement aerolex.prunel.net

## Chaîne complète
```
navigateur → Cloudflare → tunnel cloudflared (prunel-home)
          → 127.0.0.1:4140 → serve_cors.py --dir <repo>/dist
```
- Route du tunnel : `~/.cloudflared/config.yml`, hostname `aerolex.prunel.net`.
- Service : launchd `com.prunel.aerolex` (`RunAtLoad` + `KeepAlive`).
- Logs : `/tmp/aerolex-4140.log`, `/tmp/aerolex-4140.err.log`.

## Pourquoi serve_cors.py et pas `python3 -m http.server`
`http.server` n'envoie aucun en-tête CORS → tout fetch cross-origin d'un site
client échoue. `serve_cors.py` fait l'écho conditionnel de l'`Origin` sur une
**allow-list fermée** (cf. l'en-tête du fichier pour le détail du raisonnement).

## Recharger après modification
```sh
cp deploy/com.prunel.aerolex.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.prunel.aerolex.plist
launchctl load   ~/Library/LaunchAgents/com.prunel.aerolex.plist
```

## Vérifier le CORS
```sh
# origine autorisée → 200 + Access-Control-Allow-Origin en écho + Vary: Origin
curl -sI -H "Origin: https://atcf-ppl.prunel.net" \
  https://aerolex.prunel.net/aero/t/tour-de-piste.json | grep -i "access-control\|vary"

# origine refusée → 403 JSON lisible
curl -s -H "Origin: https://evil.example.com" \
  https://aerolex.prunel.net/aero/t/tour-de-piste.json
```
⚠️ `curl` ne prouve PAS que le navigateur est content : seul un fetch depuis la
vraie page cliente valide la politique CORS côté navigateur.

## Ajouter un domaine client
Éditer `ALLOWED_ORIGINS` dans `serve_cors.py`, puis recharger le service.
Les motifs génériques (`*.domaine.com`) sont spécifiés dans TODO-FEATURES.md §4quater.
