# 🚀 Airbnb Scraper - Mode Production

**Version** : 2.0.0  
**Date** : 25 mai 2026

---

## ⚡ DÉMARRAGE RAPIDE

### Option 1 : Scripts automatiques (Recommandé)

```bash
# ÉTAPE 1 : Première connexion (résoudre CAPTCHA)
setup_first_run.bat

# ÉTAPE 2 : Mode production Docker
setup_docker_production.bat
```

### Option 2 : Commandes manuelles

```bash
# ÉTAPE 1 : Première connexion
python airbnb_scraper.py
# → Résolvez le CAPTCHA manuellement

# ÉTAPE 2 : Changez .env
# HEADLESS=true

# ÉTAPE 3 : Docker
docker compose build
docker compose up
```

---

## 📋 PRÉREQUIS

- [x] Python 3.11+ installé
- [x] Docker Desktop installé et lancé
- [x] Fichier `.env` configuré avec vos identifiants Airbnb
- [x] Connexion internet stable

---

## 🎯 WORKFLOW COMPLET

### 1️⃣ Première connexion (une seule fois)

**Objectif** : Résoudre le CAPTCHA et créer la session

```bash
# Lancez le script automatique
setup_first_run.bat
```

**Ou manuellement** :

```bash
# 1. Vérifiez .env
HEADLESS=false

# 2. Lancez
python airbnb_scraper.py

# 3. Résolvez le CAPTCHA dans le navigateur Chrome
# 4. Attendez que output/airbnb_session.json soit créé
```

### 2️⃣ Mode production Docker

**Objectif** : Automatiser le scraping sans CAPTCHA

```bash
# Lancez le script automatique
setup_docker_production.bat
```

**Ou manuellement** :

```bash
# 1. Changez .env
HEADLESS=true

# 2. Build Docker
docker compose build

# 3. Lancez
docker compose up
```

---

## 📁 STRUCTURE DES FICHIERS

```
D:\Airbnb_transfer_v2\
├── .env                          ← Configuration (identifiants)
├── airbnb_scraper.py             ← Script principal
├── airbnb_api_client.py          ← Client API Next.js
├── docker-compose.yml            ← Configuration Docker
├── Dockerfile                    ← Image Docker
├── requirements.txt              ← Dépendances Python
│
├── setup_first_run.bat           ← Script 1 : Première connexion
├── setup_docker_production.bat   ← Script 2 : Mode production
│
├── output/                       ← Fichiers générés
│   ├── airbnb_session.json       ← Session persistante (IMPORTANT)
│   ├── browser_profile/          ← Profil Chrome persistant
│   ├── reservations_airbnb.csv   ← Export CSV
│   └── reservations_airbnb.json  ← Export JSON
│
└── docs/                         ← Documentation
    ├── GUIDE_EXECUTION.md        ← Docker vs Local
    ├── setup_production.md       ← Guide détaillé
    ├── CAPTCHA_SOLUTION.md       ← Gestion des CAPTCHAs
    └── ...
```

---

## 🔧 CONFIGURATION `.env`

```env
# ── Identifiants Airbnb ──────────────────────────────────
AIRBNB_EMAIL=votre@email.com
AIRBNB_PASSWORD=votre_mot_de_passe
TOTP_SECRET=votre_secret_2fa

# ── Mode d'exécution ─────────────────────────────────────
HEADLESS=false  # false pour première connexion, true pour Docker

# ── Proxy (optionnel mais recommandé) ────────────────────
PROXY_URL=http://username:password@proxy-provider.com:port

# ── API Next.js ──────────────────────────────────────────
NEXTJS_API_URL=http://localhost:3000/api/airbnb/sync
NEXTJS_API_KEY=votre_clé_api

# ── Fichiers de sortie ───────────────────────────────────
OUTPUT_CSV=output/reservations_airbnb.csv
OUTPUT_JSON=output/reservations_airbnb.json
```

---

## 🐳 COMMANDES DOCKER

```bash
# Construire l'image
docker compose build

# Lancer le scraper (foreground)
docker compose up

# Lancer en arrière-plan
docker compose up -d

# Voir les logs
docker compose logs -f

# Arrêter
docker compose down

# Reconstruire et lancer
docker compose up --build

# Nettoyer tout
docker compose down -v
```

---

## ⚠️ PROBLÈMES COURANTS

### "Session invalide" en Docker

