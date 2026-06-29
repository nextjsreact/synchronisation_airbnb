"""
targeted_scraper.py — Scraping ciblé sur demande
=================================================
Lit la sync_queue (status=pending), scrape les réservations
d'un listing spécifique via CloakBrowser, envoie à l'API Next.js.

Réutilise le flux d'auth complet de airbnb_scraper.py (CloakBrowser + TOTP).

Dépendances :
    pip install cloakbrowser pyotp requests python-dotenv

Usage :
    python targeted_scraper.py
"""

import os
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

# Forcer UTF-8 sur Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# ── Imports du scraper principal ──────────────────────────
from airbnb_scraper import (
    login,
    get_reservations,
    scrape_fallback,
    collect_ical_urls,
    enrich_with_contacts,
    _parse_reservation_node,
    SESSION_FILE,
    is_logged_in,
)
from airbnb_api_client import upsert_reservations, check_api_health, notify_cancel_check
from currency_converter import enrich_with_currency_ratio

# ── Configuration ─────────────────────────────────────────
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")
POLL_INTERVAL = int(os.environ.get("TARGETED_POLL_INTERVAL", "30"))
COLLECT_CONTACTS = os.environ.get("COLLECT_CONTACTS", "false").lower() == "true"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ── CloakBrowser ──────────────────────────────────────────
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False


# ============================================================
# QUEUE MANAGEMENT
# ============================================================

def get_pending_entries():
    """Récupère les entrées pending de la sync_queue, en priorisant les erreurs à réessayer."""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue"
            f"?status=eq.pending&order=retry_count.desc,created_at.asc&limit=5",
            headers=HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"   Erreur lecture queue: {e}")
        return []


def mark_processing(entry_id):
    """Marque une entrée comme en cours de traitement."""
    try:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/sync_queue?id=eq.{entry_id}",
            json={
                "status": "processing",
                "processed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            headers=HEADERS,
            timeout=15,
        )
    except Exception:
        pass


def mark_done(entry_id):
    """Marque une entrée comme terminée."""
    try:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/sync_queue?id=eq.{entry_id}",
            json={
                "status": "done",
                "processed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            headers=HEADERS,
            timeout=15,
        )
    except Exception:
        pass


def mark_error(entry_id, error_msg, retry_count=0):
    """Marque une entrée en erreur avec compteur de tentatives."""
    try:
        # Si moins de 3 tentatives, marquer pour retry
        if retry_count < 3:
            status = "pending"  # Réessayer
            print(f"   ⚠️  Erreur (tentative {retry_count + 1}/3) - Réessai dans 5 minutes")
        else:
            status = "error"  # Abandonner après 3 tentatives
            print(f"   ❌ Échec définitif après {retry_count} tentatives")
        
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/sync_queue?id=eq.{entry_id}",
            json={
                "status": status,
                "error_message": str(error_msg)[:500],
                "retry_count": retry_count + 1,
                "processed_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
            headers=HEADERS,
            timeout=15,
        )
    except Exception:
        pass


# ============================================================
# SCRAPING CIBLÉ
# ============================================================

def scrape_listing(page, target_listing_id):
    """
    Scrape les réservations d'un listing spécifique.
    OPTIMISÉ: Scrape uniquement /upcoming et filtre par listing_id à la volée.
    """
    target_listing_id_str = str(target_listing_id)
    print(f"   Scraping des reservations pour listing {target_listing_id}...")
    print(f"   🚀 Mode optimisé : /upcoming uniquement, filtre listing_id à la volée")

    # Essayer l'API GraphQL d'abord (rapide : 2-3 min)
    all_reservations = get_reservations(page)
    if all_reservations:
        targeted = [
            r for r in all_reservations
            if str(r.get("listing_id", "")) == target_listing_id_str
        ]
        if targeted:
            print(f"   ✅ {len(targeted)} reservations trouvees via GraphQL")
            return targeted
        print(f"   ⚠️  GraphQL OK mais listing absent, fallback...")

    # Fallback : scrape /upcoming uniquement, filtre à la volée
    print(f"   ⏳ Scraping /upcoming avec filtre listing_id à la volée...")
    targeted = scrape_fallback_upcoming_only(page, target_listing_id_str)

    print(f"   ✅ {len(targeted)} reservations trouvees pour {target_listing_id}")
    return targeted


