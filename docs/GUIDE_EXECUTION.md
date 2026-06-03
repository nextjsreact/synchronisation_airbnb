# 🚀 Guide d'exécution : Docker vs Local

**Date** : 25 mai 2026  
**Projet** : Airbnb Scraper v2.0.0

---

## 📋 DEUX MODES D'EXÉCUTION

Ce projet peut s'exécuter de **deux façons différentes** :

| Mode | Quand l'utiliser | HEADLESS | Avantages | Inconvénients |
|------|------------------|----------|-----------|---------------|
| **🐳 Docker** | Production, automatisation | `true` | Isolation, reproductible, déploiement facile | ❌ Ne peut pas résoudre CAPTCHA manuellement |
| **💻 Local** | Développement, debug, CAPTCHA | `false` | ✅ Voir le navigateur, résoudre CAPTCHA | Dépendances à installer manuellement |

---

## 🎯 VOTRE SITUATION ACTUELLE

### Problème : CAPTCHA Arkose après email

Airbnb affiche un CAPTCHA qui **doit être résolu manuellement**. 

**❌ Mode Docker ne fonctionne PAS** pour ce cas car :
- Le navigateur est en mode headless (invisible)
- Vous ne pouvez pas voir le CAPTCHA
- Vous ne pouvez pas cliquer dessus

**✅ Mode Local est NÉCESSAIRE** pour :
- Voir le navigateur Chrome s'ouvrir
- Résoudre le CAPTCHA manuellement
- Sauvegarder la session après résolution

---

## 🔄 WORKFLOW RECOMMANDÉ

### Étape 1 : Première connexion (Mode Local)

**Objectif** : Résoudre le CAPTCHA et sauvegarder la session

```bash
# 1. Assurez-vous que HEADLESS=false dans .env
HEADLESS=false

# 2. Lancez le script en mode local
python airbnb_scraper.py

# 3. Résolvez le CAPTCHA manuellement dans le navigateur
# 4. La session sera sauvegardée dans output/airbnb_session.json
```

**Résultat** : Fichier `output/airbnb_session.json` créé avec vos cookies de session

### Étape 2 : Exécutions suivantes (Mode Docker)

**Objectif** : Utiliser la session sauvegardée, plus de CAPTCHA

```bash
# 1. Changez HEADLESS=true dans .env
HEADLESS=true

# 2. Construisez l'image Docker (première fois seulement)
docker compose build

# 3. Lancez le scraper
docker compose up

# 4. Le script réutilise output/airbnb_session.json
# 5. Plus de CAPTCHA ! 🎉
```

---

## 🐳 MODE DOCKER (Production)

### Prérequis

- Docker Desktop installé
- Docker Compose installé
- Fichier `.env` configuré

### Configuration `.env` pour Docker

```env
AIRBNB_EMAIL=votre@email.com
AIRBNB_PASSWORD=votre_mot_de_passe
TOTP_SECRET=votre_secret_2fa

# ⚠️ IMPORTANT : Mode headless pour Docker
HEADLESS=true

# Proxy résidentiel (recommandé)
PROXY_URL=http://username:password@proxy-provider.com:port

# API Next.js
NEXTJS_API_URL=http://localhost:3000/api/airbnb/sync
NEXTJS_API_KEY=votre_clé_api

# Fichiers de sortie
OUTPUT_CSV=output/reservations_airbnb.csv
OUTPUT_JSON=output/reservations_airbnb.json
```

### Commandes Docker

```bash
# Construire l'image (première fois ou après modifications)
docker compose build

# Lancer le scraper
docker compose up

# Lancer en arrière-plan
docker compose up -d

# Voir les logs
docker compose logs -f

# Arrêter
docker compose down

# Reconstruire et lancer
docker compose up --build
```

### Structure des volumes

```
./output/  ← Volume monté dans le container
├── airbnb_session.json       ← Session persistante
├── reservations_airbnb.csv   ← Export CSV
├── reservations_airbnb.json  ← Export JSON
└── browser_profile/          ← Profil Chrome persistant
```

**Important** : Le dossier `output/` est partagé entre votre machine et le container Docker.

---

## 💻 MODE LOCAL (Développement/Debug)

### Prérequis

- Python 3.11+ installé
- Anaconda ou environnement virtuel
- Dépendances installées

### Installation des dépendances

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Installer Playwright et Chromium
playwright install chromium
playwright install-deps chromium
```

### Configuration `.env` pour Local

```env
AIRBNB_EMAIL=votre@email.com
AIRBNB_PASSWORD=votre_mot_de_passe
TOTP_SECRET=votre_secret_2fa

# ⚠️ IMPORTANT : Mode non-headless pour voir le navigateur
HEADLESS=false

# Proxy résidentiel (optionnel mais recommandé)
PROXY_URL=

# API Next.js
NEXTJS_API_URL=http://localhost:3000/api/airbnb/sync
NEXTJS_API_KEY=votre_clé_api

# Fichiers de sortie
OUTPUT_CSV=output/reservations_airbnb.csv
OUTPUT_JSON=output/reservations_airbnb.json
```

### Commandes Local

```bash
# Lancer le scraper
python airbnb_scraper.py

# Avec debug Python
python -u airbnb_scraper.py

