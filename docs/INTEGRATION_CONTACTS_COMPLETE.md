# ✅ INTÉGRATION COMPLÈTE - COLLECTE DES COORDONNÉES

## Date : 31 mai 2026
## Version : 2.1 (finale)

---

## 🎯 OBJECTIF

Intégrer la collecte des coordonnées des voyageurs (téléphone + email) dans le flux complet de synchronisation Airbnb → Supabase, **avant** l'insertion dans la base de données.

---

## ✅ MODIFICATIONS EFFECTUÉES

### 1. **airbnb_scraper.py** ✅

**Ajouts** :
- ✅ Fonction `get_guest_contact_info(page, confirmation_code)` (lignes ~680-730)
- ✅ Fonction `enrich_with_contacts(page, reservations, collect_contacts=True)` (lignes ~735-790)
- ✅ Variable d'environnement `COLLECT_CONTACTS` (ligne ~90)
- ✅ Intégration dans le flux principal (Étape 6, ligne ~1150)

**Flux mis à jour** :
```python
# Étape 1 : Connexion
login(page)

# Étape 2 : Réservations (API GraphQL)
gql_reservations = get_reservations(page)

# Étape 3 : Fallback réseau
net_reservations = scrape_fallback(page)

# Étape 4 : Fusion
reservations = merge(gql_reservations, net_reservations)

# Étape 5 : Collecte URLs iCal
ical_urls = collect_ical_urls(page, listing_ids)

# ✅ ÉTAPE 6 : Enrichissement avec coordonnées (NOUVEAU)
if COLLECT_CONTACTS:
    reservations = enrich_with_contacts(page, reservations, collect_contacts=True)
else:
    # Ajouter des champs vides
    for r in reservations:
        r["telephone_voyageur"] = ""
        r["email_voyageur"] = ""

# Étape 7 : Export local CSV + JSON
export_csv(reservations, OUTPUT_CSV)
export_json(reservations, OUTPUT_JSON)

# Étape 8 : Push API Next.js (avec coordonnées)
push_to_nextjs(reservations, ical_urls, sync_type='full')

# Étape 9 : Log de sync
log_sync(...)
```

---

### 2. **targeted_scraper.py** ✅

**Ajouts** :
- ✅ Import de `enrich_with_contacts` depuis `airbnb_scraper` (ligne ~30)
- ✅ Variable d'environnement `COLLECT_CONTACTS` (ligne ~40)
- ✅ Intégration dans `process_entry()` (lignes ~120-130)
- ✅ Affichage du statut dans `main()` (ligne ~180)

**Flux mis à jour** :
```python
def process_entry(page, entry):
    # 1. Scraper les réservations
    reservations = scrape_listing(page, listing_id)
    
    # ✅ 2. Enrichir avec les coordonnées (NOUVEAU)
    if COLLECT_CONTACTS:
        reservations = enrich_with_contacts(page, reservations, collect_contacts=True)
    else:
        # Ajouter des champs vides
        for r in reservations:
            r["telephone_voyageur"] = ""
            r["email_voyageur"] = ""
    
    # 3. Envoyer à l'API Next.js (avec coordonnées)
    count = upsert_reservations(reservations, sync_type="targeted")
    
    # 4. Refresh l'URL iCal
    ical_urls = collect_ical_urls(page, [listing_id])
```

---

### 3. **.env** ✅

**Ajout** :
```env
# Collecte des coordonnées des voyageurs (téléphone + email)
# true = Collecte automatique (plus lent : +5 sec par réservation)
# false = Pas de collecte automatique (utiliser 7_collecter_contacts.bat manuellement)
COLLECT_CONTACTS=false
```

**Recommandation** : Laisser à `false` par défaut pour éviter de ralentir le scraping.

---

### 4. **.env.example** ✅

**Ajout** :
```env
# Collecte des coordonnées des voyageurs (téléphone + email)
# true = Collecte automatique (plus lent : +5 sec par réservation)
# false = Pas de collecte automatique (utiliser 7_collecter_contacts.bat manuellement)
COLLECT_CONTACTS=false
```

---

## 📊 STRUCTURE DES DONNÉES

### Avant (V2.0)

```json
{
  "id": "HM4TB95HKS",
  "statut": "Confirmée",
  "voyageur": "Hamza",
  "nb_voyageurs": 2,
  "logement": "Choco Loft",
  "listing_id": "1361868072916616334",
  "date_arrivee": "2026-05-29",
  "date_depart": "2026-05-31",
  "nb_nuits": 2,
  "montant_total": 150.0,
  "devise": "EUR",
  "date_creation": "2026-05-20"
}
```

