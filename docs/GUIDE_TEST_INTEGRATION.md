# 🧪 GUIDE DE TEST - Intégration Collecte des Coordonnées

## Date : 31 mai 2026
## Version : 2.1

---

## 🎯 OBJECTIF

Tester l'intégration complète de la collecte des coordonnées dans le flux de synchronisation Airbnb → Supabase.

---

## 📋 PRÉ-REQUIS

### 1. Vérifications automatiques

**Commande** :
```batch
TEST_INTEGRATION_CONTACTS.bat
```

**Résultat attendu** :
```
✅ Fonction enrich_with_contacts trouvée
✅ Variable COLLECT_CONTACTS trouvée
✅ Champ telephone_voyageur trouvé
✅ Import enrich_with_contacts trouvé
✅ Variable COLLECT_CONTACTS trouvée dans .env
✅ Variable COLLECT_CONTACTS trouvée dans .env.example
```

---

### 2. Vérification Supabase

**Action** : Vérifier que la table `reservations` a les colonnes nécessaires.

**Méthode 1** : Via l'interface Supabase
1. Aller sur https://supabase.com/dashboard
2. Sélectionner le projet
3. Aller dans "Table Editor" → "reservations"
4. Vérifier les colonnes :
   - `guest_phone` (type: TEXT)
   - `guest_email` (type: TEXT)

**Méthode 2** : Via SQL
```sql
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'reservations'
AND column_name IN ('guest_phone', 'guest_email')
ORDER BY column_name;
```

**Résultat attendu** :
```
column_name  | data_type | is_nullable
-------------+-----------+-------------
guest_email  | text      | YES
guest_phone  | text      | YES
```

**Si les colonnes n'existent pas** :
```sql
ALTER TABLE reservations
ADD COLUMN IF NOT EXISTS guest_phone TEXT,
ADD COLUMN IF NOT EXISTS guest_email TEXT;
```

---

### 3. Vérification API Next.js

**Action** : Vérifier que l'API mappe correctement les champs.

**Fichier** : `/api/airbnb/sync/route.ts` (ou similaire)

**Code attendu** :
```typescript
// Mapping des champs
const reservation = {
  confirmation_code: data.id,
  status: data.statut,
  guest_name: data.voyageur,
  guest_phone: data.telephone_voyageur,  // ✅ NOUVEAU
  guest_email: data.email_voyageur,      // ✅ NOUVEAU
  guest_count: data.nb_voyageurs,
  listing_name: data.logement,
  airbnb_listing_id: data.listing_id,
  check_in: data.date_arrivee,
  check_out: data.date_depart,
  nights: data.nb_nuits,
  total_amount: data.montant_total,
  currency: data.devise,
  created_at: data.date_creation,
};
```

**Si le mapping n'existe pas** : Ajouter les lignes manquantes.

---

## 🧪 TEST 1 : Scraping complet avec coordonnées

### Étape 1 : Activer la collecte

**Fichier** : `.env`
```env
COLLECT_CONTACTS=true
```

---

### Étape 2 : Lancer le scraping

**Commande** :
```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

**Durée estimée** : 30-50 minutes (selon le nombre de réservations actives)

---

### Étape 3 : Vérifier les logs

**Rechercher dans les logs** :
```
📞 Enrichissement avec les coordonnées...
   ⏳ Cela prendra ~5 secondes par réservation
   ↳ 10 coordonnées collectées...
   ↳ 20 coordonnées collectées...
   ✅ 25 réservations enrichies avec coordonnées
```

**Si erreur** :
- Vérifier que la session Airbnb est valide
- Vérifier que les URLs de réservation sont accessibles
- Vérifier les captures d'écran dans `output/`

---

### Étape 4 : Vérifier le fichier JSON

**Fichier** : `output/reservations_airbnb.json`

**Ouvrir et chercher** :
```json
{
  "id": "HM4TB95HKS",
  "statut": "Confirmée",
  "voyageur": "Hamza",
  "telephone_voyageur": "+213 793 86 24 94",  // ✅ Doit être présent
  "email_voyageur": "hamza@example.com",      // ✅ Doit être présent
  "nb_voyageurs": 2,
  "logement": "Choco Loft",
  ...
}
```

**Vérifications** :
- ✅ Champ `telephone_voyageur` présent
- ✅ Champ `email_voyageur` présent
- ✅ Valeurs non vides pour les réservations actives
- ✅ Valeurs vides (`""`) pour les réservations passées/annulées

---

### Étape 5 : Vérifier Supabase

**Méthode 1** : Via l'interface Supabase
1. Aller dans "Table Editor" → "reservations"
2. Chercher une réservation récente (ex: HM4TB95HKS)
3. Vérifier les colonnes :
   - `guest_phone` : "+213 793 86 24 94"
   - `guest_email` : "hamza@example.com"

**Méthode 2** : Via SQL
```sql
SELECT 
  confirmation_code,
  guest_name,
  guest_phone,
  guest_email,
  status
