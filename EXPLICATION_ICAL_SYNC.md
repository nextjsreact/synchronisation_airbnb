# 📅 Synchronisation iCal : Comment ça fonctionne ?

**Date** : 25 mai 2026  
**Question** : "Qui fait la synchronisation avec les iCal ?"

---

## 🎯 RÉPONSE COURTE

**C'est le service `ical-watcher`** qui surveille les calendriers iCal toutes les 5 minutes et déclenche la synchronisation quand il détecte un changement.

---

## 🏗️ ARCHITECTURE COMPLÈTE

Votre projet a **3 services Docker** qui travaillent ensemble :

```
┌─────────────────────────────────────────────────────────────┐
│  ARCHITECTURE DE SYNCHRONISATION                            │
└─────────────────────────────────────────────────────────────┘

1️⃣  ical-watcher (léger, toujours actif)
    ├─ Poll les URLs iCal toutes les 5 minutes
    ├─ Calcule le hash SHA256 du contenu
    ├─ Détecte les changements
    └─ Pousse dans sync_queue si changement
         ↓
2️⃣  targeted-scraper (CloakBrowser, toujours actif)
    ├─ Lit la sync_queue toutes les 30 secondes
    ├─ Lance Chrome pour scraper le listing spécifique
    ├─ Récupère les réservations
    └─ Envoie à l'API Next.js
         ↓
3️⃣  full-scraper (CloakBrowser, manuel)
    ├─ Scrape TOUS les lofts (53 annonces)
    ├─ Lancé manuellement ou via cron
    └─ Utilisé pour synchronisation complète
```

---

## 📋 SERVICE 1 : iCal Watcher (Surveillance)

### Fichier : `ical_watcher.py`

**Rôle** : Surveiller les calendriers iCal sans navigateur

### Comment ça marche ?

```python
# Boucle infinie toutes les 5 minutes
while True:
    # 1. Récupérer les configs iCal actives depuis Supabase
    configs = get_active_ical_configs()
    # → Lit property_sync_config.ical_url_airbnb
    
    # 2. Pour chaque loft
    for config in configs:
        # Télécharger le fichier iCal via HTTP
        content = fetch_ical(config.ical_url)
        
        # Calculer le hash SHA256 (sans DTSTAMP)
        new_hash = compute_ical_hash(content)
        
        # Comparer avec le hash précédent
        if new_hash != old_hash:
            # CHANGEMENT DÉTECTÉ !
            # → Mettre à jour ical_hashes
            upsert_hash(listing_id, new_hash)
            
            # → Pousser dans sync_queue
            push_to_queue(listing_id)
            print(f"[{listing_id}] CHANGEMENT détecté -> sync_queue")
    
    # Attendre 5 minutes
    time.sleep(300)
```

### Avantages

- ✅ **Léger** : Pas de navigateur, juste des requêtes HTTP
- ✅ **Rapide** : Détecte les changements en ~30 secondes après mise à jour Airbnb
- ✅ **Économique** : ~50MB RAM (vs 2GB pour Chrome)
- ✅ **Fiable** : Pas de CAPTCHA, pas de détection

### Configuration Docker

```yaml
# docker/docker-compose.yml
airbnb-ical-watcher:
  build:
    dockerfile: Dockerfile.watcher  # Image légère sans Chromium
  command: python ical_watcher.py
  environment:
    - ICAL_POLL_INTERVAL=300  # 5 minutes
  restart: unless-stopped
  profiles:
    - ical
```

### Lancement

```bash
# Lancer le watcher
docker compose --profile ical up -d
```

---

## 📋 SERVICE 2 : Targeted Scraper (Scraping ciblé)

### Fichier : `targeted_scraper.py` (non fourni mais référencé)

**Rôle** : Scraper uniquement les listings qui ont changé

### Comment ça marche ?