### Après (V2.1) ✅

```json
{
  "id": "HM4TB95HKS",
  "statut": "Confirmée",
  "voyageur": "Hamza",
  "telephone_voyageur": "+213 793 86 24 94",  // ✅ NOUVEAU
  "email_voyageur": "hamza@example.com",      // ✅ NOUVEAU
  "nb_voyageurs": 2,
  "logement": "Choco Loft",
  "listing_id": "1361868072916616334",
  "date_arrivee": "2026-05-29",
  "date_depart": "2026-05-31",
  "nb_nuits": 2,
  "montant_total": 150.0,
  "devise": "EUR",
  "date_creation": "2026-05-20"
}
```

---

## 🔄 FLUX COMPLET (V2.1)

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTÈME DE SYNCHRONISATION                    │
│                         Airbnb → Supabase                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────┴─────────────────────┐
        │                                             │
        ↓                                             ↓
┌───────────────────┐                     ┌───────────────────┐
│   iCal Watcher    │                     │ Targeted Scraper  │
│  (Toutes les 5min)│                     │ (Toutes les 30sec)│
└───────────────────┘                     └───────────────────┘
        │                                             │
        ↓                                             ↓
┌───────────────────┐                     ┌───────────────────┐
│   sync_queue      │ ←───────────────────│  Scraping Airbnb  │
│   (Supabase)      │                     │                   │
└───────────────────┘                     └───────────────────┘
                                                    │
                                                    ↓
                                          ┌───────────────────┐
                                          │ ✅ Enrichissement │
                                          │   Coordonnées     │
                                          │ (si activé)       │
                                          └───────────────────┘
                                                    │
                                                    ↓
                                          ┌───────────────────┐
                                          │  API Next.js      │
                                          │  /api/airbnb/sync │
                                          └───────────────────┘
                                                    │
                                                    ↓
                                          ┌───────────────────┐
                                          │  Supabase         │
                                          │  (PostgreSQL)     │
                                          │  + coordonnées ✅ │
                                          └───────────────────┘
```

---

## ⚙️ CONFIGURATION

### Option 1 : Collecte automatique (plus lent)

**Fichier** : `.env`
```env
COLLECT_CONTACTS=true
```

**Avantages** :
- ✅ Coordonnées toujours à jour
- ✅ Pas d'action manuelle

**Inconvénients** :
- ⚠️ +5 secondes par réservation active
- ⚠️ Scraping plus lent (ex: 100 rés actives = +8 minutes)
- ⚠️ Plus de charge sur Airbnb (risque de rate limiting)

---

### Option 2 : Collecte manuelle (recommandé) ✅

**Fichier** : `.env`
```env
COLLECT_CONTACTS=false
```

**Avantages** :
- ✅ Scraping rapide
- ✅ Moins de charge sur Airbnb
- ✅ Collecte à la demande

**Inconvénients** :
- ⚠️ Nécessite une action manuelle

**Commande manuelle** :
```batch
7_collecter_contacts.bat
```

---

## 🧪 TESTS EFFECTUÉS

### Test 1 : Extraction standalone ✅

**Script** : `test_contact_extraction.py`  
**Commande** : `TEST_CONTACT_SIMPLE.bat`  
**Résultat** : ✅ Téléphone `+213 793 86 24 94` extrait avec succès

---

### Test 2 : Intégration dans airbnb_scraper.py ✅

**Statut** : Code intégré, **pas encore testé en conditions réelles**

**À tester** :
1. Lancer un scraping complet avec `COLLECT_CONTACTS=true`
2. Vérifier que les coordonnées sont collectées
3. Vérifier que les données sont envoyées à l'API Next.js
4. Vérifier que les données sont insérées dans Supabase

---

### Test 3 : Intégration dans targeted_scraper.py ✅

**Statut** : Code intégré, **pas encore testé en conditions réelles**

**À tester** :
1. Lancer les services Docker avec `COLLECT_CONTACTS=true`
2. Déclencher un changement iCal
3. Vérifier que le Targeted Scraper collecte les coordonnées
4. Vérifier que les données sont envoyées à l'API Next.js

---

## 📋 CHECKLIST DE VÉRIFICATION

### Avant de tester

- [x] Code intégré dans `airbnb_scraper.py`
- [x] Code intégré dans `targeted_scraper.py`
- [x] Variable `COLLECT_CONTACTS` ajoutée à `.env`
- [x] Variable `COLLECT_CONTACTS` ajoutée à `.env.example`
- [x] Documentation mise à jour (`FLUX_COMPLET_V2.1.md`)
- [ ] **Test en conditions réelles (scraping complet)**
- [ ] **Test en conditions réelles (targeted scraper)**
- [ ] **Vérification Supabase (colonnes `guest_phone` et `guest_email`)**
- [ ] **Vérification API Next.js (mapping des champs)**

---

### Après le test

- [ ] Coordonnées dans `output/reservations_airbnb.json`
- [ ] Coordonnées dans Supabase (table `reservations`)
- [ ] Logs sans erreur
- [ ] Performance acceptable (temps de scraping)

---

## 🎯 PROCHAINES ÉTAPES

### 1. Vérifier la structure Supabase

**Action** : Vérifier que la table `reservations` a les colonnes :
- `guest_phone` (TEXT)
- `guest_email` (TEXT)

**Commande** :
```sql
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'reservations' 
AND column_name IN ('guest_phone', 'guest_email');
```

---

### 2. Vérifier l'API Next.js

**Action** : Vérifier que l'API mappe correctement les champs :
- `telephone_voyageur` → `guest_phone`
- `email_voyageur` → `guest_email`

**Fichier** : `/api/airbnb/sync` dans le projet Next.js

---

### 3. Test complet

**Scénario 1** : Scraping complet avec coordonnées
```batch
# 1. Activer la collecte
# Modifier .env : COLLECT_CONTACTS=true

