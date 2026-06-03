# 📋 PLAN D'ACTION - ÉTAPE PAR ÉTAPE

## Date : 31 mai 2026

---

## 🎯 OBJECTIF

Corriger le système de synchronisation pour que les nouvelles réservations Airbnb soient automatiquement synchronisées dans votre base de données.

---

## 📊 SITUATION ACTUELLE

| Composant | État | Détails |
|-----------|------|---------|
| iCal Watcher | ✅ Fonctionne | 18 changements détectés |
| Sync Queue | ✅ Fonctionne | 16 entrées pending |
| Scraping | ✅ Fonctionne | 6195 réservations scrapées |
| Filtre listing_id | ❌ Cassé | Retourne 0 résultats |
| Synchronisation | ❌ Cassée | 0 réservations synchronisées |

---

## 🚀 PLAN D'ACTION EN 4 ÉTAPES

### ÉTAPE 1 : Synchronisation immédiate (40 minutes)

**Objectif** : Synchroniser toutes les réservations maintenant pendant qu'on corrige le système.

**Action** :
```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

**Résultat attendu** :
- 6195 réservations synchronisées dans votre base
- Données à jour

**Pendant ce temps** : Passez à l'étape 2

---

### ÉTAPE 2 : Diagnostic du problème (5 minutes)

**Objectif** : Identifier où se trouve le champ `listing_id` dans les données Airbnb.

**Action** :
```batch
6_debug_listing_id.bat
```

**Résultat attendu** :
- Fichiers `debug_api_response_1.json` et `debug_api_response_2.json` créés
- Structure JSON complète affichée dans le terminal
- Identification du chemin vers `listing_id`

**Exemple de sortie** :
```
🔬 STRUCTURE DE LA PREMIÈRE RÉSERVATION :
   📋 Clés disponibles (25) :
      • id                           : str        = HMABCD123
      • guest_user                   : dict       = dict avec 3 clés: ['id', 'first_name', 'full_name']
      • listing                      : dict       = dict avec 5 clés: ['id', 'name', 'city']
      • start_date                   : str        = 2026-06-01
      ...

   🎯 RECHERCHE DU LISTING_ID :
      ✅ Trouvé : listing.id = 1526985730296514715
```

---

### ÉTAPE 3 : Correction du code (10 minutes)

**Objectif** : Corriger le parsing pour extraire correctement le `listing_id`.

**Fichier à modifier** : `airbnb_scraper.py`

**Ligne à trouver** (environ ligne 730) :
```python
def _parse_reservation_node(node):
    # ...
    return {
        # ...
        "listing_id": _extract_field(node, 
            ["listing_id"], 
            ["listingId"], 
            default=""),
        # ...
    }
```

**Correction à appliquer** :

Si le diagnostic montre que le `listing_id` est dans `listing.id`, modifier ainsi :

```python
def _parse_reservation_node(node):
    # ...
    return {
        # ...
        "listing_id": _extract_field(node, 
            ["listing_id"],           # ← Essayer d'abord
            ["listingId"],
            ["listing", "id"],        # ← AJOUTER CE CHEMIN
            ["listing", "listing_id"],
            ["property_id"],
            default=""),
        # ...
    }
```

**Sauvegarder le fichier** après modification.

---

### ÉTAPE 4 : Test et relance (10 minutes)

**Objectif** : Vérifier que la correction fonctionne et relancer le système.

**Action 1** : Tester avec 1 listing

Créer un fichier `test_correction.py` :

```python
from airbnb_scraper import _parse_reservation_node
import json

