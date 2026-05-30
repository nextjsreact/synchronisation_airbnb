# 🐳 Airbnb Scraper - Docker + VNC

**Version** : 2.0.1  
**Architecture** : Docker avec VNC pour résolution CAPTCHA  
**Date** : 30 mai 2026

---

## 🎯 QUE FAIRE MAINTENANT ?

Vous avez tout configuré ! Il ne reste plus qu'à lancer les 3 scripts batch dans l'ordre :

```
┌─────────────────────────────────────────────────────────────┐
│  1️⃣  CRÉER LA SESSION AIRBNB                                │
│                                                              │
│  Double-cliquez sur : 1_creer_session.bat                   │
│                                                              │
│  ✅ Build l'image Docker (première fois : 10-15 min)        │
│  ✅ Lance le container avec VNC                             │
│  ✅ Ouvre http://localhost:6080 dans ton navigateur         │
│  ✅ Résous le CAPTCHA dans l'interface VNC                  │
│  ✅ Session sauvegardée : output\airbnb_session.json        │
│                                                              │
│  Durée : 15-20 minutes                                       │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  2️⃣  COLLECTER LES URLs iCal                                │
│                                                              │
│  Double-cliquez sur : 2_collecter_ical.bat                  │
│                                                              │
│  ✅ Test sur 3 lofts (5-10 min)                             │
│  ✅ Collecte complète sur 54 lofts (2-3h)                   │
│  ✅ URLs avec tokens sauvegardées dans l'API Next.js        │
│                                                              │
│  Durée : 2-3 heures                                          │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  3️⃣  LANCER LA SYNCHRONISATION AUTOMATIQUE                  │
│                                                              │
│  Double-cliquez sur : 3_lancer_sync.bat                     │
│                                                              │
│  ✅ Change HEADLESS=true automatiquement                    │
│  ✅ Lance ical-watcher (surveillance 5 min)                 │
│  ✅ Lance targeted-scraper (scraping 30s)                   │
│  ✅ Synchronisation automatique active                      │
│                                                              │
│  Durée : 5 minutes                                           │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    ✅ TERMINÉ !
```

---

## 📚 DOCUMENTATION

### Démarrage rapide
- **`DEMARRAGE_RAPIDE.md`** : Résumé en 3 étapes (⭐ COMMENCEZ ICI)

### Guides complets
- **`GUIDE_DEMARRAGE_DOCKER.md`** : Guide étape par étape avec explications
- **`GUIDE_DOCKER_VNC.md`** : Architecture et détails techniques

### Explications
- **`RESUME_MODIFICATIONS_DOCKER.md`** : Résumé des modifications apportées
- **`EXPLICATION_ICAL_SYNC.md`** : Explication de la synchronisation iCal

---

## 🔗 LIENS IMPORTANTS

- **Interface VNC** : http://localhost:6080
- **API Next.js** : http://localhost:3000/api/airbnb/sync

---

## 🎛️ COMMANDES DOCKER UTILES

### Voir les logs de la synchronisation

```cmd
docker compose -f docker-compose.sync.yml logs -f
```

### Voir l'état des containers

```cmd
docker compose -f docker-compose.sync.yml ps
```

### Arrêter la synchronisation

```cmd
docker compose -f docker-compose.sync.yml down
```

### Redémarrer la synchronisation

```cmd
docker compose -f docker-compose.sync.yml restart
```

---

## 📋 PRÉREQUIS

- ✅ Docker Desktop installé
- ✅ Fichier `.env` configuré
- ✅ API Next.js en cours d'exécution (`http://localhost:3000`)

---

## 🆘 BESOIN D'AIDE ?

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

## 📊 ARCHITECTURE

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

## 🚀 DÉMARRAGE RAPIDE

### Étape 1 : Créer la session

```cmd
1_creer_session.bat
```

Ouvre http://localhost:6080 et résous le CAPTCHA.

### Étape 2 : Collecter les URLs iCal

```cmd
2_collecter_ical.bat
```

Attend 2-3 heures pour la collecte complète.

### Étape 3 : Lancer la synchronisation

```cmd
3_lancer_sync.bat
```

La synchronisation automatique est maintenant active !

---

## ✅ CHECKLIST

- [ ] Docker Desktop installé
- [ ] Fichier `.env` configuré
- [ ] API Next.js en cours d'exécution
- [ ] Session Airbnb créée (`output\airbnb_session.json`)
- [ ] URLs iCal collectées (54 lofts)
- [ ] Synchronisation automatique lancée

---

**C'est parti !** 🎉

Double-cliquez sur `1_creer_session.bat` pour commencer.
