# ✅ Solution : Nouvelles Réservations Non Synchronisées

## 🔍 Diagnostic Complet

### Problème Identifié

Les nouvelles réservations Airbnb **ne sont PAS synchronisées** dans la base de données Supabase.

### Cause Racine

L'**API GraphQL d'Airbnb est cassée** depuis quelques jours :
- Elle retourne **0 réservations** au lieu des 6194 réservations réelles
- Le `targeted_scraper.py` utilise **uniquement** cette API GraphQL
- Résultat : Aucune nouvelle réservation n'est détectée

### Preuve

```bash
# Test effectué le 30 mai 2026 à 19:30

API GraphQL      : 0 réservations ❌
Fallback Pagination : 120 réservations (test limité) ✅
Total réel sur Airbnb : 6194 réservations
```

---

## 🛠️ Solutions Disponibles

### Solution 1 : Modifier `targeted_scraper.py` (RECOMMANDÉE)

Ajouter un fallback automatique quand l'API GraphQL échoue.

**Avantages** :
- ✅ Fonctionne immédiatement
- ✅ Rapide quand l'API GraphQL est réparée
- ✅ Fiable quand l'API GraphQL est cassée

**Inconvénient** :
- ⚠️ Lent avec le fallback (30-40 min par sync ciblé)

**Implémentation** :

```python
# Dans targeted_scraper.py - fonction scrape_listing()

def scrape_listing(page, target_listing_id):
    """
    Scrape les réservations d'un listing spécifique.
    Utilise l'API GraphQL avec fallback automatique.
    """
    print(f"   Scraping des reservations pour listing {target_listing_id}...")

    # Essayer l'API GraphQL d'abord (rapide)
    all_reservations = get_reservations(page)

    # Si vide, utiliser le fallback (lent mais fiable)
    if not all_reservations:
        print(f"   ⚠️  API GraphQL vide, utilisation du fallback...")
        all_reservations = scrape_fallback(page)

    # Filtrer par listing_id cible
    targeted = [
        r for r in all_reservations
        if r.get("listing_id") == target_listing_id
    ]

    print(f"   {len(targeted)} reservations trouvees pour {target_listing_id}")
    return targeted
```

---

### Solution 2 : Scraping Complet Périodique (MEILLEURE À LONG TERME)

Remplacer le système de queue par un **scraping complet** toutes les heures.

**Avantages** :
- ✅ Plus efficace : 1 scraping de 40 min vs 50 scraping de 40 min chacun
- ✅ Plus simple : Pas besoin de queue ni de watcher iCal
- ✅ Plus fiable : Capture toutes les modifications
- ✅ Moins de charge sur Airbnb

**Inconvénient** :
- ⚠️ Latence de 1 heure max pour les nouvelles réservations

**Implémentation** :

```python
# Nouveau fichier : full_scraper_periodic.py

import time
from datetime import datetime
from airbnb_scraper import login, scrape_fallback, is_logged_in

SCRAPE_INTERVAL = 3600  # 1 heure

while True:
    print(f"\n[{datetime.now()}] Démarrage scraping complet...")
    
    # Lancer le navigateur
    browser = cloak_launch(headless=True)
    context = browser.new_context(storage_state=SESSION_FILE)
    page = context.new_page()
    
    # Login si nécessaire
    if not is_logged_in(page):
        login(page)
    
    # Scraper TOUTES les réservations
    all_reservations = scrape_fallback(page)
    
    # Envoyer à l'API
    count = upsert_reservations(all_reservations, sync_type="full")
    print(f"   ✅ {count} réservations synchronisées")
    
    # Fermer le navigateur
    context.close()
    browser.close()
    
    # Attendre 1 heure
    print(f"   ⏳ Prochaine synchronisation dans {SCRAPE_INTERVAL}s...")
    time.sleep(SCRAPE_INTERVAL)
```

**Docker Compose** :

```yaml
# docker-compose.full-sync.yml

services:
  full-scraper:
    build: .
    container_name: airbnb-full-scraper
    command: python full_scraper_periodic.py
    environment:
      - HEADLESS=true
      - SCRAPE_INTERVAL=3600
    volumes:
      - ./output:/app/output
    restart: unless-stopped
```

---

### Solution 3 : Scraping Complet Manuel (TEMPORAIRE)

En attendant de choisir une solution permanente, lancer un scraping complet manuellement.

**Commande** :

```bash
# Windows
python airbnb_scraper.py

# Docker
docker-compose run --rm scraper python airbnb_scraper.py
```

**Durée** : 30-40 minutes pour 6194 réservations

---

## 📊 Comparaison des Solutions