def scrape_listing_with_retry(page, listing_id, retry_count):
    """
    Scrape avec gestion d'erreurs et retry.
    Retourne None en cas d'erreur réseau (pour retry), [] si vide, ou la liste des réservations.
    """
    import time
    
    max_retries = 3
    backoff_delays = [5, 15, 30]  # Délais croissants entre les tentatives
    
    for attempt in range(max_retries):
        try:
            print(f"   🔄 Tentative de scraping {attempt + 1}/{max_retries}...")
            
            # Scraper avec timeout augmenté
            reservations = scrape_listing(page, listing_id)
            
            # Succès !
            print(f"   ✅ Scraping réussi !")
            return reservations
            
        except Exception as e:
            error_msg = str(e)
            
            # Vérifier si c'est une erreur réseau
            if "Timeout" in error_msg or "NetworkError" in error_msg or "Failed to resolve" in error_msg:
                print(f"   ⚠️  Erreur réseau (tentative {attempt + 1}/{max_retries}): {error_msg[:100]}")
                
                if attempt < max_retries - 1:
                    delay = backoff_delays[attempt]
                    print(f"   ⏳ Attente de {delay}s avant réessai...")
                    time.sleep(delay)
                else:
                    print(f"   ❌ Échec après {max_retries} tentatives")
                    return None  # Erreur réseau - réessayer plus tard
            else:
                # Autre erreur (pas réseau) - propager
                print(f"   ❌ Erreur non-réseau: {error_msg[:100]}")
                raise
    
    # Si on arrive ici, toutes les tentatives ont échoué
    return None


# Cache pour les loft_id (listing_id -> loft_id) pour eviter de requeter Supabase a chaque reservation
_LOFT_ID_CACHE = {}


def _resolve_loft_id(listing_id):
    """Resout le loft_id Supabase depuis un airbnb_listing_id (avec cache)."""
    lid = str(listing_id)
    if lid in _LOFT_ID_CACHE:
        return _LOFT_ID_CACHE[lid]
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/lofts?select=id,airbnb_listing_id"
            f"&airbnb_listing_id=eq.{lid}&limit=1",
            headers=HEADERS,
            timeout=10,
        )
        rows = resp.json()
        if rows:
            _LOFT_ID_CACHE[lid] = rows[0]["id"]
            return rows[0]["id"]
    except Exception as e:
        print(f"   ⚠️  _resolve_loft_id({lid}): {e}")
    return None


def scrape_fallback_upcoming_only(page, target_listing_id):
    """
    Fallback optimisé : scrape /upcoming puis /all si besoin.
    """
    from airbnb_scraper import _parse_reservation_node

    target_listing_id_str = str(target_listing_id)
    target_reservations = []
    seen_ids = set()

    def scrape_one_page(tab_url, tab_name):
        nonlocal target_reservations
        page_responses = []

        def handle_response(response):
            url = response.url
            if response.status != 200:
                return
            if "api/v2/reservations" in url:
                try:
                    data = response.json()
                    if isinstance(data, dict) and "reservations" in data:
                        page_responses.append({
                            "url": url,
                            "reservations": data["reservations"],
                            "total_count": data.get("metadata", {}).get("total_count", 0),
                        })
                except Exception:
                    pass

        page.on("response", handle_response)
        try:
            print(f"   📄 Page : {tab_name}...")
            page_responses.clear()
            page.goto(tab_url, wait_until="networkidle", timeout=60000)
            page.wait_for_timeout(3000)

            for page_num in range(200):
                new_in_page = 0
                total = page_responses[-1]["total_count"] if page_responses else 0
                for resp in page_responses:
                    for r in resp["reservations"]:
                        parsed = _parse_reservation_node(r)
                        rid = parsed.get("id")
                        if not rid or rid in seen_ids:
                            continue
                        seen_ids.add(rid)
                        if str(parsed.get("listing_id", "")) == target_listing_id_str:
                            target_reservations.append(parsed)
                            new_in_page += 1
                print(f"      Page {page_num+1}: +{new_in_page} (total:{total}, cumul:{len(target_reservations)})")
                page_responses.clear()

                next_btn = None
                for selector in [
                    'button:has-text("Suivant")', 'button:has-text("Next")',
                    '[aria-label="Suivant"]', '[aria-label="Next"]',
                ]:
                    try:
                        btn = page.locator(selector)
                        if btn.count() > 0 and btn.first.is_visible() and btn.first.is_enabled():
                            next_btn = btn.first
                            break
                    except Exception:
                        continue

                if not next_btn:
                    break
                next_btn.click()
                page.wait_for_timeout(3000)
        finally:
            page.remove_listener("response", handle_response)

    scrape_one_page("https://www.airbnb.com/hosting/reservations/upcoming", "upcoming")

    if not target_reservations:
        scrape_one_page("https://www.airbnb.com/hosting/reservations/all", "all")

    return target_reservations


