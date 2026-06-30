"""
periodic_scraper.py — Scraping périodique (toutes les 6h)
=========================================================
Scrape TOUTES les réservations Airbnb via /all et envoie à l'API Next.js.
Détecte les annulations, modifications guest_count/montant non capturées par iCal.
"""
import os
import sys
import time
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

from airbnb_scraper import (
    login, _parse_reservation_node, SESSION_FILE, is_logged_in,
)
from airbnb_api_client import upsert_reservations, check_api_health, notify_cancel_check
from currency_converter import enrich_with_currency_ratio

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
HEADLESS = os.environ.get("HEADLESS", "true").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")
INTERVAL = int(os.environ.get("PERIODIC_INTERVAL", "21600"))
COLLECT_CONTACTS = os.environ.get("COLLECT_CONTACTS", "false").lower() == "true"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False


def get_active_listing_ids():
    """Récupère les listing_ids qui ont des réservations actives dans Supabase."""
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/lofts"
            f"?select=airbnb_listing_id"
            f"&airbnb_listing_id.not.isnull"
            f"&airbnb_listing_id.neq.",
            headers=HEADERS,
            timeout=15,
        )
        rows = resp.json()
        return [row["airbnb_listing_id"] for row in rows if row.get("airbnb_listing_id")]
    except Exception as e:
        print(f"   ⚠️ get_active_listing_ids: {e}")
        return []


def scrape_all_reservations(page):
    """Scrape /all (toutes les résas, tous statuts)."""
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
    try:
        print(f"   📄 Scraping /all...")
        page_responses.clear()
        page.goto("https://www.airbnb.com/hosting/reservations/all",
                   wait_until="networkidle", timeout=60000)
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
                    all_reservations.append(parsed)
                    new_in_page += 1
            print(f"      Page {page_num+1}: +{new_in_page} (total:{total}, cumul:{len(all_reservations)})")
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

    return all_reservations


def main():
    print("=" * 55)
    print("   Periodic Scraper — Scraping toutes les 6h")
    print(f"   Intervalle     : {INTERVAL}s ({INTERVAL//3600}h)")
    print(f"   Moteur        : {'CloakBrowser' if USE_CLOAKBROWSER else 'Playwright'}")
    print(f"   Headless      : {HEADLESS}")
    print(f"   Coordonnées   : {'Activé ✅' if COLLECT_CONTACTS else 'Désactivé'}")
    print(f"   Source        : /all (toutes les réservations)")
    print("=" * 55)

    health = check_api_health()
    if health["ok"]:
        print(f"   API accessible ({health['latency_ms']}ms)")
    else:
        print(f"   ATTENTION: API inaccessible — {health['error']}")

    cycle = 0
    while True:
        cycle += 1
        now = datetime.now().strftime("%H:%M:%S")
        print(f"\n[{now}] Cycle {cycle} — démarrage du scrape périodique")

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

            ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
            if os.path.exists(SESSION_FILE):
                print(f"   💾 Session trouvée : chargement...")
                ctx_opts["storage_state"] = SESSION_FILE
            context = browser.new_context(**ctx_opts)
            page = context.new_page()

            if os.path.exists(SESSION_FILE):
                if is_logged_in(page):
                    print("   ✅ Session valide — connexion automatique !")
                else:
                    print("   ⚠️  Session expirée — reconnexion...")
                    login(page)
            else:
                login(page)

            # Récupérer les listing_ids actifs avant le scrape
            all_listing_ids = get_active_listing_ids()
            print(f"   📋 {len(all_listing_ids)} listing(s) actif(s) en base")

            # Scraper toutes les réservations
            all_reservations = scrape_all_reservations(page)
            print(f"   ✅ {len(all_reservations)} réservation(s) trouvée(s)")

            if not all_reservations:
                print(f"   ⚠️  Aucune réservation trouvée — notification annulations pour tous les listings")
                for lid in all_listing_ids:
                    try:
                        notify_cancel_check(lid)
                    except Exception as e:
                        print(f"   ⚠️  cancel-check {lid}: {e}")
                print(f"   → Prochain cycle dans {INTERVAL//3600}h")
                time.sleep(INTERVAL)
                continue

            # Enrichir contacts
            if COLLECT_CONTACTS:
                print(f"   📞 Collecte des coordonnées activée...")
                from airbnb_scraper import enrich_with_contacts
                all_reservations = enrich_with_contacts(page, all_reservations, collect_contacts=True)
            else:
                for r in all_reservations:
                    r["telephone_voyageur"] = ""
                    r["email_voyageur"] = ""

            # Enrichir devises
            print(f"   💱 Conversion des devises...")
            all_reservations = enrich_with_currency_ratio(all_reservations)

            # Conversion DZD
            for r in all_reservations:
                devise = (r.get("devise") or r.get("currency_code") or "DZD").upper()
                if devise != "DZD":
                    ratio = r.get("currency_ratio", 1.0) or 1.0
                    try:
                        montant_orig = float(r.get("montant_total", 0) or 0)
                        r["original_currency_code"] = devise
                        r["original_amount"] = round(montant_orig, 2)
                        r["montant_total"] = round(montant_orig * ratio, 2)
                        r["currency_ratio"] = ratio
                        r["devise"] = "DZD"
                    except (TypeError, ValueError):
                        pass

            # Renommer champs
            for r in all_reservations:
                if "id" not in r and "airbnb_confirmation_code" in r:
                    r["id"] = r["airbnb_confirmation_code"]
                if "telephone_voyageur" in r and "guest_phone" not in r:
                    raw = r.pop("telephone_voyageur")
                    if isinstance(raw, str) and sum(c.isdigit() for c in raw) >= 5:
                        r["guest_phone"] = raw.strip()
                    else:
                        r["guest_phone"] = ""
                if "email_voyageur" in r and "guest_email" not in r:
                    v = r.pop("email_voyageur")
                    r["guest_email"] = v if (v and "@" in v) else ""

            # Envoyer à l'API
            count = upsert_reservations(all_reservations, sync_type="periodic")
            print(f"   {count} réservation(s) envoyée(s)")

            # Détection annulations : listings actifs non présents dans les résas scrapées
            scraped_listing_ids = set(str(r.get("listing_id", "")) for r in all_reservations if r.get("listing_id"))
            for lid in all_listing_ids:
                if str(lid) not in scraped_listing_ids:
                    print(f"   🔍 Listing {lid} absent des résultats — vérification annulation...")
                    try:
                        notify_cancel_check(lid)
                    except Exception as e:
                        print(f"   ⚠️  cancel-check {lid}: {e}")

            context.close()

        except Exception as e:
            print(f"   ERREUR session: {e}")

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

        next_cycle = datetime.now().strftime("%H:%M:%S")
        print(f"   ✅ Cycle {cycle} terminé à {next_cycle}")
        print(f"   💤 Prochain cycle dans {INTERVAL//3600}h ({INTERVAL}s)")
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
