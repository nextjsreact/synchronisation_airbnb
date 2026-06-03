# 🔍 Différence entre l'API GraphQL d'Airbnb et le Fallback

## 📊 Vue d'ensemble

Le scraper Airbnb utilise **deux méthodes** pour récupérer les réservations :

1. **API GraphQL** (méthode rapide) ⚡
2. **Fallback Pagination** (méthode lente mais fiable) 🐢

---

## 1️⃣ API GraphQL d'Airbnb

### 🎯 Qu'est-ce que c'est ?

L'API GraphQL est une **API interne** utilisée par le site web Airbnb lui-même. Quand vous visitez votre tableau de bord d'hôte sur Airbnb, le site fait des requêtes à cette API pour afficher vos réservations.

### 🔧 Comment ça marche ?

```python
# Dans airbnb_scraper.py - fonction get_reservations()

# 1. Le scraper va sur la page d'hébergement
page.goto("https://www.airbnb.com/hosting")

# 2. Il exécute du JavaScript dans le navigateur pour appeler l'API
response = page.evaluate("""
    fetch('/api/v3/HostReservationsList', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Airbnb-API-Key': document.cookie.match(/key=([^;]+)/)?.[1] || ''
        },
        body: JSON.stringify({
            operationName: 'HostReservationsList',
            variables: { first: 40, skip: 0, status: 'all' }
        })
    })
""")

# 3. L'API retourne TOUTES les réservations en JSON
# Format: { data: { reservations: { edges: [...] } } }
```

### ✅ Avantages

- **Très rapide** : 2-3 minutes pour 5000+ réservations
- **Données structurées** : JSON propre et complet
- **Pagination efficace** : 40 réservations par requête
- **Pas de clics UI** : Tout se passe en arrière-plan

### ❌ Inconvénients

- **API non documentée** : Airbnb peut la changer à tout moment
- **Actuellement cassée** : Retourne des données vides depuis quelques jours
- **Dépend des cookies** : Nécessite une session valide

### 📈 Performance

```
Temps pour 5200 réservations : 2-3 minutes
Requêtes nécessaires : ~130 (40 par requête)
Taux de succès actuel : 0% (API cassée)
```

---

## 2️⃣ Fallback Pagination (Interception Réseau)

### 🎯 Qu'est-ce que c'est ?

Le fallback simule un **utilisateur humain** qui navigue sur le site Airbnb. Il visite les pages de réservations (upcoming, completed, all) et intercepte les requêtes réseau que le navigateur fait automatiquement.

### 🔧 Comment ça marche ?

```python
# Dans airbnb_scraper.py - fonction scrape_fallback()

# 1. Intercepter toutes les réponses réseau
def handle_response(response):
    if "api/v2/reservations" in response.url:
        data = response.json()
        # Capturer les réservations de la réponse

page.on("response", handle_response)

# 2. Visiter chaque page de réservations
pages = [
    "https://www.airbnb.com/hosting/reservations/upcoming",
    "https://www.airbnb.com/hosting/reservations/completed",
    "https://www.airbnb.com/hosting/reservations/all"
]

# 3. Pour chaque page, cliquer sur "Suivant" jusqu'à la fin
for page_num in range(200):
    # Attendre que les données se chargent
    page.wait_for_timeout(5000)
    
    # Cliquer sur le bouton "Suivant"
    next_btn = page.locator('button:has-text("Suivant")')
    next_btn.click()
```

### ✅ Avantages

- **Toujours fonctionnel** : Utilise l'interface publique du site
- **Fiable** : Tant que le site existe, ça marche
- **Capture tout** : Intercepte les vraies requêtes du site
- **Pas de dépendance API** : Ne dépend pas d'une API spécifique

### ❌ Inconvénients

- **Très lent** : 30-40 minutes pour 5000+ réservations
- **Clics UI nécessaires** : Doit cliquer sur chaque page
- **Attentes longues** : 5 secondes par page pour le chargement
- **Fragile aux changements UI** : Si Airbnb change les boutons, ça casse

