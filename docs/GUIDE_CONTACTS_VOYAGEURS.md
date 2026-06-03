## 📞 GUIDE - COLLECTE DES COORDONNÉES DES VOYAGEURS

## Date : 31 mai 2026

---

## 🎯 OBJECTIF

Récupérer les **numéros de téléphone** et **emails** des voyageurs pour chaque réservation active.

---

## 📊 DONNÉES ACTUELLES vs DONNÉES ENRICHIES

### Actuellement (sans contacts)

```csv
id,statut,voyageur,nb_voyageurs,logement,listing_id,date_arrivee,date_depart
HMQWRRNJAK,Confirmée,Seg Chouiter,1,Aida Loft,1413064424044049516,2026-05-11,2026-06-05
```

### Après enrichissement (avec contacts)

```json
{
  "id": "HMQWRRNJAK",
  "statut": "Confirmée",
  "voyageur": "Seg Chouiter",
  "telephone_voyageur": "+33 6 12 34 56 78",
  "email_voyageur": "seg.chouiter@example.com",
  "nb_voyageurs": 1,
  "logement": "Aida Loft",
  ...
}
```

---

## 🚀 UTILISATION

### Prérequis

1. Avoir lancé le scraping complet au moins une fois :
   ```batch
   SCRAPING_COMPLET_MAINTENANT.bat
   ```

2. Avoir des réservations actives (à venir ou en cours)

### Lancer la collecte

```batch
7_collecter_contacts.bat
```

### Résultat

Un fichier `output/reservations_avec_contacts.json` contenant toutes les réservations avec les coordonnées.

---

## ⏱️ TEMPS DE TRAITEMENT

- **~5 secondes** par réservation
- **Exemple** : 20 réservations actives = ~2 minutes

---

## 🔍 COMMENT ÇA FONCTIONNE

### Parcours Airbnb

Pour chaque réservation, le script :

1. **Ouvre la page de détails** :
   ```
   https://www.airbnb.com/hosting/reservations/details/{confirmation_code}
   ```

2. **Extrait les coordonnées** :
   - Numéro de téléphone (regex)
   - Email (regex)
   - Menu "..." si disponible

3. **Sauvegarde** les données enrichies

### Méthodes d'extraction

Le script utilise **3 méthodes** pour trouver les coordonnées :

#### Méthode 1 : Contenu de la page
Cherche directement dans le HTML de la page avec des regex.

#### Méthode 2 : Menu "..."
Clique sur le menu (3 points) et cherche dans le contenu du menu.

#### Méthode 3 : Éléments spécifiques
Cherche les éléments contenant "téléphone" ou "phone".

---

## 📋 FILTRAGE DES RÉSERVATIONS

Le script traite **uniquement les réservations actives** :

- ✅ Confirmée
- ✅ À venir
- ✅ Séjour en cours
- ❌ Terminée
- ❌ Annulée

**Raison** : Les coordonnées ne sont plus accessibles pour les réservations passées.

---

## 📊 RÉSULTATS ATTENDUS

### Taux de succès

- **Téléphone** : ~80-90% (Airbnb affiche généralement le téléphone)
- **Email** : ~60-70% (parfois masqué par Airbnb)

### Exemple de sortie

```
📞 Enrichissement de 20 réservations avec les coordonnées...

   [1/20] HMQWRRNJAK - Seg Chouiter
      ✅ Téléphone : +33 6 12 34 56 78
      ✅ Email : seg.chouiter@example.com

   [2/20] HMBECW8ZM4 - Tarik Remous
      ✅ Téléphone : +33 7 98 76 54 32
      ⚠️  Email : N/A

   ...

✅ TERMINÉ

📊 Résultats :
   • 20 réservations traitées
   • 18 avec téléphone (90%)
   • 14 avec email (70%)

📁 Fichier créé : output/reservations_avec_contacts.json
```

---

## 🔄 INTÉGRATION AVEC LE SYSTÈME

### Option 1 : Collecte manuelle (actuelle)

Lancez manuellement quand vous avez besoin des coordonnées :

```batch
7_collecter_contacts.bat
```

### Option 2 : Collecte automatique (à implémenter)

Modifier `targeted_scraper.py` pour collecter automatiquement les coordonnées lors de la synchronisation.

**Avantage** : Coordonnées toujours à jour  
**Inconvénient** : Scraping plus lent (~5 sec par réservation)

---

## 📁 FICHIERS CRÉÉS

### reservations_avec_contacts.json

Format JSON avec toutes les données :

```json
[
  {
    "id": "HMQWRRNJAK",
    "statut": "Confirmée",
    "voyageur": "Seg Chouiter",
    "telephone_voyageur": "+33 6 12 34 56 78",
    "email_voyageur": "seg.chouiter@example.com",
    "nb_voyageurs": 1,
    "logement": "Aida Loft",
    "listing_id": "1413064424044049516",
    "date_arrivee": "2026-05-11",
    "date_depart": "2026-06-05",
    "nb_nuits": 25,
    "montant_total": 653.0,
    "devise": "GBP",
    "date_creation": "2026-05-10"
  },
  ...
]
```

