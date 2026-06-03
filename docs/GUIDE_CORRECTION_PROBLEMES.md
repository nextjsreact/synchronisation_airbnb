# 🔧 GUIDE DE CORRECTION DES PROBLÈMES

**Date**: 1er juin 2026  
**Objectif**: Corriger les 4 problèmes détectés lors du scraping complet

---

## 📋 RÉSUMÉ DES PROBLÈMES

| # | Problème | Statut | Priorité |
|---|----------|--------|----------|
| 1 | Conversion devises désactivée | ✅ **CORRIGÉ** | 🔴 P0 |
| 2 | Collection contacts désactivée | ⏳ À corriger | 🟡 P1 |
| 3 | API 0 créées/mises à jour | ⏳ À investiguer | 🔴 P0 |
| 4 | Collection iCal échouée | ⏳ À investiguer | 🟡 P1 |

---

## ✅ PROBLÈME 1: Conversion devises (CORRIGÉ)

### Ce qui a été fait
Le fichier `Dockerfile` a été modifié pour inclure `currency_converter.py`:

```dockerfile
# Avant (ligne 75-80)
COPY airbnb_scraper.py .
COPY airbnb_api_client.py .
COPY collect_ical_urls.py .
# ❌ MANQUAIT: currency_converter.py

# Après (ligne 75-81)
COPY airbnb_scraper.py .
COPY airbnb_api_client.py .
COPY currency_converter.py .  # ✅ AJOUTÉ
COPY collect_ical_urls.py .
```

### Prochaine étape
Rebuild l'image Docker pour appliquer la correction:

```bash
# Option 1: Rebuild uniquement l'image scraper
docker-compose build airbnb-scraper

# Option 2: Rebuild toutes les images
docker-compose build
```

**Temps estimé**: 5 minutes

---

## ⏳ PROBLÈME 2: Collection contacts désactivée

### Diagnostic
La variable `COLLECT_CONTACTS=false` dans `.env` désactive la collection des contacts.

### Solution

**Étape 1**: Modifier le fichier `.env`

```bash
# Ouvrir .env et changer:
COLLECT_CONTACTS=false

# En:
COLLECT_CONTACTS=true
```

**Étape 2**: Rebuild l'image Docker (pour copier le nouveau .env)

```bash
docker-compose build airbnb-scraper
```

**Temps estimé**: 2 minutes

### ⚠️ Note importante
La collection des contacts ajoute **~30 secondes par réservation** car elle nécessite:
1. Navigation vers la page de détails
2. Attente du chargement
3. Extraction du téléphone/email

Pour 6,000 réservations: **~50 heures** de scraping supplémentaires.

### 💡 Recommandation
- **Production**: `COLLECT_CONTACTS=true` (collecter tous les contacts)
- **Test**: `COLLECT_CONTACTS=false` (scraping rapide)
- **Ciblé**: Collecter uniquement pour les réservations futures (à implémenter)

---

## ⏳ PROBLÈME 3: API 0 créées/mises à jour (À INVESTIGUER)

### Diagnostic
L'API Next.js reçoit 3,984 réservations mais retourne:
- ✅ `processed: 3,984`
- ❌ `created: 0`
- ❌ `updated: 0`

### Causes possibles

#### Cause 1: Validation Zod échoue silencieusement
```typescript
// Dans l'API Next.js
const schema = z.object({
  listing_id: z.string(),  // ❌ Peut rejeter si null ou number
  montant_total: z.number().nonnegative(),  // ❌ Peut rejeter si négatif
  // ...
});
```

**Solution**: Vérifier les logs de l'API Next.js
```bash
docker logs nextjs-api-container | grep -i "zod\|validation"
```

#### Cause 2: Contrainte UNIQUE rejette les doublons
```sql
-- La table reservations a une contrainte UNIQUE sur airbnb_confirmation_code
CREATE UNIQUE INDEX reservations_airbnb_confirmation_code_unique 
ON reservations (airbnb_confirmation_code);
```