def process_entry(page, entry):
    """Traite une entrée de la sync_queue avec retry automatique."""
    entry_id = entry["id"]
    listing_id = entry["listing_id"]
    retry_count = entry.get("retry_count", 0)

    print(f"\n{'='*50}")
    print(f"   Queue #{entry_id} — listing {listing_id}")
    print(f"   Raison : {entry.get('reason', 'unknown')}")
    if retry_count > 0:
        print(f"   🔄 Tentative : {retry_count + 1}/3")
    print(f"{'='*50}")

    mark_processing(entry_id)

    try:
        # Scraper les réservations avec retry
        reservations = scrape_listing_with_retry(page, listing_id, retry_count)

        if reservations is None:
            # Erreur réseau - ne pas marquer done, réessayer plus tard
            error_msg = "Erreur réseau (timeout ou connexion)"
            print(f"   ⚠️  {error_msg}")
            mark_error(entry_id, error_msg, retry_count)
            return

        if not reservations:
            print(f"   ✅ 0 reservation trouvee pour {listing_id}")
            # Notifier Next.js pour vérifier les annulations
            try:
                print(f"   📞 notify_cancel_check({listing_id})...")
                notify_cancel_check(listing_id)
            except Exception as e:
                print(f"   ⚠️  Erreur cancel check: {e}")
            print(f"   → statut 'done'")
            mark_done(entry_id)
            return

        # Enrichir avec les coordonnées (si COLLECT_CONTACTS=true)
        if COLLECT_CONTACTS:
            print(f"   📞 Collecte des coordonnées activée...")
            reservations = enrich_with_contacts(page, reservations, collect_contacts=True)
        else:
            # Ajouter des champs vides (seront renommés guest_phone/guest_email plus bas)
            for r in reservations:
                r["telephone_voyageur"] = ""
                r["email_voyageur"] = ""

        # Enrichir avec les taux de conversion
        print(f"   💱 Conversion des devises...")
        reservations = enrich_with_currency_ratio(reservations)

        # Convertir montant_total en DZD (local) en utilisant le currency_ratio
        # Le service Next.js stocke montant_total tel quel, donc on fait la conversion ici
        for r in reservations:
            devise = (r.get("devise") or r.get("currency_code") or "DZD").upper()
            if devise != "DZD":
                ratio = r.get("currency_ratio", 1.0) or 1.0
                try:
                    montant_orig = float(r.get("montant_total", 0) or 0)
                    # Préserver la trace de la devise source pour audit/transparence
                    r["original_currency_code"] = devise
                    r["original_amount"] = round(montant_orig, 2)
                    # Conversion vers DZD
                    r["montant_total"] = round(montant_orig * ratio, 2)
                    r["currency_ratio"] = ratio
                    r["devise"] = "DZD"
                except (TypeError, ValueError):
                    pass

        # Renommer les champs pour matcher l'API (guest_phone/guest_email)
        # + garder les noms FR pour id
        for r in reservations:
            # S'assurer que id existe (c'est ce que l'API utilise comme identifiant unique)
            if "id" not in r and "airbnb_confirmation_code" in r:
                r["id"] = r["airbnb_confirmation_code"]
            # Renommer les coordonnées vers les noms attendus par l'API
            if "telephone_voyageur" in r and "guest_phone" not in r:
                raw = r.pop("telephone_voyageur")
                # Airbnb renvoie parfois un booléen (true/false) au lieu du numero
                # On ne garde que les chaines contenant au moins 5 chiffres
                if isinstance(raw, str) and sum(c.isdigit() for c in raw) >= 5:
                    r["guest_phone"] = raw.strip()
                else:
                    r["guest_phone"] = ""
            if "email_voyageur" in r and "guest_email" not in r:
                # L'API attend un email valide ou "" (z.string().email().or(z.literal('')))
                v = r.pop("email_voyageur")
                r["guest_email"] = v if (v and "@" in v) else ""
            # Resoudre loft_id optionnel (info complémentaire, pas dans le schéma)
            if "loft_id" not in r and "listing_id" in r:
                r["loft_id"] = _resolve_loft_id(r["listing_id"])

        # Envoyer à l'API Next.js
        count = upsert_reservations(reservations, sync_type="targeted")
        print(f"   {count} reservations envoyees a l'API")

        # Refresh iCal désactivé : les URLs sont déjà collectees par le full scraper
        # et le rafraichissement via CloakBrowser echoue / prend du temps
        # try:
        #     ical_urls = collect_ical_urls(page, [listing_id])
        #     if ical_urls:
        #         print(f"   URL iCal rafraichie")
        # except Exception as e:
        #     print(f"   Warning: refresh iCal echoue ({e})")

        mark_done(entry_id)
        print(f"   ✅ Traitement terminé avec succès")

    except Exception as e:
        error_msg = str(e)
        print(f"   ❌ ERREUR: {error_msg[:200]}")
        
        # Vérifier si c'est une erreur réseau
        if "Timeout" in error_msg or "NetworkError" in error_msg or "Failed to resolve" in error_msg or "Erreur réseau" in error_msg:
            print(f"   🔄 Erreur réseau détectée - réessai automatique prévu")
            mark_error(entry_id, error_msg, retry_count)
        else:
            # Autre erreur - marquer en erreur définitive
            print(f"   ⛔ Erreur non-réseau - marquage en erreur")
            mark_error(entry_id, error_msg, 999)  # 999 = ne pas réessayer


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("   Targeted Scraper — Scraping ciblé sur demande")
    print(f"   Poll interval : {POLL_INTERVAL}s")
    print(f"   Moteur        : {'CloakBrowser' if USE_CLOAKBROWSER else 'Playwright'}")
    print(f"   Headless      : {HEADLESS}")
    print(f"   Coordonnées   : {'Activé ✅' if COLLECT_CONTACTS else 'Désactivé'}")
    print(f"   Mode          : OPTIMISÉ (upcoming uniquement) 🚀")
    print("=" * 55)

    # Vérifier l'API Next.js
    print("\nVerification de l'API Next.js...")
    health = check_api_health()
    if health["ok"]:
        print(f"   API accessible ({health['latency_ms']}ms)")
    else:
        print(f"   ATTENTION: API inaccessible — {health['error']}")
        print(f"   Le scraper fonctionnera mais n'enverra pas les donnees")

    cycle = 0
    while True:
        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")

        # Lire la queue
        entries = get_pending_entries()

        if not entries:
            print(f"[{now}] Cycle {cycle} — queue vide, attente {POLL_INTERVAL}s...")
            time.sleep(POLL_INTERVAL)
            continue

        print(f"\n[{now}] Cycle {cycle} — {len(entries)} entree(s) en attente")

        # Lancer le navigateur une seule fois pour toutes les entrées
        browser = None
        pw = None
        page = None

        try:
            if USE_CLOAKBROWSER:
                print("   Lancement CloakBrowser...")
                _launch_opts = dict(
                    headless=HEADLESS,
                    args=["--no-sandbox"],
                    humanize=True,
                    human_preset="careful",
                    locale="fr-FR",
                )
                if PROXY_URL:
                    _launch_opts["proxy"] = {"server": PROXY_URL}
                browser = cloak_launch(**_launch_opts)
            else:
                from playwright.sync_api import sync_playwright
                pw = sync_playwright().start()
                _launch_opts = dict(
                    headless=HEADLESS,
                    args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
                )
                if PROXY_URL:
                    _launch_opts["proxy"] = {"server": PROXY_URL}
                browser = pw.chromium.launch(**_launch_opts)

            # Charger la session sauvegardée si disponible
            ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
            if os.path.exists(SESSION_FILE):
                print(f"   💾 Session trouvée : chargement...")
                ctx_opts["storage_state"] = SESSION_FILE
            context = browser.new_context(**ctx_opts)
            page = context.new_page()

            # Login — réutiliser la session si valide
            if os.path.exists(SESSION_FILE):
                if is_logged_in(page):
                    print("   ✅ Session valide — connexion automatique !")
                else:
                    print("   ⚠️  Session expirée — reconnexion...")
                    login(page)
                    # Sauvegarder la session après login réussi
                    try:
                        page.context.storage_state(path=SESSION_FILE)
                        print(f"   💾 Session sauvegardée après reconnexion")
                    except Exception as e:
                        print(f"   ⚠️  Échec sauvegarde session : {e}")
            else:
                login(page)
                try:
                    page.context.storage_state(path=SESSION_FILE)
                    print(f"   💾 Session sauvegardée après login")
                except Exception as e:
                    print(f"   ⚠️  Échec sauvegarde session : {e}")

            # Traiter chaque entrée
            for entry in entries:
                process_entry(page, entry)

            context.close()

        except Exception as e:
            print(f"   ERREUR session: {e}")
            # Marquer les entrées restantes en erreur avec leur retry_count réel
            for entry in entries:
                entry_id = entry["id"]
                retry = entry.get("retry_count", 0) or 0
                try:
                    mark_error(entry_id, f"Session error: {e}", retry)
                except Exception:
                    pass

        finally:
            if browser:
                try:
                    browser.close()
                except Exception:
                    pass
            if pw:
                try:
                    pw.stop()
                except Exception:
                    pass

        print(f"\n   Cycle termine. Attente {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
