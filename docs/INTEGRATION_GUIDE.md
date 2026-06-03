# Guide d'Intégration - API Client Python

## Objectif

Modifier le script `airbnb_scraper.py` pour qu'il envoie les données à l'API Next.js au lieu d'accéder directement à Supabase.

## Étape 1: Copier le fichier client

Copiez `scripts/airbnb-api-client.py` dans le dossier du script Python:

```bash
cp scripts/airbnb-api-client.py d:/Airbnb_transfer_v2/airbnb_api_client.py
```

## Étape 2: Mettre à jour le fichier .env

Ajoutez ces lignes dans `d:/Airbnb_transfer_v2/.env`:

```env
# API Next.js pour envoyer les données
NEXTJS_API_URL=http://localhost:3000/api/airbnb/sync
NEXTJS_API_KEY=NXxmDRrHzvb4I+SuGdZv9kGvd574bnhVctjKcz0rR1s=
```

## Étape 3: Modifier airbnb_scraper.py

### 3.1 Remplacer l'import Supabase (ligne ~30)

**AVANT:**
```python
try:
    from supabase_client import (
        upsert_reservations,
        upsert_listings,
        log_sync,
    )
    USE_SUPABASE = True
except Exception as e:
    print(f"⚠️  Supabase désactivé : {e}")
    USE_SUPABASE = False
```

**APRÈS:**
```python
try:
    from airbnb_api_client import (
        send_to_nextjs_api,
        upsert_reservations,
        upsert_listings,
        log_sync,
    )
    USE_API = True
except Exception as e:
    print(f"⚠️  API Next.js désactivée : {e}")
    USE_API = False
```

### 3.2 Modifier la fonction push_to_supabase (ligne ~450)

**AVANT:**
```python
def push_to_supabase(reservations: list, ical_urls: dict):
    """Envoie les données vers Supabase :
    1. Réservations → table reservations
    2. Annonces + URLs iCal → table listings
    """
    if not USE_SUPABASE:
        print("⚠️  Supabase non configuré — skip push")
        return
    
    print("\n☁️  Push vers Supabase...")
    
    # ── 1. Réservations ──────────────────────────────────────
    count = upsert_reservations(reservations)
    print(f"   ✅ {count} réservations poussées vers Supabase")
    
    # ── 2. Annonces + URLs iCal ───────────────────────────────
    # ... reste du code ...
```

**APRÈS:**
```python
def push_to_nextjs(reservations: list, ical_urls: dict, sync_type: str = "full"):
    """Envoie les données vers l'API Next.js.
    
    Args:
        reservations: Liste des réservations scrapées
        ical_urls: Dict {listing_id: ical_url} (non utilisé pour l'instant)
        sync_type: Type de synchronisation ("full", "targeted", "ical_watcher", "manual")
    """
    if not USE_API:
        print("⚠️  API Next.js non configurée — skip push")
        return
    
    print("\n☁️  Envoi vers l'API Next.js...")
    
    try:
        result = send_to_nextjs_api(reservations, sync_type=sync_type)
        
        # Afficher les annonces détectées
        listing_ids = list({r.get("listing_id") for r in reservations if r.get("listing_id")})
        with_ical = sum(1 for lid in listing_ids if ical_urls.get(lid))
        print(f"   ℹ️  {len(listing_ids)} annonces détectées — {with_ical} avec URL iCal")
        print(f"   💡 Configurez le mapping dans Supabase (table lofts.airbnb_listing_id)")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        raise
```

### 3.3 Mettre à jour l'appel dans main() (ligne ~550)

**AVANT:**
```python
# ── Étape 7 : Push Supabase (NOUVEAU v2) ──────────────────
push_to_supabase(reservations, ical_urls)
```

**APRÈS:**
```python
# ── Étape 7 : Push API Next.js (v2.0.1) ───────────────────
push_to_nextjs(reservations, ical_urls, sync_type="full")
```

### 3.4 Mettre à jour le log final (ligne ~560)

**AVANT:**
```python
# ── Étape 8 : Log de sync ─────────────────────────────────
duration = time.time() - start_time
if USE_SUPABASE:
    try:
        log_sync(
            sync_type="full",
            status="success",
            listings_count=len({r["listing_id"] for r in reservations}),
            reservations_count=len(reservations),
            duration=duration,
        )
    except Exception:
        pass
```

**APRÈS:**
```python
# ── Étape 8 : Résumé final ────────────────────────────────
duration = time.time() - start_time
# Le log est maintenant géré automatiquement par l'API Next.js
```

### 3.5 Mettre à jour l'affichage final (ligne ~570)

**AVANT:**
```python
print(f"\n🎉 Terminé en {duration:.0f}s !")
print(f"   → {OUTPUT_CSV}")
print(f"   → {OUTPUT_JSON}")
if USE_SUPABASE:
    print(f"   → Supabase mis à jour")
```

**APRÈS:**
```python
print(f"\n🎉 Terminé en {duration:.0f}s !")
print(f"   → {OUTPUT_CSV}")
print(f"   → {OUTPUT_JSON}")
if USE_API:
    print(f"   → API Next.js synchronisée")
```

## Étape 4: Installer les dépendances

```bash
cd d:/Airbnb_transfer_v2
pip install requests
```

## Étape 5: Tester

### 5.1 Démarrer le serveur Next.js

```powershell
cd C:\Users\SERVICE-INFO\IA\algerie-loft
npm run dev
```

### 5.2 Tester le client Python seul

```bash
cd d:/Airbnb_transfer_v2
python airbnb_api_client.py
```

Résultat attendu: Une réservation de test est créée.

### 5.3 Lancer le scraper complet

```bash
python airbnb_scraper.py
```

## Avantages de cette approche

✅ **Sécurité**: Les credentials Supabase restent côté serveur  
✅ **Validation**: L'API valide les données avec Zod  
✅ **Logs**: Tous les syncs sont loggés automatiquement  
✅ **Conflits**: Détection automatique des chevauchements  
✅ **Rate limiting**: Protection contre les abus  
✅ **Retry**: Gestion automatique des erreurs temporaires  

## Dépannage

### Erreur "401 Non autorisé"
- Vérifiez que `NEXTJS_API_KEY` dans `.env` correspond à `AIRBNB_API_SECRET` dans `.env.local` du projet Next.js
- Redémarrez le serveur Next.js après modification

### Erreur "Connection refused"
- Vérifiez que le serveur Next.js est démarré (`npm run dev`)
- Vérifiez l'URL dans `NEXTJS_API_URL` (doit être `http://localhost:3000/api/airbnb/sync`)

### Erreur "Timeout"
- Augmentez `TIMEOUT` dans `airbnb_api_client.py` (ligne 23)
- Vérifiez que Supabase est accessible

### Les réservations ne s'affichent pas
- Elles sont probablement en staging (`airbnb_reservations_staging`)
- Exécutez le script `check_test_reservation.sql` pour vérifier
- Vérifiez les conflits dans `airbnb_conflicts`
