# 🚀 Guide Complet A à Z : Synchronisation Airbnb

**Date** : 25 mai 2026  
**Durée totale** : ~3-4 heures (dont 2-3h automatiques)

---

## 📋 VUE D'ENSEMBLE

```
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1 : PRÉPARATION (5 minutes)                         │
│  ✅ Vérifier Python, Docker, .env                          │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2 : CRÉER LA SESSION AIRBNB (10-15 minutes)         │
│  🔐 Lancer le scraper, résoudre le CAPTCHA                 │
│  📄 Créer output/airbnb_session.json                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 3 : COLLECTER LES URLs iCal (2-3 heures)            │
│  📅 Test sur 3 lofts (5-10 min)                            │
│  📅 Collecte complète 54 lofts (2-3h)                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PHASE 4 : LANCER LA SYNCHRONISATION (5 minutes)           │
│  🐳 Build Docker images                                     │
│  🚀 Lancer ical-watcher + targeted-scraper                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  ✅ SYNCHRONISATION AUTOMATIQUE ACTIVE                      │
│  Détection des changements en ~6 minutes                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 PHASE 1 : PRÉPARATION (5 minutes)

### ✅ Checklist

- [x] Python 3.11+ installé
- [x] Docker Desktop installé et lancé
- [x] Fichier `.env` configuré
- [x] `HEADLESS=false` dans `.env`

### Vérifications

```bash
# Vérifier Python
python --version
# Attendu : Python 3.13.9 ✅

# Vérifier Docker
docker --version
# Attendu : Docker version 29.4.1 ✅

# Vérifier .env
type .env
# Attendu : HEADLESS=false ✅
```

**Tout est OK !** Passez à la phase 2.

---

## 🔐 PHASE 2 : CRÉER LA SESSION AIRBNB (10-15 minutes)

### Objectif

Créer le fichier `output/airbnb_session.json` qui contient les cookies de session Airbnb.

### Commande

```bash
# Double-cliquez sur :
1_creer_session.bat
```

### Ce qui va se passer

1. ✅ Le script vérifie que Python est installé
2. ✅ Le script vérifie que `HEADLESS=false`
3. 🌐 Un navigateur Chrome s'ouvre
4. 🔐 Le script se connecte à Airbnb
5. 🤖 **CAPTCHA DÉTECTÉ** (message dans la console)
6. ⏳ **VOTRE ACTION** : Résolvez le CAPTCHA dans le navigateur
7. ✅ Le script continue automatiquement
8. 💾 Le fichier `output/airbnb_session.json` est créé

### Logs attendus

```
========================================================================
  ÉTAPE 1 : CRÉATION DE LA SESSION AIRBNB
========================================================================

[OK] Python est installé
[OK] HEADLESS=false configuré

========================================================================
  LANCEMENT DU SCRAPER
========================================================================

🔐 Connexion à Airbnb...
✓ Email saisi
🔍 URL après email : https://fr.airbnb.com/login?...

⚠️  ═══════════════════════════════════════════════════════
   🤖 CAPTCHA DÉTECTÉ APRÈS EMAIL
   ═══════════════════════════════════════════════════════

   Airbnb utilise Arkose Labs pour la vérification de sécurité.

   📋 ACTIONS :
   1. ✅ Résolvez le CAPTCHA MANUELLEMENT dans le navigateur ouvert
   2. ⏱️  Le script attendra jusqu'à 5 minutes
   3. 🔄 Une fois résolu, le script continuera automatiquement

   ⏳ En attente de résolution manuelle...
   ═══════════════════════════════════════════════════════

   ⏳ 10s écoulées... (max 300s)
   ⏳ 20s écoulées... (max 300s)
   🔍 Debug: URL=https://fr.airbnb.com/login?... | Password field=False
   ...
   ✅ CAPTCHA résolu ! Champ mot de passe détecté...
```

### Actions à effectuer

1. **Regardez le navigateur Chrome** qui s'est ouvert
2. **Résolvez le CAPTCHA Arkose** (cliquez sur les images)
3. **Attendez** que le script affiche `✅ CAPTCHA résolu !`
4. Le script continue automatiquement

### Vérification

```bash
# Vérifier que la session a été créée
dir output\airbnb_session.json

