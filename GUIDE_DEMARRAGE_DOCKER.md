# 🚀 Guide de Démarrage : Docker + VNC

**Date** : 30 mai 2026  
**Version** : 2.0.1  
**Architecture** : Docker avec VNC pour résolution CAPTCHA

---

## 📋 RÉSUMÉ RAPIDE

Vous avez configuré un système Docker complet avec VNC pour automatiser le scraping Airbnb. Voici les 3 étapes simples :

```
1️⃣  Créer la session Airbnb (résoudre CAPTCHA via VNC)
    → Lancez : 1_creer_session.bat

2️⃣  Collecter les URLs iCal avec tokens
    → Lancez : 2_collecter_ical.bat

3️⃣  Lancer la synchronisation automatique
    → Lancez : 3_lancer_sync.bat
```

---

## 🎯 ARCHITECTURE

Votre configuration Docker permet de :
- ✅ Exécuter le scraper dans un container isolé
- ✅ Voir le navigateur Chrome via VNC (http://localhost:6080)
- ✅ Résoudre les CAPTCHAs manuellement dans l'interface VNC
- ✅ Sauvegarder la session pour éviter les CAPTCHAs futurs
- ✅ Lancer des services de synchronisation en arrière-plan

```
┌─────────────────────────────────────────────────────────────┐
│  DOCKER CONTAINER                                            │
│                                                              │
│  Xvfb :99 (Display virtuel)                                 │
│    └─ Chrome (CloakBrowser)                                 │
│       └─ Airbnb (avec CAPTCHA visible)                      │
│                                                              │
│  x11vnc :5900 (Serveur VNC)                                 │
│  noVNC :6080 (Client web VNC)                               │
│                                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  VOTRE NAVIGATEUR                                            │
│  http://localhost:6080                                       │
│  → Vous voyez Chrome dans le container                      │
│  → Vous résolvez le CAPTCHA                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 PRÉREQUIS

### 1. Docker Desktop installé

Vérifiez :
```cmd
docker --version
```

Si pas installé : https://www.docker.com/products/docker-desktop

### 2. Fichier `.env` configuré

Votre `.env` doit contenir :
```env
AIRBNB_EMAIL=loft.algerie.scl@gmail.com
AIRBNB_PASSWORD=loft.algerie.2026
TOTP_SECRET=135790
HEADLESS=false
NEXTJS_API_URL=http://host.docker.internal:3000/api/airbnb/sync
NEXTJS_API_KEY=NXxmDRrHzvb4I+SuGdZv9kGvd574bnhVctjKcz0rR1s=
```

**Important** : `HEADLESS=false` pour voir le navigateur dans VNC

### 3. API Next.js en cours d'exécution

L'API doit être accessible sur `http://localhost:3000/api/airbnb/sync`

---

## 🔧 ÉTAPE 1 : CRÉER LA SESSION AIRBNB

### Lancer le script

```cmd
1_creer_session.bat
```

### Ce qui se passe

1. **Build de l'image Docker** (première fois : 10-15 min)
   - Installe Python, Playwright, CloakBrowser
   - Installe Xvfb, x11vnc, noVNC, fluxbox
   - Prépare l'environnement

2. **Lancement du container**
   - Démarre le display virtuel (Xvfb)
   - Démarre le serveur VNC (x11vnc)
   - Démarre l'interface web VNC (noVNC)
   - Lance le scraper

3. **Logs attendus**
   ```
   airbnb-scraper  | 🖥️  Démarrage du display virtuel (Xvfb)...
   airbnb-scraper  | 🪟  Démarrage du window manager (fluxbox)...
   airbnb-scraper  | 📡 Démarrage du serveur VNC (x11vnc)...
   airbnb-scraper  | 🌐 Démarrage de noVNC sur le port 6080...
   airbnb-scraper  | 
   airbnb-scraper  | ═══════════════════════════════════════════════════════
   airbnb-scraper  |    🔗 Interface VNC : http://localhost:6080
   airbnb-scraper  | ═══════════════════════════════════════════════════════
   airbnb-scraper  | 
   airbnb-scraper  | 🔐 Connexion à Airbnb...
   airbnb-scraper  | ✓ Email saisi
   airbnb-scraper  | 
   airbnb-scraper  | ⚠️  ═══════════════════════════════════════════════════════
   airbnb-scraper  |    🤖 CAPTCHA DÉTECTÉ APRÈS EMAIL
   airbnb-scraper  |    ═══════════════════════════════════════════════════════
   ```

### Résoudre le CAPTCHA

1. **Ouvrez votre navigateur** sur : http://localhost:6080
2. **Vous verrez** l'interface noVNC avec Chrome et Airbnb
3. **Résolvez le CAPTCHA** Arkose (cliquez sur les images)
4. **Attendez** que le script continue automatiquement

### Résultat

Le fichier `output\airbnb_session.json` est créé ✅

Cette session sera réutilisée pour éviter les CAPTCHAs futurs.

---

## 📅 ÉTAPE 2 : COLLECTER LES URLs iCal

### Lancer le script

```cmd
2_collecter_ical.bat
```

### Ce qui se passe

1. **Test sur 3 lofts** (5-10 minutes)
   - Vérifie que la collecte fonctionne
   - Extrait les URLs iCal avec tokens (`?t=...`)
   - Sauvegarde dans l'API Next.js

2. **Collecte complète sur 54 lofts** (2-3 heures)
   - Parcourt tous les lofts
   - Extrait les URLs iCal avec tokens
   - Sauvegarde dans l'API Next.js

### Commandes Docker utilisées

```cmd
# Test sur 3 lofts
docker compose run --rm airbnb-scraper python collect_ical_urls.py

# Collecte complète
docker compose run --rm airbnb-scraper python collect_ical_urls.py --all
```

### Résultat

Les 54 URLs iCal avec tokens sont sauvegardées dans l'API Next.js ✅

---

## 🔄 ÉTAPE 3 : LANCER LA SYNCHRONISATION AUTOMATIQUE

### Lancer le script

```cmd
3_lancer_sync.bat
```

### Ce qui se passe

1. **Configuration automatique**
   - Change `HEADLESS=true` dans `.env`
   - Crée `docker-compose.sync.yml`

2. **Lancement de 2 services Docker**

   **Service 1 : ical-watcher**
   - Poll les URLs iCal toutes les 5 minutes
   - Détecte les changements via hash SHA256
   - Pousse dans la queue de synchronisation
   - RAM : ~50MB

   **Service 2 : targeted-scraper**
   - Lit la queue toutes les 30 secondes
   - Scrape uniquement les listings qui ont changé
   - Envoie à l'API Next.js
   - RAM : ~2GB

### Commandes utiles

```cmd
# Voir les logs de tous les services
docker compose -f docker-compose.sync.yml logs -f

# Voir les logs d'un service spécifique
docker compose -f docker-compose.sync.yml logs -f ical-watcher
docker compose -f docker-compose.sync.yml logs -f targeted-scraper

# Voir l'état des containers
docker compose -f docker-compose.sync.yml ps

# Arrêter les services
docker compose -f docker-compose.sync.yml down

# Redémarrer les services
docker compose -f docker-compose.sync.yml restart
```

### Résultat

La synchronisation automatique est active ✅

Les réservations Airbnb sont synchronisées en temps réel (~6 minutes de délai).

---

## 🎛️ COMMANDES DOCKER UTILES

### Voir les containers en cours

```cmd
docker ps
```

### Voir les logs d'un container

```cmd
docker logs -f airbnb-scraper
docker logs -f ical-watcher
docker logs -f targeted-scraper
```

### Entrer dans un container

```cmd
docker compose exec airbnb-scraper bash
```

### Arrêter tous les containers

```cmd
docker compose down
docker compose -f docker-compose.sync.yml down
```

### Nettoyer les images Docker

```cmd
# Supprimer les images non utilisées
docker image prune -a

# Supprimer les volumes non utilisés
docker volume prune
```

---

## 🔍 DEBUGGING

### Problème : VNC ne s'affiche pas

**Vérifier que le port est exposé** :
```cmd
docker compose ps
```
Attendu : `0.0.0.0:6080->6080/tcp`

**Vérifier que noVNC est démarré** :
```cmd
docker compose logs airbnb-scraper | findstr noVNC
```
Attendu : `Démarrage de noVNC sur le port 6080...`

**Tester l'accès** :
```cmd
curl http://localhost:6080
```

### Problème : CAPTCHA non détecté

**Vérifier les logs** :
```cmd
docker compose logs airbnb-scraper | findstr CAPTCHA
```

**Vérifier les captures d'écran** :
```cmd
dir output\debug_captcha_*.png
```

### Problème : Session non créée

**Vérifier le volume** :
```cmd
docker compose exec airbnb-scraper ls -la /app/output/
```

**Vérifier sur Windows** :
```cmd
dir output\airbnb_session.json
```

### Problème : Container s'arrête immédiatement

**Voir les logs** :
```cmd
docker compose logs airbnb-scraper
```

**Vérifier le fichier .env** :
```cmd
type .env
```

---

## 📊 WORKFLOW COMPLET

```
1. Build l'image Docker
   → 1_creer_session.bat (première fois)
   ↓
2. Lancer le container
   → Container démarre avec VNC
   ↓
3. Accéder à VNC
   → http://localhost:6080
   ↓
4. Résoudre le CAPTCHA
   → Dans l'interface VNC
   ↓
5. Session créée
   → output/airbnb_session.json ✅
   ↓
6. Collecter les URLs iCal
   → 2_collecter_ical.bat
   ↓
7. Lancer la synchronisation
   → 3_lancer_sync.bat
   ↓
8. Synchronisation automatique active ✅
```

---

## 🎯 RÉSUMÉ

### Fichiers importants

- `docker-compose.yml` : Configuration du container principal
- `docker-compose.sync.yml` : Configuration des services de synchronisation (créé automatiquement)
- `Dockerfile` : Image Docker avec VNC
- `entrypoint.sh` : Script de démarrage (Xvfb → x11vnc → noVNC → scraper)
- `.env` : Variables d'environnement

### Ports exposés

- `6080` : noVNC (interface web VNC)
- `5900` : VNC natif (optionnel)

### Volumes

- `./output:/app/output` : Fichiers CSV/JSON/session

### Scripts batch

- `1_creer_session.bat` : Créer la session Airbnb (Docker + VNC)
- `2_collecter_ical.bat` : Collecter les URLs iCal (Docker)
- `3_lancer_sync.bat` : Lancer la synchronisation (Docker)

---

## ✅ CHECKLIST

- [ ] Docker Desktop installé
- [ ] Fichier `.env` configuré
- [ ] API Next.js en cours d'exécution
- [ ] Session Airbnb créée (`output\airbnb_session.json`)
- [ ] URLs iCal collectées (54 lofts)
- [ ] Synchronisation automatique lancée

---

**Vous êtes prêt pour Docker + VNC !** 🐳🚀

Pour toute question, consultez `GUIDE_DOCKER_VNC.md` pour plus de détails.
