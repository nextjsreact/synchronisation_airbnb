"""
Script de debug pour targeted_scraper
======================================
Teste les deux méthodes (GraphQL et fallback) et compare les résultats
"""

import os
import sys
import time
from datetime import datetime

# Forcer UTF-8 sur Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from airbnb_scraper import (
    login,
    get_reservations,
    scrape_fallback,
    SESSION_FILE,
    is_logged_in,
)

# Configuration
HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")

# CloakBrowser
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False


def main():
    print("=" * 70)
    print("🔍 DEBUG TARGETED SCRAPER")
    print("=" * 70)
    print(f"\nMoteur    : {'CloakBrowser' if USE_CLOAKBROWSER else 'Playwright'}")
    print(f"Headless  : {HEADLESS}")
    print(f"Session   : {SESSION_FILE}")
    print()

    # Lancer le navigateur
    browser = None
    pw = None
    page = None

    try:
        if USE_CLOAKBROWSER:
            print("🚀 Lancement CloakBrowser...")
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

        # Charger la session
        ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
        if os.path.exists(SESSION_FILE):
            print(f"💾 Session trouvée : chargement...")
            ctx_opts["storage_state"] = SESSION_FILE
        context = browser.new_context(**ctx_opts)
        page = context.new_page()

        # Login
        if os.path.exists(SESSION_FILE):
            if is_logged_in(page):
                print("✅ Session valide — connexion automatique !\n")
            else:
                print("⚠️  Session expirée — reconnexion...\n")
                login(page)
        else:
            login(page)

        # Test 1 : API GraphQL
        print("\n" + "=" * 70)
        print("TEST 1 : API GraphQL")
        print("=" * 70)
        start_time = time.time()
        
        try:
            gql_reservations = get_reservations(page)
            gql_duration = time.time() - start_time
            
            print(f"\n📊 Résultats API GraphQL :")
            print(f"   Réservations trouvées : {len(gql_reservations)}")
            print(f"   Durée : {gql_duration:.1f}s")
            
            if gql_reservations:
                # Afficher les 5 dernières
                print(f"\n   📋 5 dernières réservations :")
                for i, r in enumerate(gql_reservations[:5], 1):
                    print(f"      [{i}] {r.get('confirmation_code', 'N/A')} - {r.get('guest_name', 'N/A')} - {r.get('check_in', 'N/A')}")
                
                # Compter par date de création
                today = datetime.now().date().isoformat()
                today_count = sum(1 for r in gql_reservations if r.get('created_at', '').startswith(today))
                print(f"\n   📅 Réservations créées aujourd'hui : {today_count}")
            else:
                print(f"\n   ⚠️  AUCUNE RÉSERVATION TROUVÉE")
                print(f"   ➤ L'API GraphQL semble cassée ou vide")
        
        except Exception as e:
            print(f"\n   ❌ ERREUR API GraphQL : {e}")
            gql_reservations = []

        # Test 2 : Fallback Pagination
        print("\n" + "=" * 70)
        print("TEST 2 : Fallback Pagination")
        print("=" * 70)
        print("⚠️  ATTENTION : Cette méthode prend 30-40 minutes pour tout scraper")
        print("   Pour ce test, on va scraper seulement la première page de chaque catégorie\n")
        
        start_time = time.time()
        
        try:
            # Version limitée du fallback pour le test (1 page par catégorie)
            fallback_reservations = scrape_fallback_limited(page)
            fallback_duration = time.time() - start_time
            
            print(f"\n📊 Résultats Fallback (limité) :")
            print(f"   Réservations trouvées : {len(fallback_reservations)}")
            print(f"   Durée : {fallback_duration:.1f}s")
            
            if fallback_reservations:
                # Afficher les 5 dernières
                print(f"\n   📋 5 dernières réservations :")
                for i, r in enumerate(fallback_reservations[:5], 1):
                    print(f"      [{i}] {r.get('confirmation_code', 'N/A')} - {r.get('guest_name', 'N/A')} - {r.get('check_in', 'N/A')}")
                
                # Compter par date de création
                today = datetime.now().date().isoformat()
                today_count = sum(1 for r in fallback_reservations if r.get('created_at', '').startswith(today))
                print(f"\n   📅 Réservations créées aujourd'hui : {today_count}")
            else:
                print(f"\n   ⚠️  AUCUNE RÉSERVATION TROUVÉE")
        
        except Exception as e:
            print(f"\n   ❌ ERREUR Fallback : {e}")
            fallback_reservations = []

        # Comparaison
        print("\n" + "=" * 70)
        print("📊 COMPARAISON")
        print("=" * 70)
        print(f"\nAPI GraphQL      : {len(gql_reservations)} réservations")
        print(f"Fallback (limité): {len(fallback_reservations)} réservations")
        
        if len(gql_reservations) == 0 and len(fallback_reservations) > 0:
            print(f"\n⚠️  DIAGNOSTIC :")
            print(f"   ➤ L'API GraphQL est CASSÉE (retourne 0 réservations)")
            print(f"   ➤ Le Fallback FONCTIONNE (retourne {len(fallback_reservations)} réservations)")
            print(f"\n✅ SOLUTION :")
            print(f"   ➤ Modifier targeted_scraper.py pour utiliser scrape_fallback()")
            print(f"   ➤ Ou utiliser un scraping complet périodique au lieu de ciblé")
        elif len(gql_reservations) > 0:
            print(f"\n✅ L'API GraphQL fonctionne correctement")
        else:
            print(f"\n❌ Les deux méthodes échouent — problème de connexion ?")

        context.close()

    except Exception as e:
        print(f"\n❌ ERREUR GLOBALE : {e}")
        import traceback
        traceback.print_exc()

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

    print("\n" + "=" * 70)
    print("✅ DEBUG TERMINÉ")
    print("=" * 70)


def scrape_fallback_limited(page):
    """Version limitée du fallback pour le test (1 page par catégorie)."""
    from airbnb_scraper import _parse_reservation_node
    
    print("🔄 Fallback limité : 1 page par catégorie...")

    all_reservations = []
    seen_ids = set()
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

    pages_to_scan = [
        ("upcoming", "https://www.airbnb.com/hosting/reservations/upcoming"),
        ("completed", "https://www.airbnb.com/hosting/reservations/completed"),
        ("all", "https://www.airbnb.com/hosting/reservations/all"),
    ]

    for page_name, page_url in pages_to_scan:
        print(f"\n   📄 Page : {page_name}...")
        page_responses.clear()
        page.goto(page_url)
        page.wait_for_timeout(5000)

        # Traiter seulement la première page
        new_in_page = 0
        for resp in page_responses:
            for r in resp["reservations"]:
                parsed = _parse_reservation_node(r)
                if parsed["id"] and parsed["id"] not in seen_ids:
                    all_reservations.append(parsed)
                    seen_ids.add(parsed["id"])
                    new_in_page += 1
        
        total = page_responses[-1]["total_count"] if page_responses else 0
        print(f"      Page 1: +{new_in_page} (total cat: {total})")

    page.remove_listener("response", handle_response)
    print(f"\n   ↳ {len(all_reservations)} réservations uniques (fallback limité)")
    return all_reservations


if __name__ == "__main__":
    main()
