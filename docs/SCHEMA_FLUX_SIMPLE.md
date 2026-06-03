# 📊 SCHÉMA DU FLUX - VERSION SIMPLE

## Date : 31 mai 2026

---

## 🔄 FLUX COMPLET EN 7 ÉTAPES

```
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : DÉTECTION DES CHANGEMENTS                             │
│ iCal Watcher (toutes les 5 minutes)                             │
├─────────────────────────────────────────────────────────────────┤
│ • Télécharge les calendriers iCal                               │
│ • Calcule le hash SHA256                                        │
│ • Compare avec le hash précédent                                │
│ • Si changement → INSERT dans sync_queue                        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2 : LECTURE DE LA QUEUE                                   │
│ Targeted Scraper (toutes les 30 secondes)                       │
├─────────────────────────────────────────────────────────────────┤
│ • Lit sync_queue (status=pending)                               │
│ • Récupère le listing_id à synchroniser                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3 : SCRAPING AIRBNB                                       │
│ Récupération des réservations                                   │
├─────────────────────────────────────────────────────────────────┤
│ Méthode 1 : API GraphQL (rapide - 2-3 min)                     │
│   ❌ Actuellement cassée (retourne 0)                           │
│                                                                  │
│ Méthode 2 : Fallback (lent - 30-40 min)                        │
│   ✅ Fonctionne toujours                                        │
│   • Navigue sur les pages de réservations                       │
│   • Intercepte les requêtes réseau                              │
│   • Pagine avec "Suivant"                                       │
│   • Collecte 6195 réservations                                  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4 : COLLECTE DES COORDONNÉES (OPTIONNEL)                 │
│ Si COLLECT_CONTACTS=true                                        │
├─────────────────────────────────────────────────────────────────┤
│ Pour chaque réservation active :                                │
│ • Ouvre la page de détails                                      │
│ • Extrait le numéro de téléphone                                │
│ • Extrait l'email                                               │
│ • Temps : +5 secondes par réservation                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 5 : FILTRAGE PAR LISTING_ID                               │
│ Pour le scraping ciblé uniquement                               │
├─────────────────────────────────────────────────────────────────┤
│ • Filtre les 6195 réservations                                  │
│ • Garde uniquement celles du listing_id cible                   │
│ • Exemple : 6195 → 21 réservations                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 6 : ENVOI À L'API NEXT.JS                                 │
│ POST /api/airbnb/sync                                           │
├─────────────────────────────────────────────────────────────────┤
│ • Envoie par batch de 50 réservations                           │
│ • Données : id, statut, voyageur, téléphone, email, etc.        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 7 : INSERTION DANS SUPABASE                               │
│ Table : reservations (PostgreSQL)                               │
├─────────────────────────────────────────────────────────────────┤
│ • Upsert : INSERT si nouveau, UPDATE si existe                  │
│ • Mapping des champs                                            │
│ • Données disponibles dans votre base                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 DONNÉES COLLECTÉES

### Avant V2.1 (sans coordonnées)

```
id, statut, voyageur, nb_voyageurs, logement, listing_id,
date_arrivee, date_depart, nb_nuits, montant_total, devise
```

### Après V2.1 (avec coordonnées)

```
id, statut, voyageur, telephone_voyageur, email_voyageur,
nb_voyageurs, logement, listing_id, date_arrivee, date_depart,
nb_nuits, montant_total, devise
```

---

## ⚙️ CONFIGURATION

### Collecte automatique (plus lent)

```env
COLLECT_CONTACTS=true
```

**Temps** : +5 secondes par réservation active

### Collecte manuelle (recommandé)

```env
COLLECT_CONTACTS=false
```

**Commande** : `7_collecter_contacts.bat`

---

## ⏱️ TEMPS DE TRAITEMENT

### Scraping complet

| Sans coordonnées | Avec coordonnées |
|------------------|------------------|
| 30-40 minutes | 38-48 minutes |

### Scraping ciblé (1 listing)

| Sans coordonnées | Avec coordonnées |
|------------------|------------------|
| 30-40 minutes | 30-40 minutes |

---

## 🎯 EXEMPLE CONCRET

### Scénario : Nouvelle réservation sur le listing "Choco Loft"

```
1. [00:00] Nouvelle réservation sur Airbnb
2. [00:05] iCal Watcher détecte le changement
3. [00:05] INSERT dans sync_queue (listing_id=1361868072916616334)
4. [00:05] Targeted Scraper lit la queue
5. [00:05] Scraping de toutes les réservations (30-40 min)
6. [00:40] Filtrage : 6195 → 21 réservations pour "Choco Loft"
7. [00:40] Collecte coordonnées (si activé) : +2 minutes
8. [00:42] Envoi à l'API Next.js
9. [00:42] Insertion dans Supabase
10. [00:42] Marque sync_queue comme "done"
```

**Total** : ~40 minutes

---

## 🔄 MODES DE FONCTIONNEMENT

### Mode 1 : Docker (arrière-plan)

```batch
DOCKER_START.bat
```

- ✅ Pas de fenêtres ouvertes
- ✅ Redémarrage automatique
- ✅ Tourne 24/7

### Mode 2 : Python (fenêtres)

```batch
LANCER_MAINTENANT.bat
```

- ✅ Logs visibles en temps réel
- ❌ 2 fenêtres ouvertes
- ❌ Arrêt si fermeture

---

## 📋 TABLES SUPABASE

### property_sync_config

Contient les URLs iCal de chaque listing.

### ical_hashes

Stocke les hash des calendriers iCal pour détecter les changements.

### sync_queue

File d'attente des listings à synchroniser.

### reservations

**Table finale** avec toutes les réservations et leurs coordonnées.

---

## 🎉 RÉSUMÉ

1. **iCal Watcher** détecte les changements
2. **Targeted Scraper** scrape les réservations
3. **Collecte des coordonnées** (optionnel)
4. **Filtrage** par listing_id
5. **Envoi** à l'API Next.js
6. **Insertion** dans Supabase
7. **Données disponibles** dans votre base !

---

**Créé par Kiro le 31 mai 2026**
