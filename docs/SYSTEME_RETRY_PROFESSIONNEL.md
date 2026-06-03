# 🔄 Système de Retry Professionnel

## 📋 Contexte

Problème détecté : Une nouvelle réservation Airbnb n'a pas été synchronisée à cause d'erreurs réseau (timeouts) répétées lors du scraping.

Le Targeted Scraper échouait silencieusement et marquait les entrées comme "done" même sans avoir récupéré les données.

---

## ✅ Solution Implémentée

### 1. **Système de Retry Automatique avec Backoff Exponentiel**

#### Modifications dans `targeted_scraper.py` :

1. **Fonction `scrape_listing_with_retry()`**
   - 3 tentatives maximum par listing
   - Backoff exponentiel : 5s → 15s → 30s
   - Gestion intelligente des erreurs réseau vs autres erreurs

2. **Timeout augmenté**
   - Avant : 60 secondes
   - Après : 90 secondes
   - Réduit les faux positifs d'erreurs réseau

3. **Gestion intelligente des erreurs dans `mark_error()`**
   - Si retry_count < 3 : remet status = "pending" (pour réessayer)
   - Si retry_count >= 3 : status = "error" (abandon définitif)
   - Incrémente retry_count automatiquement

4. **Priorisation de la queue dans `get_pending_entries()`**
   ```python
   ORDER BY retry_count DESC, created_at ASC
   ```
   - Les entrées ayant déjà échoué sont réessayées en priorité
   - Évite l'accumulation d'échecs

5. **Distinction des erreurs dans `process_entry()`**
   - Erreurs réseau (Timeout, Connection) : retry automatique
   - Autres erreurs : marqué en erreur définitive
   - Logging détaillé pour chaque cas

6. **Modification de `scrape_fallback_upcoming_only()`**
   - Retourne `None` en cas d'erreur réseau (signal pour retry)
   - Retourne `[]` si liste vide (succès sans données)
   - Retourne `[...]` liste de réservations (succès avec données)

---

## 🚨 ÉTAPE CRITIQUE À FAIRE MAINTENANT

### ⚠️ La colonne `retry_count` n'existe pas dans Supabase !

Le système de retry ne peut pas fonctionner sans cette colonne.

### 📝 Instructions (URGENT) :

1. **Ouvrir Supabase SQL Editor**
   - URL : https://supabase.com/dashboard
   - Projet : votre projet
   - Menu : SQL Editor

2. **Exécuter cette migration SQL :**

```sql
ALTER TABLE sync_queue 
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

UPDATE sync_queue 
SET retry_count = 0 
WHERE retry_count IS NULL;

SELECT 'Migration terminée!' as status;
```

3. **Vérifier que ça fonctionne :**
   ```bash
   11_ajouter_retry_count.bat
   ```
   ou
   ```bash
   python execute_migration.py
   ```

4. **Une fois la colonne ajoutée, les services redémarreront automatiquement**

---

## 🔍 Comment Vérifier que ça Fonctionne

### 1. Après avoir ajouté la colonne dans Supabase :

```bash
docker compose -f docker-compose.sync.yml logs -f targeted-scraper
```

### 2. Chercher dans les logs :

✅ **Succès après retry :**
```
[HH:MM:SS] 🔁 Tentative 2/3 (attente 15s...)
[HH:MM:SS] ✅ 1 reservations trouvees
```

✅ **Abandon après 3 tentatives :**
```
[HH:MM:SS] ❌ Echec final apres 3 tentatives
[HH:MM:SS] ❌ [1234567890] Erreur -> error
```

⚠️ **Erreur colonne manquante (AVANT la migration) :**
```
Erreur lecture queue: 400 Client Error: Bad Request
column sync_queue.retry_count does not exist
```

---

## 📊 État Actuel du Système

### ✅ Fait (Code modifié) :
- [x] Fonction retry avec backoff exponentiel
- [x] Timeout augmenté (90s)
- [x] Gestion intelligente des erreurs
- [x] Priorisation de la queue
- [x] Logging détaillé
- [x] Docker rebuild effectué (729.9s)
- [x] Services Docker redémarrés

### ⏳ En Attente (Action Utilisateur Requise) :
- [ ] **Ajouter colonne `retry_count` dans Supabase** ← CRITIQUE
- [ ] Vérifier les logs après migration
- [ ] Confirmer que la nouvelle réservation est synchronisée

---

## 🎯 Résultat Attendu

Une fois la colonne ajoutée :

1. **Le Targeted Scraper détectera les entrées pending**
2. **Il réessaiera automatiquement les échecs réseau (max 3 fois)**
3. **La nouvelle réservation sera scrapée avec succès**
4. **Elle apparaîtra dans l'application Next.js**
5. **Une notification sera envoyée** (si c'est une nouvelle réservation avec created_at récent)

---

## 📁 Fichiers Créés

- `add_retry_count.sql` - Migration SQL à exécuter dans Supabase
- `execute_migration.py` - Script de vérification Python
- `11_ajouter_retry_count.bat` - Batch pour vérifier la colonne
- `SYSTEME_RETRY_PROFESSIONNEL.md` - Cette documentation

---

## 💡 Avantages du Système

✅ **Robustesse** : Gère automatiquement les erreurs réseau temporaires  
✅ **Professionnel** : Backoff exponentiel (pattern industry-standard)  
✅ **Intelligent** : Distingue erreurs récupérables vs définitives  
✅ **Traçable** : Logging détaillé à chaque étape  
✅ **Priorisé** : Les échecs sont réessayés en premier  
✅ **Limite** : Maximum 3 tentatives pour éviter boucles infinies  
✅ **Optimisé** : Mode "upcoming only" conservé (2-3 min vs 30-40 min)  

---

## 🔗 Commandes Utiles

```bash
# Vérifier si la colonne existe
python execute_migration.py

# Voir les logs du targeted-scraper
docker compose -f docker-compose.sync.yml logs -f targeted-scraper

# Voir les logs de l'ical-watcher
docker compose -f docker-compose.sync.yml logs -f ical-watcher

# Redémarrer les services
docker compose -f docker-compose.sync.yml restart

# Vérifier l'état de la queue
python check_database_structure.py
```

---

**Date de création** : 2026-06-02  
**Version** : 1.0  
**Statut** : ⏳ EN ATTENTE DE MIGRATION SQL
