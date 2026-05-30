"""
Script pour corriger les 7 URLs iCal sans token
================================================
Collecte les URLs iCal avec token pour tous les lofts sans token valide
"""
import os
import sys
import time
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

# Importer les fonctions du scraper principal
from collect_ical_urls import (
    SUPABASE_URL, SUPABASE_KEY, HEADERS,
    scrape_ical_url, update_ical_in_supabase,
    login, USE_CLOAKBROWSER
)
from airbnb_scraper import SESSION_FILE, is_logged_in

print("="*70)
print("CORRECTION DES URLs iCal SANS TOKEN")
print("="*70)

# Les 7 lofts problématiques (sans token)
PROBLEMATIC_LOFTS = [
    {
        "loft_id": "46a77936-c945-4c2f-9707-cc15abf0edfb",
        "name": "Madina loft",
        "listing_id": "897794605927940108"
    },
    {
        "loft_id": "9168c1c0-a123-42b8-8b8b-7e229a227548",
        "name": "Golf view",
        "listing_id": "1000816997221844803"
    },
    {
        "loft_id": "9338c5ec-c6af-4c69-80a0-89551f2144ae",
        "name": "Rosina Loft",
        "listing_id": "1010024176351214897"
    },
    {
        "loft_id": "59d1e3d5-ed29-4be4-acb7-3429e90ed7a9",
        "name": "Rosa loft",
        "listing_id": "1010685773931128088"
    },
    {
        "loft_id": "dbdf5122-e053-494e-b3f3-ba2438713cd0",
        "name": "Oasis loft (ancien)",
        "listing_id": "1081691126719400064"
    },
    {
        "loft_id": "c0bdba5d-0e71-4d82-8672-9835c64c914b",
        "name": "Rayan loft",
        "listing_id": "1084830263659814195"
    },
    {
        "loft_id": "1f0cb6c2-b7e0-4b60-9a0a-c1ad64ae5c48",
        "name": "Aida Loft - Forest Vue",
        "listing_id": "24697659"
    }
]

print(f"\n📋 {len(PROBLEMATIC_LOFTS)} lofts à corriger:")
for loft in PROBLEMATIC_LOFTS:
    print(f"  - {loft['name']} (listing: {loft['listing_id']})")

# Lancer le navigateur
print("\n🌐 Lancement du navigateur...")
browser = None
pw = None

try:
    if USE_CLOAKBROWSER:
        from cloakbrowser import launch as cloak_launch
        _headless = os.environ.get("HEADLESS", "true").lower() != "false"
        _launch_opts = dict(headless=_headless, args=["--no-sandbox"], humanize=True, locale="fr-FR")
        proxy_url = os.environ.get("PROXY_URL", "")
        if proxy_url:
            _launch_opts["proxy"] = {"server": proxy_url}
        browser = cloak_launch(**_launch_opts)
    else:
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        _headless = os.environ.get("HEADLESS", "true").lower() != "false"
        _launch_opts = dict(headless=_headless, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        proxy_url = os.environ.get("PROXY_URL", "")
        if proxy_url:
            _launch_opts["proxy"] = {"server": proxy_url}
        browser = pw.chromium.launch(**_launch_opts)

    # Charger la session sauvegardée
    ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
    if os.path.exists(SESSION_FILE):
        print(f"   💾 Session trouvée : {SESSION_FILE}")
        ctx_opts["storage_state"] = SESSION_FILE
    context = browser.new_context(**ctx_opts)
    page = context.new_page()

    # Login
    if os.path.exists(SESSION_FILE):
        print("   🔍 Vérification de la session...")
        if is_logged_in(page):
            print("   ✅ Session valide — connexion automatique !")
        else:
            print("   ⚠️  Session expirée — reconnexion...")
            login(page)
    else:
        print("   🔐 Connexion à Airbnb...")
        login(page)

    # Scraper les URLs iCal
    print("\n📥 Collecte des URLs iCal...")
    success = 0
    failed = 0

    for i, loft in enumerate(PROBLEMATIC_LOFTS):
        print(f"\n[{i+1}/{len(PROBLEMATIC_LOFTS)}] {loft['name']} (listing: {loft['listing_id']})...")
        
        ical_url = scrape_ical_url(page, loft['listing_id'])
        
        if ical_url:
            # Vérifier le token
            has_token = '?t=' in ical_url or '?s=' in ical_url or 'calendarAccessSignature' in ical_url
            
            if has_token:
                token_type = "?t=" if "?t=" in ical_url else ("?s=" if "?s=" in ical_url else "calendarAccessSignature")
                print(f"   ✅ URL avec token trouvée ({token_type})")
                print(f"   URL: {ical_url[:80]}...")
                
                # Mettre à jour dans property_sync_config
                if update_ical_in_supabase(loft['loft_id'], ical_url):
                    print(f"   ✅ Mise à jour property_sync_config OK")
                    
                    # Mettre à jour dans lofts aussi
                    import requests
                    resp = requests.patch(
                        f"{SUPABASE_URL}/rest/v1/lofts?id=eq.{loft['loft_id']}",
                        json={"airbnb_ical_url": ical_url},
                        headers=HEADERS,
                        timeout=15,
                    )
                    if resp.status_code in (200, 204):
                        print(f"   ✅ Mise à jour lofts.airbnb_ical_url OK")
                        success += 1
                    else:
                        print(f"   ⚠️  Erreur mise à jour lofts: HTTP {resp.status_code}")
                        success += 1  # On compte quand même comme succès si property_sync_config est OK
                else:
                    print(f"   ❌ Erreur mise à jour Supabase")
                    failed += 1
            else:
                print(f"   ⚠️  URL sans token trouvée: {ical_url[:80]}...")
                print(f"   ⚠️  Cette URL ne fonctionnera pas (HTTP 400)")
                failed += 1
        else:
            print(f"   ❌ Aucune URL trouvée")
            print(f"   💡 Vérifiez la capture: output/debug_ical_{loft['listing_id']}_sharing.png")
            failed += 1
        
        time.sleep(2)  # Anti-détection

    context.close()
    browser.close()
    if pw:
        pw.stop()

    print("\n" + "="*70)
    print(f"RÉSULTAT: {success} succès, {failed} échecs")
    print("="*70)

    if success > 0:
        print("\n✅ Correction terminée !")
        print(f"\n{success} URL(s) iCal avec token ont été collectées et mises à jour.")
        print("\nLes URLs sont maintenant disponibles dans:")
        print("  - property_sync_config.ical_url_airbnb")
        print("  - lofts.airbnb_ical_url")
        print("\nLe système de surveillance automatique va maintenant les surveiller.")
    
    if failed > 0:
        print(f"\n⚠️  {failed} loft(s) n'ont pas pu être corrigés.")
        print("\nCauses possibles:")
        print("  1. La page Airbnb a changé de structure")
        print("  2. Le listing n'est pas accessible")
        print("  3. Le listing n'a pas de calendrier partageable")
        print("\nVous pouvez récupérer l'URL manuellement:")
        for loft in PROBLEMATIC_LOFTS:
            print(f"\n  {loft['name']}:")
            print(f"    https://fr.airbnb.com/multicalendar/{loft['listing_id']}/availability-settings/sharing-settings/import-calendar")

except Exception as e:
    print(f"\n❌ ERREUR: {e}")
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
