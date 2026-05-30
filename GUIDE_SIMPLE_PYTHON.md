# 🚀 Guide Simple : Synchronisation Airbnb (Python uniquement)

**Date** : 25 mai 2026  
**Durée totale** : ~3-4 heures (dont 2-3h automatiques)  
**Prérequis** : Python 3.11+ (pas besoin de Docker !)

---

## 📋 VUE D'ENSEMBLE SIMPLIFIÉE

```
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 1 : CRÉER LA SESSION AIRBNB (10-15 minutes)         │
│  🔐 Lancer airbnb_scraper.py, résoudre le CAPTCHA          │
│  📄 Créer output/airbnb_session.json                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 : COLLECTER LES URLs iCal (2-3 heures)            │
│  📅 Lancer collect_ical_urls.py                            │
│  📅 Récupérer les URLs avec token ?t= pour 54 lofts        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  ÉTAPE 3 : LANCER LA SYNCHRONISATION (continu)             │
│  🔄 Lancer ical_watcher.py (fenêtre 1)                     │
│  🤖 Lancer targeted_scraper.py (fenêtre 2) - si disponible │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  ✅ SYNCHRONISATION AUTOMATIQUE ACTIVE                      │
│  Détection des changements en ~6 minutes                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 ÉTAPE 1 : CRÉER LA SESSION AIRBNB (10-15 min)

### Commande

```bash
# Double-cliquez sur :
1_creer_session.bat

# Ou lancez directement :
python airbnb_scraper.py
```

### Ce qui va se passer

1. ✅ Un navigateur Chrome s'ouvre
2. 🔐 Le script se connecte à Airbnb
3. 🤖 **CAPTCHA DÉTECTÉ** (message dans la console)
4. ⏳ **VOTRE ACTION** : Résolvez le CAPTCHA dans le navigateur
5. ✅ Le script continue automatiquement
6. 💾 Le fichier `output/airbnb_session.json` est créé

### Vérification

```bash
# Vérifier que la session existe
dir output\airbnb_session.json

# Attendu : Le fichier existe ✅
```

---

## 📅 ÉTAPE 2 : COLLECTER LES URLs iCal (2-3 heures)

### Commande

```bash
# Double-cliquez sur :
2_collecter_ical.bat

# Ou lancez directement :
# Test sur 3 lofts (5-10 min)
python collect_ical_urls.py

# Tous les lofts (2-3 heures)
python collect_ical_urls.py --all
```

### Ce qui va se passer

1. ✅ Le script vérifie que la session existe
2. 🌐 Le navigateur Chrome se lance (réutilise la session)
3. 📍 Pour chaque loft :
   - Navigation vers la page de disponibilité
   - Clic sur "Associer des calendriers"
   - Clic sur "Me connecter à un autre site web"
   - Extraction de l'URL iCal avec token `?t=`
   - Sauvegarde dans Supabase
4. 📸 Captures d'écran sauvegardées dans `output/`

### Vérification

```sql
-- Compter les URLs avec token
SELECT 
    COUNT(*) FILTER (WHERE ical_url_airbnb LIKE '%?t=%') as with_token,
    COUNT(*) as total
FROM property_sync_config
WHERE ical_url_airbnb IS NOT NULL;

-- Attendu : with_token = 54, total = 54
```

---

## 🔄 ÉTAPE 3 : LANCER LA SYNCHRONISATION (continu)

### Option A : Avec le script batch (recommandé)

```bash
# Double-cliquez sur :
3_lancer_sync.bat
```

Le script lance automatiquement les 2 services dans des fenêtres séparées.

### Option B : Manuellement

#### Fenêtre 1 : Lancer le watcher

```bash
# Ouvrir une fenêtre PowerShell/CMD
python ical_watcher.py
```

**Ce service** :
- Poll les URLs iCal toutes les 5 minutes
- Détecte les changements (hash SHA256)
- Pousse dans `sync_queue` si changement

**Logs attendus** :
```
═══════════════════════════════════════════════════════
   iCal Watcher — Surveillance des calendriers
   Intervalle : 300s
   Supabase   : https://zlpzuyctjhajdwlxzdzk.supabase.co...
═══════════════════════════════════════════════════════

--- Cycle 1 (14:00:00) ---
   [27940108] Premier hash enregistré
   [40739075] Premier hash enregistré
   ...
   Aucun changement
   Prochain check dans 300s...

--- Cycle 2 (14:05:00) ---
   Aucun changement
   Prochain check dans 300s...
