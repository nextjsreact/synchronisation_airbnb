# 🎯 DIAGNOSTIC VISUEL DU PROBLÈME

## Date : 31 mai 2026

---

## FLUX DE DONNÉES ACTUEL

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. iCal Watcher (✅ FONCTIONNE)               │
│                                                                   │
│  Toutes les 5 minutes :                                          │
│  • Télécharge les calendriers iCal de 54 listings               │
│  • Calcule le hash SHA256 de chaque calendrier                  │
│  • Compare avec le hash précédent                                │
│  • Si changement → INSERT dans sync_queue                        │
│                                                                   │
│  Résultat : 18 changements détectés ✅                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    2. Sync Queue (✅ FONCTIONNE)                 │
│                                                                   │
│  Table Supabase avec les listings à synchroniser :              │
│                                                                   │
│  | id  | listing_id          | status     | reason      |       │
│  |-----|---------------------|------------|-------------|       │
│  | 1   | 1637669342598748246 | pending    | ical_change |       │
│  | 2   | 617505721133092844  | pending    | ical_change |       │
│  | 3   | 1637221795702469272 | pending    | ical_change |       │
│  | ... | ...                 | ...        | ...         |       │
│  | 16  | 1546499335564392461 | pending    | ical_change |       │
│  | 17  | 1526985730296514715 | processing | ical_change |       │
│  | 18  | ...                 | done       | ical_change |       │
│                                                                   │
│  Total : 16 pending + 1 processing + 1 done = 18 entrées ✅     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                3. Targeted Scraper (⚠️ PARTIELLEMENT)            │
│                                                                   │
│  Toutes les 30 secondes :                                        │
│  • Lit la sync_queue (status=pending)                            │
│  • Pour chaque entrée :                                          │
│    1. Lance le navigateur                                        │
│    2. Se connecte à Airbnb (session sauvegardée)                │
│    3. Appelle scrape_listing(page, listing_id)                   │
│                                                                   │
│  Résultat : Scraper lancé ✅                                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              4. scrape_listing() (⚠️ PROBLÈME ICI)               │
│                                                                   │
│  def scrape_listing(page, target_listing_id):                    │
│      # Étape 1 : Essayer l'API GraphQL (rapide)                 │
│      all_reservations = get_reservations(page)                   │
│      # ❌ Retourne 0 (API cassée)                                │
│                                                                   │
│      # Étape 2 : Fallback (lent mais fiable)                    │
│      if not all_reservations:                                    │
│          all_reservations = scrape_fallback(page)                │
│          # ✅ Retourne 6195 réservations (30-40 min)             │
│                                                                   │
│      # Étape 3 : Filtrer par listing_id                         │
│      targeted = [                                                │
│          r for r in all_reservations                             │
│          if r.get("listing_id") == target_listing_id             │
│      ]                                                            │
│      # ❌ Retourne 0 (PROBLÈME ICI)                              │
│                                                                   │
│      return targeted  # ← Liste vide                             │
│                                                                   │
│  Résultat : 0 réservations trouvées ❌                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 5. Synchronisation (❌ ÉCHOUE)                    │
│                                                                   │
│  if not reservations:                                            │
│      print("Aucune reservation — marquage done")                 │
│      mark_done(entry_id)                                         │
│      return                                                       │
│                                                                   │
│  Résultat : Marqué "done" sans synchroniser ❌                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## LE PROBLÈME EN 1 IMAGE

```
┌──────────────────────────────────────────────────────────────────┐
│                    SCRAPING FALLBACK                              │
│                                                                    │
│  Input  : page (navigateur Airbnb)                               │
│  Output : 6195 réservations                                       │
│                                                                    │
│  [                                                                 │
│    {                                                               │
│      "id": "HMABCD123",                                           │
│      "voyageur": "John Doe",                                      │
│      "logement": "Appartement Paris",                             │
│      "listing_id": "",  ← ❌ VIDE !                               │
│      "date_arrivee": "2026-06-01",                                │
│      ...                                                           │
│    },                                                              │
│    {                                                               │
│      "id": "HMXYZ789",                                            │
│      "voyageur": "Jane Smith",                                    │
│      "logement": "Studio Lyon",                                   │
│      "listing_id": "",  ← ❌ VIDE !                               │
│      "date_arrivee": "2026-06-05",                                │
│      ...                                                           │
│    },                                                              │
│    ... (6193 autres réservations)                                 │
│  ]                                                                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    FILTRE PAR LISTING_ID                          │
│                                                                    │
│  target_listing_id = "1526985730296514715"                        │
│                                                                    │
│  targeted = [                                                      │
│      r for r in all_reservations                                  │
│      if r.get("listing_id") == "1526985730296514715"              │
│  ]                                                                 │
│                                                                    │
│  Comparaison :                                                     │
│    "" == "1526985730296514715" → False                            │
│    "" == "1526985730296514715" → False                            │
│    "" == "1526985730296514715" → False                            │
│    ... (6195 fois)                                                 │
│                                                                    │
│  Résultat : targeted = [] (liste vide)                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## POURQUOI LE LISTING_ID EST VIDE ?

### Parsing actuel dans `_parse_reservation_node()`

```python
def _parse_reservation_node(node):
    return {
        "listing_id": _extract_field(node, 
            ["listing_id"],    # ← Cherche node["listing_id"]
            ["listingId"],     # ← Cherche node["listingId"]
            default=""),       # ← Si pas trouvé, retourne ""
    }
