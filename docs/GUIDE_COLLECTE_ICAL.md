# 📅 Guide : Collecte des URLs iCal avec token

**Date** : 25 mai 2026  
**Problème** : Les 54 URLs en base n'ont pas le token `?t=` nécessaire  
**Solution** : Scraper les URLs depuis l'interface Airbnb

---

## 🎯 PROBLÈME IDENTIFIÉ

### URLs actuelles en base (❌ Ne fonctionnent pas)

```
https://www.airbnb.com/calendar/ical/27940108.ics
https://www.airbnb.com/calendar/ical/40739075.ics
...
```

**Problème** : Airbnb retourne **HTTP 400** sans le token

### URLs nécessaires (✅ Fonctionnent)

```
https://www.airbnb.com/calendar/ical/27940108.ics?t=917150ed9fcd45a98f676b7bbc5a010f&locale=fr
https://www.airbnb.com/calendar/ical/40739075.ics?t=abc123def456...&locale=fr
```

**Avec token** : Airbnb retourne **HTTP 200** ✅

---

## 📍 CHEMIN DOCUMENTÉ PAR AIRBNB

Selon la documentation officielle Airbnb :

1. **Calendrier** → Sélectionner l'annonce
2. **Disponibilités**
3. Sous **"Associer des calendriers"** → Cliquer sur **"Me connecter à un autre site web"**
4. **Copier le lien du calendrier Airbnb** (avec token `?t=`)

---

## 🛠️ SCRIPT AMÉLIORÉ

### Fichier : `collect_ical_urls.py`

Le script a été amélioré pour :

1. ✅ Suivre le chemin documenté par Airbnb
2. ✅ Cliquer sur "Associer des calendriers"
3. ✅ Cliquer sur "Me connecter à un autre site web"
4. ✅ Extraire l'URL avec token `?t=` ou `?s=` ou `calendarAccessSignature`
5. ✅ Sauvegarder des captures d'écran pour debug
6. ✅ Vérifier que le token est présent avant de sauvegarder

### Améliorations apportées

#### 1. Navigation vers la page de disponibilité

```python
url = f"https://www.airbnb.com/hosting/listings/{listing_id}/availability"
page.goto(url, timeout=60000, wait_until="domcontentloaded")
```

#### 2. Clic sur "Associer des calendriers"

```python
sync_button_texts = [
    "Associer des calendriers",
    "Sync calendars",
    "Synchroniser les calendriers",
    "Link calendars",
    "Connect calendars",
]

for btn_text in sync_button_texts:
    btn = page.locator(f"text={btn_text}").first
    if btn.count() > 0 and btn.is_visible():
        btn.click()
        break
```

#### 3. Clic sur "Me connecter à un autre site web"

```python
export_texts = [
    "Me connecter à un autre site web",
    "Export calendar",
    "Exporter le calendrier",
    "Connect to another website",
]

for export_text in export_texts:
    link = page.locator(f"text={export_text}").first
    if link.count() > 0 and link.is_visible():
        link.click()
        break
```

#### 4. Extraction de l'URL avec token

```python
ical_url = page.evaluate("""
    () => {
        // Chercher dans les inputs
        const inputs = document.querySelectorAll('input[type="text"], input[type="url"], input[readonly]');
        for (const inp of inputs) {
            const val = inp.value || '';
            // Chercher URL avec token ?t= ou ?s= ou calendarAccessSignature
            if (val.includes('calendar/ical/') && 
                (val.includes('?t=') || val.includes('?s=') || val.includes('calendarAccessSignature'))) {
                return val;
            }
        }
        return null;
    }
""")
```

#### 5. Validation du token

```python
if ical_url:
    # Vérifier que l'URL a bien un token
    if '?t=' in ical_url or '?s=' in ical_url or 'calendarAccessSignature' in ical_url:
        print(f"   ✅ URL iCal trouvée avec token")
        return ical_url
    else:
        print(f"   ⚠️  URL trouvée mais sans token")
        return None  # Ne pas sauvegarder une URL inutilisable
```

#### 6. Captures d'écran pour debug