```python
# Boucle infinie toutes les 30 secondes
while True:
    # 1. Lire la sync_queue
    pending = get_pending_from_queue()
    
    # 2. Pour chaque listing en attente
    for item in pending:
        listing_id = item.listing_id
        
        # Lancer Chrome avec CloakBrowser
        browser = cloak_launch(headless=True)
        page = browser.new_page()
        
        # Se connecter à Airbnb (réutilise session)
        login(page)
        
        # Scraper les réservations du listing spécifique
        reservations = scrape_listing(page, listing_id)
        
        # Envoyer à l'API Next.js
        send_to_api(reservations)
        
        # Marquer comme traité dans sync_queue
        mark_as_processed(item.id)
    
    # Attendre 30 secondes
    time.sleep(30)
```

### Avantages

- ✅ **Ciblé** : Scrape seulement ce qui a changé
- ✅ **Rapide** : 1-2 minutes par listing (vs 1h pour tout scraper)
- ✅ **Économique** : Chrome lancé uniquement quand nécessaire

### Configuration Docker

```yaml
airbnb-scraper-targeted:
  build:
    dockerfile: Dockerfile  # Image complète avec Chromium
  command: python targeted_scraper.py
  environment:
    - TARGETED_POLL_INTERVAL=30  # 30 secondes
    - HEADLESS=true
  restart: unless-stopped
  profiles:
    - targeted
```

### Lancement

```bash
# Lancer le targeted scraper
docker compose --profile targeted up -d
```

---

## 📋 SERVICE 3 : Full Scraper (Scraping complet)

### Fichier : `airbnb_scraper.py`

**Rôle** : Scraper TOUS les lofts (synchronisation complète)

### Quand l'utiliser ?

- 🔄 **Synchronisation initiale** : Première fois
- 🔄 **Synchronisation hebdomadaire** : Via cron pour vérifier la cohérence
- 🔄 **Après problème** : Si le watcher a raté des changements

### Configuration Docker

```yaml
airbnb-scraper-full:
  build:
    dockerfile: Dockerfile
  command: python airbnb_scraper.py
  environment:
    - HEADLESS=true
  restart: "no"  # Manuel uniquement
  profiles:
    - manual
```

### Lancement

```bash
# Lancer le scraper complet
docker compose --profile manual up
```

---

## 🔄 WORKFLOW COMPLET

### Scénario : Nouvelle réservation sur Airbnb

```
t=0s     Voyageur réserve sur Airbnb
         └─ Airbnb met à jour le calendrier

t=30s    Airbnb met à jour le fichier iCal
         └─ URL: https://airbnb.com/calendar/ical/...?signature=...

t=5min   ical-watcher poll l'URL iCal
         ├─ Télécharge le fichier
         ├─ Calcule le hash SHA256
         ├─ Compare avec le hash précédent
         └─ CHANGEMENT DÉTECTÉ !
              ├─ Mise à jour ical_hashes
              └─ Push dans sync_queue

t=5min   targeted-scraper lit la sync_queue
30s      ├─ Voit le listing_id en attente
         ├─ Lance Chrome (CloakBrowser)
         ├─ Se connecte à Airbnb
         ├─ Scrape les réservations du listing
         ├─ Envoie à l'API Next.js
         └─ Marque comme traité

t=6min   API Next.js reçoit les données
         ├─ Insère/met à jour dans Supabase
         ├─ Envoie notification (optionnel)
         └─ Frontend mis à jour en temps réel
```

**Délai total** : ~6 minutes entre la réservation et l'affichage dans votre app ! 🚀

---

## 📊 TABLES SUPABASE

### 1. `property_sync_config`

Stocke les URLs iCal pour chaque loft

```sql
CREATE TABLE property_sync_config (
    id UUID PRIMARY KEY,
    loft_id UUID REFERENCES lofts(id),
    ical_url_airbnb TEXT,  -- URL avec signature
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ
);
```

