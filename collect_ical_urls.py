"""
Script rapide : collecte les URLs iCal réelles (avec signature) pour quelques lofts,
puis met à jour property_sync_config dans Supabase.

Usage : python collect_ical_urls.py [--all]
  --all : collecte pour tous les 53 lofts actifs (long)
  sans   : collecte pour les 3 premiers lofts (test rapide)
"""

import os
import sys
import re
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()  # Supprime encoding='utf-8' pour eviter les erreurs

# ── Config ──────────────────────────────────────────────
SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"
AIRBNB_EMAIL = os.environ.get("AIRBNB_EMAIL", "")
AIRBNB_PASSWORD = os.environ.get("AIRBNB_PASSWORD", "")
TOTP_SECRET = os.environ.get("TOTP_SECRET", "")
PROXY_URL = os.environ.get("PROXY_URL", "")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

# ── Browser setup ───────────────────────────────────────
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False


def get_lofts_to_process(all_lofts=False):
    """Récupère les lofts actifs avec leur listing_id depuis Supabase."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=id,name,airbnb_listing_id&status=eq.available&order=name",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        timeout=15,
    )
    lofts = resp.json()
    if not all_lofts:
        lofts = lofts[:3]  # Test rapide : 3 lofts seulement
    return lofts


def get_existing_ical_urls():
    """Récupère les configs iCal déjà existantes."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/property_sync_config?select=loft_id,ical_url_airbnb",
        headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
        timeout=15,
    )
    return {c["loft_id"]: c["ical_url_airbnb"] for c in resp.json() if c.get("ical_url_airbnb")}


def login(page):
    """Connexion à Airbnb — même flux que airbnb_scraper.login()."""
    from airbnb_scraper import (
        _dismiss_overlays, _find_email_field, handle_2fa,
        login as scraper_login,
    )
    scraper_login(page)


def scrape_ical_url(page, listing_id):
    """
    Scrape l'URL iCal depuis la page de disponibilité d'un loft.
    
    Suit le chemin documenté par Airbnb :
    1. Calendrier → Disponibilités
    2. Sous "Associer des calendriers" → "Me connecter à un autre site web"
    3. Copier le lien du calendrier Airbnb (avec token ?t=)
    """
    try:
        # Étape 1 : Aller sur la page de partage de calendrier (NOUVELLE URL)
        url = f"https://fr.airbnb.com/multicalendar/{listing_id}/availability-settings/sharing-settings/import-calendar"
        print(f"   📍 Navigation vers : {url}")
        page.goto(url, timeout=60000, wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        
        # Attendre que la page soit chargée
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            page.wait_for_timeout(3000)
        
        # Sauvegarder une capture d'écran pour debug
        try:
            screenshot_path = f"output/debug_ical_{listing_id}_sharing.png"
            page.screenshot(path=screenshot_path)
            print(f"   📸 Capture : {screenshot_path}")
        except Exception:
            pass
        
        # Chercher directement l'URL iCal dans les inputs
        # Sur cette page, le champ "Étape 1" contient l'URL iCal
        print(f"   🔍 Recherche de l'URL iCal dans les champs...")
        ical_url = page.evaluate("""
            () => {
                // Chercher dans tous les inputs
                const inputs = document.querySelectorAll('input');
                for (const inp of inputs) {
                    const val = inp.value || '';
                    
                    // Chercher URL complète avec token
                    if (val.includes('calendar/ical/') && (val.includes('?t=') || val.includes('?s=') || val.includes('calendarAccessSignature'))) {
                        return val;
                    }
                    
                    // Chercher URL complète sans token
                    if (val.includes('calendar/ical/') && val.includes('.ics')) {
                        return val;
                    }
                }
                
                return null;
            }
        """)
        
        if ical_url:
            print(f"   ✅ URL iCal trouvée : {ical_url[:100]}...")
            
            # Vérifier qu'elle a un token
            if '?t=' in ical_url or '?s=' in ical_url or 'calendarAccessSignature' in ical_url:
                return ical_url
            else:
                print(f"   ⚠️  URL sans token trouvée")
                return ical_url  # On la retourne quand même
        
        print(f"   ❌ Aucune URL iCal trouvée")
        print(f"   💡 Vérifiez la capture d'écran : output/debug_ical_{listing_id}_sharing.png")
        
        return None
        
    except Exception as e:
        print(f"   ⚠️  Erreur scraping {listing_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_ical_in_supabase(loft_id, ical_url):
    """Met à jour l'URL iCal dans property_sync_config."""
    # Vérifier si une config existe
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/property_sync_config?loft_id=eq.{loft_id}&select=id",
        headers=HEADERS, timeout=15,
    )
    existing = resp.json()

    if existing:
        # Update
        r = requests.patch(
            f"{SUPABASE_URL}/rest/v1/property_sync_config?loft_id=eq.{loft_id}",
            json={"ical_url_airbnb": ical_url},
            headers=HEADERS, timeout=15,
        )
    else:
        # Insert
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/property_sync_config",
            json={"loft_id": loft_id, "ical_url_airbnb": ical_url, "is_active": True},
            headers=HEADERS, timeout=15,
        )

    return r.status_code in (200, 201, 204)