```python
# Avant les clics
screenshot_path = f"output/debug_ical_{listing_id}_availability.png"
page.screenshot(path=screenshot_path)

# Après les clics
screenshot_path = f"output/debug_ical_{listing_id}_export.png"
page.screenshot(path=screenshot_path)
```

---

## 🚀 UTILISATION

### Prérequis

1. ✅ Session Airbnb valide (résoudre le CAPTCHA une fois)
2. ✅ Fichier `output/airbnb_session.json` existe
3. ✅ `.env` configuré avec `HEADLESS=false` (pour voir ce qui se passe)

### Commandes

#### Test rapide (3 lofts)

```bash
python collect_ical_urls.py
```

**Durée** : ~5-10 minutes  
**Résultat** : 3 URLs iCal avec token

#### Tous les lofts (54 annonces)

```bash
python collect_ical_urls.py --all
```

**Durée** : ~2-3 heures (2-3 min par loft)  
**Résultat** : 54 URLs iCal avec token

### Logs attendus

```
═══════════════════════════════════════════════════════
  Collecte des URLs iCal — TOUS les lofts
  Début : 13:45:00
═══════════════════════════════════════════════════════

📋 54 lofts à traiter

📎 54 URLs iCal déjà en base

⏭️  0 lofts ont déjà une URL iCal avec token — tous à mettre à jour

🌐 Lancement CloakBrowser...
   💾 Session trouvée : output/airbnb_session.json
   🔍 Vérification de la session sauvegardée...
   ✅ Session valide — connexion automatique !

[1/54] Loft Alger Centre (27940108)...
   📍 Navigation vers : https://www.airbnb.com/hosting/listings/27940108/availability
   📸 Capture : output/debug_ical_27940108_availability.png
   🔘 Clic sur : Associer des calendriers
   🔗 Clic sur : Me connecter à un autre site web
   📸 Capture : output/debug_ical_27940108_export.png
   ✅ URL iCal trouvée avec token
   🔗 https://www.airbnb.com/calendar/ical/27940108.ics?t=917150ed9fcd45a98f676b7bbc5a010f...
   ✅ URL iCal mise à jour (token: ?t=)

[2/54] Loft Oran Mer (40739075)...
   📍 Navigation vers : https://www.airbnb.com/hosting/listings/40739075/availability
   ...
```

---

## 🔍 VÉRIFICATION

### Vérifier qu'une URL a un token

```bash
# Tester l'URL sans token (doit retourner 400)
curl -I "https://www.airbnb.com/calendar/ical/27940108.ics"
# HTTP/1.1 400 Bad Request

# Tester l'URL avec token (doit retourner 200)
curl -I "https://www.airbnb.com/calendar/ical/27940108.ics?t=917150ed9fcd45a98f676b7bbc5a010f"
# HTTP/1.1 200 OK
```

### Vérifier les URLs en base

```sql
-- Compter les URLs avec token
SELECT 
    COUNT(*) FILTER (WHERE ical_url_airbnb LIKE '%?t=%') as with_t_token,
    COUNT(*) FILTER (WHERE ical_url_airbnb LIKE '%?s=%') as with_s_token,
    COUNT(*) FILTER (WHERE ical_url_airbnb LIKE '%calendarAccessSignature=%') as with_signature,
    COUNT(*) FILTER (WHERE ical_url_airbnb NOT LIKE '%?%') as without_token,
    COUNT(*) as total
FROM property_sync_config
WHERE ical_url_airbnb IS NOT NULL;
```

**Attendu après collecte** :
```
with_t_token: 54
with_s_token: 0
with_signature: 0
without_token: 0
total: 54
```

### Vérifier les captures d'écran

```bash
# Lister les captures
dir output\debug_ical_*.png

# Ouvrir une capture
start output\debug_ical_27940108_export.png
```

**Vous devriez voir** :
- Page de disponibilité avec le calendrier
- Modal "Associer des calendriers" ouvert
- Input avec l'URL iCal complète (avec token)

---

## ⚠️ PROBLÈMES COURANTS

### Problème 1 : Bouton "Associer des calendriers" introuvable

**Cause** : Airbnb a changé l'interface ou le texte du bouton

**Solution** :
1. Vérifiez les captures d'écran dans `output/`
2. Identifiez le texte exact du bouton
3. Ajoutez-le dans la liste `sync_button_texts`

