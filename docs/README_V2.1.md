# 🎉 AIRBNB SCRAPER V2.1 - Collecte des Coordonnées

## ✅ INTÉGRATION COMPLÈTE

---

## 🆕 NOUVEAUTÉS V2.1

### Collecte des coordonnées des voyageurs

**Avant (V2.0)** :
```json
{
  "id": "HM4TB95HKS",
  "voyageur": "Hamza",
  "logement": "Choco Loft"
}
```

**Après (V2.1)** ✅ :
```json
{
  "id": "HM4TB95HKS",
  "voyageur": "Hamza",
  "telephone_voyageur": "+213 793 86 24 94",  // ✅ NOUVEAU
  "email_voyageur": "hamza@example.com",      // ✅ NOUVEAU
  "logement": "Choco Loft"
}
```

---

## 🚀 DÉMARRAGE RAPIDE

### 1. Configuration

**Fichier** : `.env`
```env
# Collecte automatique (plus lent : +5 sec par réservation)
COLLECT_CONTACTS=true

# OU collecte manuelle (recommandé)
COLLECT_CONTACTS=false
```

---

### 2. Utilisation

#### Option A : Collecte automatique

```batch
# Activer dans .env
COLLECT_CONTACTS=true

# Lancer le scraping
SCRAPING_COMPLET_MAINTENANT.bat

# Les coordonnées sont collectées automatiquement
```

#### Option B : Collecte manuelle (recommandé) ✅

```batch
# Désactiver dans .env
COLLECT_CONTACTS=false

# Lancer le scraping (rapide)
SCRAPING_COMPLET_MAINTENANT.bat

# Collecter les coordonnées manuellement (quand nécessaire)
7_collecter_contacts.bat
```

---

## 🧪 TESTS

### Test automatique

```batch
TEST_INTEGRATION_CONTACTS.bat
```

**Vérifie** :
- ✅ Code intégré dans `airbnb_scraper.py`
- ✅ Code intégré dans `targeted_scraper.py`
- ✅ Variable `COLLECT_CONTACTS` dans `.env`

---

### Test en conditions réelles

**Étape 1** : Activer la collecte
```env
COLLECT_CONTACTS=true
```

**Étape 2** : Lancer le scraping
```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

**Étape 3** : Vérifier les résultats
- `output/reservations_airbnb.json` (champs `telephone_voyageur` et `email_voyageur`)
- Supabase (colonnes `guest_phone` et `guest_email`)

**Guide détaillé** : `GUIDE_TEST_INTEGRATION.md`

---

## ⚠️ PRÉREQUIS

### Supabase

**Colonnes nécessaires** :
- `guest_phone` (TEXT)
- `guest_email` (TEXT)

**SQL** :
```sql
ALTER TABLE reservations
ADD COLUMN IF NOT EXISTS guest_phone TEXT,
ADD COLUMN IF NOT EXISTS guest_email TEXT;
```

---

### API Next.js

**Mapping nécessaire** :
```typescript
const reservation = {
  guest_phone: data.telephone_voyageur,  // ✅ AJOUTER
  guest_email: data.email_voyageur,      // ✅ AJOUTER
  // ... autres champs
};
```

---

## 📊 PERFORMANCE

### Temps supplémentaire

| Réservations actives | Temps supplémentaire |
|---------------------|----------------------|
| 10                  | +50 secondes         |
| 50                  | +4 minutes           |
| 100                 | +8 minutes           |
| 200                 | +17 minutes          |

---

## 💡 RECOMMANDATION

### Pour la production : Collecte manuelle ✅

**Configuration** :
```env
COLLECT_CONTACTS=false
```

**Raisons** :
- ✅ Scraping rapide
- ✅ Moins de charge sur Airbnb
- ✅ Collecte ciblée quand nécessaire

**Quand collecter** :
- 1-2 jours avant l'arrivée des voyageurs
- En cas d'urgence (besoin de contacter rapidement)

**Commande** :
```batch
7_collecter_contacts.bat
```

---

## 📚 DOCUMENTATION

| Document | Description |
|----------|-------------|
| `INTEGRATION_TERMINEE.md` | ⭐ Résumé de l'intégration |
| `RESUME_INTEGRATION_V2.1.md` | 📄 Résumé concis |
| `GUIDE_TEST_INTEGRATION.md` | 🧪 Guide de test détaillé |
| `INTEGRATION_CONTACTS_COMPLETE.md` | 📖 Documentation technique |
| `FLUX_COMPLET_V2.1.md` | 🔄 Flux complet |

---

## 📋 CHECKLIST

### Code ✅

- [x] `airbnb_scraper.py` intégré
- [x] `targeted_scraper.py` intégré
- [x] `.env` configuré
- [x] Tests automatiques passent

### Infrastructure ⚠️

- [ ] Colonnes Supabase créées
- [ ] API Next.js mise à jour

### Tests ⚠️

- [ ] Test en conditions réelles
- [ ] Vérification Supabase
- [ ] Vérification performance

---

## 🎯 PROCHAINES ÉTAPES

1. **Vérifier Supabase** : Créer les colonnes `guest_phone` et `guest_email`
2. **Vérifier l'API Next.js** : Ajouter le mapping des champs
3. **Tester** : Lancer un scraping complet avec `COLLECT_CONTACTS=true`
4. **Vérifier** : Coordonnées dans Supabase

**Guide détaillé** : `GUIDE_TEST_INTEGRATION.md`

---

## 🔄 FLUX COMPLET

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

## 🎉 RÉSUMÉ

### ✅ Ce qui a été fait

1. ✅ Code intégré dans `airbnb_scraper.py`
2. ✅ Code intégré dans `targeted_scraper.py`
3. ✅ Variable `COLLECT_CONTACTS` ajoutée
4. ✅ Tests automatiques créés
5. ✅ Documentation complète créée

### ⚠️ Ce qui reste à faire

1. ⚠️ Vérifier/créer les colonnes Supabase
2. ⚠️ Vérifier/mettre à jour l'API Next.js
3. ⚠️ Tester en conditions réelles

---

**Version** : 2.1  
**Date** : 31 mai 2026  
**Créé par** : Kiro
