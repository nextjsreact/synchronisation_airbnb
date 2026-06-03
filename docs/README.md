# 🏠 Airbnb Synchronization System

Système automatique de synchronisation des réservations Airbnb vers Supabase avec surveillance des calendriers iCal.

[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11-green)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

---

## 🎯 Fonctionnalités

- ✅ **Surveillance automatique** des calendriers iCal (toutes les 5 minutes)
- ✅ **Détection intelligente** des changements via hash SHA256
- ✅ **Scraping ciblé** des réservations modifiées uniquement
- ✅ **Session persistante** Airbnb (pas de reconnexion à chaque fois)
- ✅ **Gestion 2FA** avec TOTP (Google Authenticator)
- ✅ **Anti-détection** avec CloakBrowser
- ✅ **Synchronisation** vers API Next.js et Supabase
- ✅ **Monitoring** en temps réel avec dashboard

---

## 📋 Prérequis

- **Docker** et **Docker Compose**
- **Python 3.11+** (pour les scripts locaux)
- **Compte Airbnb** avec accès aux listings
- **Base de données Supabase** (ou PostgreSQL)
- **API Next.js** (optionnel)

---

## 🚀 Installation

### 1. Cloner le Repository

```bash
git clone https://github.com/votre-username/airbnb-sync.git
cd airbnb-sync
```

### 2. Configuration

```bash
# Copier le fichier d'exemple
cp .env.example .env

# Éditer avec vos credentials
nano .env
```

**Variables importantes** :
- `AIRBNB_EMAIL` : Votre email Airbnb
- `AIRBNB_PASSWORD` : Votre mot de passe Airbnb
- `TOTP_SECRET` : Secret Google Authenticator (si 2FA activée)
- `NEXT_PUBLIC_SUPABASE_URL` : URL de votre projet Supabase
- `SUPABASE_SERVICE_ROLE_KEY` : Clé service role Supabase

### 3. Créer la Session Airbnb

```bash
# Windows
1_creer_session.bat

# Linux/Mac
docker compose up airbnb-scraper
```

**Important** : 
- Accédez à http://localhost:6080 pour voir le navigateur
- Résolvez le CAPTCHA si nécessaire
- La session sera sauvegardée dans `output/airbnb_session.json`

### 4. Collecter les URLs iCal

```bash
# Windows
2_collecter_ical.bat

# Linux/Mac
docker compose run --rm airbnb-scraper python collect_ical_urls.py --all
```

### 5. Lancer la Synchronisation

```bash
# Windows
3_lancer_sync.bat

# Linux/Mac
docker compose -f docker-compose.sync.yml up -d
```

---

## 📊 Monitoring

### Dashboard en Temps Réel

```bash
# Windows
4_monitor_sync.bat

# Linux/Mac
watch -n 30 'docker compose -f docker-compose.sync.yml ps && docker logs ical-watcher --tail 5'
```

### Vérification de Santé

```bash
python check_health.py
```

**Score de santé** :
- ✅ **90-100%** : Excellent
- ⚠️ **70-89%** : Bon (quelques points à surveiller)
- ⚠️ **50-69%** : Moyen (plusieurs problèmes)
- ❌ **<50%** : Critique (intervention nécessaire)

### Logs

```bash
# Voir les logs en temps réel
docker logs -f ical-watcher
docker logs -f targeted-scraper

# Dernières 50 lignes
docker logs ical-watcher --tail 50
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  FLUX DE SYNCHRONISATION                 │
└─────────────────────────────────────────────────────────┘

1. iCal Watcher (toutes les 5 min)
   ↓
   Télécharge les fichiers iCal depuis Airbnb
   ↓
   Calcule le hash SHA256
   ↓
   Compare avec le hash précédent
   ↓
   Si changement → Pousse dans sync_queue

2. Targeted Scraper (toutes les 30 sec)
   ↓
   Lit sync_queue (status=pending)
   ↓
   Lance CloakBrowser + Session Airbnb
   ↓
   Scrape les réservations du listing
   ↓
   Envoie à l'API Next.js
   ↓
   Marque comme "done" dans sync_queue
```

---

## 🗂️ Structure du Projet