---

## 🔧 PERSONNALISATION

### Modifier les réservations à traiter

Dans `scrape_guest_contacts.py`, ligne ~250 :

```python
# Actuellement : réservations actives uniquement
active_reservations = [
    r for r in reservations
    if r.get("statut", "").lower() in [
        "confirmée", "upcoming", "séjour en cours", "en cours",
        "à venir", "future", "accepted"
    ]
]

# Pour traiter TOUTES les réservations :
active_reservations = reservations
```

### Modifier la pause entre réservations

Dans `scrape_guest_contacts.py`, ligne ~230 :

```python
# Actuellement : 2 secondes
time.sleep(2)

# Pour aller plus vite (risque de rate limiting) :
time.sleep(1)

# Pour être plus prudent :
time.sleep(5)
```

---

## ⚠️ LIMITATIONS

### 1. Réservations passées

Les coordonnées ne sont plus accessibles pour les réservations terminées ou annulées.

**Solution** : Collecter les coordonnées dès la réservation confirmée.

### 2. Rate limiting

Airbnb peut bloquer si trop de requêtes en peu de temps.

**Solution** : Pause de 2 secondes entre chaque réservation (configurable).

### 3. Coordonnées masquées

Airbnb peut masquer certaines coordonnées pour des raisons de confidentialité.

**Solution** : Aucune, c'est une limitation Airbnb.

---

## 🎯 CAS D'USAGE

### 1. Contacter les voyageurs avant l'arrivée

```batch
# Collecter les coordonnées
7_collecter_contacts.bat

# Utiliser les données pour envoyer des SMS/emails
```

### 2. Créer une liste de contacts

Importer `reservations_avec_contacts.json` dans votre CRM ou application.

### 3. Automatiser les communications

Utiliser les coordonnées pour automatiser :
- SMS de bienvenue
- Instructions d'arrivée
- Demande d'avis après le séjour

---

## 🔄 MISE À JOUR DES COORDONNÉES

### Fréquence recommandée

- **Quotidienne** : Si vous avez beaucoup de nouvelles réservations
- **Hebdomadaire** : Si vous avez peu de réservations
- **À la demande** : Quand vous avez besoin des coordonnées

### Automatisation

Pour automatiser la collecte quotidienne, créez une tâche planifiée Windows :

1. Ouvrez "Planificateur de tâches"
2. Créez une nouvelle tâche
3. Déclencheur : Quotidien à 8h00
4. Action : Lancer `7_collecter_contacts.bat`

---

## 📊 STATISTIQUES

### Temps de traitement

| Nombre de réservations | Temps estimé |
|------------------------|--------------|
| 10 réservations | ~1 minute |
| 20 réservations | ~2 minutes |
| 50 réservations | ~5 minutes |
| 100 réservations | ~10 minutes |

### Taux de succès typique

| Donnée | Taux de succès |
|--------|----------------|
| Téléphone | 80-90% |
| Email | 60-70% |
| Les deux | 50-60% |

---

## 🛠️ DÉPANNAGE

### Problème : "Fichier introuvable : reservations_airbnb.json"

**Solution** : Lancez d'abord le scraping complet :
```batch
SCRAPING_COMPLET_MAINTENANT.bat
```

### Problème : "Aucune réservation active à enrichir"

**Solution** : Vérifiez que vous avez des réservations à venir ou en cours dans Airbnb.

### Problème : Taux de succès faible (<50%)

**Solutions** :
1. Vérifiez que vous êtes bien connecté à Airbnb
2. Augmentez la pause entre réservations (5 secondes)
3. Vérifiez les logs pour voir les erreurs

### Problème : "Session expirée"

**Solution** : Le script va automatiquement se reconnecter. Si ça échoue, lancez d'abord :
```batch
1_creer_session.bat
```

---

## 📝 NOTES IMPORTANTES

### Confidentialité

Les coordonnées des voyageurs sont des **données personnelles sensibles**.

**Obligations** :
- ✅ Utiliser uniquement pour la gestion des réservations
- ✅ Ne pas partager avec des tiers
- ✅ Supprimer après la fin du séjour (RGPD)
- ❌ Ne pas utiliser pour du marketing non sollicité

### Conformité RGPD

Si vous êtes en Europe, vous devez :
1. Informer les voyageurs de la collecte de leurs données
2. Obtenir leur consentement (implicite via Airbnb)
3. Leur permettre d'accéder/modifier/supprimer leurs données
4. Supprimer les données après un délai raisonnable

---

## 🎉 AVANTAGES

✅ **Communication directe** : Contacter les voyageurs sans passer par Airbnb  
✅ **Automatisation** : Envoyer des messages automatiques  
✅ **Meilleure expérience** : Instructions personnalisées  
✅ **Urgences** : Contacter rapidement en cas de problème  

---

**Créé par Kiro le 31 mai 2026**
