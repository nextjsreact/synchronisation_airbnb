"""
airbnb_api_client.py - Client pour envoyer les données à l'API Next.js
=======================================================================
Version  : 2.0.2
Date     : Mai 2026 (patché Juin 2026)

Ce module remplace l'accès direct à Supabase par des appels à l'API Next.js.
À intégrer dans airbnb_scraper.py à la place de supabase_client.py

CHANGELOG v2.0.2 (2026-06-30) :
  + FIX bug "montant_total=0.0 → reservation ignorée" : la vérification des
    champs requis traitait `0` comme une valeur manquante au même titre que
    `None` ou `""` (via `r_copy[req] in (None, "", 0)`). Or montant_total=0
    est une valeur LÉGITIME (résa annulée, séjour gratuit, montant pas
    encore affiché par Airbnb) et non une absence de données. Ces
    réservations étaient donc silencieusement rejetées AVANT même d'être
    envoyées à l'API Next.js — elles n'apparaissaient ni dans les logs
    Supabase, ni dans les erreurs Zod, ni dans le service de sync.
    Correctif : séparation des champs requis "non-numériques" (où une
    chaîne vide ou None signale une vraie absence) des champs "numériques"
    (où 0 est une valeur valide, seule l'absence de clé ou None compte
    comme manquant).

Dépendances :
    pip install requests python-dotenv

Usage :
    from airbnb_api_client import send_to_nextjs_api
    
    reservations = [...]  # Liste des réservations scrapées
    result = send_to_nextjs_api(reservations, sync_type="full")
"""

import os
import time
import json
import requests
from typing import List, Dict, Any
from datetime import datetime

# Charger les variables d'environnement depuis .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv non installé. Installez avec: pip install python-dotenv")
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL = os.environ.get("NEXTJS_API_URL", "http://localhost:3000/api/airbnb/sync")
API_KEY = os.environ.get("NEXTJS_API_KEY", "")

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # secondes
TIMEOUT = 120  # secondes (par batch)

# ── FIX (2026-06-30) ─────────────────────────────────────────────────────
# Champs requis dont une valeur "vide" (None, "", absente) signale une vraie
# anomalie de scraping. Pour ceux-ci on garde la vérification stricte.
REQUIRED_FR_FIELDS_NON_NUMERIC = (
    "id", "listing_id", "statut", "voyageur",
    "date_arrivee", "date_depart", "devise",
)
# Champs requis NUMÉRIQUES où 0 est une valeur légitime (montant nul,
# annulation, etc.) — seule l'absence de clé ou une valeur None est
# considérée comme manquante. nb_voyageurs et nb_nuits restent à >0 car
# une réservation a forcément au moins 1 voyageur et 1 nuit ; montant_total
# en revanche peut légitimement valoir 0.
REQUIRED_FR_FIELDS_NUMERIC_ALLOW_ZERO = ("montant_total",)
REQUIRED_FR_FIELDS_NUMERIC_STRICT = ("nb_voyageurs", "nb_nuits")
# ─────────────────────────────────────────────────────────────────────────


# ============================================================================
# HEALTH CHECK
# ============================================================================

def check_api_health() -> dict:
    """
    Vérifie que l'API Next.js est accessible avant de scraper.

    Returns:
        {"ok": True, "url": ..., "latency_ms": ...} si accessible
        {"ok": False, "url": ..., "error": ...} si injoignable
    """
    url = API_URL.rsplit("/", 1)[0] + "/health"  # /api/airbnb/health
    fallback_url = API_URL  # /api/airbnb/sync en GET

    for target in [url, fallback_url]:
        try:
            start = time.time()
            resp = requests.get(target, timeout=10, headers={"x-api-key": API_KEY} if API_KEY else {})
            latency = int((time.time() - start) * 1000)
            if resp.status_code < 500:
                return {"ok": True, "url": target, "latency_ms": latency, "status": resp.status_code}
        except requests.ConnectionError:
            return {"ok": False, "url": target, "error": "Connexion refusée — le serveur ne répond pas"}
        except requests.Timeout:
            return {"ok": False, "url": target, "error": "Timeout — le serveur met trop de temps à répondre"}
        except Exception as e:
            return {"ok": False, "url": target, "error": str(e)}

    return {"ok": False, "url": API_URL, "error": "API injoignable"}