# Attendu : Le fichier existe ✅
```

### ⚠️ Si problème

**Timeout après 5 minutes** :
- Relancez `1_creer_session.bat`
- Résolvez le CAPTCHA plus rapidement

**Session non créée** :
- Vérifiez vos identifiants dans `.env`
- Vérifiez votre connexion internet
- Relancez `1_creer_session.bat`

---

## 📅 PHASE 3 : COLLECTER LES URLs iCal (2-3 heures)

### Objectif

Récupérer les URLs iCal avec token `?t=` pour les 54 lofts.

### Commande

```bash
# Double-cliquez sur :
2_collecter_ical.bat
```

### Ce qui va se passer

#### Étape 3.1 : Test sur 3 lofts (5-10 minutes)

1. ✅ Le script vérifie que la session existe
2. 🌐 Le navigateur Chrome se lance (réutilise la session)
3. 📍 Navigation vers la page de disponibilité du loft 1
4. 🔘 Clic sur "Associer des calendriers"
5. 🔗 Clic sur "Me connecter à un autre site web"
6. 📸 Capture d'écran sauvegardée
7. 🔗 URL iCal extraite (avec token `?t=`)
8. ✅ URL sauvegardée dans Supabase
9. ⏭️ Répéter pour les lofts 2 et 3

#### Étape 3.2 : Collecte complète (2-3 heures)

Si le test réussit, le script propose de collecter les 54 lofts.

### Logs attendus

```
========================================================================
  ÉTAPE 2 : COLLECTE DES URLs iCal
========================================================================

[OK] Session trouvée : output\airbnb_session.json

Voulez-vous lancer le test sur 3 lofts ? (O/N)
> O

========================================================================
  TEST : COLLECTE SUR 3 LOFTS
========================================================================

═══════════════════════════════════════════════════════
  Collecte des URLs iCal — Test rapide (3 lofts)
  Début : 14:00:00
═══════════════════════════════════════════════════════

📋 3 lofts à traiter

📎 54 URLs iCal déjà en base

⏭️  0 lofts ont déjà une URL iCal avec token — tous à mettre à jour

🌐 Lancement CloakBrowser...
   💾 Session trouvée : output/airbnb_session.json
   🔍 Vérification de la session sauvegardée...
   ✅ Session valide — connexion automatique !

[1/3] Loft Alger Centre (27940108)...
   📍 Navigation vers : https://www.airbnb.com/hosting/listings/27940108/availability
   📸 Capture : output/debug_ical_27940108_availability.png
   🔘 Clic sur : Associer des calendriers
   🔗 Clic sur : Me connecter à un autre site web
   📸 Capture : output/debug_ical_27940108_export.png
   ✅ URL iCal trouvée avec token
   🔗 https://www.airbnb.com/calendar/ical/27940108.ics?t=917150ed...
   ✅ URL iCal mise à jour (token: ?t=)

[2/3] Loft Oran Mer (40739075)...
   ...

[3/3] Loft Constantine (...)...
   ...

═══════════════════════════════════════════════════════
  Résultat : 3 succès, 0 échecs
  Fin : 14:08:00
═══════════════════════════════════════════════════════

Voulez-vous maintenant collecter les 54 lofts ? (O/N)
(Durée estimée : 2-3 heures)
> O

========================================================================
  COLLECTE COMPLÈTE : 54 LOFTS
========================================================================

[INFO] Lancement de la collecte complète...
[INFO] Durée estimée : 2-3 heures
[INFO] Vous pouvez minimiser cette fenêtre

[4/54] ...
[5/54] ...
...
[54/54] ...

═══════════════════════════════════════════════════════
  Résultat : 54 succès, 0 échecs
  Fin : 16:30:00
═══════════════════════════════════════════════════════
```

### Vérification

```sql
-- Compter les URLs avec token
SELECT 
    COUNT(*) FILTER (WHERE ical_url_airbnb LIKE '%?t=%') as with_token,
    COUNT(*) FILTER (WHERE ical_url_airbnb NOT LIKE '%?%') as without_token,
    COUNT(*) as total
FROM property_sync_config
WHERE ical_url_airbnb IS NOT NULL;

-- Attendu :
-- with_token: 54
-- without_token: 0
-- total: 54
```

### 💡 Conseils

- **Vous pouvez minimiser la fenêtre** pendant la collecte
- **Le navigateur se ferme automatiquement** à la fin
- **Les captures d'écran** sont dans `output/debug_ical_*.png`
- **Si une URL échoue**, vérifiez les captures pour voir pourquoi

---

## 🐳 PHASE 4 : LANCER LA SYNCHRONISATION (5 minutes)

### Objectif

Lancer les 2 services Docker :
1. **ical-watcher** : Surveille les calendriers toutes les 5 minutes
2. **targeted-scraper** : Scrape les changements toutes les 30 secondes

### Commande

```bash
# Double-cliquez sur :
3_lancer_sync.bat
```

### Ce qui va se passer

1. ✅ Vérification que Docker est lancé
2. 🔧 Configuration de `HEADLESS=true` dans `.env`
3. 🏗️ Construction de l'image Docker du watcher (~2 minutes)
4. 🏗️ Construction de l'image Docker du scraper (~10-15 minutes)
5. 🚀 Lancement du watcher
6. 🚀 Lancement du targeted scraper

### Logs attendus

```
========================================================================
  ÉTAPE 3 : LANCEMENT DE LA SYNCHRONISATION AUTOMATIQUE
========================================================================

[OK] Docker est installé et lancé

Voulez-vous continuer ? (O/N)
> O

