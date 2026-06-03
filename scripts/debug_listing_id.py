"""
debug_listing_id.py — Diagnostic du problème de listing_id
===========================================================
Ce script scrape 1 page de réservations et affiche la structure JSON
pour identifier où se trouve le listing_id.

Usage :
    python debug_listing_id.py
"""

import json
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
    _parse_reservation_node,
)

HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")

# CloakBrowser
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False


def scrape_one_page_debug(page):
    """Scrape 1 page de réservations et retourne les données brutes."""
    print("\n📋 Scraping 1 page de réservations (mode debug)...")
    
    all_responses = []
    
    def handle_response(response):
        url = response.url
        if response.status != 200:
            return
        if "api/v2/reservations" in url or "api/v3/HostReservationsList" in url:
            try:
                data = response.json()
                all_responses.append({
                    "url": url,
                    "data": data,
                })
                print(f"   ✅ Réponse API capturée : {url[:80]}...")
            except Exception as e:
                print(f"   ⚠️  Erreur parsing JSON : {e}")
    
    page.on("response", handle_response)
    
    # Aller sur la page des réservations
    print("   🌐 Navigation vers /hosting/reservations/all...")
    page.goto("https://www.airbnb.com/hosting/reservations/all")
    page.wait_for_timeout(8000)
    
    page.remove_listener("response", handle_response)
    
    return all_responses


def analyze_reservation_structure(responses):
    """Analyse la structure des réservations pour trouver le listing_id."""
    print("\n🔍 ANALYSE DE LA STRUCTURE DES RÉSERVATIONS")
    print("=" * 70)
    
    if not responses:
        print("❌ Aucune réponse API capturée")
        return
    
    for i, resp in enumerate(responses):
        print(f"\n📦 Réponse #{i+1}")
        print(f"   URL : {resp['url']}")
        
        data = resp['data']
        
        # Sauvegarder la réponse complète
        debug_file = f"debug_api_response_{i+1}.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"   💾 Sauvegardé : {debug_file}")
        
        # Essayer de trouver les réservations
        reservations = []
        
        # Méthode 1 : data.reservations
        if isinstance(data, dict) and "reservations" in data:
            res_data = data["reservations"]
            if isinstance(res_data, list):
                reservations = res_data
            elif isinstance(res_data, dict) and "edges" in res_data:
                reservations = [e.get("node", e) for e in res_data["edges"]]
        
        # Méthode 2 : data.data.reservations
        if not reservations and isinstance(data, dict) and "data" in data:
            inner_data = data["data"]
            if isinstance(inner_data, dict) and "reservations" in inner_data:
                res_data = inner_data["reservations"]
                if isinstance(res_data, list):
                    reservations = res_data
                elif isinstance(res_data, dict) and "edges" in res_data:
                    reservations = [e.get("node", e) for e in res_data["edges"]]
        
        print(f"   📊 {len(reservations)} réservations trouvées")
        
        if reservations:
            # Analyser la première réservation
            first_res = reservations[0]
            print(f"\n   🔬 STRUCTURE DE LA PREMIÈRE RÉSERVATION :")
            print(f"   " + "-" * 66)
            
            # Afficher les clés de premier niveau
            if isinstance(first_res, dict):
                print(f"   📋 Clés disponibles ({len(first_res)}) :")
                for key in sorted(first_res.keys()):
                    value = first_res[key]
                    value_type = type(value).__name__
                    
                    # Afficher un aperçu de la valeur
                    if isinstance(value, (str, int, float, bool)):
                        preview = str(value)[:50]
                    elif isinstance(value, dict):
                        preview = f"dict avec {len(value)} clés: {list(value.keys())[:3]}"
                    elif isinstance(value, list):
                        preview = f"list avec {len(value)} éléments"
                    else:
                        preview = value_type
                    
                    print(f"      • {key:30s} : {value_type:10s} = {preview}")
                
                # Chercher spécifiquement le listing_id
                print(f"\n   🎯 RECHERCHE DU LISTING_ID :")
                print(f"   " + "-" * 66)
                
                listing_id_found = False
                
                # Recherche directe
                for key in ["listing_id", "listingId", "listing_ID", "property_id", "propertyId"]:
                    if key in first_res:
                        print(f"   ✅ Trouvé : {key} = {first_res[key]}")
                        listing_id_found = True
                
                # Recherche dans les sous-objets
                for key, value in first_res.items():
                    if isinstance(value, dict):
                        for subkey in ["listing_id", "listingId", "id", "listing_ID"]:
                            if subkey in value:
                                print(f"   ✅ Trouvé : {key}.{subkey} = {value[subkey]}")
                                listing_id_found = True
                
                if not listing_id_found:
                    print(f"   ❌ Aucun champ listing_id trouvé dans les clés standards")
                    print(f"   💡 Vérifiez le fichier {debug_file} manuellement")
                
                # Tester le parsing actuel
                print(f"\n   🧪 TEST DU PARSING ACTUEL :")
                print(f"   " + "-" * 66)
                parsed = _parse_reservation_node(first_res)
                print(f"   listing_id parsé : '{parsed.get('listing_id')}'")
                print(f"   logement parsé   : '{parsed.get('logement')}'")
                print(f"   id parsé         : '{parsed.get('id')}'")
                
                if not parsed.get('listing_id'):
                    print(f"   ❌ Le parsing actuel ne trouve PAS le listing_id")
                else:
                    print(f"   ✅ Le parsing actuel trouve le listing_id")


def main():
    print("=" * 70)
    print("   DEBUG LISTING_ID — Diagnostic du problème de filtrage")
    print(f"   Démarré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 70)
    
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
    
    # Scraper 1 page
    responses = scrape_one_page_debug(page)
    
    # Analyser
    analyze_reservation_structure(responses)
    
    # Fermer
    context.close()
    browser.close()
    if not USE_CLOAKBROWSER:
        pw.stop()
    
    print("\n" + "=" * 70)
    print("   ✅ DEBUG TERMINÉ")
    print("=" * 70)
    print("\n📋 PROCHAINES ÉTAPES :")
    print("   1. Vérifiez les fichiers debug_api_response_*.json")
    print("   2. Identifiez le chemin correct vers listing_id")
    print("   3. Corrigez _parse_reservation_node() dans airbnb_scraper.py")
    print("   4. Relancez le système")
    print()


if __name__ == "__main__":
    main()