```
airbnb-sync/
├── 📄 Scripts de démarrage
│   ├── 1_creer_session.bat       # Créer la session Airbnb
│   ├── 2_collecter_ical.bat      # Collecter les URLs iCal
│   ├── 3_lancer_sync.bat         # Lancer la synchronisation
│   └── 4_monitor_sync.bat        # Monitoring en temps réel
│
├── 🐍 Scripts Python
│   ├── airbnb_scraper.py         # Scraper principal
│   ├── ical_watcher.py           # Surveillance iCal
│   ├── targeted_scraper.py       # Scraping ciblé
│   ├── collect_ical_urls.py      # Collecte URLs iCal
│   ├── airbnb_api_client.py      # Client API
│   └── check_health.py           # Vérification santé
│
├── 🐳 Docker
│   ├── Dockerfile                # Image principale
│   ├── docker-compose.yml        # Config principale
│   └── docker-compose.sync.yml   # Config synchronisation
│
├── 📚 Documentation
│   ├── README.md                 # Ce fichier
│   ├── README_FINAL.md           # Guide complet
│   ├── GUIDE_MONITORING.md       # Guide monitoring
│   └── INSTRUCTIONS_CORRECTION_MANUELLE.md
│
├── ⚙️ Configuration
│   ├── .env.example              # Template configuration
│   ├── requirements.txt          # Dépendances Python
│   └── .gitignore               # Fichiers à ignorer
│
└── 📁 output/                    # Données générées (ignoré par Git)
    ├── airbnb_session.json       # Session sauvegardée
    └── .gitkeep
```

---

## 🔧 Commandes Utiles

### Gestion des Services

```bash
# Démarrer
docker compose -f docker-compose.sync.yml up -d

# Arrêter
docker compose -f docker-compose.sync.yml down

# Redémarrer
docker compose -f docker-compose.sync.yml restart

# Voir le statut
docker compose -f docker-compose.sync.yml ps

# Rebuild
docker compose -f docker-compose.sync.yml build
```

### Maintenance

```bash
# Nettoyer les anciennes entrées de la queue (> 7 jours)
# Exécuter dans Supabase SQL Editor
DELETE FROM sync_queue
WHERE status = 'done'
  AND processed_at < NOW() - INTERVAL '7 days';

# Recréer la session si expirée
1_creer_session.bat
```

---

## 🚨 Dépannage

### Containers en Restart Loop

```bash
# Voir les logs
docker logs ical-watcher --tail 50
docker logs targeted-scraper --tail 50

# Rebuild et restart
docker compose -f docker-compose.sync.yml down
docker compose -f docker-compose.sync.yml build
docker compose -f docker-compose.sync.yml up -d
```

### Erreurs HTTP 400

**Cause** : URLs iCal sans token valide

**Solution** : Voir `INSTRUCTIONS_CORRECTION_MANUELLE.md`

### Session Airbnb Expirée

```bash
# Recréer la session
1_creer_session.bat
```

---

## 📊 Base de Données Supabase

### Tables Requises

```sql
-- Table des lofts
CREATE TABLE lofts (
  id UUID PRIMARY KEY,
  name TEXT,
  airbnb_listing_id TEXT,
  airbnb_ical_url TEXT,
  status TEXT
);

-- Table de configuration
CREATE TABLE property_sync_config (
  id UUID PRIMARY KEY,
  loft_id UUID REFERENCES lofts(id),
  ical_url_airbnb TEXT,
  is_active BOOLEAN DEFAULT true,
  last_sync_at TIMESTAMPTZ,
  last_sync_status TEXT
);

-- Table des hash iCal
CREATE TABLE ical_hashes (
  listing_id TEXT PRIMARY KEY,
  hash TEXT,
  checked_at TIMESTAMPTZ,
  changed_at TIMESTAMPTZ
);

-- Table de la queue de synchronisation
CREATE TABLE sync_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  listing_id TEXT,
  status TEXT,
  reason TEXT,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  processed_at TIMESTAMPTZ
);

-- Table des réservations
CREATE TABLE reservations (
  id UUID PRIMARY KEY,
  loft_id UUID REFERENCES lofts(id),
  confirmation_code TEXT,
  guest_name TEXT,
  check_in DATE,
  check_out DATE,
  status TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📝 License

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

---

## 🙏 Remerciements

- [CloakBrowser](https://github.com/cloakbrowser/cloakbrowser) - Anti-détection
- [Playwright](https://playwright.dev/) - Automation navigateur
- [Supabase](https://supabase.com/) - Base de données
- [Docker](https://www.docker.com/) - Containerisation

---

## 📞 Support

Pour toute question ou problème :

1. Consultez la [documentation complète](README_FINAL.md)
2. Vérifiez les [issues existantes](https://github.com/votre-username/airbnb-sync/issues)
3. Créez une [nouvelle issue](https://github.com/votre-username/airbnb-sync/issues/new)

---

## 🔒 Sécurité

**⚠️ IMPORTANT** :

- Ne **JAMAIS** commiter le fichier `.env`
- Ne **JAMAIS** commiter `output/airbnb_session.json`
- Utiliser des variables d'environnement pour les secrets
- Activer la 2FA sur votre compte Airbnb
- Utiliser un proxy résidentiel en production

---

**Dernière mise à jour** : 30 Mai 2026  
**Version** : 2.0