# 2. Lancer le scraping
SCRAPING_COMPLET_MAINTENANT.bat

# 3. Vérifier les résultats
# - output/reservations_airbnb.json (champs telephone_voyageur et email_voyageur)
# - Supabase (colonnes guest_phone et guest_email)
```

**Scénario 2** : Scraping ciblé avec coordonnées
```batch
# 1. Activer la collecte
# Modifier .env : COLLECT_CONTACTS=true

# 2. Lancer les services
DOCKER_START.bat

# 3. Déclencher un changement (modifier une réservation sur Airbnb)

# 4. Vérifier les logs
DOCKER_LOGS.bat

# 5. Vérifier Supabase
```

---

## 📊 TEMPS DE TRAITEMENT ESTIMÉS

### Scraping complet

| Réservations actives | Sans coordonnées | Avec coordonnées | Différence |
|---------------------|------------------|------------------|------------|
| 10                  | 30-40 min        | 31-41 min        | +1 min     |
| 50                  | 30-40 min        | 34-44 min        | +4 min     |
| 100                 | 30-40 min        | 38-48 min        | +8 min     |
| 200                 | 30-40 min        | 47-57 min        | +17 min    |

### Scraping ciblé (1 listing)

| Réservations actives | Sans coordonnées | Avec coordonnées | Différence |
|---------------------|------------------|------------------|------------|
| 1                   | 30-40 min        | 30-40 min        | +5 sec     |
| 5                   | 30-40 min        | 30-40 min        | +25 sec    |
| 10                  | 30-40 min        | 31-41 min        | +50 sec    |

---

## 🎉 RÉSUMÉ

### Ce qui a été fait ✅

1. ✅ Fonction `get_guest_contact_info()` créée et testée
2. ✅ Fonction `enrich_with_contacts()` créée
3. ✅ Intégration dans `airbnb_scraper.py` (Étape 6)
4. ✅ Intégration dans `targeted_scraper.py` (process_entry)
5. ✅ Variable `COLLECT_CONTACTS` ajoutée à `.env`
6. ✅ Documentation complète créée

### Ce qui reste à faire ⚠️

1. ⚠️ **Tester en conditions réelles** (scraping complet)
2. ⚠️ **Tester en conditions réelles** (targeted scraper)
3. ⚠️ **Vérifier la structure Supabase** (colonnes guest_phone et guest_email)
4. ⚠️ **Vérifier l'API Next.js** (mapping des champs)

---

## 💡 RECOMMANDATIONS

### Pour la production

1. **Laisser `COLLECT_CONTACTS=false` par défaut**
   - Scraping plus rapide
   - Moins de charge sur Airbnb
   - Collecte manuelle à la demande

2. **Collecter manuellement avant l'arrivée des voyageurs**
   - Lancer `7_collecter_contacts.bat` 1-2 jours avant
   - Envoyer les instructions d'arrivée avec les coordonnées

3. **Monitorer les performances**
   - Vérifier les logs pour détecter les erreurs
   - Ajuster `COLLECT_CONTACTS` selon les besoins

---

**Créé par Kiro le 31 mai 2026**