**Cause** : Le fichier `output/airbnb_session.json` n'existe pas

**Solution** :
```bash
# Relancez la première connexion
setup_first_run.bat
```

### CAPTCHA redemandé

**Cause** : Session expirée ou IP suspecte

**Solution** :
1. Supprimez `output/airbnb_session.json`
2. Configurez un proxy résidentiel dans `.env`
3. Relancez `setup_first_run.bat`

### Timeout lors du chargement

**Cause** : Connexion lente ou Airbnb bloque

**Solution** :
1. Vérifiez votre connexion internet
2. Utilisez un proxy résidentiel
3. Augmentez le timeout dans le script (ligne ~148)

### Docker ne démarre pas

**Cause** : Docker Desktop pas lancé

**Solution** :
1. Lancez Docker Desktop
2. Attendez qu'il soit complètement démarré (icône verte)
3. Relancez `setup_docker_production.bat`

---

## 📊 MONITORING

### Vérifier que tout fonctionne

```bash
# Vérifier la session
dir output\airbnb_session.json

# Vérifier les exports
dir output\reservations_airbnb.csv
dir output\reservations_airbnb.json

# Voir les logs Docker
docker compose logs --tail=50
```

### Automatisation quotidienne

**Windows Task Scheduler** :
1. Ouvrez Task Scheduler
2. Créez une nouvelle tâche
3. Déclencheur : Tous les jours à 2h du matin
4. Action : `docker compose up`
5. Répertoire : `D:\Airbnb_transfer_v2`

---

## 💡 CONSEILS

### Proxy résidentiel (fortement recommandé)

Un proxy résidentiel réduit drastiquement les CAPTCHAs :

```env
PROXY_URL=http://username:password@proxy-provider.com:port
```

**Providers recommandés** :
- Bright Data (ex-Luminati) - https://brightdata.com
- Smartproxy - https://smartproxy.com
- Oxylabs - https://oxylabs.io

### Backup de la session

Sauvegardez régulièrement votre session :

```bash
copy output\airbnb_session.json output\airbnb_session.backup.json
```

### Logs détaillés

Pour plus de logs en Docker :

```bash
docker compose up --verbose
```

---

## 📚 DOCUMENTATION

- **GUIDE_EXECUTION.md** : Docker vs Local, quand utiliser chaque mode
- **setup_production.md** : Guide détaillé du passage en production
- **CAPTCHA_SOLUTION.md** : Tout sur les CAPTCHAs Arkose
- **FIX_CAPTCHA_DETECTION.md** : Correction de la détection CAPTCHA
- **FIX_TIMEOUT_CHARGEMENT.md** : Résolution des timeouts

---

## 🆘 SUPPORT

### Logs de debug

En cas de problème, partagez :

1. **Logs du script** :
   ```bash
   python airbnb_scraper.py > logs.txt 2>&1
   ```

2. **Logs Docker** :
   ```bash
   docker compose logs > docker_logs.txt
   ```

3. **Captures d'écran** :
   - `output/debug_captcha_*.png`
   - `output/debug_no_password_field.html`

### Checklist de diagnostic

- [ ] Python 3.11+ installé : `python --version`
- [ ] Docker installé et lancé : `docker --version`
- [ ] Fichier `.env` configuré
- [ ] Session créée : `output/airbnb_session.json` existe
- [ ] Connexion internet stable
- [ ] Docker Desktop lancé (icône verte)

---

## ✅ CHECKLIST DE PRODUCTION

Avant de passer en production :

- [ ] ✅ CAPTCHA résolu au moins une fois
- [ ] ✅ `output/airbnb_session.json` existe
- [ ] ✅ `output/browser_profile/` existe
- [ ] ✅ `.env` configuré avec `HEADLESS=true`
- [ ] ✅ Docker Desktop installé et lancé
- [ ] ✅ `docker compose build` réussi
- [ ] ✅ `docker compose up` fonctionne sans CAPTCHA
- [ ] ✅ Les réservations sont récupérées
- [ ] ✅ Les fichiers CSV/JSON sont créés

---

## 🎉 RÉSUMÉ

1. **Première fois** : `setup_first_run.bat` → Résoudre CAPTCHA → Session créée
2. **Production** : `setup_docker_production.bat` → Docker → Plus de CAPTCHA
3. **Automatisation** : Task Scheduler → Scraping quotidien automatique

**C'est tout ! Vous êtes prêt pour la production.** 🚀
