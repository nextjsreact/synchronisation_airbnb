# 🐳 Guide Complet : Docker avec VNC pour Airbnb Scraper

**Date** : 25 mai 2026  
**Architecture** : Docker + VNC (noVNC) pour résoudre les CAPTCHAs

---

## 🎯 ARCHITECTURE

Vous avez configuré Docker avec **VNC** pour pouvoir résoudre les CAPTCHAs directement dans le container :

```
┌─────────────────────────────────────────────────────────────┐
│  DOCKER CONTAINER (airbnb-scraper)                          │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Xvfb :99 (Display virtuel 1280x800)               │    │
│  │  ├─ fluxbox (Window Manager)                       │    │
│  │  └─ Chrome (CloakBrowser)                          │    │
│  │     └─ Airbnb (avec CAPTCHA visible)               │    │
│  └────────────────────────────────────────────────────┘    │
│                      ▲                                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  x11vnc :5900 (Serveur VNC)                        │    │
│  └────────────────────────────────────────────────────┘    │
│                      ▲                                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  noVNC :6080 (Client web VNC)                      │    │
│  └────────────────────────────────────────────────────┘    │
│                      │                                       │
└──────────────────────┼───────────────────────────────────────┘
                       │ Port 6080 exposé
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  VOTRE NAVIGATEUR                                            │
│  http://localhost:6080                                       │
│  → Vous voyez Chrome dans le container                      │
│  → Vous résolvez le CAPTCHA                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 PLAN D'ACTION COMPLET

### PHASE 1 : Build l'image Docker (10-15 min)
### PHASE 2 : Lancer le container et résoudre le CAPTCHA (10-15 min)
### PHASE 3 : Collecter les URLs iCal (2-3 heures)
### PHASE 4 : Lancer la synchronisation automatique (continu)

---

## 🏗️ PHASE 1 : BUILD L'IMAGE DOCKER

### Étape 1.1 : Vérifier Docker

```bash
docker --version
# Attendu : Docker version 29.4.1 ✅
```

### Étape 1.2 : Vérifier la configuration

Votre `.env` doit avoir :
```env
HEADLESS=false  # Important pour voir le navigateur dans VNC
```

### Étape 1.3 : Build l'image

```bash
# Aller à la racine du projet
cd D:\Airbnb_transfer_v2

# Build l'image Docker
docker compose build
```

**Durée** : ~10-15 minutes (première fois)

**Ce qui est installé** :
- Python 3.11
- Playwright + Chromium
- CloakBrowser
- Xvfb (display virtuel)
- x11vnc (serveur VNC)
- noVNC (client web VNC)
- fluxbox (window manager)

---

## 🔐 PHASE 2 : CRÉER LA SESSION AIRBNB

### Étape 2.1 : Lancer le container

```bash
docker compose up
```

**Logs attendus** :
```
airbnb-scraper  | 🖥️  Démarrage du display virtuel (Xvfb)...
airbnb-scraper  | 🪟  Démarrage du window manager (fluxbox)...
airbnb-scraper  | 📡 Démarrage du serveur VNC (x11vnc)...
airbnb-scraper  | 🌐 Démarrage de noVNC sur le port 6080...
airbnb-scraper  | 
airbnb-scraper  | ═══════════════════════════════════════════════════════
airbnb-scraper  |    🔗 Interface VNC : http://localhost:6080
airbnb-scraper  |    🔗 VNC natif    : localhost:5900
airbnb-scraper  | ═══════════════════════════════════════════════════════
airbnb-scraper  | 
airbnb-scraper  | 🔐 Connexion à Airbnb...
airbnb-scraper  | ✓ Email saisi
airbnb-scraper  | 🔍 URL après email : https://fr.airbnb.com/login?...
airbnb-scraper  | 
airbnb-scraper  | ⚠️  ═══════════════════════════════════════════════════════
airbnb-scraper  |    🤖 CAPTCHA DÉTECTÉ APRÈS EMAIL
airbnb-scraper  |    ═══════════════════════════════════════════════════════
```

### Étape 2.2 : Accéder à VNC

Ouvrez votre navigateur et allez sur :
```
http://localhost:6080
```

**Vous devriez voir** :
- Interface noVNC (client VNC web)
- Le bureau virtuel avec fluxbox
- Le navigateur Chrome avec Airbnb
- Le CAPTCHA Arkose visible

### Étape 2.3 : Résoudre le CAPTCHA

1. **Dans l'interface VNC** (http://localhost:6080)
2. **Cliquez sur le CAPTCHA** Arkose
3. **Résolvez les images** demandées
4. **Attendez la validation**

**Dans les logs Docker**, vous verrez :
```
airbnb-scraper  |    ⏳ 10s écoulées... (max 300s)
airbnb-scraper  |    ⏳ 20s écoulées... (max 300s)
airbnb-scraper  |    🔍 Debug: URL=https://fr.airbnb.com/login?... | Password field=False
airbnb-scraper  |    📸 Capture sauvegardée : output/debug_captcha_30s.png
airbnb-scraper  |    ...
airbnb-scraper  |    ✅ CAPTCHA résolu ! Champ mot de passe détecté...
```

### Étape 2.4 : Vérifier la session

Le container va créer le fichier `output/airbnb_session.json`.

```bash
# Vérifier que la session existe
dir output\airbnb_session.json

# Attendu : Le fichier existe ✅
```

---

## 📅 PHASE 3 : COLLECTER LES URLs iCal

### Option A : Dans le même container

Si le scraper principal a réussi, vous pouvez lancer la collecte dans le même container :

```bash
# Entrer dans le container
docker compose exec airbnb-scraper bash

