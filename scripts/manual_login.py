"""
manual_login.py — Login manuel Airbnb pour sauvegarder la session
=================================================================
Ouvre un navigateur VISIBLE (non-headless), te laisse faire le login
complet (CAPTCHA, magic link, 2FA, etc.), puis sauvegarde la session.

Usage :
    python scripts/manual_login.py

Après exécution, la session sera dans output/airbnb_session.json
Le targeted-scraper la réutilisera automatiquement.
"""

import os
import sys
import time
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from airbnb_scraper import SESSION_FILE, EMAIL

def main():
    print("=" * 55)
    print("   Login Manuel Airbnb — Session Builder")
    print("=" * 55)
    print()
    print(f"   Email   : {EMAIL}")
    print(f"   Session : {SESSION_FILE}")
    print()

    try:
        from cloakbrowser import launch as cloak_launch
        USE_CLOAKBROWSER = True
        print("   Moteur  : CloakBrowser")
    except ImportError:
        USE_CLOAKBROWSER = False
        print("   Moteur  : Playwright Chromium")

    print()
    print("   🔓 Un navigateur VISIBLE va s'ouvrir.")
    print("   📝 Connecte-toi normalement à Airbnb.")
    print("   ⏳ Le script détectera quand tu seras connecté.")
    print("   💾 La session sera sauvegardée automatiquement.")
    print()
    print("   Appuie sur ENTRÉE pour commencer...")
    input()

    pw = None
    if USE_CLOAKBROWSER:
        browser = cloak_launch(
            headless=False,
            args=["--no-sandbox"],
            humanize=True,
            human_preset="careful",
            locale="fr-FR",
        )
    else:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        browser = pw.chromium.launch(
            headless=False,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )

    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        locale="fr-FR",
    )
    page = context.new_page()

    print("   🔐 Navigation vers Airbnb login...")
    page.goto("https://www.airbnb.com/login", wait_until="domcontentloaded", timeout=60000)
    print("   ✅ Page de login chargée. Connecte-toi maintenant.")
    print()

    # Attendre que l'utilisateur soit connecté (max 10 minutes)
    logged_in = False
    for i in range(300):  # 300 * 2s = 10 min
        time.sleep(2)
        current_url = page.url
        if i % 15 == 0:
            print(f"   ⏳ En attente... ({i*2}s)")

        # Vérifier l'URL d'abord
        if "login" not in current_url and "signin" not in current_url:
            logged_in = True
            break

        # Airbnb est un SPA — l'URL peut rester sur /login même après connexion
        # Vérifier le contenu de la page
        try:
            page_text = page.inner_text("body").lower()
            page_html = page.content().lower()

            # Indicateurs de connexion réussie
            logged_in_indicators = [
                "déconnexion", "log out", "sign out", "mon compte",
                "my account", "hosting", "réservations", "reservations",
                "tableau de bord", "dashboard", "annonces", "listings",
            ]
            if any(kw in page_text for kw in logged_in_indicators):
                logged_in = True
                print(f"   🔍 Indicateur de connexion détecté dans le contenu !")
                break

            # Vérifier la présence de cookies d'authentification Airbnb
            cookies = context.cookies()
            auth_cookies = [c for c in cookies if c["name"] in ("session", "_airbnb_session_id", "airbnb_session")]
            if auth_cookies:
                print(f"   🔍 Cookies d'auth trouvés ({len(auth_cookies)}) — vérification du contenu...")

        except Exception:
            pass

    if not logged_in:
        # Dernière tentative
        time.sleep(5)
        current_url = page.url
        if "login" not in current_url and "signin" not in current_url:
            logged_in = True

    if logged_in:
        print()
        print("   ✅ Connexion détectée !")
        
        # Naviguer vers la page hosting pour confirmer et charger les bons cookies
        print("   🔍 Vérification en allant sur /hosting...")
        try:
            page.goto("https://www.airbnb.com/hosting/reservations/upcoming", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)
            verify_url = page.url
            print(f"   🔍 URL après vérification : {verify_url}")
            if "login" in verify_url or "signin" in verify_url:
                print("   ⚠️  Redirigé vers login — la connexion n'est peut-être pas complète")
                print("   💡 Essaye de cliquer sur 'Hostinger' ou 'Annonces' dans le menu")
            else:
                print("   ✅ Page hosting accessible — session valide !")
        except Exception as e:
            print(f"   ⚠️  Erreur navigation : {e}")
        
        print()
        print("   💾 Sauvegarde de la session...")

        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        context.storage_state(path=SESSION_FILE)
        print(f"   💾 Session sauvegardée : {SESSION_FILE}")

        # Vérifier que le fichier existe
        if os.path.exists(SESSION_FILE):
            size = os.path.getsize(SESSION_FILE)
            print(f"   📦 Taille : {size} octets")
            print()
            print("   ✅ SESSION PRÊTE !")
            print("   ➤ Le targeted-scraper va maintenant réutiliser cette session.")
            print("   ➤ relance-le avec : docker compose -f docker-compose.sync.yml restart targeted-scraper")
        else:
            print("   ❌ Erreur : fichier de session non créé")
    else:
        print()
        print("   ❌ Timeout — connexion non détectée après 10 minutes.")
        print("   Vérifie que tu es bien connecté à Airbnb.")

    print()
    print("   Fermeture du navigateur dans 5 secondes...")
    time.sleep(5)
    context.close()
    browser.close()
    if pw:
        pw.stop()

    print("   ✅ Terminé !")


if __name__ == "__main__":
    main()
