# Instructions pour Corriger Manuellement les 7 URLs iCal Sans Token

**Date**: 30 Mai 2026  
**Problème**: 7 lofts ont des URLs iCal sans token → HTTP 400 lors de la surveillance

---

## 📋 Liste des 7 Lofts à Corriger

| # | Nom | Listing ID | Loft ID |
|---|-----|------------|---------|
| 1 | **Madina loft** | 897794605927940108 | 46a77936-c945-4c2f-9707-cc15abf0edfb |
| 2 | **Golf view** | 1000816997221844803 | 9168c1c0-a123-42b8-8b8b-7e229a227548 |
| 3 | **Rosina Loft** | 1010024176351214897 | 9338c5ec-c6af-4c69-80a0-89551f2144ae |
| 4 | **Rosa loft** | 1010685773931128088 | 59d1e3d5-ed29-4be4-acb7-3429e90ed7a9 |
| 5 | **Oasis loft (ancien)** | 1081691126719400064 | dbdf5122-e053-494e-b3f3-ba2438713cd0 |
| 6 | **Rayan loft** | 1084830263659814195 | c0bdba5d-0e71-4d82-8672-9835c64c914b |
| 7 | **Aida Loft - Forest Vue** | 24697659 | 1f0cb6c2-b7e0-4b60-9a0a-c1ad64ae5c48 |

---

## 🔧 Méthode 1 : Récupération Manuelle via Airbnb (RECOMMANDÉ)

### Étape 1 : Connexion à Airbnb
1. Ouvrez votre navigateur
2. Allez sur https://www.airbnb.com
3. Connectez-vous avec : `loft.algerie.scl@gmail.com`

### Étape 2 : Pour Chaque Listing
Pour chaque listing de la liste ci-dessus :

1. **Ouvrez l'URL de partage de calendrier** :
   ```
   https://fr.airbnb.com/multicalendar/{LISTING_ID}/availability-settings/sharing-settings/import-calendar
   ```
   
   Remplacez `{LISTING_ID}` par le Listing ID du tableau ci-dessus.
   
   **Exemples** :
   - Madina loft : https://fr.airbnb.com/multicalendar/897794605927940108/availability-settings/sharing-settings/import-calendar
   - Golf view : https://fr.airbnb.com/multicalendar/1000816997221844803/availability-settings/sharing-settings/import-calendar
   - Rosina Loft : https://fr.airbnb.com/multicalendar/1010024176351214897/availability-settings/sharing-settings/import-calendar
   - etc.

2. **Copiez l'URL iCal** qui apparaît dans le champ "Étape 1"
   - L'URL doit ressembler à : `https://fr.airbnb.com/calendar/ical/897794605927940108.ics?t=abc123def456...`
   - **IMPORTANT** : L'URL DOIT contenir `?t=` ou `?s=` ou `calendarAccessSignature`
   - Si l'URL ne contient pas de token, elle ne fonctionnera pas !

3. **Mettez à jour Supabase** avec l'URL copiée

### Étape 3 : Mise à Jour dans Supabase

#### Option A : Via SQL Editor (Plus Rapide)
Dans le **SQL Editor** de Supabase, exécutez pour chaque loft :

