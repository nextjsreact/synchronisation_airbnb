# 🚀 Système de Synchronisation Automatique Airbnb - Guide Complet

**Version**: 2.0  
**Date**: 30 Mai 2026  
**Statut**: ✅ Opérationnel (51/58 URLs avec token)

---

## 📋 Table des Matières

1. [Vue d'Ensemble](#vue-densemble)
2. [Démarrage Rapide](#démarrage-rapide)
3. [Architecture](#architecture)
4. [Fichiers Importants](#fichiers-importants)
5. [Commandes Essentielles](#commandes-essentielles)
6. [Monitoring](#monitoring)
7. [Dépannage](#dépannage)

---

## 🎯 Vue d'Ensemble

Ce système surveille automatiquement les calendriers iCal de vos lofts Airbnb et synchronise les réservations vers votre base de données Supabase.

### Fonctionnalités

✅ **Surveillance automatique** des calendriers iCal (toutes les 5 minutes)  
✅ **Détection des changements** via hash SHA256  
✅ **Scraping ciblé** des réservations modifiées  
✅ **Session persistante** Airbnb (pas de reconnexion à chaque fois)  
✅ **Gestion de la 2FA** avec TOTP  
✅ **Anti-détection** avec CloakBrowser  
✅ **Synchronisation** vers API Next.js  

### Statistiques Actuelles

- **58 lofts** configurés
- **51 URLs iCal** avec token valide ✅
- **7 URLs** à corriger manuellement ⚠️
- **Taux de succès**: 88%

---

## 🚀 Démarrage Rapide

### Première Installation

```bash
# 1. Créer la session Airbnb (une seule fois)
1_creer_session.bat

# 2. Collecter les URLs iCal (une seule fois)
2_collecter_ical.bat

# 3. Lancer la synchronisation automatique
3_lancer_sync.bat

# 4. Surveiller le système
4_monitor_sync.bat
```

### Utilisation Quotidienne

```bash
# Vérifier que tout fonctionne
python check_health.py

# Voir les logs en temps réel
4_monitor_sync.bat

# Redémarrer si nécessaire
docker compose -f docker-compose.sync.yml restart
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

3. API Next.js
   ↓
   Reçoit les réservations
   ↓
   Stocke dans Supabase
```

---

## 📁 Fichiers Importants

### Scripts de Démarrage

| Fichier | Description |
|---------|-------------|
| `1_creer_session.bat` | Crée la session Airbnb (Docker + VNC) |
| `2_collecter_ical.bat` | Collecte les URLs iCal avec tokens |
| `3_lancer_sync.bat` | Lance les services de synchronisation |
| `4_monitor_sync.bat` | Surveille les services en temps réel |

### Scripts Python

| Fichier | Description |
|---------|-------------|
| `airbnb_scraper.py` | Scraper principal Airbnb |
| `ical_watcher.py` | Surveillance des calendriers iCal |
| `targeted_scraper.py` | Scraping ciblé sur changement |
| `collect_ical_urls.py` | Collecte des URLs iCal |
| `check_health.py` | Vérification de santé du système |
| `sync_ical_urls_final.py` | Synchronisation URLs vers lofts |

### Configuration

| Fichier | Description |
|---------|-------------|
| `.env` | Variables d'environnement (credentials) |
| `docker-compose.yml` | Config Docker principale |
| `docker-compose.sync.yml` | Config Docker synchronisation |
| `Dockerfile` | Image Docker |

### Documentation

| Fichier | Description |
|---------|-------------|
| `README_FINAL.md` | Ce fichier |
| `GUIDE_MONITORING.md` | Guide complet de monitoring |
| `INSTRUCTIONS_CORRECTION_MANUELLE.md` | Correction des URLs sans token |
| `SYNC_SERVICES_STATUS.md` | Statut des services |
| `RAPPORT_ICAL_FINAL.md` | Rapport de collecte iCal |

### Données

| Fichier/Dossier | Description |
|-----------------|-------------|
| `output/airbnb_session.json` | Session Airbnb sauvegardée |
| `output/reservations_airbnb.json` | Réservations scrapées |
| `output/debug_*.png` | Captures d'écran de debug |

---

## 🔧 Commandes Essentielles

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

# Rebuild après modification
docker compose -f docker-compose.sync.yml build
docker compose -f docker-compose.sync.yml up -d
```

### Logs

```bash
# Logs en temps réel (les 2 services)
docker compose -f docker-compose.sync.yml logs -f

# Logs iCal Watcher
docker logs -f ical-watcher

# Logs Targeted Scraper
docker logs -f targeted-scraper

# Dernières 50 lignes
docker logs ical-watcher --tail 50
```

### Vérifications

```bash
# Santé globale du système
python check_health.py

# URLs sans token
python check_all_without_token.py

# Statistiques URLs iCal
python check_ical_urls.py

# Structure de la base de données
python check_database_structure.py
```

---

## 📊 Monitoring

### Vérification Rapide (30 secondes)

```bash
# 1. Containers en cours d'exécution ?
docker compose -f docker-compose.sync.yml ps

# 2. Erreurs récentes ?
docker logs ical-watcher --tail 20 | findstr "ERROR ERREUR HTTP 400"

# 3. Santé globale
python check_health.py
```

### Monitoring Continu

```bash
# Dashboard automatique (rafraîchit toutes les 30s)
4_monitor_sync.bat
```

### Indicateurs de Santé

✅ **Système Sain** :
- 2 containers "Up"
- Pas d'erreurs dans les logs
- Queue vide ou traitée rapidement
- Score santé > 90%

⚠️ **Attention Requise** :
- Containers en "Restarting"
- Beaucoup d'erreurs HTTP 400
- Queue avec beaucoup de "pending" ou "error"
- Score santé 50-90%

❌ **Intervention Urgente** :
- Containers arrêtés
- Erreurs critiques répétées
- Session Airbnb expirée
- Score santé < 50%

---

## 🔍 Requêtes SQL Utiles

### Derniers Changements Détectés

```sql
SELECT 
  listing_id,
  checked_at,
  changed_at,
  hash
FROM ical_hashes
ORDER BY changed_at DESC
LIMIT 10;
```

### Queue de Synchronisation

```sql
SELECT 
  id,
  listing_id,
  status,
  reason,
  created_at,
  processed_at,
  error_message
FROM sync_queue
WHERE status IN ('pending', 'processing', 'error')
ORDER BY created_at DESC;
```

### URLs iCal Sans Token

```sql
SELECT 
  l.name,
  l.airbnb_listing_id,
  l.airbnb_ical_url,
  CASE 
    WHEN l.airbnb_ical_url LIKE '%?t=%' THEN '✅ Token ?t='
    WHEN l.airbnb_ical_url LIKE '%?s=%' THEN '✅ Token ?s='
    WHEN l.airbnb_ical_url LIKE '%calendarAccessSignature%' THEN '✅ Token signature'
    ELSE '❌ PAS DE TOKEN'
  END as token_status
FROM lofts l
WHERE l.airbnb_ical_url IS NOT NULL
  AND l.airbnb_ical_url NOT LIKE '%?t=%'
  AND l.airbnb_ical_url NOT LIKE '%?s=%'
  AND l.airbnb_ical_url NOT LIKE '%calendarAccessSignature%';
```

### Statistiques de Synchronisation

```sql
SELECT 
  status,
  COUNT(*) as count,
  MAX(created_at) as last_entry
FROM sync_queue
GROUP BY status
ORDER BY count DESC;
```

---

## 🚨 Dépannage

### Problème : Containers en Restart Loop

**Symptôme** :
```bash
docker compose -f docker-compose.sync.yml ps
# STATUS = "Restarting"
```

**Solution** :
```bash
# 1. Voir les logs
docker logs ical-watcher --tail 50
docker logs targeted-scraper --tail 50

# 2. Rebuild et restart
docker compose -f docker-compose.sync.yml down
docker compose -f docker-compose.sync.yml build
docker compose -f docker-compose.sync.yml up -d
```

---

### Problème : Beaucoup d'Erreurs HTTP 400

**Symptôme** :
```
HTTP 400 pour https://www.airbnb.com/calendar/ical/...
```

**Cause** : URLs iCal sans token valide

**Solution** : Voir `INSTRUCTIONS_CORRECTION_MANUELLE.md`

---

### Problème : Session Airbnb Expirée

**Symptôme** :
```
⚠️  Session expirée — reconnexion...
```

**Solution** :
```bash
# Recréer la session
1_creer_session.bat
```

---

### Problème : API Next.js Inaccessible

**Symptôme** :
```
⚠️  ATTENTION: API inaccessible
```

**Solution** :
1. Vérifier que l'API tourne
2. Vérifier l'URL dans `.env` : `NEXTJS_API_URL`
3. Le scraper continuera de fonctionner sans l'API

---

## 📞 Support

### Logs de Debug

```bash
# Activer le mode debug
set DEBUG=true

# Voir tous les logs
docker compose -f docker-compose.sync.yml logs --no-log-prefix
```

### Fichiers à Vérifier

1. `.env` - Credentials et configuration
2. `output/airbnb_session.json` - Session Airbnb
3. Logs Docker - Erreurs d'exécution
4. Supabase - Données synchronisées

---

## ✅ Checklist de Maintenance

### Quotidienne
- [ ] Vérifier que les 2 containers sont "Up"
- [ ] Vérifier les logs pour les erreurs
- [ ] Lancer `python check_health.py`

### Hebdomadaire
- [ ] Nettoyer les anciennes entrées de `sync_queue`
- [ ] Vérifier les URLs sans token
- [ ] Vérifier les statistiques de synchronisation

### Mensuelle
- [ ] Recréer la session Airbnb si nécessaire
- [ ] Mettre à jour les images Docker
- [ ] Vérifier que toutes les URLs iCal sont valides

---

## 🎯 Prochaines Étapes

1. ✅ Corriger les 7 URLs sans token (voir `INSTRUCTIONS_CORRECTION_MANUELLE.md`)
2. ✅ Surveiller le système pendant 24h
3. ✅ Ajuster les intervalles si nécessaire (5 min / 30 sec)
4. ✅ Mettre en place des alertes automatiques (optionnel)

---

## 📚 Documentation Complète

- **Guide de Monitoring** : `GUIDE_MONITORING.md`
- **Correction Manuelle** : `INSTRUCTIONS_CORRECTION_MANUELLE.md`
- **Statut des Services** : `SYNC_SERVICES_STATUS.md`
- **Rapport iCal** : `RAPPORT_ICAL_FINAL.md`

---

**Dernière mise à jour** : 30 Mai 2026 20:45  
**Auteur** : Kiro AI Assistant  
**Version** : 2.0 - Production Ready