# Charger une réservation depuis le fichier debug
with open("debug_api_response_1.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Extraire la première réservation
# (adapter selon la structure trouvée)
reservations = data.get("reservations", [])
if reservations:
    first_res = reservations[0]
    parsed = _parse_reservation_node(first_res)
    
    print(f"listing_id parsé : '{parsed.get('listing_id')}'")
    print(f"logement parsé   : '{parsed.get('logement')}'")
    
    if parsed.get('listing_id'):
        print("✅ CORRECTION RÉUSSIE !")
    else:
        print("❌ listing_id toujours vide")
```

Lancer :
```batch
python test_correction.py
```

**Résultat attendu** :
```
listing_id parsé : '1526985730296514715'
logement parsé   : 'Appartement Paris'
✅ CORRECTION RÉUSSIE !
```

**Action 2** : Relancer le système

```batch
LANCER_MAINTENANT.bat
```

**Résultat attendu** :
- 2 fenêtres ouvertes (iCal Watcher + Targeted Scraper)
- Le scraper traite les 16 entrées pending
- Les réservations sont synchronisées avec succès

---

## ✅ VÉRIFICATION FINALE

### Vérifier que tout fonctionne

**Action** :
```batch
python voir_queue.py
```

**Résultat attendu** :
```
Sync Queue : 0 pending, 0 processing, 18 done
```

**Action** :
```batch
python view_reservations.py
```

**Résultat attendu** :
```
6195 réservations dans la base
Dernière mise à jour : 31/05/2026 14:30
```

---

## 🔄 MAINTENANCE CONTINUE

### Surveillance quotidienne

**Action** :
```batch
4_monitor_sync.bat
```

**Vérifier** :
- iCal Watcher détecte les changements
- Sync Queue est traitée (pending → done)
- Nouvelles réservations apparaissent dans la base

### En cas de problème

1. Vérifier les logs dans les fenêtres du watcher et du scraper
2. Vérifier la sync_queue : `python voir_queue.py`
3. Vérifier les réservations : `python view_reservations.py`
4. Si nécessaire, relancer : `LANCER_MAINTENANT.bat`

---

## 📊 TEMPS ESTIMÉ TOTAL

| Étape | Durée | Peut être fait en parallèle |
|-------|-------|----------------------------|
| 1. Scraping complet | 40 min | Oui (en arrière-plan) |
| 2. Diagnostic | 5 min | Oui (pendant le scraping) |
| 3. Correction | 10 min | Oui (pendant le scraping) |
| 4. Test et relance | 10 min | Non (après le scraping) |

**Total séquentiel** : 65 minutes  
**Total optimisé** : 50 minutes (en parallélisant 1+2+3)

---

## 🎯 RÉSULTAT FINAL ATTENDU

Après avoir suivi ce plan :

✅ Toutes les 6195 réservations synchronisées  
✅ Système de synchronisation automatique fonctionnel  
✅ Nouvelles réservations détectées et synchronisées automatiquement  
✅ Temps de synchronisation : 2-3 minutes par listing (au lieu de 40 min)  

---

## 📞 EN CAS DE BLOCAGE

### Si l'étape 2 (diagnostic) ne trouve pas le listing_id

**Solution** : Ouvrir manuellement `debug_api_response_1.json` et chercher un champ qui ressemble à un ID de listing (long nombre).

### Si l'étape 3 (correction) ne fonctionne pas

**Solution de contournement** : Utiliser le scraping complet périodique (toutes les heures) au lieu du scraping ciblé.

Créer un fichier `scraping_periodique.bat` :
```batch
@echo off
:loop
echo Scraping complet en cours...
python airbnb_scraper.py
echo Attente 1 heure...
timeout /t 3600 /nobreak
goto loop
```

### Si le système est trop lent

**Option** : Accepter le scraping complet toutes les heures (40 min de scraping + 20 min de pause).

---

## 📝 CHECKLIST

Cochez au fur et à mesure :

- [ ] Étape 1 : Scraping complet lancé
- [ ] Étape 2 : Diagnostic exécuté
- [ ] Étape 2 : Fichiers JSON créés
- [ ] Étape 2 : Chemin vers listing_id identifié
- [ ] Étape 3 : Code corrigé dans airbnb_scraper.py
- [ ] Étape 3 : Fichier sauvegardé
- [ ] Étape 4 : Test de correction réussi
- [ ] Étape 4 : Système relancé
- [ ] Vérification : Sync queue traitée
- [ ] Vérification : Réservations synchronisées

---

## 🎉 FÉLICITATIONS !

Une fois toutes les étapes complétées, votre système de synchronisation Airbnb sera pleinement fonctionnel et automatique.

**Créé par Kiro le 31 mai 2026**
