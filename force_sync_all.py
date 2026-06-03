"""
Script pour forcer une synchronisation complète de toutes les réservations
===========================================================================
Scrape TOUTES les réservations de TOUS les lofts (pas seulement les changements)
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

print("="*70)
print("🔄 SYNCHRONISATION COMPLÈTE FORCÉE")
print("="*70)
print()
print("Ce script va scraper TOUTES les réservations de TOUS les lofts.")
print("Cela peut prendre 10-15 minutes.")
print()
input("Appuyez sur Entrée pour continuer...")
print()

# Importer les fonctions du scraper
from airbnb_scraper import (
    login, get_reservations, SESSION_FILE, is_logged_in
)
from airbnb_api_client import upsert_reservations, check_api_health

# Vérifier l'API
print("🌐 Vérification de l'API Next.js...")
health = check_api_health()
if health["ok"]:
    print(f"   ✅ API accessible ({health['latency_ms']}ms)")
else:
    print(f"   ⚠️  API inaccessible : {health['error']}")
    print("   Les données seront scrapées mais pas envoyées à l'API")
print()

# Lancer le navigateur
print("🌐 Lancement du navigateur...")
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False

browser = None
pw = None

try:
    if USE_CLOAKBROWSER:
        print("   Utilisation de CloakBrowser")
        _headless = os.environ.get("HEADLESS", "true").lower() == "true"
        _launch_opts = dict(
            headless=_headless,
            args=["--no-sandbox"],
            humanize=True,
            locale="fr-FR"
        )
        proxy_url = os.environ.get("PROXY_URL", "")
        if proxy_url:
            _launch_opts["proxy"] = {"server": proxy_url}
        browser = cloak_launch(**_launch_opts)
    else:
        from playwright.sync_api import sync_playwright
        print("   Utilisation de Playwright")
        pw = sync_playwright().start()
        _headless = os.environ.get("HEADLESS", "true").lower() == "true"
        _launch_opts = dict(
            headless=_headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
        )
        proxy_url = os.environ.get("PROXY_URL", "")
        if proxy_url:
            _launch_opts["proxy"] = {"server": proxy_url}
        browser = pw.chromium.launch(**_launch_opts)

    # Créer le contexte
    ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
    if os.path.exists(SESSION_FILE):
        print(f"   💾 Chargement de la session : {SESSION_FILE}")
        ctx_opts["storage_state"] = SESSION_FILE
    
    context = browser.new_context(**ctx_opts)
    page = context.new_page()

    # Login
    print()
    print("🔐 Connexion à Airbnb...")
    if os.path.exists(SESSION_FILE):
        if is_logged_in(page):
            print("   ✅ Session valide — connexion automatique !")
        else:
            print("   ⚠️  Session expirée — reconnexion...")
            login(page)
    else:
        login(page)

    # Scraper TOUTES les réservations
    print()
    print("📥 Scraping de TOUTES les réservations...")
    print("   (Cela peut prendre plusieurs minutes)")
    print()
    
    reservations = get_reservations(page)
    
    print()
    print(f"✅ {len(reservations)} réservations trouvées")
    print()

    if reservations:
        # Afficher quelques exemples
        print("📋 Exemples de réservations :")
        for i, r in enumerate(reservations[:5], 1):
            print(f"   [{i}] {r.get('guest_name', 'N/A')} - {r.get('check_in', 'N/A')} → {r.get('check_out', 'N/A')}")
        
        if len(reservations) > 5:
            print(f"   ... et {len(reservations) - 5} autres")
        print()

        # Envoyer à l'API
        if health["ok"]:
            # Conversion en DZD (local) + renommage contacts vers noms API
            for r in reservations:
                devise = (r.get("devise") or r.get("currency_code") or "DZD").upper()
                if devise != "DZD":
                    ratio = r.get("currency_ratio", 1.0) or 1.0
                    try:
                        montant_orig = float(r.get("montant_total", 0) or 0)
                        r["montant_total"] = round(montant_orig * ratio, 2)
                        r["devise"] = "DZD"
                    except (TypeError, ValueError):
                        pass
                if "telephone_voyageur" in r and "guest_phone" not in r:
                    raw = r.pop("telephone_voyageur")
                    if isinstance(raw, str) and sum(c.isdigit() for c in raw) >= 5:
                        r["guest_phone"] = raw.strip()
                    else:
                        r["guest_phone"] = ""
                if "email_voyageur" in r and "guest_email" not in r:
                    v = r.pop("email_voyageur")
                    r["guest_email"] = v if (v and "@" in v) else ""
            print("📤 Envoi à l'API Next.js...")
            count = upsert_reservations(reservations, sync_type="full")
            print(f"   ✅ {count} réservations envoyées")
        else:
            print("   ⚠️  API inaccessible — données non envoyées")
        
        # Sauvegarder localement
        import json
        output_file = "output/reservations_full_sync.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(reservations, f, indent=2, ensure_ascii=False)
        print(f"   💾 Sauvegardé dans : {output_file}")
    else:
        print("❌ Aucune réservation trouvée")
        print()
        print("Causes possibles :")
        print("   1. Session Airbnb expirée")
        print("   2. API GraphQL d'Airbnb a changé")
        print("   3. Aucune réservation active")
        print()
        print("Solution : Recréez la session avec 1_creer_session.bat")

    context.close()
    browser.close()
    if pw:
        pw.stop()

    print()
    print("="*70)
    print("✅ SYNCHRONISATION COMPLÈTE TERMINÉE")
    print("="*70)
    print()
    print("Vérifiez maintenant avec : python view_reservations.py")

except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
    
    if browser:
        try:
            browser.close()
        except:
            pass
    if pw:
        try:
            pw.stop()
        except:
            pass