```sql
-- Madina loft
UPDATE property_sync_config
SET ical_url_airbnb = 'COLLEZ_URL_ICI'
WHERE loft_id = '46a77936-c945-4c2f-9707-cc15abf0edfb';

UPDATE lofts
SET airbnb_ical_url = 'COLLEZ_URL_ICI'
WHERE id = '46a77936-c945-4c2f-9707-cc15abf0edfb';

-- Golf view
UPDATE property_sync_config
SET ical_url_airbnb = 'COLLEZ_URL_ICI'
WHERE loft_id = '9168c1c0-a123-42b8-8b8b-7e229a227548';

UPDATE lofts
SET airbnb_ical_url = 'COLLEZ_URL_ICI'
WHERE id = '9168c1c0-a123-42b8-8b8b-7e229a227548';

-- Rosina Loft
UPDATE property_sync_config
SET ical_url_airbnb = 'COLLEZ_URL_ICI'
WHERE loft_id = '9338c5ec-c6af-4c69-80a0-89551f2144ae';

UPDATE lofts
SET airbnb_ical_url = 'COLLEZ_URL_ICI'
WHERE id = '9338c5ec-c6af-4c69-80a0-89551f2144ae';

-- Rosa loft
UPDATE property_sync_config
SET ical_url_airbnb = 'COLLEZ_URL_ICI'
WHERE loft_id = '59d1e3d5-ed29-4be4-acb7-3429e90ed7a9';

UPDATE lofts
SET airbnb_ical_url = 'COLLEZ_URL_ICI'
WHERE id = '59d1e3d5-ed29-4be4-acb7-3429e90ed7a9';

-- Oasis loft (ancien)
UPDATE property_sync_config
SET ical_url_airbnb = 'COLLEZ_URL_ICI'
WHERE loft_id = 'dbdf5122-e053-494e-b3f3-ba2438713cd0';

UPDATE lofts
SET airbnb_ical_url = 'COLLEZ_URL_ICI'
WHERE id = 'dbdf5122-e053-494e-b3f3-ba2438713cd0';

-- Rayan loft
UPDATE property_sync_config
SET ical_url_airbnb = 'COLLEZ_URL_ICI'
WHERE loft_id = 'c0bdba5d-0e71-4d82-8672-9835c64c914b';

UPDATE lofts
SET airbnb_ical_url = 'COLLEZ_URL_ICI'
WHERE id = 'c0bdba5d-0e71-4d82-8672-9835c64c914b';

-- Aida Loft - Forest Vue
UPDATE property_sync_config
SET ical_url_airbnb = 'COLLEZ_URL_ICI'
WHERE loft_id = '1f0cb6c2-b7e0-4b60-9a0a-c1ad64ae5c48';

UPDATE lofts
SET airbnb_ical_url = 'COLLEZ_URL_ICI'
WHERE id = '1f0cb6c2-b7e0-4b60-9a0a-c1ad64ae5c48';
```

#### Option B : Via Table Editor (Interface Graphique)
1. Ouvrez la table `property_sync_config`
2. Trouvez la ligne avec le `loft_id` correspondant
3. Modifiez le champ `ical_url_airbnb` avec l'URL copiée
4. Répétez pour la table `lofts` (champ `airbnb_ical_url`)

---

## 🔧 Méthode 2 : Script Python (Si Méthode 1 Échoue)

Si vous ne pouvez pas accéder aux pages Airbnb ou si les URLs ne s'affichent pas :

```bash
python sync_ical_urls_final.py
```

Ce script va re-synchroniser les URLs depuis `property_sync_config` vers `lofts`.

---

## ✅ Vérification

Après avoir mis à jour les URLs, vérifiez qu'elles fonctionnent :

### Test 1 : Vérifier dans la Base de Données
```sql
SELECT 
  l.name,
  l.airbnb_listing_id,
  l.airbnb_ical_url,
  CASE 
    WHEN l.airbnb_ical_url LIKE '%?t=%' THEN '✅ Token ?t='
    WHEN l.airbnb_ical_url LIKE '%?s=%' THEN '✅ Token ?s='
    WHEN l.airbnb_ical_url LIKE '%calendarAccessSignature%' THEN '✅ Token signature'
    ELSE '❌ PAS DE TOKEN'
  END as token_status
FROM lofts l
WHERE l.name IN (
  'Madina loft', 'Golf view', 'Rosina Loft', 'Rosa loft',
  'Oasis loft (ancien)', 'Rayan loft', 'Aida Loft - Forest Vue'
);
```

### Test 2 : Tester l'URL iCal
Pour chaque URL, testez-la dans votre navigateur ou avec curl :

```bash
curl -I "https://fr.airbnb.com/calendar/ical/897794605927940108.ics?t=VOTRE_TOKEN"
```

- **HTTP 200** = ✅ URL valide
- **HTTP 400** = ❌ Pas de token ou token invalide
- **HTTP 404** = ❌ Listing introuvable

### Test 3 : Vérifier les Logs du Watcher
```bash
docker logs ical-watcher --tail 50 | grep "HTTP 400"
```

Si vous ne voyez plus d'erreurs HTTP 400 pour ces listings, c'est bon ! ✅

---

## 📊 Résumé

**Avant correction** :
- 51 URLs avec token ✅
- 7 URLs sans token ❌

**Après correction** :
- 58 URLs avec token ✅
- 0 URLs sans token ✅

**Taux de succès** : 100% 🎉

---

## 🆘 Besoin d'Aide ?

Si un listing ne peut pas être corrigé :
1. Vérifiez que le listing existe toujours sur Airbnb
2. Vérifiez que vous avez accès au calendrier du listing
3. Contactez le support Airbnb si le calendrier n'est pas accessible
4. En dernier recours, désactivez le listing dans `property_sync_config` :
   ```sql
   UPDATE property_sync_config
   SET is_active = false
   WHERE loft_id = 'LOFT_ID_ICI';
   ```

---

**Dernière mise à jour** : 30 Mai 2026 20:10
