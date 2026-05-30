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
    collect_ical_urls,
    _parse_reservation_node,
    SESSION_FILE,
    is_logged_in,
)
from airbnb_api_client import upsert_reservations, check_api_health

# ── Configuration ─────────────────────────────────────────
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")
POLL_INTERVAL = int(os.environ.get("TARGETED_POLL_INTERVAL", "30"))

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
    """Récupère les entrées pending de la sync_queue."""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue"
            f"?status=eq.pending&order=created_at.asc&limit=5",
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


def mark_error(entry_id, error_msg):
    """Marque une entrée en erreur."""
    try:
        requests.patch(
            f"{SUPABASE_URL}/rest/v1/sync_queue?id=eq.{entry_id}",
            json={
                "status": "error",
                "error_message": str(error_msg)[:500],
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
    Réutilise get_reservations() du scraper principal puis filtre.
    """
    print(f"   Scraping des reservations pour listing {target_listing_id}...")

    # get_reservations() récupère TOUTES les réservations via GraphQL
    all_reservations = get_reservations(page)

    # Filtrer par listing_id cible
    targeted = [
        r for r in all_reservations
        if r.get("listing_id") == target_listing_id
    ]

    print(f"   {len(targeted)} reservations trouvees pour {target_listing_id}")
    return targeted


def process_entry(page, entry):
    """Traite une entrée de la sync_queue."""
    entry_id = entry["id"]
    listing_id = entry["listing_id"]

    print(f"\n{'='*50}")
    print(f"   Queue #{entry_id} — listing {listing_id}")
    print(f"   Raison : {entry.get('reason', 'unknown')}")
    print(f"{'='*50}")

    mark_processing(entry_id)

    try:
        # Scraper les réservations
        reservations = scrape_listing(page, listing_id)

        if not reservations:
            print(f"   Aucune reservation — marquage done")
            mark_done(entry_id)
            return

        # Envoyer à l'API Next.js
        count = upsert_reservations(reservations, sync_type="targeted")
        print(f"   {count} reservations envoyees a l'API")

        # Refresh l'URL iCal pour ce listing
        try:
            ical_urls = collect_ical_urls(page, [listing_id])
            if ical_urls:
                print(f"   URL iCal rafraichie")
        except Exception as e:
            print(f"   Warning: refresh iCal echoue ({e})")

        mark_done(entry_id)
        print(f"   Termine avec succes")

    except Exception as e:
        print(f"   ERREUR: {e}")
        mark_error(entry_id, str(e))


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 55)
    print("   Targeted Scraper — Scraping ciblé sur demande")
    print(f"   Poll interval : {POLL_INTERVAL}s")
    print(f"   Moteur        : {'CloakBrowser' if USE_CLOAKBROWSER else 'Playwright'}")
    print(f"   Headless      : {HEADLESS}")
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
            else:
                login(page)

            # Traiter chaque entrée
            for entry in entries:
                process_entry(page, entry)

            context.close()

        except Exception as e:
            print(f"   ERREUR session: {e}")
            # Marquer les entrées restantes en erreur
            for entry in entries:
                entry_id = entry["id"]
                try:
                    mark_error(entry_id, f"Session error: {e}")
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