# Vérifier la syntaxe
python -m py_compile airbnb_scraper.py
```

---

## 🎯 CAS D'USAGE

### Cas 1 : Première utilisation (jamais connecté)

**Problème** : Airbnb affiche un CAPTCHA  
**Solution** : Mode Local

```bash
# 1. Configurez .env avec HEADLESS=false
# 2. Lancez : python airbnb_scraper.py
# 3. Résolvez le CAPTCHA dans le navigateur
# 4. La session est sauvegardée
# 5. Passez en mode Docker pour les prochaines fois
```

### Cas 2 : Session expirée

**Problème** : Le script dit "Session invalide" ou redemande le CAPTCHA  
**Solution** : Mode Local pour reconnecter

```bash
# 1. Supprimez output/airbnb_session.json
# 2. Changez HEADLESS=false dans .env
# 3. Lancez : python airbnb_scraper.py
# 4. Résolvez le CAPTCHA
# 5. Repassez en mode Docker
```

### Cas 3 : Automatisation quotidienne

**Problème** : Scraper doit tourner tous les jours automatiquement  
**Solution** : Mode Docker avec cron

```bash
# 1. Assurez-vous que output/airbnb_session.json existe
# 2. Configurez .env avec HEADLESS=true
# 3. Ajoutez un cron job :
0 2 * * * cd /path/to/project && docker compose up
```

### Cas 4 : Développement/Debug

**Problème** : Besoin de voir ce qui se passe dans le navigateur  
**Solution** : Mode Local

```bash
# 1. HEADLESS=false dans .env
# 2. python airbnb_scraper.py
# 3. Observez le navigateur en temps réel
```

---

## 🔍 DIAGNOSTIC

### Le script fonctionne en local mais pas en Docker

**Causes possibles** :
1. ❌ `output/airbnb_session.json` n'existe pas dans le volume
2. ❌ `HEADLESS=true` mais CAPTCHA requis
3. ❌ Proxy non accessible depuis le container

**Solutions** :
1. Vérifiez que le volume `./output` est bien monté
2. Faites une première connexion en mode local
3. Testez le proxy : `docker compose exec airbnb-scraper curl -x $PROXY_URL https://www.airbnb.com`

### Le script timeout en Docker

**Causes possibles** :
1. ❌ Pas assez de mémoire (Chromium gourmand)
2. ❌ Réseau Docker lent
3. ❌ Proxy non configuré

**Solutions** :
1. Augmentez `mem_limit` dans docker-compose.yml (actuellement 2GB)
2. Utilisez `network_mode: host` dans docker-compose.yml
3. Configurez `PROXY_URL` dans .env

---

## 📊 COMPARAISON DÉTAILLÉE

| Aspect | Docker | Local |
|--------|--------|-------|
| **Installation** | Docker Desktop | Python + Playwright + Chromium |
| **Dépendances** | Tout inclus dans l'image | À installer manuellement |
| **Isolation** | ✅ Container isolé | ❌ Utilise l'environnement système |
| **Reproductibilité** | ✅ Identique partout | ❌ Dépend de l'OS/config |
| **Performance** | Légèrement plus lent | Plus rapide |
| **Mémoire** | ~2GB (container) | ~1GB (processus) |
| **Résolution CAPTCHA** | ❌ Impossible (headless) | ✅ Possible (navigateur visible) |
| **Automatisation** | ✅ Idéal (cron, CI/CD) | ⚠️ Possible mais moins robuste |
| **Debug** | ⚠️ Difficile (logs uniquement) | ✅ Facile (voir le navigateur) |
| **Déploiement VPS** | ✅ Simple (docker compose) | ⚠️ Complexe (dépendances) |

---

## 🎯 RECOMMANDATION FINALE

### Pour votre cas actuel (CAPTCHA à résoudre)

**Utilisez le mode LOCAL** :

```bash
# 1. Vérifiez .env
HEADLESS=false

# 2. Lancez
python airbnb_scraper.py

# 3. Résolvez le CAPTCHA manuellement

# 4. Vérifiez que output/airbnb_session.json est créé

# 5. Pour les prochaines fois, passez en Docker :
HEADLESS=true
docker compose up
```

### Pour la production (après première connexion)

**Utilisez le mode DOCKER** :

```bash
# 1. Assurez-vous que output/airbnb_session.json existe
# 2. Configurez .env avec HEADLESS=true
# 3. Lancez : docker compose up
# 4. Automatisez avec cron si besoin
```

---

## ❓ FAQ

### Pourquoi ne pas toujours utiliser le mode local ?

Le mode local fonctionne, mais Docker offre :
- ✅ Isolation (pas de conflit avec d'autres projets)
- ✅ Reproductibilité (même environnement partout)
- ✅ Déploiement facile (un seul fichier docker-compose.yml)
- ✅ Gestion des ressources (limites mémoire/CPU)

### Puis-je résoudre le CAPTCHA en Docker ?

Non, pas avec le setup actuel. Il faudrait :
- Utiliser un service de résolution de CAPTCHA (2Captcha, CapSolver)
- Ou utiliser un proxy résidentiel de très haute qualité
- Ou faire la première connexion en local puis passer en Docker

### La session expire-t-elle ?

Oui, après quelques jours/semaines. Quand ça arrive :
1. Supprimez `output/airbnb_session.json`
2. Relancez en mode local avec `HEADLESS=false`
3. Résolvez le CAPTCHA
4. Repassez en mode Docker

---

**Vous avez maintenant tous les outils pour choisir le bon mode d'exécution !** 🚀