**Exemple** :
```json
{
  "loft_id": "123e4567-e89b-12d3-a456-426614174000",
  "ical_url_airbnb": "https://www.airbnb.com/calendar/ical/27940108.ics?s=abc123...",
  "is_active": true
}
```

### 2. `ical_hashes`

Stocke les hashes pour détecter les changements

```sql
CREATE TABLE ical_hashes (
    listing_id TEXT PRIMARY KEY,
    hash TEXT NOT NULL,
    checked_at TIMESTAMPTZ,
    changed_at TIMESTAMPTZ
);
```

**Exemple** :
```json
{
  "listing_id": "27940108",
  "hash": "a3f5b2c1d4e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2",
  "checked_at": "2026-05-25T13:00:00Z",
  "changed_at": "2026-05-25T12:55:00Z"
}
```

### 3. `sync_queue`

File d'attente pour le targeted scraper

```sql
CREATE TABLE sync_queue (
    id UUID PRIMARY KEY,
    listing_id TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending, processing, completed, failed
    reason TEXT,  -- ical_change, manual, scheduled
    created_at TIMESTAMPTZ,
    processed_at TIMESTAMPTZ
);
```

**Exemple** :
```json
{
  "id": "456e7890-e89b-12d3-a456-426614174001",
  "listing_id": "27940108",
  "status": "pending",
  "reason": "ical_change",
  "created_at": "2026-05-25T13:05:00Z"
}
```

---

## 🛠️ COLLECTE DES URLs iCal

### Fichier : `collect_ical_urls.py`

**Rôle** : Récupérer les URLs iCal avec signature depuis Airbnb

### Pourquoi ?

Les URLs iCal Airbnb contiennent une **signature** qui change régulièrement :
```
https://www.airbnb.com/calendar/ical/27940108.ics?s=abc123def456...
                                                    ^^^^^^^^^^^^^^^^
                                                    Signature requise
```

Sans signature, l'URL retourne une erreur 403.

### Comment ça marche ?

```python
# 1. Récupérer les lofts depuis Supabase
lofts = get_lofts_to_process()

# 2. Pour chaque loft
for loft in lofts:
    # Lancer Chrome
    browser = cloak_launch()
    page = browser.new_page()
    
    # Se connecter à Airbnb
    login(page)
    
    # Aller sur la page de disponibilité
    page.goto(f"https://www.airbnb.com/hosting/listings/{listing_id}/availability")
    
    # Scraper l'URL iCal (avec signature)
    ical_url = scrape_ical_url(page, listing_id)
    
    # Mettre à jour dans Supabase
    update_ical_in_supabase(loft_id, ical_url)
```

### Lancement

```bash
# Test rapide (3 lofts)
python collect_ical_urls.py

# Tous les lofts (53 annonces)
python collect_ical_urls.py --all
```

**Durée** : ~2-3 minutes par loft (total ~2h pour 53 lofts)

---

## 🚀 MISE EN PRODUCTION

### Étape 1 : Collecter les URLs iCal

```bash
# Première fois : collecter toutes les URLs
python collect_ical_urls.py --all
```

**Résultat** : Table `property_sync_config` remplie avec les URLs iCal

### Étape 2 : Lancer le watcher

```bash
# Lancer le service de surveillance
cd docker
docker compose --profile ical up -d
```

**Résultat** : Le watcher poll les iCal toutes les 5 minutes

### Étape 3 : Lancer le targeted scraper

```bash
# Lancer le service de scraping ciblé
docker compose --profile targeted up -d
```

**Résultat** : Le scraper traite la queue toutes les 30 secondes

### Étape 4 : Vérifier les logs

```bash
# Logs du watcher
docker compose logs -f airbnb_ical_watcher

# Logs du targeted scraper
docker compose logs -f airbnb_scraper_targeted
```

### Étape 5 : Synchronisation complète (optionnel)

```bash
# Une fois par semaine, scraper complet
docker compose --profile manual up
```

---

## 📊 MONITORING

