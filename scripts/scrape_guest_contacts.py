"""
scrape_guest_contacts.py — Récupération des coordonnées des voyageurs
======================================================================
Ce script récupère les numéros de téléphone et emails des voyageurs
pour chaque réservation en suivant le parcours Airbnb.

Usage :
    python scrape_guest_contacts.py
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
)

HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")

# CloakBrowser
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False


def get_guest_contact_info(page, confirmation_code):
    """
    Récupère les coordonnées d'un voyageur pour une réservation.
    
    Parcours :
    1. Aller sur la page de la réservation (format /hosting/stay/{code})
    2. Ouvrir le menu "Gérer la réservation"
    3. Extraire le numéro de téléphone et l'email
    
    Returns:
        dict: {"phone": "...", "email": "..."}
    """
    print(f"\n   📞 Récupération des coordonnées pour {confirmation_code}...")
    
    try:
        # Aller sur la page de la réservation (format Airbnb)
        url = f"https://fr.airbnb.com/hosting/stay/{confirmation_code}?tab=upcoming"
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        phone = None
        email = None
        
        # Méthode 1 : Cliquer sur le bouton "Gérer la réservation" ou les 3 points
        try:
            # Chercher le bouton avec les 3 points ou "Gérer"
            menu_selectors = [
                'button:has-text("Gérer")',
                'button[aria-label*="Gérer"]',
                'button[aria-label*="menu"]',
                'button[aria-label*="Menu"]',
                'button:has-text("⋯")',
                'button:has-text("...")',
                '[data-testid="reservation-menu-button"]',
                'button[aria-haspopup="menu"]',
            ]
            
            menu_button = None
            for selector in menu_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        menu_button = btn
                        print(f"      ✓ Bouton menu trouvé : {selector}")
                        break
                except Exception:
                    continue
            
            if menu_button:
                menu_button.click()
                page.wait_for_timeout(2000)
                
                # Chercher "Numéro de téléphone" dans le menu
                try:
                    # Attendre que le menu soit visible
                    page.wait_for_selector('text=/Numéro de téléphone|Phone number/i', timeout=5000)
                    
                    # Extraire le contenu du menu
                    menu_content = page.content()
                    
                    # Regex pour trouver le numéro après "Numéro de téléphone"
                    import re
                    
                    # Pattern pour "Numéro de téléphone : Nom\n+XX XXX XX XX XX"
                    phone_pattern = r'Numéro de téléphone[:\s]*[^+\n]*\n?\s*(\+?\d[\d\s\-\(\)]{8,})'
                    match = re.search(phone_pattern, menu_content, re.IGNORECASE)
                    if match:
                        phone = match.group(1).strip()
                        print(f"      ✅ Téléphone trouvé : {phone}")
                    
                    # Si pas trouvé, chercher tous les numéros dans le menu
                    if not phone:
                        phone_patterns = [
                            r'\+\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9}',
                            r'\d{10,}',
                        ]
                        
                        for pattern in phone_patterns:
                            matches = re.findall(pattern, menu_content)
                            if matches:
                                # Prendre le premier numéro qui ressemble à un téléphone
                                for match in matches:
                                    clean = match.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                                    if len(clean) >= 10:
                                        phone = match
                                        print(f"      ✅ Téléphone trouvé (fallback) : {phone}")
                                        break
                            if phone:
                                break
                    
                    # Chercher l'email
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    email_matches = re.findall(email_pattern, menu_content)
                    if email_matches:
                        # Filtrer les emails Airbnb
                        for em in email_matches:
                            if "airbnb" not in em.lower():
                                email = em
                                print(f"      ✅ Email trouvé : {email}")
                                break
                    
                except Exception as e:
                    print(f"      ⚠️  Erreur extraction menu : {e}")
                
                # Fermer le menu (cliquer ailleurs ou ESC)
                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
                except Exception:
                    pass
            else:
                print(f"      ⚠️  Bouton menu non trouvé")
        
        except Exception as e:
            print(f"      ⚠️  Erreur menu : {e}")
        
        # Méthode 2 : Chercher directement dans la page (si le menu n'a pas fonctionné)
        if not phone or not email:
            try:
                page_content = page.content()
                
                import re
                
                if not phone:
                    # Chercher "Numéro de téléphone" dans toute la page
                    phone_pattern = r'Numéro de téléphone[:\s]*[^+\n]*\n?\s*(\+?\d[\d\s\-\(\)]{8,})'
                    match = re.search(phone_pattern, page_content, re.IGNORECASE)
                    if match:
                        phone = match.group(1).strip()
                        print(f"      ✅ Téléphone trouvé (page) : {phone}")
                    
                    # Fallback : tous les numéros
                    if not phone:
                        phone_patterns = [
                            r'\+\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9}',
                        ]
                        
                        for pattern in phone_patterns:
                            matches = re.findall(pattern, page_content)
                            if matches:
                                # Prendre le premier qui ressemble à un téléphone international
                                for match in matches:
                                    if match.startswith('+'):
                                        phone = match
                                        print(f"      ✅ Téléphone trouvé (page fallback) : {phone}")
                                        break
                            if phone:
                                break
                
                if not email:
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    email_matches = re.findall(email_pattern, page_content)
                    if email_matches:
                        for em in email_matches:
                            if "airbnb" not in em.lower():
                                email = em
                                print(f"      ✅ Email trouvé (page) : {email}")
                                break
            
            except Exception as e:
                print(f"      ⚠️  Erreur page : {e}")
        
        result = {
            "phone": phone or "",
            "email": email or "",
        }
        
        if phone or email:
            print(f"      ✅ Téléphone : {phone or 'N/A'}")
            print(f"      ✅ Email : {email or 'N/A'}")
        else:
            print(f"      ⚠️  Aucune coordonnée trouvée")
        
        return result
        
    except Exception as e:
        print(f"      ❌ Erreur : {e}")
        return {"phone": "", "email": ""}


def enrich_reservations_with_contacts(page, reservations):
    """
    Enrichit les réservations avec les coordonnées des voyageurs.
    
    Args:
        page: Page Playwright
        reservations: Liste des réservations (dicts)
    
    Returns:
        Liste des réservations enrichies
    """
    print(f"\n📞 Enrichissement de {len(reservations)} réservations avec les coordonnées...")
    
    enriched = []
    
    for i, reservation in enumerate(reservations):
        confirmation_code = reservation.get("id", "")
        
        if not confirmation_code:
            print(f"\n   [{i+1}/{len(reservations)}] Pas de code de confirmation, skip")
            enriched.append(reservation)
            continue
        
        print(f"\n   [{i+1}/{len(reservations)}] {confirmation_code} - {reservation.get('voyageur', 'N/A')}")
        
        # Récupérer les coordonnées
        contacts = get_guest_contact_info(page, confirmation_code)
        
        # Ajouter aux données
        reservation["telephone_voyageur"] = contacts["phone"]
        reservation["email_voyageur"] = contacts["email"]
        
        enriched.append(reservation)
        
        # Pause pour éviter le rate limiting
        time.sleep(2)
        
        # Sauvegarder tous les 10
        if (i + 1) % 10 == 0:
            print(f"\n   💾 Sauvegarde intermédiaire ({i+1}/{len(reservations)})...")
            save_enriched_data(enriched)
    
    return enriched


def save_enriched_data(reservations):
    """Sauvegarde les données enrichies."""
    output_file = "output/reservations_avec_contacts.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(reservations, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Sauvegardé : {output_file}")


def main():
    print("=" * 70)
    print("   Scraping des coordonnées des voyageurs")
    print(f"   Démarré le : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 70)
    
    # Charger les réservations existantes
    input_file = "output/reservations_airbnb.json"
    
    if not os.path.exists(input_file):
        print(f"\n❌ Fichier introuvable : {input_file}")
        print(f"   Lancez d'abord le scraping complet : SCRAPING_COMPLET_MAINTENANT.bat")
        return
    
    with open(input_file, "r", encoding="utf-8") as f:
        reservations = json.load(f)
    
    print(f"\n📊 {len(reservations)} réservations chargées")
    
    # Filtrer les réservations actives (upcoming ou en cours)
    active_reservations = [
        r for r in reservations
        if r.get("statut", "").lower() in [
            "confirmée", "upcoming", "séjour en cours", "en cours",
            "à venir", "future", "accepted"
        ]
    ]
    
    print(f"   ↳ {len(active_reservations)} réservations actives")
    
    if not active_reservations:
        print(f"\n⚠️  Aucune réservation active à enrichir")
        return
    
    # Demander confirmation
    print(f"\n⚠️  Ce script va récupérer les coordonnées de {len(active_reservations)} voyageurs")
    print(f"   Durée estimée : {len(active_reservations) * 5 // 60} minutes")
    
    response = input("\nContinuer ? (o/n) : ")
    if response.lower() != "o":
        print("Annulé")
        return
    
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
    
    # Enrichir les réservations
    enriched = enrich_reservations_with_contacts(page, active_reservations)
    
    # Sauvegarder
    save_enriched_data(enriched)
    
    # Fermer
    context.close()
    browser.close()
    if not USE_CLOAKBROWSER:
        pw.stop()
    
    print("\n" + "=" * 70)
    print("   ✅ TERMINÉ")
    print("=" * 70)
    print(f"\n📊 Résultats :")
    
    with_phone = sum(1 for r in enriched if r.get("telephone_voyageur"))
    with_email = sum(1 for r in enriched if r.get("email_voyageur"))
    
    print(f"   • {len(enriched)} réservations traitées")
    print(f"   • {with_phone} avec téléphone ({with_phone*100//len(enriched)}%)")
    print(f"   • {with_email} avec email ({with_email*100//len(enriched)}%)")
    print(f"\n📁 Fichier créé : output/reservations_avec_contacts.json")
    print()


if __name__ == "__main__":
    main()
