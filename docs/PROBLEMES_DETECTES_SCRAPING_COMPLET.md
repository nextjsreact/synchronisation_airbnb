# 🔍 PROBLÈMES DÉTECTÉS - SCRAPING COMPLET

**Date**: 1er juin 2026  
**Durée du scraping**: 58 minutes (3475 secondes)  
**Réservations scrapées**: 6,196  
**Réservations envoyées à l'API**: 3,984  

---

## ❌ PROBLÈME 1: Conversion des devises désactivée dans Docker

### Symptôme
```csv
currency_code,currency_ratio
GBP,1.0
GBP,1.0
GBP,1.0
```

**Attendu**: `GBP,270.0` (taux depuis Supabase)  
**Obtenu**: `GBP,1.0` (taux par défaut)

### Cause racine
Le fichier `currency_converter.py` n'est **pas copié dans l'image Docker**.

```dockerfile
# Dockerfile - ligne 75-80
COPY airbnb_scraper.py .
COPY airbnb_api_client.py .
COPY collect_ical_urls.py .
COPY ical_watcher.py .
COPY targeted_scraper.py .
# ❌ MANQUE: COPY currency_converter.py .
```

### Logs Docker
```
ModuleNotFoundError: No module named 'currency_converter'
```

### Impact
- ✅ Les champs `currency_code` et `currency_ratio` sont présents dans le CSV
- ❌ Mais `currency_ratio = 1.0` au lieu du taux réel (270 pour GBP)
- ❌ Les montants en DZD dans Supabase sont **incorrects**

### Solution
Ajouter la ligne dans le Dockerfile après la ligne 79:

```dockerfile
COPY currency_converter.py .
```

---

## ❌ PROBLÈME 2: Collection des contacts désactivée

### Symptôme
```csv
telephone_voyageur,email_voyageur
,
,
,
```

**Attendu**: `+213 793 86 24 94,guest@example.com`  
**Obtenu**: Colonnes vides

### Cause racine
La variable d'environnement `COLLECT_CONTACTS=false` dans `.env`

```bash
# .env
COLLECT_CONTACTS=false  # ❌ Désactivé par défaut
```

### Impact
- ✅ Les colonnes `telephone_voyageur` et `email_voyageur` existent
- ❌ Mais elles sont vides pour toutes les réservations
- ❌ Impossible de contacter les voyageurs

### Solution
**Option 1**: Activer dans `.env` (recommandé pour production)
```bash
COLLECT_CONTACTS=true
```

**Option 2**: Passer en argument au script Docker
```bash
docker run -e COLLECT_CONTACTS=true ...
```

---

## ⚠️ PROBLÈME 3: API Next.js - 0 créées, 0 mises à jour

### Symptôme
```
📊 Métriques:
   • Traitées:  3,984
   • Créées:    0        ❌
   • Mises à jour: 0     ❌
   • Ignorées:  0
   • Échouées:  0
```

**Attendu**: 3,984 créées OU 3,984 mises à jour  
**Obtenu**: 3,984 traitées mais 0 créées/mises à jour

### Cause possible
1. **Validation Zod échoue silencieusement** dans l'API Next.js
2. **Contrainte UNIQUE sur `airbnb_confirmation_code`** rejette les doublons
3. **Problème de mapping des champs** entre Python et API

### Logs à vérifier
```bash
# Vérifier les logs de l'API Next.js
docker logs nextjs-api-container

# Chercher les erreurs Zod
grep "ZodError" logs.txt
grep "validation" logs.txt
```

### Impact
- ✅ L'API reçoit les données (3,984 traitées)
- ❌ Mais elles ne sont **pas insérées** dans Supabase
- ❌ La base de données reste vide ou inchangée

### Solution
**Étape 1**: Vérifier les données dans Supabase
```sql
-- Compter les réservations dans Supabase
SELECT COUNT(*) FROM reservations;

-- Vérifier les dernières insertions
SELECT airbnb_confirmation_code, created_at, synced_at
FROM reservations
ORDER BY synced_at DESC
LIMIT 10;
```

**Étape 2**: Vérifier les logs de l'API Next.js
```bash
# Chercher les erreurs de validation
docker logs nextjs-api | grep -i "error\|validation\|zod"
```

**Étape 3**: Tester avec une seule réservation
```bash
# Utiliser le script de test rapide
python TEST_RAPIDE_UNE_RESERVATION.py
```

