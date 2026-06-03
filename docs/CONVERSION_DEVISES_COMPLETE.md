# 💱 CONVERSION DES DEVISES - Documentation Complète

## Date : 31 mai 2026
## Version : 2.1.1

---

## 🎯 OBJECTIF

Convertir automatiquement les montants des réservations Airbnb (GBP, EUR, USD, etc.) en Dinar Algérien (DZD) en utilisant les taux de conversion stockés dans la table `currencies` de Supabase.

---

## 📊 STRUCTURE DES DONNÉES

### Table `currencies` (Supabase)

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| `id` | uuid | Identifiant unique | - |
| `code` | varchar(3) | Code ISO de la devise | GBP |
| `name` | varchar(50) | Nom de la devise | Livre Sterling |
| `symbol` | varchar(3) | Symbole | £ |
| `ratio` | numeric | Taux de conversion vers DZD | 270.0 |
| `is_default` | boolean | Devise par défaut (DZD) | false |
| `created_at` | timestamp | Date de création | - |
| `updated_at` | timestamp | Date de mise à jour | - |

**Exemples de taux** :
- **DZD** : 1.0 (devise de base)
- **GBP** : 270.0 (1 GBP = 270 DZD)
- **EUR** : 250.0 (1 EUR = 250 DZD)
| **USD** : 250.0 (1 USD = 250 DZD)
- **CAD** : 162.0 (1 CAD = 162 DZD)

---

### Table `reservations` (Supabase)

| Colonne | Type | Description | Exemple |
|---------|------|-------------|---------|
| `total_amount` | numeric | Montant dans la devise d'origine | 653.0 |
| `currency_code` | varchar(10) | Code de la devise | GBP |
| `currency_ratio` | numeric | Taux de conversion | 270.0 |
| `base_price` | numeric | Prix de base | 600.0 |
| `cleaning_fee` | numeric | Frais de ménage | 30.0 |
| `service_fee` | numeric | Frais de service | 20.0 |
| `taxes` | numeric | Taxes | 3.0 |

**Calcul du montant en DZD** :
```
montant_dzd = total_amount × currency_ratio
```

**Exemple** :
```
653.0 GBP × 270.0 = 176,310 DZD
```

---

## 🔄 FLUX DE CONVERSION

### Avant (V2.0)

```
Scraping Airbnb
      ↓
Données brutes : {montant_total: 653.0, devise: "GBP"}
      ↓
Export → API Next.js → Supabase
      ↓
❌ Pas de conversion, montant en GBP stocké tel quel
```

### Après (V2.1.1) ✅

```
Scraping Airbnb
      ↓
Données brutes : {montant_total: 653.0, devise: "GBP"}
      ↓
✅ Récupération du taux depuis table currencies (GBP = 270.0)
      ↓
✅ Enrichissement : {
    montant_total: 653.0,
    devise: "GBP",
    currency_code: "GBP",
    currency_ratio: 270.0
}
      ↓
Export → API Next.js → Supabase
      ↓
✅ Montant en DZD calculable : 653.0 × 270.0 = 176,310 DZD
```

---

## 💻 IMPLÉMENTATION

### Module `currency_converter.py`

**Fonctions principales** :

1. **`get_currency_rates()`** : Récupère les taux depuis Supabase
   ```python
   rates = get_currency_rates()
   # {"GBP": 270.0, "EUR": 250.0, "USD": 250.0, "DZD": 1.0, "CAD": 162.0}
   ```

2. **`enrich_with_currency_ratio(reservations)`** : Enrichit les réservations
   ```python
   reservations = enrich_with_currency_ratio(reservations)
   # Ajoute currency_code et currency_ratio à chaque réservation
   ```

3. **`calculate_amount_in_dzd(amount, currency_code)`** : Calcule le montant en DZD
   ```python
   amount_dzd = calculate_amount_in_dzd(100, "GBP")
   # 27000.0 DZD
   ```

