# ⚡ Démarrage Rapide : 3 Étapes

**Architecture** : Docker + VNC  
**Durée totale** : ~3-4 heures (dont 2-3h automatiques)

---

## 🚀 LES 3 ÉTAPES

### 1️⃣  Créer la session Airbnb (15-20 min)

```cmd
1_creer_session.bat
```

**Actions** :
- Build l'image Docker (première fois : 10-15 min)
- Lance le container avec VNC
- Ouvre http://localhost:6080 dans ton navigateur
- Résous le CAPTCHA dans l'interface VNC
- Session sauvegardée dans `output\airbnb_session.json`

---

### 2️⃣  Collecter les URLs iCal (2-3 heures)

```cmd
2_collecter_ical.bat
```

**Actions** :
- Test sur 3 lofts (5-10 min)
- Si OK, collecte complète sur 54 lofts (2-3h)
- URLs avec tokens sauvegardées dans l'API Next.js

---

### 3️⃣  Lancer la synchronisation (5 min)

```cmd
3_lancer_sync.bat
```

**Actions** :
- Change `HEADLESS=true` automatiquement
- Lance 2 containers Docker en arrière-plan :
  - `ical-watcher` : Surveille les calendriers (5 min)
  - `targeted-scraper` : Scrape les changements (30s)
- Synchronisation automatique active ✅

---

## 📋 PRÉREQUIS

- ✅ Docker Desktop installé
- ✅ Fichier `.env` configuré
- ✅ API Next.js en cours d'exécution (`http://localhost:3000`)

---

## 🎛️ COMMANDES UTILES

### Voir les logs

```cmd
# Logs de la synchronisation
docker compose -f docker-compose.sync.yml logs -f

# Logs d'un service spécifique
docker compose -f docker-compose.sync.yml logs -f ical-watcher
docker compose -f docker-compose.sync.yml logs -f targeted-scraper
```

### Arrêter les services

```cmd
docker compose -f docker-compose.sync.yml down
```

### Redémarrer les services

```cmd
docker compose -f docker-compose.sync.yml restart
```

### Voir l'état des containers

```cmd
docker compose -f docker-compose.sync.yml ps
```

---

## 🔗 LIENS IMPORTANTS

- **Interface VNC** : http://localhost:6080
- **API Next.js** : http://localhost:3000/api/airbnb/sync

---

## 📚 DOCUMENTATION COMPLÈTE

- `GUIDE_DEMARRAGE_DOCKER.md` : Guide complet étape par étape
- `GUIDE_DOCKER_VNC.md` : Architecture et détails techniques
- `EXPLICATION_ICAL_SYNC.md` : Explication de la synchronisation iCal

---

## 🆘 PROBLÈMES COURANTS

### VNC ne s'affiche pas

```cmd
docker compose ps
docker compose logs airbnb-scraper | findstr noVNC
```

### Session non créée

```cmd
dir output\airbnb_session.json
docker compose logs airbnb-scraper | findstr CAPTCHA
```

### Container s'arrête

```cmd
docker compose logs airbnb-scraper
type .env
```

---

**C'est tout !** 🎉

Suis les 3 étapes et tu auras un système de synchronisation automatique Airbnb fonctionnel.
