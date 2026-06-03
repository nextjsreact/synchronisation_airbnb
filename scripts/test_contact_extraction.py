"""
test_contact_extraction.py — Test de l'extraction des coordonnées
==================================================================
Test rapide avec un code de confirmation spécifique.

Usage :
    python test_contact_extraction.py HM4TB95HKS
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

from dotenv import load_dotenv
load_dotenv(encoding='utf-8')

# Imports du scraper
from airbnb_scraper import (
    login,
    is_logged_in,
    SESSION_FILE,
)

from scrape_guest_contacts import get_guest_contact_info

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
    print("   Test d'extraction des coordonnées")
    print(f"   Démarré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 70)
    
    # Code de confirmation à tester
    if len(sys.argv) > 1:
        confirmation_code = sys.argv[1]
    else:
        confirmation_code = "HM4TB95HKS"  # Votre exemple
    
    print(f"\n📋 Test avec le code : {confirmation_code}")
    
    # Lancer le navigateur
    if USE_CLOAKBROWSER:
        print("\n🕵️  Lancement CloakBrowser...")
        launch_args = {
            "headless": HEADLESS,
            "args": ["--no-sandbox"],
            "humanize": True,
            "human_preset": "careful",
            "locale": "fr-FR",
        }
        if PROXY_URL:
            launch_args["proxy"] = {"server": PROXY_URL}
        browser = cloak_launch(**launch_args)
    else:
        print("\n🌐 Lancement Playwright...")
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        launch_args = {
            "headless": HEADLESS,
            "args": ["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        }
        if PROXY_URL:
            launch_args["proxy"] = {"server": PROXY_URL}
        browser = pw.chromium.launch(**launch_args)
    
    # Charger la session
    ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
    if os.path.exists(SESSION_FILE):
        print(f"   💾 Session trouvée : chargement...")
        ctx_opts["storage_state"] = SESSION_FILE
    
    context = browser.new_context(**ctx_opts)
    page = context.new_page()
    
    # Login
    if os.path.exists(SESSION_FILE):
        if is_logged_in(page):
            print("   ✅ Session valide — connexion automatique !")
        else:
            print("   ⚠️  Session expirée — reconnexion...")
            login(page)
    else:
        login(page)
    
    # Tester l'extraction
    print(f"\n{'='*70}")
    print("   TEST D'EXTRACTION")
    print(f"{'='*70}")
    
    contacts = get_guest_contact_info(page, confirmation_code)
    
    print(f"\n{'='*70}")
    print("   RÉSULTAT")
    print(f"{'='*70}")
    print(f"\n📞 Téléphone : {contacts['phone'] or '❌ Non trouvé'}")
    print(f"📧 Email     : {contacts['email'] or '❌ Non trouvé'}")
    
    # Sauvegarder une capture d'écran pour debug
    screenshot_path = f"output/test_contact_{confirmation_code}.png"
    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
    try:
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n📸 Capture d'écran : {screenshot_path}")
    except Exception:
        pass
    
    # Fermer
    context.close()
    browser.close()
    if not USE_CLOAKBROWSER:
        pw.stop()
    
    print(f"\n{'='*70}")
    print("   ✅ TEST TERMINÉ")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