---

### Intégration dans `airbnb_scraper.py`

**Étape 6.5** : Conversion des devises (après collecte des coordonnées)

```python
# ── Étape 6.5 : Conversion des devises (NOUVEAU v2.1.1) ───
if USE_CURRENCY_CONVERSION:
    reservations = enrich_with_currency_ratio(reservations)
else:
    # Ajouter des champs par défaut
    for r in reservations:
        r["currency_code"] = r.get("devise", "DZD").upper()
        r["currency_ratio"] = 1.0
```

---

### Intégration dans `targeted_scraper.py`

```python
# Enrichir avec les taux de conversion
print(f"   💱 Conversion des devises...")
reservations = enrich_with_currency_ratio(reservations)
```

---

## 📊 EXEMPLE DE DONNÉES

### Avant conversion

```json
{
  "id": "HM4TB95HKS",
  "voyageur": "Hamza",
  "montant_total": 653.0,
  "devise": "GBP",
  "logement": "Choco Loft"
}
```

### Après conversion ✅

```json
{
  "id": "HM4TB95HKS",
  "voyageur": "Hamza",
  "montant_total": 653.0,
  "devise": "GBP",
  "currency_code": "GBP",
  "currency_ratio": 270.0,
  "logement": "Choco Loft"
}
```

**Montant en DZD** : `653.0 × 270.0 = 176,310 DZD`

---

## 🧪 TESTS

### Test du module

```bash
python currency_converter.py
```

**Résultat attendu** :
```
✅ 5 taux de conversion chargés depuis Supabase

📊 Taux de conversion disponibles :
   • CAD : 162.0
   • DZD : 1.0
   • EUR : 250.0
   • GBP : 270.0
   • USD : 250.0

💰 Exemples de conversion :
   • 100 GBP = 27,000.00 DZD
   • 100 EUR = 25,000.00 DZD
   • 100 USD = 25,000.00 DZD
   • 100 DZD = 100.00 DZD

✅ Réservations enrichies :
   • TEST001 : 653.0 GBP × 270.0 = 176,310.00 DZD
   • TEST002 : 150.0 EUR × 250.0 = 37,500.00 DZD
   • TEST003 : 5000.0 DZD × 1.0 = 5,000.00 DZD
```

---

### Test avec le scraping complet

```bash
SCRAPING_COMPLET_MAINTENANT.bat
```

**Vérifier dans les logs** :
```
💱 Enrichissement avec les taux de conversion...
   ✅ 5 taux de conversion chargés depuis Supabase
   ✅ 120 réservations enrichies avec currency_ratio

   📊 Exemple de conversion :
      Montant original : 653.0 GBP
      Taux de conversion : 270.0
      Montant en DZD : 176,310.00 DZD
```

---

## ⚙️ CONFIGURATION

### Cache des taux

Les taux de conversion sont mis en cache pendant **1 heure** pour éviter de requêter Supabase à chaque scraping.

**Configuration dans `currency_converter.py`** :
```python
CACHE_DURATION = 3600  # 1 heure (en secondes)
```

---

### Taux par défaut (fallback)

Si la connexion à Supabase échoue, les taux par défaut sont utilisés :

```python
{
    "DZD": 1.0,
    "GBP": 270.0,
    "EUR": 250.0,
    "USD": 250.0,
    "CAD": 162.0,
}
```

---

## 🔧 MAINTENANCE

### Mettre à jour les taux de conversion

**Option 1** : Via l'interface Supabase
1. Aller sur https://supabase.com/dashboard
2. Sélectionner le projet
3. Aller dans "Table Editor" → "currencies"
4. Modifier la colonne `ratio` pour la devise souhaitée

**Option 2** : Via SQL
```sql
UPDATE currencies
SET ratio = 275.0, updated_at = NOW()
WHERE code = 'GBP';
```

**Le cache sera automatiquement rafraîchi après 1 heure.**

