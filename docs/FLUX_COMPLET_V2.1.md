# 🔄 FLUX COMPLET DE SYNCHRONISATION - V2.1

## Date : 31 mai 2026
## Version : 2.1 (avec collecte des coordonnées)

---

## 📊 VUE D'ENSEMBLE

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
│   (Supabase)      │                     │  + Coordonnées    │
└───────────────────┘                     └───────────────────┘
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
                                          └───────────────────┘
```

---

## 🔄 FLUX DÉTAILLÉ

### ÉTAPE 1 : Détection des changements (iCal Watcher)

**Fréquence** : Toutes les 5 minutes

```
1. Récupère les URLs iCal depuis property_sync_config
2. Télécharge chaque calendrier iCal
3. Calcule le hash SHA256 (sans DTSTAMP)
4. Compare avec le hash précédent (table ical_hashes)
5. Si changement détecté :
   → INSERT dans sync_queue (status=pending)
```

**Tables utilisées** :
- `property_sync_config` (lecture)
- `ical_hashes` (lecture/écriture)
- `sync_queue` (écriture)

---

### ÉTAPE 2 : Traitement de la queue (Targeted Scraper)

**Fréquence** : Toutes les 30 secondes

```
1. Lit sync_queue (status=pending, limit=5)
2. Pour chaque entrée :
   a. Marque status=processing
   b. Lance le scraping pour ce listing_id
   c. Collecte les réservations
   d. [NOUVEAU] Collecte les coordonnées (si COLLECT_CONTACTS=true)
   e. Envoie à l'API Next.js
   f. Marque status=done
```

**Tables utilisées** :
- `sync_queue` (lecture/écriture)

---

### ÉTAPE 3 : Scraping Airbnb

**Méthode 1** : API GraphQL (rapide - 2-3 min)
```
1. Appelle /api/v3/HostReservationsList
2. Récupère toutes les réservations
3. Parse les données JSON
```

**Méthode 2** : Fallback (lent - 30-40 min)
```
1. Navigue sur /hosting/reservations/upcoming
2. Navigue sur /hosting/reservations/completed
3. Navigue sur /hosting/reservations/all
4. Intercepte les requêtes réseau
5. Pagine avec le bouton "Suivant"
6. Collecte toutes les réservations
```

**Résultat** : Liste de réservations avec :
- id (code de confirmation)
- statut
- voyageur (nom)
- nb_voyageurs
- logement
- listing_id
- date_arrivee
- date_depart
- nb_nuits
- montant_total
- devise
- date_creation

---

### ÉTAPE 4 : Collecte des coordonnées (NOUVEAU V2.1)

**Activation** : Variable `COLLECT_CONTACTS=true` dans `.env`

**Processus** :
```
1. Filtre les réservations actives (confirmée, à venir, en cours)
2. Pour chaque réservation active :
   a. Ouvre https://fr.airbnb.com/hosting/stay/{CODE}?tab=upcoming
   b. Cherche "Numéro de téléphone" dans la page
   c. Extrait le numéro avec regex
   d. Cherche l'email (si disponible)
   e. Ajoute telephone_voyageur et email_voyageur
   f. Pause 2 secondes (rate limiting)