FROM reservations
WHERE guest_phone IS NOT NULL
  AND guest_phone != ''
ORDER BY updated_at DESC
LIMIT 10;
```

**Résultat attendu** :
```
confirmation_code | guest_name | guest_phone        | guest_email           | status
------------------+------------+--------------------+-----------------------+----------
HM4TB95HKS        | Hamza      | +213 793 86 24 94  | hamza@example.com     | Confirmée
...
```

---

### Étape 6 : Statistiques

**SQL** :
```sql
-- Nombre total de réservations
SELECT COUNT(*) as total FROM reservations;

-- Nombre avec téléphone
SELECT COUNT(*) as with_phone 
FROM reservations 
WHERE guest_phone IS NOT NULL AND guest_phone != '';

-- Nombre avec email
SELECT COUNT(*) as with_email 
FROM reservations 
WHERE guest_email IS NOT NULL AND guest_email != '';

-- Taux de collecte
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN guest_phone IS NOT NULL AND guest_phone != '' THEN 1 END) as with_phone,
  ROUND(100.0 * COUNT(CASE WHEN guest_phone IS NOT NULL AND guest_phone != '' THEN 1 END) / COUNT(*), 2) as phone_rate,
  COUNT(CASE WHEN guest_email IS NOT NULL AND guest_email != '' THEN 1 END) as with_email,
  ROUND(100.0 * COUNT(CASE WHEN guest_email IS NOT NULL AND guest_email != '' THEN 1 END) / COUNT(*), 2) as email_rate
FROM reservations
WHERE status IN ('Confirmée', 'upcoming', 'accepted');
```

---

## 🧪 TEST 2 : Scraping ciblé avec coordonnées

### Étape 1 : Activer la collecte

**Fichier** : `.env`
```env
COLLECT_CONTACTS=true
```

---

### Étape 2 : Lancer les services Docker

**Commande** :
```batch
DOCKER_START.bat
```

**Vérifier les logs** :
```batch
DOCKER_LOGS.bat
```

**Rechercher** :
```
Targeted Scraper — Scraping ciblé sur demande
Poll interval : 30s
Moteur        : CloakBrowser
Headless      : True
Coordonnées   : Activé ✅  // ✅ Doit être présent
```

---

### Étape 3 : Déclencher un changement

**Méthode 1** : Modifier une réservation sur Airbnb
1. Aller sur https://fr.airbnb.com/hosting/reservations
2. Modifier une réservation (ex: changer les dates)
3. Sauvegarder

**Méthode 2** : Forcer un changement iCal
1. Télécharger le fichier iCal d'une annonce
2. Modifier une date
3. Re-télécharger (le hash changera)

---

### Étape 4 : Vérifier les logs du Targeted Scraper

**Commande** :
```batch
DOCKER_LOGS.bat
```

**Rechercher** :
```
Queue #123 — listing 1460801131962293583
Raison : ical_changed
Scraping des reservations pour listing 1460801131962293583...
21 reservations trouvees pour 1460801131962293583
📞 Collecte des coordonnées activée...  // ✅ Doit être présent
   ✅ 5 réservations enrichies avec coordonnées
21 reservations envoyees a l'API
Termine avec succes
```

---

### Étape 5 : Vérifier Supabase

**SQL** :
```sql
SELECT 
  confirmation_code,
  guest_name,
  guest_phone,
  guest_email,
  status,
  updated_at
FROM reservations
WHERE airbnb_listing_id = '1460801131962293583'
  AND updated_at > NOW() - INTERVAL '10 minutes'
ORDER BY updated_at DESC;
```

**Vérifier** :
- ✅ Réservations mises à jour récemment
- ✅ Champs `guest_phone` et `guest_email` remplis

---

## 🧪 TEST 3 : Collecte manuelle

### Étape 1 : Désactiver la collecte automatique

**Fichier** : `.env`
```env
COLLECT_CONTACTS=false
```

---

### Étape 2 : Lancer le scraping complet

**Commande** :
```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

**Vérifier** : Les champs `telephone_voyageur` et `email_voyageur` sont vides (`""`)

---

### Étape 3 : Collecter manuellement

**Commande** :
```batch
7_collecter_contacts.bat
```

**Durée estimée** : ~5 secondes par réservation active

---

### Étape 4 : Vérifier le fichier JSON

**Fichier** : `output/reservations_avec_contacts.json`

**Vérifier** :
- ✅ Champs `telephone_voyageur` et `email_voyageur` remplis
- ✅ Uniquement pour les réservations actives

