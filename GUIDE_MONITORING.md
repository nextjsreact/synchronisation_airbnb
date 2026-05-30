# 📊 Guide de Monitoring - Synchronisation Automatique Airbnb

**Date**: 30 Mai 2026  
**Version**: 2.0

---

## 🏗️ Architecture du Système

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTÈME DE SYNCHRONISATION                    │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│  iCal Watcher    │         │ Targeted Scraper │
│  (Container 1)   │         │  (Container 2)   │
│                  │         │                  │
│  • Poll: 5 min   │         │  • Poll: 30 sec  │
│  • Lit: iCal     │         │  • Lit: queue    │
│  • Détecte: Δ    │────────▶│  • Scrape: loft  │
│  • Écrit: queue  │         │  • Envoie: API   │
└──────────────────┘         └──────────────────┘
        │                             │
        │                             │
        ▼                             ▼
┌─────────────────────────────────────────────┐
│            SUPABASE (PostgreSQL)            │
│                                             │
│  • ical_hashes (hash des calendriers)       │
│  • sync_queue (changements détectés)        │
│  • property_sync_config (config URLs)       │
│  • lofts (données des lofts)                │
│  • reservations (réservations Airbnb)       │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         API Next.js (Port 3000)             │
│  /api/airbnb/sync                           │
└─────────────────────────────────────────────┘
```

---

## 🔄 Processus qui Doivent Tourner en Permanence

### 1️⃣ iCal Watcher (Container)
**Rôle** : Surveille les calendriers iCal toutes les 5 minutes

**Commande** :
```bash
docker ps | grep ical-watcher
```

**Statut attendu** :
```
ical-watcher   Up 2 hours   5900/tcp, 6080/tcp
```

**Ce qu'il fait** :
1. Récupère les URLs iCal depuis `property_sync_config`
2. Télécharge chaque fichier iCal
3. Calcule le hash SHA256 du contenu
4. Compare avec le hash précédent dans `ical_hashes`
5. Si changement → pousse `listing_id` dans `sync_queue`

**Logs à surveiller** :
```bash
docker logs -f ical-watcher
```

**Logs normaux** :
```
--- Cycle 42 (20:15:00) ---
   Aucun changement
   Prochain check dans 300s...
```

**Logs avec changement** :
```
--- Cycle 43 (20:20:00) ---
   [1621838473144867162] CHANGEMENT detecte -> sync_queue
   1 changement(s) detecte(s)
   Prochain check dans 300s...
```

**Logs d'erreur** :
```
   HTTP 400 pour https://www.airbnb.com/calendar/ical/...
   HTTP 404 pour https://www.airbnb.com/calendar/ical/...
```

---

### 2️⃣ Targeted Scraper (Container)
**Rôle** : Scrape les réservations des lofts modifiés toutes les 30 secondes

**Commande** :
```bash
docker ps | grep targeted-scraper
```

**Statut attendu** :
```
targeted-scraper   Up 2 hours   5900/tcp, 6080/tcp
```

**Ce qu'il fait** :
1. Lit `sync_queue` (status=pending)
2. Lance CloakBrowser avec la session sauvegardée
3. Scrape les réservations du listing spécifique
4. Envoie les données à l'API Next.js
5. Marque l'entrée comme "done" dans `sync_queue`

**Logs à surveiller** :
```bash
docker logs -f targeted-scraper
```

**Logs normaux (queue vide)** :
```
[20:15:30] Cycle 125 — queue vide, attente 30s...
```

**Logs avec traitement** :
```
==================================================
   Queue #42 — listing 1621838473144867162
   Raison : ical_change
==================================================
   💾 Session trouvée : chargement...
   ✅ Session valide — connexion automatique !
   Scraping des reservations pour listing 1621838473144867162...
   📋 Récupération des réservations (API GraphQL)...
   12 reservations trouvees pour 1621838473144867162
   12 reservations envoyees a l'API
   Termine avec succes