```

#### Fenêtre 2 : Lancer le targeted scraper (si disponible)

```bash
# Ouvrir une autre fenêtre PowerShell/CMD
python targeted_scraper.py
```

**Ce service** :
- Lit la `sync_queue` toutes les 30 secondes
- Lance Chrome pour scraper les listings en attente
- Envoie les données à l'API Next.js

**Note** : Si `targeted_scraper.py` n'existe pas encore, ce n'est pas grave. Le watcher fonctionnera quand même et détectera les changements.

---

## 🎛️ GESTION DES SERVICES

### Voir les logs

Les logs s'affichent directement dans les fenêtres PowerShell/CMD.

### Arrêter les services

- **Fermez les fenêtres** PowerShell/CMD
- Ou appuyez sur **Ctrl+C** dans chaque fenêtre

### Redémarrer les services

Relancez simplement :
```bash
3_lancer_sync.bat
```

Ou manuellement :
```bash
# Fenêtre 1
python ical_watcher.py

# Fenêtre 2 (si disponible)
python targeted_scraper.py
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

## 🔧 CONFIGURATION

### Variables d'environnement (.env)

```env
# ── Identifiants Airbnb ──────────────────────────────────
AIRBNB_EMAIL=loft.algerie.scl@gmail.com
AIRBNB_PASSWORD=loft.algerie.2026
TOTP_SECRET=135790

# ── Mode d'exécution ─────────────────────────────────────
HEADLESS=false  # false pour étape 1 et 2, true pour étape 3

# ── Supabase ──────────────────────────────────────────────
NEXT_PUBLIC_SUPABASE_URL=https://zlpzuyctjhajdwlxzdzk.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# ── API Next.js ───────────────────────────────────────────
NEXTJS_API_URL=http://localhost:3000/api/airbnb/sync
NEXTJS_API_KEY=NXxmDRrHzvb4I+SuGdZv9kGvd574bnhVctjKcz0rR1s=

# ── iCal Watcher ──────────────────────────────────────────
ICAL_POLL_INTERVAL=300  # 5 minutes
```

---

## ⚠️ DIFFÉRENCES AVEC DOCKER

### Avantages de l'approche Python locale

✅ **Plus simple** : Pas besoin d'installer Docker  
✅ **Plus rapide** : Pas de build d'images  
✅ **Plus facile à débugger** : Logs directement dans la console  
✅ **Plus flexible** : Facile de modifier et relancer  

### Inconvénients

❌ **Moins isolé** : Les services partagent l'environnement Python  
❌ **Moins robuste** : Si une fenêtre se ferme, le service s'arrête  
❌ **Pas de restart automatique** : Il faut relancer manuellement  

### Quand utiliser Docker ?

- **Production** : Pour un serveur qui tourne 24/7
- **Automatisation** : Pour des services qui redémarrent automatiquement
- **Isolation** : Pour éviter les conflits entre projets

### Quand utiliser Python local ?

- **Développement** : Pour tester et débugger
- **Utilisation ponctuelle** : Pour lancer manuellement quand nécessaire
- **Simplicité** : Quand Docker n'est pas nécessaire

---

## 🎯 WORKFLOW COMPLET

### Scénario : Nouvelle réservation sur Airbnb

```
t=0s     Voyageur réserve sur Airbnb
         └─ Airbnb met à jour le calendrier

t=30s    Airbnb met à jour le fichier iCal
         └─ URL: https://airbnb.com/calendar/ical/...?t=...

t=5min   ical_watcher.py poll l'URL iCal
         ├─ Télécharge le fichier
         ├─ Calcule le hash SHA256
         ├─ Compare avec le hash précédent
         └─ CHANGEMENT DÉTECTÉ !
              ├─ Mise à jour ical_hashes
              └─ Push dans sync_queue

t=5min   targeted_scraper.py lit la sync_queue
30s      ├─ Voit le listing_id en attente
         ├─ Lance Chrome (CloakBrowser)
         ├─ Se connecte à Airbnb
         ├─ Scrape les réservations du listing
         ├─ Envoie à l'API Next.js
         └─ Marque comme traité

t=6min   API Next.js reçoit les données
         ├─ Insère/met à jour dans Supabase
         └─ Frontend mis à jour en temps réel
```

**Délai total : ~6 minutes** 🚀

---

## 🎉 RÉSUMÉ

### Ce que vous avez maintenant

✅ **Session Airbnb** : `output/airbnb_session.json`  
✅ **54 URLs iCal** : Avec token `?t=` dans Supabase  
✅ **ical_watcher.py** : Surveille les changements toutes les 5 minutes  
✅ **targeted_scraper.py** : Scrape les changements (si disponible)  

### Commandes essentielles

```bash
# Créer la session
python airbnb_scraper.py

# Collecter les URLs iCal
python collect_ical_urls.py --all

# Lancer la synchronisation
python ical_watcher.py
```

### Prochaines étapes

1. ✅ Lancez `1_creer_session.bat`
2. ✅ Lancez `2_collecter_ical.bat`
3. ✅ Lancez `3_lancer_sync.bat`
4. 🎉 Profitez de la synchronisation automatique !

---

**Pas besoin de Docker ! Tout fonctionne avec Python.** 🚀