# Lancer la collecte
python collect_ical_urls.py --all
```

### Option B : Nouveau container dédié

Créez un nouveau service dans `docker-compose.yml` :

```yaml
services:
  # ... airbnb-scraper existant ...

  # Service de collecte iCal
  ical-collector:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ical-collector
    env_file:
      - .env
    ports:
      - "6081:6080"  # Port VNC différent
      - "5901:5900"
    volumes:
      - ./output:/app/output
    shm_size: "2gb"
    mem_limit: "4g"
    command: python collect_ical_urls.py --all
    profiles:
      - collect
```

Puis lancez :
```bash
docker compose --profile collect up
```

Accédez à VNC sur : `http://localhost:6081`

---

## 🔄 PHASE 4 : SYNCHRONISATION AUTOMATIQUE

### Étape 4.1 : Changer HEADLESS=true

Une fois la session créée, changez dans `.env` :
```env
HEADLESS=true  # Plus besoin de VNC maintenant
```

### Étape 4.2 : Lancer les services de synchronisation

Vous avez 2 options :

#### Option A : Utiliser le docker-compose dans `docker/`

```bash
cd docker

# Lancer le watcher (surveillance iCal)
docker compose --profile ical up -d

# Lancer le targeted scraper (scraping ciblé)
docker compose --profile targeted up -d

# Voir les logs
docker compose logs -f
```

#### Option B : Créer un docker-compose simplifié à la racine

Créez `docker-compose.sync.yml` :

```yaml
services:
  # Watcher iCal
  ical-watcher:
    build:
      context: .
      dockerfile: Dockerfile.watcher
    container_name: ical-watcher
    env_file:
      - .env
    restart: unless-stopped
    command: python ical_watcher.py

  # Targeted scraper
  targeted-scraper:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: targeted-scraper
    env_file:
      - .env
    volumes:
      - ./output:/app/output
    shm_size: "2gb"
    mem_limit: "4g"
    restart: unless-stopped
    command: python targeted_scraper.py
```

Puis lancez :
```bash
docker compose -f docker-compose.sync.yml up -d
```

---

## 🎛️ COMMANDES UTILES

### Voir les logs

```bash
# Logs du scraper principal
docker compose logs -f airbnb-scraper

# Logs du watcher
docker compose logs -f ical-watcher

# Logs du targeted scraper
docker compose logs -f targeted-scraper
```

### Arrêter les services

```bash
# Arrêter tout
docker compose down

# Arrêter un service spécifique
docker compose stop airbnb-scraper
```

### Redémarrer les services

```bash
# Redémarrer tout
docker compose up -d

# Redémarrer un service spécifique
docker compose restart airbnb-scraper
```

### Entrer dans un container

```bash
# Entrer dans le container
docker compose exec airbnb-scraper bash

# Lister les fichiers
ls -la output/

# Vérifier la session
cat output/airbnb_session.json
```

---

## 🔍 DEBUGGING

### Problème : VNC ne s'affiche pas

**Vérifier que le port est exposé** :
```bash
docker compose ps
# Vérifier que 6080:6080 est listé
```

**Vérifier que noVNC est démarré** :
```bash
docker compose logs airbnb-scraper | grep noVNC
# Attendu : "Démarrage de noVNC sur le port 6080..."
```

**Tester l'accès** :
```bash
curl http://localhost:6080
# Attendu : HTML de noVNC
```

### Problème : CAPTCHA non détecté

**Vérifier les logs** :
```bash
docker compose logs airbnb-scraper | grep CAPTCHA
```

**Vérifier les captures d'écran** :
```bash
dir output\debug_captcha_*.png
```

### Problème : Session non créée

**Vérifier le volume** :
```bash
docker compose exec airbnb-scraper ls -la /app/output/
```

**Vérifier les permissions** :
```bash
# Sur Windows, pas de problème de permissions normalement
dir output\
```

---

## 📊 WORKFLOW COMPLET

```
1. Build l'image Docker
   docker compose build
   ↓
2. Lancer le container
   docker compose up
   ↓
3. Accéder à VNC
   http://localhost:6080
   ↓
4. Résoudre le CAPTCHA
   (dans l'interface VNC)
   ↓
5. Session créée
   output/airbnb_session.json ✅
   ↓
6. Collecter les URLs iCal
   docker compose exec airbnb-scraper python collect_ical_urls.py --all
   ↓
7. Changer HEADLESS=true
   ↓
8. Lancer la synchronisation
   cd docker
   docker compose --profile ical --profile targeted up -d
   ↓
9. Synchronisation automatique active ✅
```

---

## 🎯 RÉSUMÉ

### Votre configuration Docker

✅ **Dockerfile** : Installe Xvfb, x11vnc, noVNC, fluxbox  
✅ **entrypoint.sh** : Démarre tous les services VNC  
✅ **docker-compose.yml** : Expose les ports 6080 et 5900  
✅ **HEADLESS=false** : Pour voir le navigateur dans VNC  

### Workflow

1. **Build** : `docker compose build`
2. **Lancer** : `docker compose up`
3. **VNC** : `http://localhost:6080`
4. **CAPTCHA** : Résoudre dans VNC
5. **Session** : Créée automatiquement
6. **Collecter** : URLs iCal avec token
7. **Sync** : Lancer les services de synchronisation

---

**Vous êtes prêt pour Docker + VNC !** 🐳🚀