def main():
    all_lofts = "--all" in sys.argv
    print(f"{'='*55}")
    print(f"  Collecte des URLs iCal — {'TOUS les lofts' if all_lofts else 'Test rapide (3 lofts)'}")
    print(f"  Début : {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*55}\n")

    # 1. Récupérer les lofts
    lofts = get_lofts_to_process(all_lofts)
    print(f"📋 {len(lofts)} lofts à traiter\n")

    # 2. Vérifier les URLs existantes
    existing = get_existing_ical_urls()
    print(f"📎 {len(existing)} URLs iCal déjà en base\n")

    # Filtrer ceux qui ont besoin d'une URL (ou qui ont une URL sans token)
    def needs_update(loft_id):
        url = existing.get(loft_id)
        if not url:
            return True  # Pas d'URL
        # Vérifier si l'URL a un token valide (?t= ou ?s= ou calendarAccessSignature)
        has_token = ('?t=' in url or '?s=' in url or 'calendarAccessSignature' in url)
        return not has_token  # Besoin de mise à jour si pas de token

    to_process = [l for l in lofts if needs_update(l["id"])]
    already_done = len(lofts) - len(to_process)
    if already_done > 0:
        print(f"⏭️  {already_done} lofts ont déjà une URL iCal avec signature — skip\n")

    if not to_process:
        print("✅ Tous les lofts ont déjà une URL iCal !")
        return

    # 3. Lancer le navigateur
    from airbnb_scraper import SESSION_FILE, is_logged_in
    browser = None
    pw = None
    if USE_CLOAKBROWSER:
        print("🌐 Lancement CloakBrowser...")
        _headless = os.environ.get("HEADLESS", "true").lower() != "false"
        _launch_opts = dict(headless=_headless, args=["--no-sandbox"], humanize=True, locale="fr-FR")
        if PROXY_URL:
            _launch_opts["proxy"] = {"server": PROXY_URL}
        browser = cloak_launch(**_launch_opts)
    else:
        print("🌐 Lancement Playwright standard...")
        from playwright.sync_api import sync_playwright
        pw = sync_playwright().start()
        _headless = os.environ.get("HEADLESS", "true").lower() != "false"
        _launch_opts = dict(headless=_headless, args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        if PROXY_URL:
            _launch_opts["proxy"] = {"server": PROXY_URL}
        browser = pw.chromium.launch(**_launch_opts)

    # Charger la session sauvegardée si disponible
    ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
    if os.path.exists(SESSION_FILE):
        print(f"   💾 Session trouvée : {SESSION_FILE}")
        ctx_opts["storage_state"] = SESSION_FILE
    context = browser.new_context(**ctx_opts)
    page = context.new_page()

    try:
        # 4. Connexion — réutiliser la session si valide
        if os.path.exists(SESSION_FILE):
            print("   🔍 Vérification de la session sauvegardée...")
            if is_logged_in(page):
                print("   ✅ Session valide — connexion automatique !")
            else:
                print("   ⚠️  Session expirée — reconnexion...")
                login(page)
        else:
            login(page)

        # 5. Scraper les URLs iCal
        success = 0
        failed = 0
        for i, loft in enumerate(to_process):
            lid = loft["airbnb_listing_id"]
            name = loft["name"]
            print(f"[{i+1}/{len(to_process)}] {name} ({lid})...")

            ical_url = scrape_ical_url(page, lid)

            if ical_url:
                # Vérifier le type de token
                has_t_token = '?t=' in ical_url
                has_s_token = '?s=' in ical_url
                has_signature = 'calendarAccessSignature' in ical_url
                
                if has_t_token or has_s_token or has_signature:
                    token_type = "?t=" if has_t_token else ("?s=" if has_s_token else "calendarAccessSignature")
                    if update_ical_in_supabase(loft["id"], ical_url):
                        print(f"   ✅ URL iCal mise à jour (token: {token_type})")
                        success += 1
                    else:
                        print(f"   ❌ Erreur mise à jour Supabase")
                        failed += 1
                else:
                    print(f"   ⚠️  URL sans token: {ical_url[:80]}...")
                    print(f"   ⚠️  Cette URL ne fonctionnera pas avec ical_watcher (HTTP 400)")
                    # On ne la met pas en base car elle est inutilisable
                    failed += 1
            else:
                print(f"   ❌ Aucune URL trouvée")
                failed += 1

            time.sleep(2)  # Anti-détection

        print(f"\n{'='*55}")
        print(f"  Résultat : {success} succès, {failed} échecs")
        print(f"  Fin : {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*55}")

    finally:
        browser.close()
        if not USE_CLOAKBROWSER:
            pw.stop()


if __name__ == "__main__":
    main()