```

### Structure réelle de l'API Airbnb (hypothèse)

```json
{
  "id": "HMABCD123",
  "guest_user": { "full_name": "John Doe" },
  "listing": {
    "id": "1526985730296514715",  ← Le listing_id est ICI !
    "name": "Appartement Paris"
  },
  "start_date": "2026-06-01",
  ...
}
```

### Correction nécessaire

```python
def _parse_reservation_node(node):
    return {
        "listing_id": _extract_field(node, 
            ["listing_id"],           # ← Essayer d'abord
            ["listingId"],
            ["listing", "id"],        # ← AJOUTER CE CHEMIN
            ["listing", "listing_id"],
            ["property_id"],
            default=""),
    }
```

---

## IMPACT DU PROBLÈME

### Temps perdu

```
Pour chaque changement détecté (16 actuellement) :
  • Scraping complet : 40 minutes
  • Filtrage : 0 résultats
  • Synchronisation : 0 réservations
  
Total : 16 × 40 min = 10h40 de scraping pour RIEN
```

### Données non synchronisées

```
Nouvelles réservations Airbnb : OUI (détectées par iCal)
Réservations dans votre base : NON (filtre cassé)

Résultat : Vos données sont obsolètes
```

---

## SOLUTION EN 3 ÉTAPES

### ÉTAPE 1 : Synchroniser maintenant (40 min)

```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

Cela va synchroniser **toutes** les 6195 réservations immédiatement.

### ÉTAPE 2 : Identifier le problème (5 min)

```batch
6_debug_listing_id.bat
```

Cela va créer des fichiers JSON montrant la structure exacte de l'API.

### ÉTAPE 3 : Corriger le code (10 min)

Modifier `airbnb_scraper.py` avec le bon chemin vers `listing_id`.

---

## COMPARAISON DES APPROCHES

### Approche A : Scraping ciblé (actuel, cassé)

```
Avantages :
  ✅ Rapide (2-3 min par listing avec API GraphQL)
  ✅ Économise de la bande passante
  ✅ Moins de charge sur Airbnb

Inconvénients :
  ❌ API GraphQL cassée (retourne 0)
  ❌ Fallback lent (30-40 min)
  ❌ Filtre cassé (retourne 0)
  ❌ Ne fonctionne pas actuellement

État : ❌ CASSÉ
```

### Approche B : Scraping complet périodique

```
Avantages :
  ✅ Fonctionne à coup sûr
  ✅ Simple à maintenir
  ✅ Pas de filtre nécessaire

Inconvénients :
  ❌ Lent (40 min par scraping)
  ❌ Beaucoup de bande passante
  ❌ Charge élevée sur Airbnb

État : ✅ FONCTIONNE (mais lent)
```

### Approche C : Scraping ciblé corrigé (recommandé)

```
Avantages :
  ✅ Rapide (30-40 min pour scraper tout)
  ✅ Filtre fonctionne (après correction)
  ✅ Synchronisation ciblée (2-3 min par listing)

Inconvénients :
  ⚠️  Nécessite de corriger le parsing
  ⚠️  API GraphQL toujours cassée (utilise fallback)

État : 🔧 À CORRIGER
```

---

## FICHIERS À CONSULTER

1. **PROBLEME_IDENTIFIE.md** : Analyse technique détaillée
2. **REPONSES_COMPLETES.md** : Réponses à toutes vos questions
3. **DIAGNOSTIC_VISUEL.md** : Ce fichier (schémas visuels)
4. **debug_listing_id.py** : Script de diagnostic
5. **6_debug_listing_id.bat** : Lanceur du diagnostic

---

## PROCHAINE ACTION RECOMMANDÉE

```batch
# 1. Synchroniser maintenant (pendant que vous lisez)
SCRAPING_COMPLET_MAINTENANT.bat

# 2. Pendant ce temps, lancer le diagnostic
6_debug_listing_id.bat

# 3. Corriger le code avec les résultats du diagnostic

# 4. Relancer le système
LANCER_MAINTENANT.bat
```

---

**Créé par Kiro le 31 mai 2026**