---

## ❌ PROBLÈME 4: Collection iCal échouée (0/102)

### Symptôme
```
iCal URLs: 0 créées, 0 mises à jour, 0 ignorées
102 failed
```

**Attendu**: 49-51 URLs collectées (96% de succès)  
**Obtenu**: 0 URLs collectées (0% de succès)

### Cause possible
1. **Session Airbnb expirée** dans Docker
2. **Cookies non partagés** entre le scraper et le collecteur iCal
3. **Timeout** lors de la navigation vers les pages de paramètres

### Impact
- ❌ Les URLs iCal ne sont **pas mises à jour** dans `property_sync_config`
- ❌ Le service `ical-watcher` ne peut **pas détecter** les nouvelles réservations
- ❌ La synchronisation automatique est **cassée**

### Solution
**Option 1**: Recréer la session Airbnb
```bash
# Arrêter les services
docker-compose down

# Recréer la session
1_creer_session.bat

# Relancer la collection iCal
2_collecter_ical.bat
```

**Option 2**: Vérifier les cookies
```python
# Dans collect_ical_urls.py
print(f"Cookies disponibles: {len(context.cookies())}")
```

---

## 📋 PLAN D'ACTION

### 🔧 Corrections immédiates

1. **Fixer le Dockerfile** (2 minutes)
   ```dockerfile
   COPY currency_converter.py .
   ```

2. **Activer la collection des contacts** (1 minute)
   ```bash
   # Dans .env
   COLLECT_CONTACTS=true
   ```

3. **Rebuild l'image Docker** (5 minutes)
   ```bash
   docker-compose build
   ```

### 🔍 Investigations nécessaires

4. **Vérifier les données dans Supabase** (5 minutes)
   ```sql
   SELECT COUNT(*) FROM reservations;
   SELECT * FROM reservations ORDER BY synced_at DESC LIMIT 5;
   ```

5. **Vérifier les logs de l'API Next.js** (5 minutes)
   ```bash
   docker logs nextjs-api | grep -i "error"
   ```

6. **Tester avec une réservation** (2 minutes)
   ```bash
   python TEST_RAPIDE_UNE_RESERVATION.py
   ```

### 🚀 Re-scraping complet

7. **Relancer le scraping complet** (60 minutes)
   ```bash
   # Après avoir fixé les problèmes
   .\DOCKER_SCRAPING_COMPLET.bat
   ```

---

## 📊 MÉTRIQUES ATTENDUES (après corrections)

```
✅ Scraping complet réussi!
   Réservations scrapées: 6,196
   Réservations envoyées: 6,196
   
   📊 Métriques API:
      • Traitées:  6,196
      • Créées:    4,500  ✅ (nouvelles)
      • Mises à jour: 1,696  ✅ (existantes)
      • Ignorées:  0
      • Échouées:  0
   
   💱 Conversion des devises:
      • GBP × 270 = DZD  ✅
      • EUR × 250 = DZD  ✅
      • USD × 250 = DZD  ✅
   
   📞 Contacts collectés:
      • Téléphones: 5,800  ✅
      • Emails: 6,196  ✅
   
   📅 iCal URLs:
      • Collectées: 49/51  ✅ (96%)
```

---

## 🎯 PRIORITÉS

| Priorité | Problème | Impact | Temps |
|----------|----------|--------|-------|
| 🔴 **P0** | Conversion devises | Montants incorrects en DZD | 2 min |
| 🔴 **P0** | API 0 créées/mises à jour | Données non insérées | 15 min |
| 🟡 **P1** | Collection contacts | Impossible de contacter voyageurs | 1 min |
| 🟡 **P1** | Collection iCal | Sync automatique cassée | 10 min |

---

## ✅ CHECKLIST DE VÉRIFICATION

Avant de relancer le scraping complet:

- [ ] `currency_converter.py` copié dans Dockerfile
- [ ] `COLLECT_CONTACTS=true` dans `.env`
- [ ] Image Docker rebuild (`docker-compose build`)
- [ ] Test avec une réservation réussi
- [ ] Données visibles dans Supabase
- [ ] API Next.js retourne `created > 0` ou `updated > 0`
- [ ] Session Airbnb valide (cookies présents)
- [ ] iCal URLs collectées (> 45/51)

---

**Prochaine étape**: Fixer le Dockerfile et rebuild l'image Docker.