```

**Temps supplémentaire** : ~5 secondes par réservation active

**Exemple** :
- 20 réservations actives = +100 secondes (~2 minutes)
- 100 réservations actives = +500 secondes (~8 minutes)

**Données ajoutées** :
- `telephone_voyageur` : "+213 793 86 24 94"
- `email_voyageur` : "hamza@example.com"

---

### ÉTAPE 5 : Filtrage par listing_id

**Pour le scraping ciblé uniquement** :

```python
# Convertir en string pour comparaison
target_listing_id_str = str(target_listing_id)
targeted = [
    r for r in all_reservations
    if str(r.get("listing_id", "")) == target_listing_id_str
]
```

**Correction V2.0.1** : Conversion explicite en string pour éviter les problèmes de comparaison int vs string.

---

### ÉTAPE 6 : Envoi à l'API Next.js

**Endpoint** : `POST /api/airbnb/sync`

**Payload** :
```json
{
  "reservations": [
    {
      "id": "HM4TB95HKS",
      "statut": "Confirmée",
      "voyageur": "Hamza",
      "telephone_voyageur": "+213 793 86 24 94",
      "email_voyageur": "hamza@example.com",
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
  ],
  "sync_type": "targeted"
}
```

**Traitement par batch** : 50 réservations par requête

---

### ÉTAPE 7 : Insertion dans Supabase

**L'API Next.js gère** :

1. **Validation** des données
2. **Upsert** dans la table `reservations` :
   - Si `id` existe : UPDATE
   - Sinon : INSERT
3. **Mapping** des champs :
   - `id` → `confirmation_code`
   - `voyageur` → `guest_name`
   - `telephone_voyageur` → `guest_phone`
   - `email_voyageur` → `guest_email`
   - `logement` → `listing_name`
   - `listing_id` → `airbnb_listing_id`
   - etc.

**Table finale** : `reservations` dans Supabase

---

## 📊 STRUCTURE DES DONNÉES

### Table : reservations

```sql
CREATE TABLE reservations (
  id BIGSERIAL PRIMARY KEY,
  confirmation_code TEXT UNIQUE NOT NULL,
  status TEXT,
  guest_name TEXT,
  guest_phone TEXT,              -- NOUVEAU V2.1
  guest_email TEXT,              -- NOUVEAU V2.1
  guest_count INTEGER,
  listing_name TEXT,
  airbnb_listing_id TEXT,
  check_in DATE,
  check_out DATE,
  nights INTEGER,
  total_amount DECIMAL(10,2),
  currency TEXT,
  created_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

## ⚙️ CONFIGURATION

### Variables d'environnement (.env)

```env
# Airbnb
AIRBNB_EMAIL=votre@email.com
AIRBNB_PASSWORD=votre_mot_de_passe
TOTP_SECRET=votre_secret_2fa

# Mode
HEADLESS=true
PROXY_URL=

# API Next.js
NEXTJS_API_URL=http://host.docker.internal:3000/api/airbnb/sync
NEXTJS_API_KEY=votre_cle_api

# Supabase
NEXT_PUBLIC_SUPABASE_URL=https://votre-projet.supabase.co
SUPABASE_SERVICE_ROLE_KEY=votre_service_role_key

# Intervalles
ICAL_POLL_INTERVAL=300
TARGETED_POLL_INTERVAL=30

# Coordonnées (NOUVEAU V2.1)
COLLECT_CONTACTS=false
```

### Activation de la collecte des coordonnées

**Option 1** : Collecte automatique (plus lent)
```env
COLLECT_CONTACTS=true
```

**Option 2** : Collecte manuelle (recommandé)
```env
COLLECT_CONTACTS=false
```

Puis lancer manuellement :
```batch
7_collecter_contacts.bat
```

---

## ⏱️ TEMPS DE TRAITEMENT

### Scraping complet (toutes les réservations)

| Composant | Temps | Avec coordonnées |
|-----------|-------|------------------|
| API GraphQL | 2-3 min | +8 min (100 rés actives) |
| Fallback | 30-40 min | +8 min (100 rés actives) |
| **Total** | **30-40 min** | **38-48 min** |

### Scraping ciblé (1 listing)

| Composant | Temps | Avec coordonnées |
|-----------|-------|------------------|
| Fallback | 30-40 min | +5 sec (1 rés) |
| Filtrage | <1 sec | - |
| Envoi API | <1 sec | - |
| **Total** | **30-40 min** | **30-40 min** |

---

## 🎯 RECOMMANDATIONS

### Pour la collecte des coordonnées

**Recommandé** : `COLLECT_CONTACTS=false` + collecte manuelle

**Raisons** :
1. ✅ Scraping plus rapide (pas de +5 sec par réservation)
2. ✅ Moins de charge sur Airbnb
3. ✅ Collecte à la demande quand vous en avez besoin
4. ✅ Évite le rate limiting

**Quand collecter manuellement** :
- Avant l'arrivée des voyageurs (pour envoyer instructions)
- En cas d'urgence (besoin de contacter rapidement)
- Périodiquement (1x par semaine)

### Pour le scraping

**Scraping complet** : 1x par jour (nuit)
```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

**Scraping ciblé** : En continu (Docker)
```batch
DOCKER_START.bat
```

---

## 🔄 FLUX ALTERNATIFS

### Flux 1 : Scraping complet quotidien

```
1. Arrêter les services Docker
2. Lancer le scraping complet (40 min)
3. Collecter les coordonnées (optionnel, +8 min)
4. Relancer les services Docker
```

**Avantage** : Données toujours à jour  
**Inconvénient** : Lent

### Flux 2 : Scraping ciblé en continu (actuel)

```
1. iCal Watcher détecte les changements
2. Targeted Scraper traite la queue
3. Synchronisation automatique
```

**Avantage** : Rapide pour les mises à jour  
**Inconvénient** : Fallback lent (30-40 min par listing)

### Flux 3 : Hybride (recommandé)

```
1. Scraping complet 1x par jour (nuit)
2. Scraping ciblé en continu (jour)
3. Collecte coordonnées manuelle (à la demande)
```

**Avantage** : Meilleur compromis  
**Inconvénient** : Plus complexe

---

## 📋 CHECKLIST DE VÉRIFICATION

### Avant le scraping

- [ ] Docker Desktop lancé (si utilisation Docker)
- [ ] Session Airbnb valide (`1_creer_session.bat`)
- [ ] Variables d'environnement configurées (`.env`)
- [ ] API Next.js accessible
- [ ] Supabase accessible

### Après le scraping

- [ ] Réservations dans `output/reservations_airbnb.json`
- [ ] Réservations dans Supabase (table `reservations`)
- [ ] Coordonnées collectées (si `COLLECT_CONTACTS=true`)
- [ ] Logs sans erreur

---

## 🎉 AMÉLIORATIONS V2.1

1. ✅ **Collecte des coordonnées** : Téléphone + Email
2. ✅ **Configuration flexible** : Variable `COLLECT_CONTACTS`
3. ✅ **Collecte manuelle** : Script `7_collecter_contacts.bat`
4. ✅ **Filtrage corrigé** : Conversion string pour comparaison
5. ✅ **Documentation complète** : Ce fichier

---

**Créé par Kiro le 31 mai 2026**