### 📈 Performance

```
Temps pour 5200 réservations : 30-40 minutes
Pages à visiter : ~130 pages (40 réservations par page)
Attente par page : 5 secondes
Taux de succès actuel : 100% ✅
```

---

## 🔄 Comparaison Directe

| Critère | API GraphQL | Fallback Pagination |
|---------|-------------|---------------------|
| **Vitesse** | ⚡ 2-3 min | 🐢 30-40 min |
| **Fiabilité** | ❌ Cassée actuellement | ✅ Fonctionne toujours |
| **Maintenance** | ⚠️ Peut casser sans préavis | ✅ Stable |
| **Complexité** | 🟢 Simple (1 API call) | 🟡 Moyenne (navigation UI) |
| **Données** | 📊 JSON structuré | 📊 JSON structuré (même source) |
| **Dépendances** | API interne | Interface publique |

---

## 🚨 Problème Actuel

### Pourquoi les nouvelles réservations n'apparaissent pas ?

Le `targeted_scraper.py` utilise **uniquement l'API GraphQL** :

```python
# Dans targeted_scraper.py - fonction scrape_listing()

def scrape_listing(page, target_listing_id):
    # ❌ Utilise get_reservations() qui appelle l'API GraphQL
    all_reservations = get_reservations(page)
    
    # Filtre par listing_id
    targeted = [r for r in all_reservations if r.get("listing_id") == target_listing_id]
    return targeted
```

**Résultat** : Comme l'API GraphQL est cassée, `get_reservations()` retourne une liste vide, donc aucune nouvelle réservation n'est détectée.

---

## ✅ Solution

### Option 1 : Modifier `targeted_scraper.py` pour utiliser le fallback

```python
def scrape_listing(page, target_listing_id):
    # ✅ Utiliser le fallback au lieu de l'API GraphQL
    all_reservations = scrape_fallback(page)
    
    # Filtrer par listing_id
    targeted = [r for r in all_reservations if r.get("listing_id") == target_listing_id]
    return targeted
```

**Inconvénient** : Très lent (30-40 min par sync)

### Option 2 : Utiliser le fallback uniquement si l'API GraphQL échoue

```python
def scrape_listing(page, target_listing_id):
    # Essayer l'API GraphQL d'abord
    all_reservations = get_reservations(page)
    
    # Si vide, utiliser le fallback
    if not all_reservations:
        print("   ⚠️  API GraphQL vide, utilisation du fallback...")
        all_reservations = scrape_fallback(page)
    
    # Filtrer par listing_id
    targeted = [r for r in all_reservations if r.get("listing_id") == target_listing_id]
    return targeted
```

**Avantage** : Rapide quand l'API fonctionne, fiable quand elle est cassée

### Option 3 : Scraper complet périodique au lieu de ciblé

Au lieu de scraper un listing à la fois (lent avec fallback), faire un **scraping complet** toutes les heures :

```python
# Toutes les heures : scraper TOUTES les réservations avec fallback
# Avantage : 1 seul scraping de 30-40 min au lieu de 50 scraping de 30-40 min chacun
```

---

## 🎯 Recommandation

**Court terme** : Utiliser Option 2 (fallback automatique si GraphQL échoue)

**Long terme** : Passer à Option 3 (scraping complet périodique) car :
- Plus efficace : 1 scraping de 40 min vs 50 scraping de 40 min
- Plus simple : Pas besoin de queue
- Plus fiable : Capture toutes les modifications

---

## 📝 Résumé pour l'utilisateur

**API GraphQL** = Méthode rapide mais cassée actuellement
**Fallback** = Méthode lente mais fiable qui fonctionne toujours

Le problème actuel : `targeted_scraper.py` utilise uniquement l'API GraphQL cassée, donc il ne voit aucune nouvelle réservation.

La solution : Modifier `targeted_scraper.py` pour utiliser le fallback quand l'API GraphQL est vide.