| Critère | Solution 1 (Fallback Auto) | Solution 2 (Périodique) | Solution 3 (Manuel) |
|---------|---------------------------|------------------------|---------------------|
| **Rapidité** | 🟡 Variable (2 min ou 40 min) | 🟢 40 min toutes les heures | 🟡 40 min à la demande |
| **Fiabilité** | 🟢 Haute | 🟢 Très haute | 🟢 Haute |
| **Maintenance** | 🟡 Moyenne | 🟢 Faible | 🔴 Manuelle |
| **Latence** | 🟢 Temps réel | 🟡 Max 1 heure | 🔴 À la demande |
| **Complexité** | 🟢 Simple | 🟢 Simple | 🟢 Très simple |
| **Charge Airbnb** | 🔴 Haute (1 scraping par changement) | 🟢 Faible (1 scraping/heure) | 🟢 Faible |

---

## 🎯 Recommandation Finale

### Court Terme (Aujourd'hui)

**Utiliser Solution 1** : Modifier `targeted_scraper.py` avec fallback automatique

**Pourquoi** :
- Fonctionne immédiatement
- Garde l'architecture actuelle
- Sera rapide quand Airbnb réparera l'API GraphQL

### Long Terme (Cette Semaine)

**Migrer vers Solution 2** : Scraping complet périodique

**Pourquoi** :
- Plus efficace (1 scraping vs 50 scraping)
- Plus simple (pas de queue, pas de watcher)
- Plus fiable (capture tout)
- Moins de charge sur Airbnb (meilleure relation avec leur serveur)

---

## 📝 Étapes d'Implémentation

### Étape 1 : Fix Immédiat (5 minutes)

1. Modifier `targeted_scraper.py` :
   ```bash
   # Ajouter l'import
   from airbnb_scraper import scrape_fallback
   
   # Modifier scrape_listing()
   # (voir code Solution 1 ci-dessus)
   ```

2. Redémarrer le container :
   ```bash
   docker-compose -f docker-compose.sync.yml restart targeted-scraper
   ```

3. Vérifier les logs :
   ```bash
   docker-compose -f docker-compose.sync.yml logs -f targeted-scraper
   ```

### Étape 2 : Migration Long Terme (1 heure)

1. Créer `full_scraper_periodic.py` (voir code Solution 2)

2. Créer `docker-compose.full-sync.yml` (voir config Solution 2)

3. Arrêter l'ancien système :
   ```bash
   docker-compose -f docker-compose.sync.yml down
   ```

4. Démarrer le nouveau système :
   ```bash
   docker-compose -f docker-compose.full-sync.yml up -d
   ```

5. Supprimer les anciens services (optionnel) :
   - `ical_watcher.py` (plus nécessaire)
   - `targeted_scraper.py` (remplacé)
   - Tables `ical_hashes` et `sync_queue` (plus utilisées)

---

## 🔍 Vérification

### Après Solution 1

```bash
# Vérifier que le fallback est utilisé
docker-compose -f docker-compose.sync.yml logs targeted-scraper | grep "fallback"

# Vérifier les nouvelles réservations
python view_reservations.py
```

### Après Solution 2

```bash
# Vérifier le scraping périodique
docker-compose -f docker-compose.full-sync.yml logs -f full-scraper

# Vérifier les nouvelles réservations
python view_reservations.py
```

---

## 📚 Fichiers Créés

1. `DIFFERENCE_API_GRAPHQL_VS_FALLBACK.md` - Explication détaillée des deux méthodes
2. `debug_targeted_scraper.py` - Script de test et diagnostic
3. `5_debug_scraper.bat` - Lancement du debug
4. `SOLUTION_NOUVELLES_RESERVATIONS.md` - Ce fichier
5. `view_reservations.py` - Corrigé pour afficher les réservations

---

## ❓ Questions Fréquentes

### Q : Pourquoi l'API GraphQL est cassée ?

**R** : Airbnb change régulièrement ses APIs internes sans préavis. C'est normal pour une API non documentée.

### Q : Quand sera-t-elle réparée ?

**R** : Impossible à savoir. Peut-être jamais. C'est pourquoi le fallback est essentiel.

### Q : Le fallback est-il légal ?

**R** : Oui, il simule un utilisateur humain qui navigue sur le site. C'est la même chose que si vous cliquiez manuellement.

### Q : Pourquoi 30-40 minutes ?

**R** : Le fallback doit :
- Visiter 3 pages (upcoming, completed, all)
- Cliquer sur ~130 pages (40 réservations par page)
- Attendre 5 secondes par page (pour éviter le rate limiting)
- Total : 130 pages × 5 secondes = 650 secondes ≈ 11 minutes par catégorie × 3 = 33 minutes

### Q : Peut-on accélérer le fallback ?

**R** : Non, réduire les attentes risque de déclencher le rate limiting d'Airbnb et bloquer votre compte.

---

## 🎉 Résumé

**Problème** : API GraphQL cassée → Aucune nouvelle réservation synchronisée

**Solution Immédiate** : Ajouter fallback automatique dans `targeted_scraper.py`

**Solution Long Terme** : Scraping complet périodique (1 fois par heure)

**Résultat** : Synchronisation fiable et complète de toutes les réservations Airbnb
