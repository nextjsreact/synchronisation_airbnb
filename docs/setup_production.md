# 🚀 Setup Mode Production

**Objectif** : Passer en mode production avec Docker après avoir résolu le CAPTCHA

---

## ⚠️ PRÉREQUIS OBLIGATOIRE

**Vous devez d'abord créer la session Airbnb en résolvant le CAPTCHA une fois.**

Airbnb affiche un CAPTCHA Arkose qui nécessite une interaction humaine. Docker en mode headless ne peut pas le résoudre.

---

## 📋 ÉTAPE 1 : Résoudre le CAPTCHA (une seule fois)

### 1.1 Vérifiez que HEADLESS=false dans .env

Le fichier `.env` a été mis à jour avec :
```env
HEADLESS=false
```

### 1.2 Lancez le script en mode local

```bash
python airbnb_scraper.py
```

### 1.3 Résolvez le CAPTCHA

Quand vous voyez ce message :
```
⚠️  ═══════════════════════════════════════════════════════
   🤖 CAPTCHA DÉTECTÉ APRÈS EMAIL
   ═══════════════════════════════════════════════════════
```

**Actions** :
1. Regardez le navigateur Chrome qui s'est ouvert
2. Résolvez le CAPTCHA Arkose (cliquez sur les images)
3. Attendez que le script affiche : `✅ CAPTCHA résolu !`
4. Le script continuera automatiquement

### 1.4 Vérifiez que la session est créée

Après connexion réussie, vérifiez :
```bash
dir output\airbnb_session.json
```

**Attendu** : Le fichier doit exister et contenir des cookies de session.

---

## 📋 ÉTAPE 2 : Passer en mode production Docker

### 2.1 Changez HEADLESS=true dans .env

```env
HEADLESS=true
```

### 2.2 Vérifiez que la session existe

```bash
# Le fichier doit exister
dir output\airbnb_session.json

# Le dossier browser_profile doit exister
dir output\browser_profile
```

### 2.3 Construisez l'image Docker

```bash
docker compose build
```

**Durée** : ~5-10 minutes (première fois, télécharge ~500MB)

### 2.4 Lancez le scraper en production

```bash
docker compose up
```

**Attendu** :
```
airbnb-scraper  | ═══════════════════════════════════════════════════════
airbnb-scraper  | Airbnb Scraper — v2.0.0
airbnb-scraper  | Démarré le : 25/05/2026 13:30
airbnb-scraper  | Moteur     : CloakBrowser (stealth) ✅
airbnb-scraper  | Headless   : Oui
airbnb-scraper  | API Next.js: Activé ✅
airbnb-scraper  | ═══════════════════════════════════════════════════════
airbnb-scraper  | 🕵️  Mode stealth activé
airbnb-scraper  | 🔐 Connexion à Airbnb...
airbnb-scraper  | ✅ Session valide réutilisée !
airbnb-scraper  | 📊 Récupération des réservations...
```

**Plus de CAPTCHA !** 🎉

---

## 🔄 AUTOMATISATION (Optionnel)

### Option 1 : Lancer en arrière-plan

```bash
docker compose up -d
```

### Option 2 : Cron job quotidien

Ajoutez dans votre crontab (Linux/Mac) ou Task Scheduler (Windows) :

```bash
# Tous les jours à 2h du matin
0 2 * * * cd D:\Airbnb_transfer_v2 && docker compose up
```

### Option 3 : Redémarrage automatique

Modifiez `docker-compose.yml` :
```yaml
restart: "always"  # Au lieu de "no"
```

---

## 🔍 VÉRIFICATIONS

### La session est-elle valide ?

```bash
# Vérifiez la taille du fichier (doit être > 1KB)
dir output\airbnb_session.json

# Vérifiez le contenu (doit contenir des cookies)
type output\airbnb_session.json
```

### Le volume Docker est-il monté ?

```bash
# Lancez le container
docker compose up -d

# Vérifiez que le fichier est accessible dans le container
docker compose exec airbnb-scraper ls -la /app/output/airbnb_session.json
```

**Attendu** : Le fichier doit être visible dans le container.

### Les logs Docker

