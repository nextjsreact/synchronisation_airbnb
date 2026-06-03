# 📞 RÉSUMÉ - SYSTÈME DE COLLECTE DES COORDONNÉES

## Date : 31 mai 2026

---

## ✅ CE QUI A ÉTÉ CRÉÉ

### Scripts Python

1. **scrape_guest_contacts.py** - Script principal de collecte
   - Charge les réservations existantes
   - Filtre les réservations actives
   - Extrait téléphone + email pour chaque réservation
   - Sauvegarde dans `reservations_avec_contacts.json`

2. **test_contact_extraction.py** - Script de test
   - Teste l'extraction sur UNE réservation
   - Utile pour vérifier que ça fonctionne
   - Sauvegarde une capture d'écran

### Scripts Batch (Windows)

3. **7_collecter_contacts.bat** - Collecte complète
4. **TEST_CONTACT.bat** - Test avec un code spécifique
5. **TEST_CONTACT_SIMPLE.bat** - Test avec HM4TB95HKS

### Documentation

6. **GUIDE_CONTACTS_VOYAGEURS.md** - Guide complet
7. **RESUME_CONTACTS.md** - Ce fichier

---

## 🎯 COMMENT ÇA FONCTIONNE

### URL utilisée

```
https://fr.airbnb.com/hosting/stay/{CODE}?tab=upcoming
```

**Exemple** : `https://fr.airbnb.com/hosting/stay/HM4TB95HKS?tab=upcoming`

### Extraction

1. Ouvre la page de la réservation
2. Clique sur le bouton "Gérer la réservation" (3 points)
3. Cherche "Numéro de téléphone : Nom"
4. Extrait le numéro avec regex : `+213 793 86 24 94`
5. Cherche l'email (si disponible)

### Méthodes d'extraction (3 niveaux)

**Niveau 1** : Menu "Gérer la réservation"
- Clique sur le bouton
- Cherche "Numéro de téléphone"
- Extrait avec regex

**Niveau 2** : Contenu de la page
- Si le menu ne fonctionne pas
- Cherche dans tout le HTML

**Niveau 3** : Éléments spécifiques
- Cherche les éléments contenant "téléphone"
- Extrait les numéros trouvés

---

## 🚀 UTILISATION

### Test rapide (1 réservation)

```batch
TEST_CONTACT_SIMPLE.bat
```

Teste avec votre exemple : HM4TB95HKS (Hamza, +213 793 86 24 94)

### Collecte complète (toutes les réservations actives)

```batch
7_collecter_contacts.bat
```

Traite toutes les réservations à venir et en cours.

---

## 📊 DONNÉES COLLECTÉES

### Format de sortie

```json
{
  "id": "HM4TB95HKS",
  "statut": "Confirmée",
  "voyageur": "Hamza",
  "telephone_voyageur": "+213 793 86 24 94",
  "email_voyageur": "hamza@example.com",
  "logement": "Choco Loft",
  "date_arrivee": "2026-05-29",
  "date_depart": "2026-05-31",
  "nb_nuits": 2
}
```

### Fichier créé

`output/reservations_avec_contacts.json`

---

## ⏱️ TEMPS DE TRAITEMENT

- **Test (1 réservation)** : ~10 secondes
- **Collecte (20 réservations)** : ~2-3 minutes
- **Collecte (100 réservations)** : ~10-15 minutes

---

## 🎯 PROCHAINES ÉTAPES

### 1. Tester avec votre exemple

```batch
TEST_CONTACT_SIMPLE.bat
```

**Résultat attendu** :
```
📞 Téléphone : +213 793 86 24 94
📧 Email     : (si disponible)
```

### 2. Si le test fonctionne, lancer la collecte complète

```batch
7_collecter_contacts.bat
```

### 3. Utiliser les données

Importer `output/reservations_avec_contacts.json` dans votre application.

---

## 🔧 AMÉLIORATION POSSIBLE

### Intégration automatique

Modifier `targeted_scraper.py` pour collecter automatiquement les coordonnées lors de la synchronisation.

**Avantage** : Coordonnées toujours à jour  
**Inconvénient** : Scraping plus lent

### Code à ajouter dans targeted_scraper.py

```python
from scrape_guest_contacts import get_guest_contact_info

def process_entry(page, entry):
    # ... code existant ...
    
    # Après avoir récupéré les réservations
    for reservation in reservations:
        # Ajouter les coordonnées
        contacts = get_guest_contact_info(page, reservation["id"])
        reservation["telephone_voyageur"] = contacts["phone"]
        reservation["email_voyageur"] = contacts["email"]
    
    # ... suite du code ...
```

---

## 📋 CHECKLIST

- [ ] Tester avec HM4TB95HKS : `TEST_CONTACT_SIMPLE.bat`
- [ ] Vérifier que le téléphone est bien extrait : `+213 793 86 24 94`
- [ ] Si OK, lancer la collecte complète : `7_collecter_contacts.bat`
- [ ] Vérifier le fichier créé : `output/reservations_avec_contacts.json`
- [ ] Importer les données dans votre application

---

## ⚠️ POINTS D'ATTENTION

### Confidentialité

Les numéros de téléphone sont des **données personnelles sensibles**.

**À faire** :
- ✅ Utiliser uniquement pour la gestion des réservations
- ✅ Ne pas partager avec des tiers
- ✅ Respecter le RGPD

**À ne pas faire** :
- ❌ Marketing non sollicité
- ❌ Partage avec des tiers
- ❌ Conservation après la fin du séjour

### Limitations

- **Réservations passées** : Coordonnées plus accessibles
- **Rate limiting** : Pause de 2 secondes entre chaque réservation
- **Coordonnées masquées** : Airbnb peut masquer certaines données

---

## 🎉 AVANTAGES

✅ **Communication directe** : Contacter sans passer par Airbnb  
✅ **Automatisation** : SMS/emails automatiques  
✅ **Urgences** : Contact rapide en cas de problème  
✅ **Expérience** : Instructions personnalisées  

---

**Créé par Kiro le 31 mai 2026**