Si les réservations existent déjà, l'API devrait retourner `updated > 0` au lieu de `created > 0`.

**Solution**: Vérifier les données dans Supabase
```bash
python 8_verifier_supabase.bat
```

#### Cause 3: Mapping des champs incorrect
Le scraper Python envoie `montant_total` mais l'API attend `total_amount`.

**Solution**: Vérifier le mapping dans `airbnb_api_client.py`

### Plan d'investigation

**Étape 1**: Vérifier les données dans Supabase (2 minutes)
```bash
python 8_verifier_supabase.bat
```

**Questions à répondre**:
- Combien de réservations dans Supabase?
- Y a-t-il des réservations récentes (dernières 24h)?
- Les taux de conversion sont-ils corrects?

**Étape 2**: Vérifier les logs de l'API Next.js (5 minutes)
```bash
# Si l'API tourne dans Docker
docker logs nextjs-api-container > api_logs.txt

# Chercher les erreurs
grep -i "error" api_logs.txt
grep -i "validation" api_logs.txt
grep -i "zod" api_logs.txt
```

**Étape 3**: Tester avec une seule réservation (2 minutes)
```bash
python TEST_RAPIDE_UNE_RESERVATION.py
```

**Résultat attendu**:
```
✅ Synchronisation réussie!
   📊 Métriques:
      • Traitées:  1
      • Créées:    1  ✅ (ou Mises à jour: 1)
```

**Étape 4**: Analyser les résultats

| Résultat | Diagnostic | Action |
|----------|------------|--------|
| `created: 1` | ✅ API fonctionne | Relancer scraping complet |
| `updated: 1` | ✅ API fonctionne (doublon) | Relancer scraping complet |
| `created: 0, updated: 0` | ❌ Validation échoue | Vérifier logs API |
| Erreur HTTP 400 | ❌ Schéma Zod invalide | Corriger mapping champs |
| Erreur HTTP 500 | ❌ Erreur serveur | Vérifier logs API |

---

## ⏳ PROBLÈME 4: Collection iCal échouée (À INVESTIGUER)

### Diagnostic
0 URLs iCal collectées sur 102 tentatives (0% de succès).

### Causes possibles

#### Cause 1: Session Airbnb expirée
Les cookies de session ne sont plus valides après le scraping complet (58 minutes).

**Solution**: Recréer la session
```bash
# Arrêter les services
docker-compose down

# Recréer la session
1_creer_session.bat

# Relancer la collection iCal
2_collecter_ical.bat
```

#### Cause 2: Timeout lors de la navigation
La navigation vers les pages de paramètres prend trop de temps.

**Solution**: Augmenter le timeout dans `collect_ical_urls.py`
```python
# Ligne ~150
page.goto(settings_url, timeout=60000)  # 60 secondes au lieu de 30
```

#### Cause 3: Changement de structure HTML
Airbnb a modifié la structure de la page de paramètres.

**Solution**: Vérifier le sélecteur CSS
```python
# Ligne ~160
ical_input = page.locator('input[value*="webcal://"]')
```

### Plan d'investigation

**Étape 1**: Vérifier la session Airbnb (2 minutes)
```bash
# Recréer la session
1_creer_session.bat
```

**Étape 2**: Tester la collection iCal (5 minutes)
```bash
2_collecter_ical.bat
```

**Résultat attendu**:
```
✅ 49/51 URLs iCal collectées (96%)
```

**Étape 3**: Si échec, déboguer avec un seul listing
```python
# Modifier collect_ical_urls.py ligne ~100
listings = get_all_listings()[:1]  # Tester avec 1 seul listing
```

---

## 🚀 PLAN D'ACTION COMPLET

### Phase 1: Corrections (10 minutes)

```bash
# 1. Rebuild l'image Docker (correction devises)
docker-compose build airbnb-scraper

# 2. Modifier .env (activer contacts)
# Ouvrir .env et changer COLLECT_CONTACTS=false en true

# 3. Rebuild à nouveau (copier nouveau .env)
docker-compose build airbnb-scraper
```