```bash
# Voir les logs en temps réel
docker compose logs -f

# Voir les dernières 50 lignes
docker compose logs --tail=50
```

---

## ⚠️ PROBLÈMES COURANTS

### Problème 1 : "Session invalide" en Docker

**Cause** : Le fichier `output/airbnb_session.json` n'existe pas ou est corrompu

**Solution** :
```bash
# 1. Arrêtez Docker
docker compose down

# 2. Supprimez la session
del output\airbnb_session.json

# 3. Changez HEADLESS=false dans .env
# 4. Relancez en local : python airbnb_scraper.py
# 5. Résolvez le CAPTCHA
# 6. Repassez en mode Docker
```

### Problème 2 : CAPTCHA redemandé en Docker

**Cause** : La session a expiré ou Airbnb détecte quelque chose

**Solution** :
```bash
# 1. Utilisez un proxy résidentiel
PROXY_URL=http://username:password@proxy-provider.com:port

# 2. Recréez la session en mode local
# 3. Relancez en Docker
```

### Problème 3 : Timeout en Docker

**Cause** : Pas assez de mémoire ou réseau lent

**Solution** :
```yaml
# Dans docker-compose.yml, augmentez :
mem_limit: "4g"  # Au lieu de 2g
shm_size: "4gb"  # Au lieu de 2gb
```

### Problème 4 : Le container crash immédiatement

**Cause** : Erreur dans le script ou dépendances manquantes

**Solution** :
```bash
# Voir les logs d'erreur
docker compose logs

# Reconstruire l'image
docker compose build --no-cache

# Relancer
docker compose up
```

---

## 📊 CHECKLIST DE PRODUCTION

Avant de passer en production, vérifiez :

- [ ] ✅ CAPTCHA résolu au moins une fois en mode local
- [ ] ✅ Fichier `output/airbnb_session.json` existe
- [ ] ✅ Dossier `output/browser_profile/` existe
- [ ] ✅ `.env` configuré avec `HEADLESS=true`
- [ ] ✅ Docker Desktop installé et lancé
- [ ] ✅ `docker compose build` réussi
- [ ] ✅ `docker compose up` fonctionne sans CAPTCHA
- [ ] ✅ Les réservations sont récupérées
- [ ] ✅ Les fichiers CSV/JSON sont créés dans `output/`

---

## 🎯 COMMANDES RAPIDES

```bash
# ── ÉTAPE 1 : Première connexion (local) ──────────────────
python airbnb_scraper.py
# → Résolvez le CAPTCHA manuellement

# ── ÉTAPE 2 : Vérification ────────────────────────────────
dir output\airbnb_session.json
# → Le fichier doit exister

# ── ÉTAPE 3 : Changez .env ────────────────────────────────
# HEADLESS=true

# ── ÉTAPE 4 : Build Docker ────────────────────────────────
docker compose build

# ── ÉTAPE 5 : Lancer en production ────────────────────────
docker compose up

# ── ÉTAPE 6 : Automatisation (optionnel) ──────────────────
docker compose up -d  # Arrière-plan
```

---

## 💡 CONSEILS

### Proxy résidentiel (fortement recommandé)

Ajoutez dans `.env` :
```env
PROXY_URL=http://username:password@proxy-provider.com:port
```

**Avantages** :
- ✅ Moins de CAPTCHAs
- ✅ Session plus stable
- ✅ Moins de détection

**Providers recommandés** :
- Bright Data (ex-Luminati)
- Smartproxy
- Oxylabs

### Surveillance

Ajoutez un monitoring pour être alerté en cas d'échec :
```bash
# Exemple avec un webhook
docker compose up || curl -X POST https://your-webhook.com/alert
```

### Backup de la session

```bash
# Sauvegardez régulièrement
copy output\airbnb_session.json output\airbnb_session.backup.json
```

---

## 🚀 RÉSUMÉ

1. **Première fois** : Mode local (`HEADLESS=false`) → Résoudre CAPTCHA → Session créée
2. **Production** : Mode Docker (`HEADLESS=true`) → Réutilise session → Plus de CAPTCHA
3. **Automatisation** : Cron job ou `restart: always` → Scraping automatique

**Vous êtes prêt pour la production !** 🎉