---

### Étape 5 : Envoyer à Supabase

**Option 1** : Relancer le scraping complet
```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

**Option 2** : Utiliser un script d'import (à créer)
```python
# import_contacts.py
import json
from airbnb_api_client import upsert_reservations

with open("output/reservations_avec_contacts.json", "r", encoding="utf-8") as f:
    reservations = json.load(f)

upsert_reservations(reservations, sync_type="manual")
print(f"✅ {len(reservations)} réservations envoyées")
```

---

## 📊 RÉSULTATS ATTENDUS

### Taux de collecte

| Type de réservation | Téléphone | Email |
|---------------------|-----------|-------|
| Confirmée / À venir | 80-95%    | 50-70% |
| En cours            | 80-95%    | 50-70% |
| Passée              | 0%        | 0% |
| Annulée             | 0%        | 0% |

**Note** : Le taux de collecte dépend de la disponibilité des informations sur Airbnb.

---

### Performance

| Nombre de réservations actives | Temps supplémentaire |
|--------------------------------|----------------------|
| 10                             | +50 secondes         |
| 50                             | +4 minutes           |
| 100                            | +8 minutes           |
| 200                            | +17 minutes          |

---

## ❌ PROBLÈMES COURANTS

### Problème 1 : Aucune coordonnée collectée

**Symptôme** : Tous les champs `telephone_voyageur` et `email_voyageur` sont vides.

**Causes possibles** :
1. `COLLECT_CONTACTS=false` dans `.env`
2. Aucune réservation active
3. Session Airbnb expirée
4. Changement de structure HTML Airbnb

**Solutions** :
1. Vérifier `.env` : `COLLECT_CONTACTS=true`
2. Vérifier qu'il y a des réservations actives
3. Recréer la session : `1_creer_session.bat`
4. Vérifier les captures d'écran dans `output/`

---

### Problème 2 : Erreur "Timeout"

**Symptôme** : Erreur "Timeout 30000ms exceeded" dans les logs.

**Causes possibles** :
1. Page Airbnb trop lente à charger
2. Connexion internet lente
3. Airbnb bloque les requêtes (rate limiting)

**Solutions** :
1. Augmenter le timeout dans `get_guest_contact_info()` :
   ```python
   page.goto(url, wait_until="domcontentloaded", timeout=60000)  # 60 secondes
   ```
2. Ajouter une pause plus longue entre les requêtes :
   ```python
   time.sleep(5)  # Au lieu de 2 secondes
   ```
3. Utiliser un proxy résidentiel (variable `PROXY_URL`)

---

### Problème 3 : Coordonnées non insérées dans Supabase

**Symptôme** : Coordonnées dans le JSON mais pas dans Supabase.

**Causes possibles** :
1. Colonnes `guest_phone` et `guest_email` n'existent pas
2. API Next.js ne mappe pas les champs
3. Erreur dans l'API Next.js

**Solutions** :
1. Créer les colonnes (voir section "Vérification Supabase")
2. Vérifier le mapping dans l'API Next.js
3. Vérifier les logs de l'API Next.js

---

### Problème 4 : Rate limiting Airbnb

**Symptôme** : Erreur "Too many requests" ou blocage temporaire.

**Causes possibles** :
1. Trop de requêtes en peu de temps
2. Pas de proxy résidentiel

**Solutions** :
1. Augmenter la pause entre les requêtes :
   ```python
   time.sleep(5)  # Au lieu de 2 secondes
   ```
2. Utiliser `COLLECT_CONTACTS=false` et collecter manuellement
3. Configurer un proxy résidentiel (variable `PROXY_URL`)

---

## ✅ CHECKLIST FINALE

### Avant la mise en production

- [ ] Test 1 réussi (scraping complet avec coordonnées)
- [ ] Test 2 réussi (scraping ciblé avec coordonnées)
- [ ] Test 3 réussi (collecte manuelle)
- [ ] Colonnes Supabase créées
- [ ] API Next.js mise à jour
- [ ] Taux de collecte > 80% pour les téléphones
- [ ] Performance acceptable (< 10 min supplémentaires)
- [ ] Aucune erreur dans les logs
- [ ] Documentation à jour

---

### Configuration recommandée pour la production

**Fichier** : `.env`
```env
# Collecte automatique désactivée (recommandé)
COLLECT_CONTACTS=false
```

**Raisons** :
- ✅ Scraping plus rapide
- ✅ Moins de charge sur Airbnb
- ✅ Collecte manuelle à la demande (avant l'arrivée des voyageurs)

**Collecte manuelle** :
```batch
# Lancer 1-2 jours avant l'arrivée des voyageurs
7_collecter_contacts.bat
```

---

**Créé par Kiro le 31 mai 2026**