========================================================================
  CHANGEMENT DE CONFIGURATION
========================================================================

[INFO] Configuration de HEADLESS=true pour Docker...
[OK] HEADLESS=true configuré

========================================================================
  CONSTRUCTION DES IMAGES DOCKER
========================================================================

[INFO] Construction de l'image du watcher (légère)...

[+] Building 45.2s (12/12) FINISHED
 => [internal] load build definition from Dockerfile.watcher
 => => transferring dockerfile: 1.23kB
 ...
 => exporting to image
 => => exporting layers
 => => writing image sha256:abc123...

[OK] Image watcher construite

[INFO] Construction de l'image du scraper (complète)...
[INFO] Cela peut prendre 10-15 minutes (première fois)...

[+] Building 645.8s (18/18) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 2.45kB
 ...
 => exporting to image
 => => exporting layers
 => => writing image sha256:def456...

[OK] Image scraper construite

========================================================================
  LANCEMENT DES SERVICES
========================================================================

[INFO] Lancement du watcher...

[+] Running 1/1
 ✔ Container airbnb_ical_watcher  Started

[OK] Watcher lancé

[INFO] Lancement du targeted scraper...

[+] Running 1/1
 ✔ Container airbnb_scraper_targeted  Started

[OK] Targeted scraper lancé

========================================================================
  ✅ SYNCHRONISATION AUTOMATIQUE ACTIVE
========================================================================

Les 2 services sont maintenant actifs :

  ✅ ical-watcher : Surveille les calendriers toutes les 5 minutes
  ✅ targeted-scraper : Scrape les changements toutes les 30 secondes
```

### Vérification

```bash
# Voir les logs du watcher
cd docker
docker compose logs -f airbnb_ical_watcher

# Logs attendus :
# ═══════════════════════════════════════════════════════
#    iCal Watcher — Surveillance des calendriers
#    Intervalle : 300s
#    Supabase   : https://zlpzuyctjhajdwlxzdzk.supabase.co...
# ═══════════════════════════════════════════════════════
# 
# --- Cycle 1 (14:35:00) ---
#    [27940108] Premier hash enregistré
#    [40739075] Premier hash enregistré
#    ...
#    Aucun changement
#    Prochain check dans 300s...
```

```bash
# Voir les logs du scraper
docker compose logs -f airbnb_scraper_targeted

# Logs attendus :
# ═══════════════════════════════════════════════════════
#    Targeted Scraper — Scraping ciblé
#    Intervalle : 30s
#    Supabase   : https://zlpzuyctjhajdwlxzdzk.supabase.co...
# ═══════════════════════════════════════════════════════
# 
# --- Cycle 1 (14:35:00) ---
#    Aucun listing en attente
#    Prochain check dans 30s...
```

---

## ✅ SYNCHRONISATION ACTIVE !

### Ce qui se passe maintenant

```
Toutes les 5 minutes :
  ├─ ical-watcher télécharge les 54 fichiers iCal
  ├─ Calcule les hashes SHA256
  ├─ Compare avec les hashes précédents
  └─ Si changement → pousse dans sync_queue

Toutes les 30 secondes :
  ├─ targeted-scraper lit la sync_queue
  ├─ Si listing en attente :
  │   ├─ Lance Chrome
  │   ├─ Se connecte à Airbnb
  │   ├─ Scrape les réservations du listing
  │   ├─ Envoie à l'API Next.js
  │   └─ Marque comme traité
  └─ Sinon : attend 30 secondes
```

### Délai de synchronisation

```
t=0s     Voyageur réserve sur Airbnb
t=30s    Airbnb met à jour le fichier iCal
t=5min   ical-watcher détecte le changement
t=5min   targeted-scraper scrape le listing
30s
t=6min   Données dans Supabase ✅
```

**Délai total : ~6 minutes** 🚀

---

## 🎛️ COMMANDES UTILES

### Voir les logs

```bash
cd docker

# Logs du watcher
docker compose logs -f airbnb_ical_watcher

# Logs du scraper
docker compose logs -f airbnb_scraper_targeted

# Logs des 2 services
docker compose logs -f
```

### Arrêter les services

```bash
cd docker
docker compose down
```

### Redémarrer les services

```bash
cd docker
docker compose --profile ical --profile targeted up -d
```

### Vérifier l'état des services

```bash
cd docker
docker compose ps
```

---

## 📊 MONITORING

### Vérifier les hashes iCal

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

## 🎉 FÉLICITATIONS !

Vous avez maintenant une **synchronisation automatique temps réel** :

- ✅ **54 URLs iCal** avec token `?t=`
- ✅ **ical-watcher** surveille toutes les 5 minutes
- ✅ **targeted-scraper** scrape les changements
- ✅ **Délai de synchronisation** : ~6 minutes
- ✅ **Automatique** : Aucune intervention manuelle

**Votre système est opérationnel !** 🚀