---

### Ajouter une nouvelle devise

```sql
INSERT INTO currencies (code, name, symbol, ratio, is_default)
VALUES ('CHF', 'Franc Suisse', 'CHF', 260.0, false);
```

---

## 📋 MAPPING DES CHAMPS

### Scraper → API Next.js → Supabase

| Scraper | API Next.js | Supabase | Description |
|---------|-------------|----------|-------------|
| `montant_total` | `total_amount` | `total_amount` | Montant dans la devise d'origine |
| `devise` | `currency` | - | Code devise (non stocké) |
| `currency_code` | `currency_code` | `currency_code` | Code devise (GBP, EUR, etc.) |
| `currency_ratio` | `currency_ratio` | `currency_ratio` | Taux de conversion |

---

## 💡 UTILISATION CÔTÉ FRONTEND

### Afficher le montant en DZD

```typescript
// Dans votre composant React/Next.js
const reservation = {
  total_amount: 653.0,
  currency_code: "GBP",
  currency_ratio: 270.0
};

// Calcul du montant en DZD
const amountInDZD = reservation.total_amount * reservation.currency_ratio;

console.log(`${amountInDZD.toLocaleString('fr-DZ')} DZD`);
// Affiche : "176 310 DZD"
```

---

### Afficher les deux montants

```tsx
<div>
  <p>Montant original : {reservation.total_amount} {reservation.currency_code}</p>
  <p>Montant en DZD : {(reservation.total_amount * reservation.currency_ratio).toLocaleString('fr-DZ')} DZD</p>
</div>
```

**Résultat** :
```
Montant original : 653 GBP
Montant en DZD : 176 310 DZD
```

---

## 🎯 AVANTAGES

### ✅ Avantages de cette approche

1. **Flexibilité** : Les taux sont stockés dans Supabase et peuvent être mis à jour facilement
2. **Performance** : Cache de 1 heure pour éviter les requêtes répétées
3. **Traçabilité** : Le montant original ET le taux sont stockés
4. **Calcul côté client** : Le montant en DZD peut être recalculé à tout moment
5. **Historique** : Si les taux changent, les anciennes réservations gardent leur taux d'origine

---

### ❌ Alternative non retenue

**Stocker directement le montant en DZD** :
- ❌ Perte de l'information originale
- ❌ Impossible de recalculer avec un nouveau taux
- ❌ Pas de traçabilité

---

## 📊 STATISTIQUES

### Exemple de répartition des devises

```sql
SELECT 
    currency_code,
    COUNT(*) as count,
    SUM(total_amount) as total_original,
    SUM(total_amount * currency_ratio) as total_dzd
FROM reservations
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY currency_code
ORDER BY count DESC;
```

**Résultat attendu** :
```
currency_code | count | total_original | total_dzd
--------------+-------+----------------+------------
GBP           | 85    | 45,230.50      | 12,212,235
EUR           | 20    | 8,500.00       | 2,125,000
USD           | 10    | 3,200.00       | 800,000
DZD           | 5     | 150,000.00     | 150,000
```

---

## 🎉 RÉSUMÉ

### Ce qui a été fait ✅

1. ✅ Module `currency_converter.py` créé
2. ✅ Intégration dans `airbnb_scraper.py`
3. ✅ Intégration dans `targeted_scraper.py`
4. ✅ Tests réussis avec Supabase
5. ✅ Cache des taux (1 heure)
6. ✅ Fallback avec taux par défaut
7. ✅ Documentation complète

### Ce qui reste à faire ⚠️

1. ⚠️ Vérifier que l'API Next.js accepte `currency_code` et `currency_ratio`
2. ⚠️ Tester le flux complet (scraping → API → Supabase)
3. ⚠️ Vérifier l'affichage côté frontend

---

**Version** : 2.1.1  
**Date** : 31 mai 2026  
**Créé par** : Kiro
