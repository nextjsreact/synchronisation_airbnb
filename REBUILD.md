# REBUILD airbnb-scraper-full

> Documentation des conditions de rebuild du scraper complet.
> Le service est en profile `manual` + `restart: "no"` : il ne se lance jamais automatiquement.

## Statut actuel (2026-06-07)

- **Code source** : `airbnb_scraper.py:1248-1260` patché (préserve `original_currency_code` + `original_amount`)
- **Image Docker** : ❌ Non rebuildée (fix dormant)
- **Service démarré** : ❌ Non (profile=manual)

## Quand rebuild ?

Rebuild **UNIQUEMENT** si l'un de ces cas :

| # | Cas | Risque accepté | Commande |
|---|---|---|---|
| 1 | Ré-import complet nécessaire (re-mapping massif) | Élevé | `docker-compose -f docker/docker-compose.yml --profile manual build airbnb-scraper-full` |
| 2 | Pannage du targeted-scraper (queue bloquée) | Moyen | Idem |
| 3 | Test nouvelle extraction iCal (Aida/Madina HTTP 400) | Moyen | Idem |
| 4 | Validation du fix devise en conditions réelles | Faible* | Idem |

*Faible si on scrape 1 seul loft de test (via override `command`), pas les 54.

## Comment lancer après rebuild

```bash
# Rebuild
docker-compose -f docker/docker-compose.yml --profile manual build airbnb-scraper-full

# Run (⚠️ lance le full scrape des 54 lofts)
docker-compose -f docker/docker-compose.yml --profile manual up airbnb-scraper-full

# Run sur 1 loft spécifique (override command)
docker run --rm -it \
  --env-file .env \
  -v airbnb-output:/app/output \
  airbnb_scraper_full \
  python airbnb_scraper.py --loft_id <LOFT_ID>
```

## ⚠️ Risques du full scrape

- **30+ min d'exécution** (54 lofts)
- **Rate limit Airbnb** → CAPTCHAs → ban potentiel
- **Surcharge API Next.js** (POST batch × 54)
- **Duplicates** : le full scraper ne respecte pas le `sync_queue` (il scrape tout)
- **Overwrite** : `source: "airbnb_scraper"` écrasera les fixes `original_currency_code` des futures résas

## Alternative : utiliser le targeted-scraper

Le `targeted-scraper` (en prod) est **préférable** au full scraper :
- Traite uniquement la `sync_queue` (pas de duplicates)
- Pas de rate limit (1 loft à la fois)
- Intégré au workflow ical-watcher → monitoring
- Fix devise déjà appliqué et rebuild

## Fichiers liés

- `D:\Airbnb_transfer_v2\airbnb_scraper.py:1248-1260` : fix devise (préserve original_*)
- `D:\Airbnb_transfer_v2\docker\docker-compose.yml:7-38` : service `airbnb-scraper-full` (profile=manual)
- `D:\Airbnb_transfer_v2\entrypoint.sh:46` : `python airbnb_scraper.py` (CMD par défaut)
