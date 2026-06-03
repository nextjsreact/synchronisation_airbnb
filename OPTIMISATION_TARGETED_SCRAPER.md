# 🚀 Optimisation du Targeted Scraper

## 📊 Problème identifié

Le **Targeted Scraper** scrape **toutes les réservations** (upcoming + completed) au lieu de seulement les réservations futures, ce qui prend **30-40 minutes** au lieu de **2-3 minutes**.

### Logs observés
```
📄 Page : upcoming...
   Page 1-3: 105 réservations ✅

📄 Page : completed...
   Page 1-73: 2905+ réservations ❌ (inutile!)
```

---

## ✅ Solution implémentée

### 1. Nouvelle fonction optimisée

**Fichier**: `targeted_scraper.py`

```python
def scrape_fallback_upcoming_only(page):
    """
    Fallback optimisé : scrape uniquement les réservations "upcoming" (futures).
    Beaucoup plus rapide que scrape_fallback() qui scrape tout l'historique.
    """
    from airbnb_scraper import _parse_reservation_node
    
    all_reservations = []
    
    # Scraper uniquement la catégorie "upcoming"
    categories = ["upcoming"]  # ✅ Au lieu de ["upcoming", "completed", "cancelled"]
    
    for cat in categories:
        print(f"\n   📄 Page : {cat}...")
        
        # Naviguer vers la page
        url = f"https://www.airbnb.com/hosting/reservations/{cat}"
        try:
            page.goto(url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)
        except Exception as e:
            print(f"      ⚠️  Erreur navigation {cat}: {e}")
            continue
        
        # Pagination
        page_num = 0
        while True:
            page_num += 1
            
            # Attendre que les réservations se chargent
            try:
                page.wait_for_selector('[data-testid="reservation-list-item"]', timeout=10000)
            except Exception:
                print(f"      ⚠️  Aucune réservation trouvée sur page {page_num}")
                break
            
            # Parser les réservations
            nodes = page.query_selector_all('[data-testid="reservation-list-item"]')
            
            if not nodes:
                break
            
            before_count = len(all_reservations)
            for node in nodes:
                try:
                    res = _parse_reservation_node(node)
                    if res:
                        all_reservations.append(res)
                except Exception as e:
                    print(f"      ⚠️  Erreur parsing: {e}")
            
            added = len(all_reservations) - before_count
            print(f"      Page {page_num}: +{added} (total cat: {len(nodes)}, cumul: {len(all_reservations)})")
            
            # Vérifier s'il y a une page suivante
            try:
                next_button = page.query_selector('button[aria-label*="Next"], a[aria-label*="Next"]')
                if not next_button or next_button.is_disabled():
                    break
                
                next_button.click()
                page.wait_for_timeout(2000)
            except Exception:
                break
    
    return all_reservations
```

### 2. Modification de `scrape_listing()`

```python
def scrape_listing(page, target_listing_id):
    """
    Scrape les réservations d'un listing spécifique.
    OPTIMISÉ: Scrape uniquement les réservations "upcoming" (futures) pour être rapide.
    """
    print(f"   Scraping des reservations pour listing {target_listing_id}...")
    print(f"   🚀 Mode optimisé : uniquement réservations futures (upcoming)")

    # Essayer l'API GraphQL d'abord (rapide : 2-3 min)
    all_reservations = get_reservations(page)

    # Si vide ou erreur, utiliser le fallback MAIS uniquement pour "upcoming"
    if not all_reservations:
        print(f"   ⚠️  API GraphQL vide ou cassée, utilisation du fallback...")
        print(f"   ⏳ Scraping uniquement 'upcoming' (2-3 minutes)...")
        all_reservations = scrape_fallback_upcoming_only(page)  # ✅ Nouvelle fonction
```

---

## 🔧 Déploiement

### Rebuild Docker (en cours)

```powershell
docker compose -f docker-compose.sync.yml build --no-cache targeted-scraper
```

⏳ **Temps estimé**: 5-10 minutes

### Redémarrage

```powershell
docker compose -f docker-compose.sync.yml up -d
docker compose -f docker-compose.sync.yml logs -f targeted-scraper
```

---

## 📈 Résultats attendus

### Avant (version actuelle)
```
📄 Page : upcoming...
   Page 1-3: 105 réservations

📄 Page : completed...
   Page 1-130: 5210 réservations

⏱️ Temps total: 30-40 minutes
```

### Après (version optimisée)
```
📄 Page : upcoming...
   Page 1-3: 105 réservations

✅ Terminé!

⏱️ Temps total: 2-3 minutes
```

### Gain de performance
- **15x plus rapide** 🚀
- **Scraping ciblé** : uniquement les réservations futures
- **Moins de charge** sur Airbnb
- **Synchronisation quasi-instantanée**

---

## 🎯 Cas d'usage

### Quand utiliser le Targeted Scraper ?

1. **Changement détecté par iCal Watcher**
   - Une nouvelle réservation apparaît dans l'iCal
   - Le watcher ajoute une entrée dans `sync_queue`
   - Le scraper récupère **uniquement les réservations futures** du listing concerné

2. **Mise à jour manuelle**
   - L'utilisateur modifie une réservation
   - Le système détecte le changement
   - Scraping rapide (2-3 min) au lieu de 30-40 min

3. **Synchronisation continue**
   - Le système tourne en boucle
   - Traite les changements au fur et à mesure
   - Chaque scraping est ultra-rapide

---

## ✅ Vérification

Une fois le rebuild terminé, vous devriez voir :

```
🚀 Mode optimisé : uniquement réservations futures (upcoming)
⏳ Scraping uniquement 'upcoming' (2-3 minutes)...

📄 Page : upcoming...
   Page 1: +40 (total cat: 105, cumul: 40)
   Page 2: +40 (total cat: 105, cumul: 80)
   Page 3: +25 (total cat: 105, cumul: 105)

✅ 105 reservations trouvees pour 1482835556465318279
```

**Pas de "completed" ni "cancelled"** = Optimisation active ! 🎉

---

## 📝 Notes

- Le **scraping complet** (`airbnb_scraper.py`) continue de scraper **tout l'historique** (normal)
- Le **Targeted Scraper** scrape **uniquement upcoming** (optimisé)
- Les **données historiques** sont déjà en base (pas besoin de les re-scraper)
- Les **nouvelles réservations** sont détectées par iCal et scrapées rapidement

---

**Date**: 1er juin 2026  
**Statut**: ⏳ Rebuild en cours  
**Prochaine étape**: Redémarrer les services et vérifier les logs
