# CHANGELOG — Airbnb Scraper

Toutes les modifications notables de ce projet sont documentées ici.
Format : [Version] — Date — Description

---

## [2.0.0] — Mai 2026

### Nouveautés
- **Intégration Supabase complète** — les réservations sont poussées
  automatiquement vers Supabase après chaque scrape
- **iCal Watcher** (`ical_watcher.py`) — surveille les 85 annonces toutes
  les 5 minutes sans lancer de navigateur, détecte les nouvelles réservations
- **Targeted Scraper** (`targeted_scraper.py`) — scrape ciblé d'une seule
  annonce quand un changement iCal est détecté (~2 min de délai)
- **Client Supabase partagé** (`supabase_client.py`) — fonctions upsert,
  gestion de la queue, logs de synchronisation
- **Collecte des URLs iCal** — le scrape complet collecte automatiquement
  les URLs iCal de chaque annonce et les stocke dans la table `listings`
- **Schéma SQL Supabase** (`sql/schema.sql`) — 5 tables avec RLS, index,
  triggers `updated_at`
- **3 services Docker** — `ical-watcher`, `targeted-scraper`, `full-scraper`
- **Dockerfile.watcher** — image légère (pas de Chromium) pour le watcher
- **Logs de synchronisation** — chaque run est enregistré dans `sync_logs`
- **Architecture 3 couches** — délai moyen de synchronisation < 10 minutes

### Améliorations
- `airbnb_scraper.py` conserve toute la logique v1 + 3 étapes supplémentaires :
  collecte iCal, push Supabase, log sync
- Export CSV + JSON local conservé en parallèle du push Supabase
- Meilleure gestion des erreurs avec logs détaillés

### Fichiers ajoutés
```
ical_watcher.py
targeted_scraper.py
supabase_client.py
sql/schema.sql
Dockerfile.watcher
requirements.watcher.txt
docs/GUIDE_UTILISATEUR.md
docs/ARCHITECTURE.md
CHANGELOG.md
```

---

## [1.0.0] — Mai 2026

### Version initiale — développée par Karim TIGUI

#### Fonctionnalités
- **CloakBrowser stealth** — anti-detection navigateur (fingerprint, canvas, WebGL, humanize)
  Ne résout PAS les CAPTCHAs — la session authentifiée + proxy résidentiel les évitent
- **Fallback Playwright** — si CloakBrowser non installé, bascule
  automatiquement sur Playwright standard
- **Double méthode de scraping** :
  - API GraphQL interne d'Airbnb (méthode principale)
  - Interception réseau + pagination UI (fallback)
- **Fusion intelligente** — dédoublonnage par ID de confirmation,
  complétion des champs vides entre les deux méthodes
- **Gestion 2FA complète** :
  - Code SMS / Email (saisie manuelle dans le terminal)
  - TOTP automatique via Google Authenticator / Authy (pyotp)
  - Lien email (pause manuelle)
- **Sélecteurs email robustes** — 8 sélecteurs CSS testés en cascade
- **Parser multi-structure** — s'adapte aux différentes versions de l'API Airbnb
  (`_extract_field`, `_parse_earnings`, `_parse_reservation_node`)
- **Pagination complète** — scrape les 3 catégories (upcoming/completed/all)
  avec clic automatique sur "Suivant"
- **Export CSV + JSON** avec encodage UTF-8
- **Fichiers de debug** — réponse API brute sauvegardée pour diagnostic
- **Docker complet** — Dockerfile, docker-compose.yml, entrypoint.sh
- **Configuration via .env** — aucun identifiant dans le code
- **Mode headless automatique** en Docker, navigateur visible en local

#### Données exportées par réservation
| Champ | Description |
|-------|-------------|
| id | Code de confirmation Airbnb |
| statut | État de la réservation |
| voyageur | Prénom du voyageur |
| nb_voyageurs | Nombre de personnes |
| logement | Nom de l'annonce |
| listing_id | ID de l'annonce Airbnb |
| date_arrivee | Date d'arrivée |
| date_depart | Date de départ |
| nb_nuits | Durée du séjour |
| montant_total | Revenus hôte |
| devise | Devise (GBP, EUR, USD) |
| date_creation | Date de réservation |

#### Problèmes résolus durant le développement
- ❌ `cloakbrowser>=0.9.0` n'existait pas → corrigé en `>=0.3.28`
- ❌ `version` obsolète dans docker-compose → supprimé
- ❌ `await cloak_launch()` bloquait silencieusement → API sync détectée
- ❌ Conflit asyncio + Playwright sync via `asyncio.to_thread` → script
  réécrit en 100% synchrone
- ❌ `wait_for_load_state("networkidle")` timeout → remplacé par
  `wait_for_timeout` avec délais fixes
