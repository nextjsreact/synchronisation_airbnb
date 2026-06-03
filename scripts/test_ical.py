"""
test_ical.py - Test rapide de collecte iCal sur 1 annonce
Usage : docker compose run --rm -e ICAL_TEST=true airbnb-scraper python test_ical.py
"""
import os
import sys
import re
import time

sys.stdout.reconfigure(encoding='utf-8')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "airbnb_session.json")
HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")

def main():
    # Charger un listing_id depuis le JSON
    import json
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "reservations_airbnb.json")
    if not os.path.exists(json_path):
        print("❌ Fichier reservations_airbnb.json introuvable")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Prendre le premier listing_id unique
    listing_ids = list(set(r.get("listing_id") for r in data if r.get("listing_id")))[:3]
    print(f"📋 Test iCal sur {len(listing_ids)} annonces : {listing_ids}")

    # Lancer le navigateur
    try:
        from cloakbrowser import cloak_launch
        USE_CLOAKBROWSER = True
        print("   Moteur: CloakBrowser")
    except ImportError:
        from playwright.sync_api import sync_playwright
        USE_CLOAKBROWSER = False
        print("   Moteur: Playwright standard")

    if USE_CLOAKBROWSER:
        launch_args = {"headless": False, "humanize": True}
        if PROXY_URL:
            launch_args["proxy"] = {"server": PROXY_URL}
        browser = cloak_launch(**launch_args)
    else:
        pw = sync_playwright().start()
        launch_args = {"headless": True}
        if PROXY_URL:
            launch_args["proxy"] = {"server": PROXY_URL}
        browser = pw.chromium.launch(**launch_args)

    # Charger la session
    context_opts = {"viewport": {"width": 1280, "height": 800}}
    if os.path.exists(SESSION_FILE):
        context_opts["storage_state"] = SESSION_FILE
        print(f"   Session chargée: {SESSION_FILE}")

    context = browser.new_context(**context_opts)
    page = context.new_page()

    # Tester chaque listing
    for listing_id in listing_ids:
        print(f"\n{'='*60}")
        print(f"🔍 Test listing: {listing_id}")

        # Essayer plusieurs URLs possibles pour l'export iCal
        urls_to_try = [
            f"https://www.airbnb.com/hosting/listings/{listing_id}/availability",
            f"https://www.airbnb.com/hosting/listings/{listing_id}/calendar/export",
        ]

        for url in urls_to_try:
            print(f"\n   URL: {url}")
            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)
                try:
                    page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    page.wait_for_timeout(3000)

                # Screenshot
                safe_id = str(listing_id)[-8:]
                debug_path = os.path.join("output", f"debug_ical_{safe_id}_{url.split('/')[-1]}.png")
                os.makedirs("output", exist_ok=True)
                page.screenshot(path=debug_path, full_page=True)
                print(f"   📸 Screenshot: {debug_path}")

                # Chercher URL iCal dans le HTML
                content = page.content()

                # Méthode JS
                ical_url = page.evaluate("""
                    () => {
                        const inputs = document.querySelectorAll('input[type="text"], input[type="url"], input[readonly]');
                        for (const inp of inputs) {
                            if (inp.value && inp.value.includes('ical'))
                                return inp.value;
                        }
                        const links = document.querySelectorAll('a[href*="ical"], a[href*=".ics"]');
                        if (links.length > 0) return links[0].href;
                        const text = document.body.innerText;
                        const m = text.match(/https:\\/\\/www\\.airbnb\\.com\\/calendar\\/ical\\/[^\\s]+/);
                        return m ? m[0] : null;
                    }
                """)
                if ical_url:
                    print(f"   ✅ URL iCal trouvée (JS): {ical_url[:80]}...")
                    continue

                # Méthode regex
                for pattern in [
                    r'https://www\.airbnb\.com/calendar/ical/[\w.?=&%+\-]+',
                    r'airbnb\.com/calendar/ical/[^\s"\'<>]+',
                    r'calendarAccessSignature[^\s"\'<>]+',
                ]:
                    match = re.search(pattern, content)
                    if match:
                        print(f"   ✅ URL iCal trouvée (regex): {match.group(0)[:80]}...")
                        break
                else:
                    # Chercher des indices dans le texte
                    body_text = page.inner_text("body").lower()
                    if "ical" in body_text or "export" in body_text or "calendrier" in body_text:
                        print(f"   ⚠️  Mot-clé 'ical/export/calendrier' trouvé dans le texte mais pas d'URL")
                    else:
                        print(f"   ❌ Aucun mot-clé iCal trouvé sur cette page")

            except Exception as e:
                print(f"   ❌ Erreur: {e}")

    context.close()
    browser.close()
    print(f"\n✅ Test terminé. Vérifiez les screenshots dans output/")

if __name__ == "__main__":
    main()