# ============================================================================
# FONCTIONS PRINCIPALES
# ============================================================================

def send_to_nextjs_api(
    reservations: List[Dict[str, Any]], 
    sync_type: str = "full",
    script_version: str = "2.0.2"
) -> Dict[str, Any]:
    """
    Envoie les réservations à l'API Next.js avec retry automatique.
    
    Args:
        reservations: Liste des réservations au format Airbnb
        sync_type: Type de sync ("ical_watcher", "targeted", "full", "manual")
        script_version: Version du script Python
        
    Returns:
        Dict contenant la réponse de l'API avec les métriques
        
    Raises:
        Exception: Si l'envoi échoue après tous les retries
    """
    
    if not API_KEY:
        raise ValueError("NEXTJS_API_KEY non configurée dans .env")

    if not reservations:
        print("⚠️  Aucune réservation à envoyer")
        return {"success": False, "error": "No reservations to send"}

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    batch_size = 20
    total = len(reservations)
    batches = [reservations[i:i+batch_size] for i in range(0, total, batch_size)]

    print(f"\n☁️  Envoi de {total} réservations à l'API Next.js...")
    print(f"   URL: {API_URL}")
    print(f"   Type: {sync_type}")
    print(f"   Batches: {len(batches)} × {batch_size}")

    total_processed = 0
    total_created = 0
    total_updated = 0
    total_linked = 0
    total_skipped = 0
    total_conflicts = 0
    total_errors = []
    total_dropped_locally = 0  # FIX: compteur des résa droppées AVANT envoi (visibilité)

    for batch_idx, batch in enumerate(batches, 1):
        # L'API attend les noms de champs FRANÇAIS (voyageur, date_arrivee, etc.)
        # cf. ReservationSchema dans app/api/airbnb/sync/route.ts
        sanitized_batch = []
        # Champs requis par le Zod schema (utilisé seulement pour info/debug
        # ci-dessous ; la vérification réelle se fait via les 3 listes dédiées
        # ci-dessus pour distinguer champs numériques vs non-numériques)
        required_fr_fields_all = (
            "id", "listing_id", "statut", "voyageur", "nb_voyageurs",
            "date_arrivee", "date_depart", "nb_nuits", "montant_total", "devise",
        )
        for r in batch:
            r_copy = dict(r)
            # ── Conversion en DZD (local) si devise étrangère ────────────
            # Le service Next.js stocke montant_total/devise tels quels.
            # On convertit donc ici vers DZD en utilisant le currency_ratio.
            devise = (r_copy.get("devise") or r_copy.get("currency_code") or "DZD").upper()
            if devise != "DZD":
                ratio = r_copy.get("currency_ratio", 1.0) or 1.0
                try:
                    montant_orig = float(r_copy.get("montant_total", 0) or 0)
                    # Conversion vers DZD (montant_total) mais on garde la devise source
                    # dans devise (mappé vers currency_code) et le taux pour traçabilité
                    r_copy["montant_total"] = round(montant_orig * ratio, 2)
                    r_copy["currency_ratio"] = ratio
                    r_copy["original_currency_code"] = devise
                    r_copy["original_amount"] = round(montant_orig, 2)
                except (TypeError, ValueError):
                    pass
            # ── Renommer les contacts vers les noms attendus par l'API ──
            if "telephone_voyageur" in r_copy and "guest_phone" not in r_copy:
                raw = r_copy.pop("telephone_voyageur")
                if isinstance(raw, str) and sum(c.isdigit() for c in raw) >= 5:
                    r_copy["guest_phone"] = raw.strip()
                else:
                    r_copy["guest_phone"] = ""
            if "email_voyageur" in r_copy and "guest_email" not in r_copy:
                v = r_copy.pop("email_voyageur")
                r_copy["guest_email"] = v if (v and "@" in v) else ""
            # listing_id doit être un string (Zod: z.string())
            if "listing_id" in r_copy and r_copy["listing_id"] is not None:
                r_copy["listing_id"] = str(r_copy["listing_id"])
            # Champs numériques: s'assurer qu'ils sont des nombres (Zod: z.number())
            for nf in ("nb_voyageurs", "nb_nuits", "montant_total"):
                if nf in r_copy and r_copy[nf] is not None:
                    try:
                        v = r_copy[nf]
                        if isinstance(v, str):
                            v = float(v)
                        r_copy[nf] = int(v) if nf in ("nb_voyageurs", "nb_nuits") else v
                    except (TypeError, ValueError):
                        r_copy[nf] = 0
                elif nf in required_fr_fields_all and r_copy.get(nf) is None:
                    r_copy[nf] = 0
            # Champs optionnels null → retirer
            for field in ("base_price", "cleaning_fee", "service_fee", "taxes",
                          "guest_email", "guest_phone", "guest_nationality", "special_requests"):
                if field in r_copy and r_copy[field] is None:
                    del r_copy[field]

            # ── Vérifier champs requis (FIX 2026-06-30) ──────────────────
            # On distingue désormais 3 catégories pour éviter de traiter
            # une valeur 0 légitime comme une absence de donnée :
            #   1. Champs non-numériques : None/""/absent = vraiment manquant
            #   2. Champs numériques stricts (nb_voyageurs, nb_nuits) :
            #      0 ou absent = vraiment manquant (une résa a toujours
            #      au moins 1 voyageur et 1 nuit)
            #   3. Champs numériques permissifs (montant_total) :
            #      seule l'ABSENCE de clé ou une valeur None compte comme
            #      manquante ; 0 est une valeur valide et conservée.
            rejection_reason = None

            for req in REQUIRED_FR_FIELDS_NON_NUMERIC:
                if req not in r_copy or r_copy[req] in (None, ""):
                    rejection_reason = f"{req}={r_copy.get(req)!r}"
                    break

            if rejection_reason is None:
                for req in REQUIRED_FR_FIELDS_NUMERIC_STRICT:
                    if req not in r_copy or r_copy[req] in (None, 0):
                        rejection_reason = f"{req}={r_copy.get(req)!r}"
                        break

            if rejection_reason is None:
                for req in REQUIRED_FR_FIELDS_NUMERIC_ALLOW_ZERO:
                    if req not in r_copy or r_copy[req] is None:
                        rejection_reason = f"{req}={r_copy.get(req)!r} (clé absente ou None)"
                        break

            if rejection_reason is not None:
                print(
                    f"   ⚠️  Champ FR requis manquant: {rejection_reason} "
                    f"(id={r_copy.get('id', '?')}) → reservation ignorée"
                )
                total_dropped_locally += 1
                r_copy = None
            elif r_copy.get("montant_total") == 0:
                # Pas une erreur — juste une trace explicite pour audit,
                # puisque c'est précisément le cas qui disparaissait avant.
                print(
                    f"   ℹ️  montant_total=0.0 conservé et envoyé "
                    f"(id={r_copy.get('id', '?')}, statut={r_copy.get('statut', '?')!r})"
                )

            if r_copy is not None:
                sanitized_batch.append(r_copy)

        payload = {
            "reservations": sanitized_batch,
            "sync_metadata": {
                "sync_type": sync_type,
                "timestamp": datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ") if hasattr(datetime, 'UTC') else datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "script_version": script_version
            }
        }

        if not sanitized_batch:
            print(f"   ⚠️  Batch {batch_idx}/{len(batches)} entièrement vide après filtrage local — skip envoi")
            continue

        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(
                    API_URL,
                    json=payload,
                    headers=headers,
                    timeout=120
                )

                if response.status_code == 200:
                    result = response.json()
                    metrics = result.get("metrics", {})
                    total_processed += metrics.get("processed", 0)
                    total_created += metrics.get("created", 0)
                    total_updated += metrics.get("updated", 0)
                    total_linked += metrics.get("linked", 0)
                    total_skipped += metrics.get("skipped", 0)
                    total_conflicts += metrics.get("conflicts", 0)
                    if result.get("errors"):
                        total_errors.extend(result["errors"])
                    if batch_idx % 5 == 0 or batch_idx == len(batches):
                        print(f"   ✅ Batch {batch_idx}/{len(batches)} — {total_processed}/{total} traitées")
                    break

                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f": {error_data.get('error', 'Unknown error')}"
                    # Log les détails de validation Zod pour debug
                    if response.status_code == 400:
                        # Toujours afficher le body complet en 400 pour debug
                        print(f"   🔍 Body réponse 400 (batch {batch_idx}): {json.dumps(error_data, ensure_ascii=False)[:800]}")
                        if error_data.get('details'):
                            print(f"   🔍 Détails validation batch {batch_idx}:")
                            for detail in error_data['details'][:5]:
                                path = '.'.join(str(p) for p in detail.get('path', []))
                                print(f"      - {path}: {detail.get('message', '')}")
                        # Afficher la 1ère reservation du batch (sanitisée) pour comparer au schéma
                        if sanitized_batch:
                            sample = {k: v for k, v in sanitized_batch[0].items() if v is not None}
                            print(f"   📋 Payload sanitisée envoyée: {json.dumps(sample, ensure_ascii=False, default=str)[:600]}")
                except Exception as je:
                    error_msg += f": {response.text[:200]}"
                    print(f"   🔍 Body brut 400 (non-JSON): {response.text[:500]}")

                if response.status_code == 429:
                    retry_after = int(response.headers.get('Retry-After', RETRY_DELAY * 2))
                    print(f"   ⚠️  Rate limit - attente {retry_after}s...")
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    last_error = error_msg
                    if attempt < MAX_RETRIES:
                        print(f"   ⚠️  Batch {batch_idx} tentative {attempt}/{MAX_RETRIES}: {error_msg}")
                        time.sleep(RETRY_DELAY * attempt)
                        continue

                raise Exception(error_msg)

            except requests.exceptions.Timeout:
                last_error = f"Timeout après 120s"
                if attempt < MAX_RETRIES:
                    print(f"   ⚠️  Batch {batch_idx} timeout - tentative {attempt}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY * attempt)
                    continue

            except requests.exceptions.ConnectionError as e:
                last_error = f"Connexion: {e}"
                if attempt < MAX_RETRIES:
                    print(f"   ⚠️  Batch {batch_idx} connexion échouée - tentative {attempt}/{MAX_RETRIES}")
                    time.sleep(RETRY_DELAY * attempt)
                    continue

            except Exception as e:
                last_error = str(e)
                if attempt < MAX_RETRIES:
                    print(f"   ⚠️  Batch {batch_idx} erreur - tentative {attempt}/{MAX_RETRIES}: {e}")
                    time.sleep(RETRY_DELAY * attempt)
                    continue
        else:
            print(f"   ❌ Batch {batch_idx} échoué après {MAX_RETRIES} tentatives: {last_error} — SKIP")
            total_errors.append({"batch": batch_idx, "error": last_error})

    result = {
        "success": True,
        "metrics": {
            "processed": total_processed,
            "created": total_created,
            "updated": total_updated,
            "linked": total_linked,
            "skipped": total_skipped,
            "failed": len(total_errors),
            "conflicts": total_conflicts,
            "dropped_locally": total_dropped_locally,  # FIX: visibilité sur le filtrage Python
        },
        "errors": total_errors
    }
    _print_success(result)
    return result


def _print_success(result: Dict[str, Any]):
    """Affiche les résultats de la synchronisation."""
    metrics = result.get("metrics", {})
    errors = result.get("errors", [])
    warnings = result.get("warnings", [])
    
    print(f"\n✅ Synchronisation réussie!")
    print(f"   Batch ID: {result.get('sync_batch_id', 'N/A')}")
    print(f"\n   📊 Métriques:")
    print(f"      • Traitées:  {metrics.get('processed', 0)}")
    print(f"      • Créées:    {metrics.get('created', 0)}")
    print(f"      • Mises à jour: {metrics.get('updated', 0)}")
    print(f"      • Liées (fuzzy): {metrics.get('linked', 0)}")
    print(f"      • Ignorées:  {metrics.get('skipped', 0)}")
    print(f"      • Échouées:  {metrics.get('failed', 0)}")
    print(f"      • Conflits:  {metrics.get('conflicts', 0)}")
    dropped = metrics.get('dropped_locally', 0)
    if dropped:
        print(f"      • Rejetées localement (avant envoi): {dropped}")
    
    if errors:
        print(f"\n   ⚠️  Erreurs ({len(errors)}):")
        for err in errors[:5]:  # Afficher max 5 erreurs
            print(f"      • [{err.get('reservation_id', 'N/A')}] {err.get('error', 'Unknown')}")
        if len(errors) > 5:
            print(f"      ... et {len(errors) - 5} autres")
    
    if warnings:
        print(f"\n   ⚠️  Avertissements ({len(warnings)}):")
        for warn in warnings[:5]:
            print(f"      • [{warn.get('reservation_id', 'N/A')}] {warn.get('warning', 'Unknown')}")
        if len(warnings) > 5:
            print(f"      ... et {len(warnings) - 5} autres")


# ============================================================================
# FONCTIONS DE COMPATIBILITÉ (pour remplacer supabase_client.py)
# ============================================================================

def upsert_reservations(reservations: List[Dict[str, Any]], sync_type: str = "full") -> int:
    """
    Fonction de compatibilité avec l'ancien supabase_client.py
    Envoie les réservations via l'API Next.js.

    Returns:
        Nombre de réservations traitées
    """
    try:
        result = send_to_nextjs_api(reservations, sync_type=sync_type)
        return result.get("metrics", {}).get("processed", 0)
    except Exception as e:
        print(f"❌ Erreur lors de l'envoi: {e}")
        return 0


def upsert_listings(listings: List[Dict[str, Any]]):
    """
    Envoie les URLs iCal collectées par le scraper vers l'API Next.js.
    L'endpoint /api/airbnb/ical-urls upsert dans property_sync_config.
    """
    if not API_KEY:
        print("   ⚠️  NEXTJS_API_KEY non configurée — skip iCal URLs")
        return

    # Filtrer les listings qui ont une URL iCal
    with_ical = [l for l in listings if l.get("ical_url")]
    if not with_ical:
        print("   ℹ️  Aucune URL iCal collectée")
        return

    ical_url_endpoint = API_URL.rsplit("/", 1)[0] + "/ical-urls"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {"listings": with_ical}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                ical_url_endpoint,
                json=payload,
                headers=headers,
                timeout=30,
            )
            if resp.status_code == 200:
                result = resp.json()
                m = result.get("metrics", {})
                print(f"   ✅ iCal URLs: {m.get('created',0)} créées, {m.get('updated',0)} mises à jour, {m.get('skipped',0)} ignorées")
                return
            else:
                print(f"   ⚠️  iCal URLs tentative {attempt}/{MAX_RETRIES}: HTTP {resp.status_code}")
        except requests.Timeout:
            print(f"   ⚠️  iCal URLs tentative {attempt}/{MAX_RETRIES}: timeout")
        except requests.ConnectionError:
            print(f"   ⚠️  iCal URLs tentative {attempt}/{MAX_RETRIES}: connexion refusée")
        except Exception as e:
            print(f"   ⚠️  iCal URLs tentative {attempt}/{MAX_RETRIES}: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)

    print("   ❌ iCal URLs: échec après toutes les tentatives")


def log_sync(sync_type: str, status: str, listings_count: int, 
             reservations_count: int, duration: float):
    """
    Fonction de compatibilité - Le log est maintenant géré par l'API Next.js.
    Cette fonction ne fait rien.
    """
    pass


def notify_cancel_check(listing_id: str) -> bool:
    """
    Notifie Next.js qu'un listing a 0 réservation (possible annulation).
    Next.js vérifie s'il y a des réservations actives dans Supabase
    avec airbnb_confirmation_code et les annule si nécessaire.
    
    Returns:
        True si l'appel a réussi, False sinon
    """
    if not API_KEY:
        print("   ⚠️  NEXTJS_API_KEY non configurée — skip cancel check")
        return False

    cancel_url = API_URL + "/cancel-check"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "listing_id": str(listing_id),
        "sync_metadata": {
            "sync_type": "targeted",
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "script_version": "2.1.0",
        },
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.post(
                cancel_url,
                json=payload,
                headers=headers,
                timeout=TIMEOUT,
            )
            if resp.status_code == 200:
                result = resp.json()
                count = result.get("cancelled_count", 0)
                msg = result.get("message", "")
                if count > 0:
                    print(f"   🔔 {count} réservation(s) annulée(s) par Next.js")
                elif msg:
                    print(f"   ℹ️  Cancel check: {msg}")
                else:
                    print(f"   ℹ️  Cancel check: aucune résa à annuler")
                return True
            else:
                print(f"   ⚠️  Cancel check tentative {attempt}/{MAX_RETRIES}: HTTP {resp.status_code}")
        except requests.Timeout:
            print(f"   ⚠️  Cancel check tentative {attempt}/{MAX_RETRIES}: timeout")
        except requests.ConnectionError:
            print(f"   ⚠️  Cancel check tentative {attempt}/{MAX_RETRIES}: connexion refusée")
        except Exception as e:
            print(f"   ⚠️  Cancel check tentative {attempt}/{MAX_RETRIES}: {e}")

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY * attempt)

    print("   ❌ Cancel check: échec après toutes les tentatives")
    return False


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    # Test avec une réservation fictive
    test_reservation = {
        "id": "PYTEST001",
        "listing_id": "12345678",
        "statut": "Confirmee",
        "voyageur": "Test User",
        "nb_voyageurs": 2,
        "date_arrivee": "2026-06-10",
        "date_depart": "2026-06-15",
        "nb_nuits": 5,
        "montant_total": 50000.0,
        "devise": "DZD",
        "base_price": 45000.0,
        "cleaning_fee": 3000.0,
        "service_fee": 1500.0,
        "taxes": 500.0,
        "guest_email": "test@example.com",
        "guest_phone": "+213555000000",
        "guest_nationality": "FR",
        "special_requests": "Test de l'API client Python"
    }

    test_reservation_zero_amount = {
        "id": "PYTEST002",
        "listing_id": "12345678",
        "statut": "Annulee",
        "voyageur": "Test User Zero",
        "nb_voyageurs": 1,
        "date_arrivee": "2026-07-01",
        "date_depart": "2026-07-02",
        "nb_nuits": 1,
        "montant_total": 0.0,  # FIX (2026-06-30) : doit maintenant être envoyé, pas ignoré
        "devise": "DZD",
    }
    
    try:
        result = send_to_nextjs_api(
            [test_reservation, test_reservation_zero_amount],
            sync_type="manual"
        )
        print(f"\n✅ Test réussi!")
    except Exception as e:
        print(f"\n❌ Test échoué: {e}")
        