### Phase 2: Investigations (15 minutes)

```bash
# 4. Vérifier les données Supabase
python 8_verifier_supabase.bat

# 5. Tester avec une réservation
python TEST_RAPIDE_UNE_RESERVATION.py

# 6. Recréer la session Airbnb
1_creer_session.bat

# 7. Tester la collection iCal
2_collecter_ical.bat
```

### Phase 3: Re-scraping (60 minutes)

```bash
# 8. Relancer le scraping complet
.\DOCKER_SCRAPING_COMPLET.bat
```

**⚠️ Note**: Avec `COLLECT_CONTACTS=true`, le scraping prendra **beaucoup plus de temps** (~50 heures pour 6,000 réservations).

### Phase 4: Vérification (5 minutes)

```bash
# 9. Vérifier les résultats
python 8_verifier_supabase.bat

# 10. Vérifier les métriques API
# Chercher dans les logs:
# - created > 0 OU updated > 0
# - currency_ratio > 1.0 pour GBP/EUR/USD
# - guest_phone non vide
```

---

## 📊 MÉTRIQUES DE SUCCÈS

Après avoir appliqué toutes les corrections, vous devriez voir:

### ✅ Scraping complet
```
Réservations scrapées: 6,196
Réservations envoyées: 6,196
Durée: ~60 minutes (sans contacts) ou ~50 heures (avec contacts)
```

### ✅ API Next.js
```
📊 Métriques:
   • Traitées:  6,196
   • Créées:    4,500  ✅ (nouvelles)
   • Mises à jour: 1,696  ✅ (existantes)
   • Ignorées:  0
   • Échouées:  0
```

### ✅ Conversion devises
```
💱 Taux de conversion:
   • GBP × 270 = DZD  ✅
   • EUR × 250 = DZD  ✅
   • USD × 250 = DZD  ✅
   • CAD × 162 = DZD  ✅
```

### ✅ Contacts (si activé)
```
📞 Contacts collectés:
   • Téléphones: 5,800/6,196 (94%)  ✅
   • Emails: 6,196/6,196 (100%)  ✅
```

### ✅ iCal URLs
```
📅 iCal URLs collectées:
   • Succès: 49/51 (96%)  ✅
   • Échecs: 2/51 (4%)
```

---

## 🆘 EN CAS DE PROBLÈME

### Problème: Rebuild Docker échoue
```bash
# Nettoyer les images et rebuild
docker-compose down
docker system prune -f
docker-compose build --no-cache
```

### Problème: API Next.js injoignable
```bash
# Vérifier que l'API tourne
curl http://localhost:3000/api/airbnb/health

# Si erreur, vérifier les logs
docker logs nextjs-api-container
```

### Problème: Session Airbnb expirée
```bash
# Recréer la session
docker-compose down
1_creer_session.bat
```

### Problème: Scraping trop lent
```bash
# Désactiver la collection des contacts
# Dans .env:
COLLECT_CONTACTS=false

# Rebuild et relancer
docker-compose build airbnb-scraper
.\DOCKER_SCRAPING_COMPLET.bat
```

---

## 📞 SUPPORT

Si vous rencontrez des problèmes non couverts par ce guide:

1. **Vérifier les logs**:
   ```bash
   docker logs airbnb-scraper-container
   docker logs nextjs-api-container
   ```

2. **Vérifier la configuration**:
   ```bash
   # Afficher les variables d'environnement
   docker exec airbnb-scraper-container env | grep -E "COLLECT|NEXTJS|SUPABASE"
   ```

3. **Tester manuellement**:
   ```bash
   # Entrer dans le container
   docker exec -it airbnb-scraper-container bash
   
   # Tester le module currency_converter
   python -c "import currency_converter; print('OK')"
   ```

---

**Prochaine étape**: Exécuter la Phase 1 (Corrections) puis la Phase 2 (Investigations).