```python
sync_button_texts = [
    "Associer des calendriers",
    "Sync calendars",
    "NOUVEAU_TEXTE_ICI",  # Ajoutez le texte trouvé
]
```

### Problème 2 : URL trouvée mais sans token

**Cause** : Le script n'a pas cliqué au bon endroit

**Solution** :
1. Vérifiez les captures d'écran
2. Lancez en mode non-headless pour voir ce qui se passe :
   ```env
   HEADLESS=false
   ```
3. Observez le navigateur et notez où cliquer

### Problème 3 : Session expirée

**Cause** : Le fichier `output/airbnb_session.json` est invalide

**Solution** :
```bash
# Supprimer la session
del output\airbnb_session.json

# Recréer la session
HEADLESS=false
python airbnb_scraper.py
# → Résoudre le CAPTCHA

# Relancer la collecte
python collect_ical_urls.py --all
```

### Problème 4 : Timeout lors de la navigation

**Cause** : Connexion lente ou Airbnb bloque

**Solution** :
1. Utilisez un proxy résidentiel :
   ```env
   PROXY_URL=http://username:password@proxy-provider.com:port
   ```
2. Augmentez le timeout dans le script (ligne ~105) :
   ```python
   page.goto(url, timeout=120000)  # 2 minutes au lieu de 1
   ```

---

## 🎯 APRÈS LA COLLECTE

### 1. Vérifier les résultats

```bash
# Compter les succès
python -c "
import requests
resp = requests.get('https://zlpzuyctjhajdwlxzdzk.supabase.co/rest/v1/property_sync_config?select=ical_url_airbnb', 
                    headers={'apikey': 'votre_key'})
urls = [c['ical_url_airbnb'] for c in resp.json() if c.get('ical_url_airbnb')]
with_token = [u for u in urls if '?t=' in u or '?s=' in u or 'calendarAccessSignature' in u]
print(f'{len(with_token)}/{len(urls)} URLs avec token')
"
```

### 2. Nettoyer les URLs invalides

```sql
-- Supprimer les URLs sans token (inutilisables)
DELETE FROM property_sync_config
WHERE ical_url_airbnb IS NOT NULL
  AND ical_url_airbnb NOT LIKE '%?t=%'
  AND ical_url_airbnb NOT LIKE '%?s=%'
  AND ical_url_airbnb NOT LIKE '%calendarAccessSignature=%';

-- Supprimer l'entrée test.ics (bug)
DELETE FROM property_sync_config
WHERE ical_url_airbnb LIKE '%test.ics%';
```

### 3. Lancer le watcher

```bash
# Une fois que toutes les URLs ont un token
cd docker
docker compose --profile ical up -d

# Vérifier les logs
docker compose logs -f airbnb_ical_watcher
```

**Logs attendus** :
```
--- Cycle 1 (13:50:00) ---
   [27940108] Premier hash enregistré
   [40739075] Premier hash enregistré
   ...
   Aucun changement
   Prochain check dans 300s...
```

---

## 📊 STATISTIQUES

### Avant la collecte

```
54 URLs en base
0 URLs avec token (?t= ou ?s= ou calendarAccessSignature)
54 URLs inutilisables (HTTP 400)
```

### Après la collecte

```
54 URLs en base
54 URLs avec token (?t=)
0 URLs inutilisables
```

### Temps de collecte

| Nombre de lofts | Temps estimé | Commande |
|-----------------|--------------|----------|
| 3 (test) | 5-10 minutes | `python collect_ical_urls.py` |
| 54 (tous) | 2-3 heures | `python collect_ical_urls.py --all` |

**Conseil** : Lancez d'abord le test (3 lofts) pour vérifier que tout fonctionne, puis lancez la collecte complète.

---

## 🎉 RÉSUMÉ

1. **Problème** : 54 URLs sans token → HTTP 400
2. **Solution** : Script amélioré qui suit le chemin Airbnb
3. **Résultat** : 54 URLs avec token `?t=` → HTTP 200 ✅
4. **Prochaine étape** : Lancer `ical_watcher` pour surveiller les changements

**Le watcher pourra maintenant fonctionner !** 🚀