### Vérifier que le watcher fonctionne

```sql
-- Derniers checks
SELECT listing_id, checked_at, changed_at
FROM ical_hashes
ORDER BY checked_at DESC
LIMIT 10;
```

### Vérifier la queue

```sql
-- Items en attente
SELECT * FROM sync_queue
WHERE status = 'pending'
ORDER BY created_at;
```

### Vérifier les changements détectés

```sql
-- Changements des dernières 24h
SELECT listing_id, changed_at
FROM ical_hashes
WHERE changed_at > NOW() - INTERVAL '24 hours'
ORDER BY changed_at DESC;
```

---

## ⚙️ CONFIGURATION

### Variables d'environnement

```env
# ── iCal Watcher ──────────────────────────────────────
ICAL_POLL_INTERVAL=300  # Intervalle de polling (secondes)

# ── Targeted Scraper ──────────────────────────────────
TARGETED_POLL_INTERVAL=30  # Intervalle de lecture queue (secondes)

# ── Supabase ──────────────────────────────────────────
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ── API Next.js ───────────────────────────────────────
NEXTJS_API_URL=http://host.docker.internal:3000/api/airbnb/sync
NEXTJS_API_KEY=votre_clé_api
```

---

## 🎯 AVANTAGES DE CETTE ARCHITECTURE

### 1. **Rapidité** ⚡
- Détection en ~5 minutes (vs 1h pour scraping complet)
- Scraping ciblé en 1-2 minutes (vs 1h pour tout)

### 2. **Économie** 💰
- Watcher : ~50MB RAM (léger)
- Targeted : Chrome lancé uniquement si nécessaire
- Full : Utilisé rarement (1x/semaine)

### 3. **Fiabilité** 🛡️
- iCal : Pas de CAPTCHA, pas de détection
- Scraping : Seulement quand nécessaire
- Queue : Retry automatique en cas d'échec

### 4. **Scalabilité** 📈
- Peut gérer 100+ lofts facilement
- Watcher : O(n) en temps, O(1) en mémoire
- Targeted : Parallélisable (plusieurs workers)

---

## 🔧 DÉPANNAGE

### Le watcher ne détecte pas les changements

**Causes possibles** :
1. URL iCal expirée (signature invalide)
2. Airbnb a changé le format iCal
3. Problème réseau

**Solutions** :
```bash
# Recollecte les URLs iCal
python collect_ical_urls.py --all

# Vérifier les logs
docker compose logs airbnb_ical_watcher
```

### Le targeted scraper ne traite pas la queue

**Causes possibles** :
1. Session Airbnb expirée
2. CAPTCHA requis
3. Problème de connexion

**Solutions** :
```bash
# Vérifier les logs
docker compose logs airbnb_scraper_targeted

# Recréer la session
HEADLESS=false python airbnb_scraper.py
```

---

## 📝 RÉSUMÉ

| Service | Fichier | Rôle | Fréquence | RAM |
|---------|---------|------|-----------|-----|
| **iCal Watcher** | `ical_watcher.py` | Surveille les iCal | 5 min | ~50MB |
| **Targeted Scraper** | `targeted_scraper.py` | Scrape ciblé | 30s | ~2GB |
| **Full Scraper** | `airbnb_scraper.py` | Scrape complet | Manuel | ~2GB |
| **Collect iCal** | `collect_ical_urls.py` | Collecte URLs | 1x/mois | ~2GB |

**Workflow** :
1. 📅 **iCal Watcher** détecte un changement
2. 📝 Pousse dans **sync_queue**
3. 🤖 **Targeted Scraper** lit la queue
4. 🌐 Scrape le listing spécifique
5. 📤 Envoie à l'**API Next.js**
6. 💾 Sauvegarde dans **Supabase**

**Délai total** : ~6 minutes de bout en bout ! 🚀

---

**Vous avez maintenant une architecture de synchronisation temps réel !** 🎉