```

**Logs d'erreur** :
```
   ⚠️  API GraphQL vide ou erreur
   ⚠️  Session expirée — reconnexion...
   ERREUR: [détails de l'erreur]
```

---

### 3️⃣ API Next.js (Optionnel mais Recommandé)
**Rôle** : Reçoit les réservations et les stocke dans Supabase

**Commande** :
```bash
# Si l'API tourne localement
curl http://localhost:3000/api/airbnb/health
```

**Réponse attendue** :
```json
{"status": "ok", "timestamp": "2026-05-30T20:15:00Z"}
```

**Note** : Si l'API n'est pas accessible, le scraper continuera de fonctionner mais les données ne seront pas envoyées.

---

## 📊 Commandes de Monitoring

### Vérifier que les Containers Tournent
```bash
docker compose -f docker-compose.sync.yml ps
```

**Résultat attendu** :
```
NAME               STATUS         PORTS
ical-watcher       Up 2 hours     5900/tcp, 6080/tcp
targeted-scraper   Up 2 hours     5900/tcp, 6080/tcp
```

**⚠️ Si STATUS = "Restarting"** → Problème ! Voir les logs.

---

### Voir les Logs en Temps Réel

**iCal Watcher** :
```bash
docker logs -f ical-watcher
```

**Targeted Scraper** :
```bash
docker logs -f targeted-scraper
```

**Les deux en même temps** :
```bash
docker compose -f docker-compose.sync.yml logs -f
```

---

### Vérifier les Derniers Changements Détectés

**Dans Supabase (SQL Editor)** :
```sql
-- Derniers changements détectés
SELECT 
  listing_id,
  checked_at,
  changed_at,
  hash
FROM ical_hashes
ORDER BY changed_at DESC
LIMIT 10;
```

**Résultat attendu** :
```
listing_id          | checked_at          | changed_at          | hash
--------------------|---------------------|---------------------|------
1621838473144867162 | 2026-05-30 20:15:00 | 2026-05-30 18:30:00 | abc123...
1637669342598748246 | 2026-05-30 20:15:00 | 2026-05-30 15:20:00 | def456...
```

---

### Vérifier la Queue de Synchronisation

**Dans Supabase (SQL Editor)** :
```sql
-- Entrées en attente
SELECT 
  id,
  listing_id,
  status,
  reason,
  created_at,
  processed_at
FROM sync_queue
WHERE status IN ('pending', 'processing')
ORDER BY created_at DESC;
```

**Résultat attendu** :
- **Queue vide** = ✅ Tout est traité
- **Entrées "pending"** = ⏳ En attente de traitement (normal si récent)
- **Entrées "processing" > 5 min** = ⚠️ Problème de scraping

---

### Vérifier les Erreurs

**Dans Supabase (SQL Editor)** :
```sql
-- Entrées en erreur
SELECT 
  id,
  listing_id,
  status,
  error_message,
  created_at,
  processed_at
FROM sync_queue
WHERE status = 'error'
ORDER BY created_at DESC
LIMIT 10;
```

---

### Statistiques Globales

**Dans Supabase (SQL Editor)** :
```sql
-- Statistiques de synchronisation
SELECT 
  status,
  COUNT(*) as count,
  MAX(created_at) as last_entry
FROM sync_queue
GROUP BY status
ORDER BY count DESC;
```

**Résultat attendu** :
```
status      | count | last_entry
------------|-------|-------------------
done        | 1250  | 2026-05-30 20:15:00
pending     | 2     | 2026-05-30 20:14:30
error       | 5     | 2026-05-30 18:00:00
```

---

## 🚨 Alertes et Problèmes Courants

### ⚠️ Container en Restart Loop

**Symptôme** :
```bash
docker compose -f docker-compose.sync.yml ps
# STATUS = "Restarting"
```

**Diagnostic** :
```bash
docker logs ical-watcher --tail 50
docker logs targeted-scraper --tail 50
```

**Causes fréquentes** :
1. Erreur d'encodage UTF-8 (`.env`)
2. Erreur de connexion Supabase
3. Erreur Python (import manquant)

**Solution** :
```bash
# Rebuild et restart
docker compose -f docker-compose.sync.yml down
docker compose -f docker-compose.sync.yml build
docker compose -f docker-compose.sync.yml up -d
```

---

### ⚠️ Beaucoup d'Erreurs HTTP 400

**Symptôme** :
```bash
docker logs ical-watcher | grep "HTTP 400"
# Beaucoup de lignes
```

**Cause** : URLs iCal sans token valide

**Solution** : Voir `INSTRUCTIONS_CORRECTION_MANUELLE.md`

---

### ⚠️ Session Airbnb Expirée

**Symptôme** :
```
⚠️  Session expirée — reconnexion...
```

**Cause** : La session sauvegardée dans `output/airbnb_session.json` a expiré

**Solution** :
1. Le scraper va automatiquement se reconnecter
2. Si échec répété → Recréer la session :
   ```bash
   1_creer_session.bat
   ```

---

### ⚠️ API Next.js Inaccessible

**Symptôme** :
```
⚠️  ATTENTION: API inaccessible — [erreur]
Le scraper fonctionnera mais n'enverra pas les donnees
```

**Cause** : L'API Next.js n'est pas démarrée ou inaccessible

**Solution** :
1. Vérifier que l'API tourne : `curl http://localhost:3000/api/airbnb/health`
2. Démarrer l'API si nécessaire
3. Le scraper continuera de fonctionner et réessaiera au prochain cycle

---

## 📈 Dashboard de Monitoring (Recommandé)

### Script de Monitoring Automatique

Créez un fichier `monitor.bat` :

```batch
@echo off
:loop
cls
echo ========================================
echo   MONITORING SYNCHRONISATION AIRBNB
echo ========================================
echo.
echo [1] Status des Containers
docker compose -f docker-compose.sync.yml ps
echo.
echo [2] Derniers Logs iCal Watcher (5 lignes)
docker logs ical-watcher --tail 5
echo.
echo [3] Derniers Logs Targeted Scraper (5 lignes)
docker logs targeted-scraper --tail 5
echo.
echo ========================================
echo Rafraichissement dans 30 secondes...
echo Appuyez sur Ctrl+C pour arreter
timeout /t 30 /nobreak >nul
goto loop
```

**Lancer** :
```bash
monitor.bat
```

---

## ✅ Checklist de Santé du Système

Exécutez cette checklist quotidiennement :

- [ ] Les 2 containers sont "Up" (pas "Restarting")
- [ ] Pas d'erreurs dans les logs des 5 dernières minutes
- [ ] Moins de 5 entrées "error" dans `sync_queue` sur les dernières 24h
- [ ] Moins de 10 URLs avec HTTP 400 dans les logs
- [ ] L'API Next.js répond (si utilisée)
- [ ] La session Airbnb est valide (pas de reconnexion fréquente)

---

## 🔧 Maintenance Régulière

### Quotidienne
- ✅ Vérifier les logs pour les erreurs
- ✅ Vérifier que les containers tournent

### Hebdomadaire
- ✅ Nettoyer les anciennes entrées de `sync_queue` (status=done, > 7 jours)
  ```sql
  DELETE FROM sync_queue
  WHERE status = 'done'
    AND processed_at < NOW() - INTERVAL '7 days';
  ```

### Mensuelle
- ✅ Vérifier que toutes les URLs iCal ont un token valide
- ✅ Recréer la session Airbnb si nécessaire
- ✅ Mettre à jour les images Docker si nouvelles versions

---

## 📞 Commandes Rapides

```bash
# Démarrer les services
docker compose -f docker-compose.sync.yml up -d

# Arrêter les services
docker compose -f docker-compose.sync.yml down

# Redémarrer les services
docker compose -f docker-compose.sync.yml restart

# Voir les logs en temps réel
docker compose -f docker-compose.sync.yml logs -f

# Voir le statut
docker compose -f docker-compose.sync.yml ps

# Rebuild après modification
docker compose -f docker-compose.sync.yml build
docker compose -f docker-compose.sync.yml up -d
```

---

## 🎯 Résumé

**2 Processus Essentiels** :
1. ✅ **iCal Watcher** (toutes les 5 min)
2. ✅ **Targeted Scraper** (toutes les 30 sec)

**Monitoring Minimal** :
- Vérifier que les 2 containers sont "Up"
- Vérifier les logs 1x par jour

**Tout fonctionne si** :
- Pas d'erreurs dans les logs
- Queue vide ou traitée rapidement
- Pas de restart loops

---

**Dernière mise à jour** : 30 Mai 2026 20:30
