# ARCHITECTURE — Airbnb Scraper v2

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                         VPS / Serveur                           │
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   ical-watcher   │    │ targeted-scraper │                  │
│  │  (5 min, léger)  │    │  (sur demande)   │                  │
│  │  sans navigateur │    │  CloakBrowser    │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │ changement             │ scrape                     │
│           ▼ détecté               │                            │
│  ┌────────────────┐               │                            │
│  │  sync_queue    │───────────────┘                            │
│  │  (Supabase)    │                                            │
│  └────────────────┘                                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              full-scraper (cron 2h du matin)             │  │
│  │         airbnb_scraper.py — CloakBrowser stealth         │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ upsert
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Supabase                               │
│                                                                 │
│  reservations  listings  ical_hashes  sync_queue  sync_logs    │
│                                                                 │
│  Row Level Security · Realtime · PostgreSQL                     │
└─────────────────────────────────────┬───────────────────────────┘
                                      │ websocket realtime
                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Next.js sur Vercel                           │
│                                                                 │
│  API Routes · Server Components · Supabase Realtime             │
│  Dashboard réservations mis à jour instantanément              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flux de données — Nouvelle réservation

```
t=0    Voyageur réserve sur Airbnb
t=30s  Airbnb met à jour le fichier iCal de l'annonce
t=5min iCal Watcher détecte le hash différent
t=5min push_to_queue(listing_id) → sync_queue
t=6min targeted_scraper lit la queue
t=6min CloakBrowser se connecte à Airbnb
t=8min scrape de l'annonce → réservation récupérée
t=8min upsert_reservations() → Supabase
t=8min Supabase Realtime notifie Next.js
t=8min Dashboard mis à jour ✅
```

---

## Services Docker

| Service | Image | Restart | RAM | Rôle |
|---------|-------|---------|-----|------|
| `ical-watcher` | Dockerfile.watcher (légère) | always | ~50MB | Surveille les iCal |
| `targeted-scraper` | Dockerfile (CloakBrowser) | always | ~2GB | Scrape ciblé |
| `full-scraper` | Dockerfile (CloakBrowser) | no | ~3GB | Scrape complet (cron) |

---

## Tables Supabase

### reservations
```sql
id               TEXT PRIMARY KEY  -- Code de confirmation Airbnb
statut           TEXT              -- confirmed, cancelled, etc.
voyageur         TEXT
nb_voyageurs     INTEGER
logement         TEXT
listing_id       TEXT
date_arrivee     DATE
date_depart      DATE
nb_nuits         INTEGER
montant_total    NUMERIC
devise           TEXT              -- GBP, EUR, USD
date_creation    TIMESTAMP
scraped_at       TIMESTAMP         -- Quand scraper a récupéré la donnée
updated_at       TIMESTAMP         -- Mis à jour automatiquement (trigger)
```

### listings
```sql
listing_id       TEXT PRIMARY KEY
nom              TEXT
ical_url         TEXT              -- URL iCal collectée par le scraper
actif            BOOLEAN
created_at       TIMESTAMP
updated_at       TIMESTAMP
```

### ical_hashes
```sql
listing_id       TEXT PRIMARY KEY  -- FK → listings
hash             TEXT              -- SHA256 du contenu iCal (sans DTSTAMP)
checked_at       TIMESTAMP         -- Dernière vérification
changed_at       TIMESTAMP         -- Dernier changement détecté
```

### sync_queue
```sql
id               BIGSERIAL PRIMARY KEY
listing_id       TEXT
status           TEXT              -- pending | processing | done | error
reason           TEXT              -- ical_change | manual
created_at       TIMESTAMP
processed_at     TIMESTAMP
error_message    TEXT
```

### sync_logs
```sql
id               BIGSERIAL PRIMARY KEY
type             TEXT              -- full | targeted | ical_check
status           TEXT              -- success | error | partial
listings_count   INTEGER
reservations_count INTEGER
duration_seconds NUMERIC
error_message    TEXT
created_at       TIMESTAMP
```

---

## Sécurité

- **Row Level Security (RLS)** activé sur toutes les tables
- **service_role** : accès complet (scraper Python)
- **anon/authenticated** : lecture seule (Next.js frontend)
- **Identifiants** : jamais dans le code, uniquement dans `.env`
- **Docker** : utilisateur non-root dans les containers
- **CloakBrowser** : anti-detection (fingerprint, canvas, WebGL) — ne résout PAS les CAPTCHAs

---

## Choix technologiques

| Technologie | Pourquoi |
|-------------|----------|
| **CloakBrowser** | Anti-detection (fingerprint, canvas, WebGL, humanize) — pas anti-CAPTCHA |
| **iCal polling** | Léger (HTTP simple), pas de navigateur, mis à jour dans les secondes par Airbnb |
| **Supabase** | PostgreSQL managé + Realtime websocket intégré + RLS |
| **Docker** | Isolation, reproductibilité, déploiement VPS simple |
| **Python sync** | CloakBrowser v0.3.x n'a pas d'API async — sync évite les conflits asyncio |
