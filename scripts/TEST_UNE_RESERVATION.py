"""
TEST_UNE_RESERVATION.py - Test avec une seule réservation
==========================================================
Ce script teste le flux complet avec UNE réservation :
1. Scraping d'une réservation spécifique
2. Collecte des coordonnées (téléphone + email)
3. Conversion de la devise
4. Envoi à l'API Next.js

Usage :
    python TEST_UNE_RESERVATION.py [CODE_CONFIRMATION]
    
Exemple :
    python TEST_UNE_RESERVATION.py HM4TB95HKS
"""

import os
import sys
import json
from datetime import datetime

# Forcer UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(encoding='utf-8')

# Imports
from airbnb_scraper import (
    login,
    is_logged_in,
    get_reservations,
    SESSION_FILE,
)
from currency_converter import enrich_with_currency_ratio
from airbnb_api_client import send_to_nextjs_api

# CloakBrowser
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False
    print("⚠️  CloakBrowser non installé, utilisation de Playwright")

HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")


def get_guest_contact_info(page, confirmation_code):
    """
    Récupère les coordonnées d'un voyageur pour une réservation.
    """
    print(f"\n📞 Récupération des coordonnées pour {confirmation_code}...")
    
    try:
        # Aller sur la page de la réservation
        url = f"https://fr.airbnb.com/hosting/stay/{confirmation_code}?tab=upcoming"
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        phone = None
        email = None
        
        # Chercher dans le contenu de la page
        page_content = page.content()
        
        import re
        
        # Pattern pour "Numéro de téléphone : Nom\n+XX XXX XX XX XX"
        phone_pattern = r'Numéro de téléphone[:\s]*[^+\n]*\n?\s*(\+?\d[\d\s\-\(\)]{8,})'
        match = re.search(phone_pattern, page_content, re.IGNORECASE)
        if match:
            phone = match.group(1).strip()
            print(f"   ✅ Téléphone trouvé : {phone}")
        
        # Fallback : tous les numéros internationaux
        if not phone:
            phone_patterns = [r'\+\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{1,9}']
            for pattern in phone_patterns:
                matches = re.findall(pattern, page_content)
                if matches:
                    for match in matches:
                        if match.startswith('+'):
                            phone = match
                            print(f"   ✅ Téléphone trouvé (fallback) : {phone}")
                            break
                if phone:
                    break
        
        # Chercher l'email
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        email_matches = re.findall(email_pattern, page_content)
        if email_matches:
            for em in email_matches:
                if "airbnb" not in em.lower():
                    email = em
                    print(f"   ✅ Email trouvé : {email}")
                    break
        
        if not phone and not email:
            print(f"   ⚠️  Aucune coordonnée trouvée")
        
        return {"phone": phone or "", "email": email or ""}
        
    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return {"phone": "", "email": ""}


def main():
    print("="*70)
    print("   🧪 TEST AVEC UNE SEULE RÉSERVATION")
    print("="*70)
    print(f"\n   Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Récupérer le code de confirmation
    if len(sys.argv) > 1:
        target_code = sys.argv[1]
    else:
        # Utiliser HM4TB95HKS par défaut (Hamza)
        target_code = "HM4TB95HKS"
    
    print(f"   Code de confirmation : {target_code}")
    print(f"   Moteur : {'CloakBrowser' if USE_CLOAKBROWSER else 'Playwright'}")
    print(f"   Headless : {HEADLESS}")
    
    # Lancer le navigateur
    print(f"\n{'='*70}")
    print(f"   ÉTAPE 1 : LANCEMENT DU NAVIGATEUR")
    print(f"{'='*70}\n")
    
    if USE_CLOAKBROWSER:
        print("🕵️  Lancement CloakBrowser...")
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
        print("🌐 Lancement Playwright...")
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
    
    try:
        # Login
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 2 : CONNEXION À AIRBNB")
        print(f"{'='*70}\n")
        
        if os.path.exists(SESSION_FILE):
            if is_logged_in(page):
                print("   ✅ Session valide — connexion automatique !")
            else:
                print("   ⚠️  Session expirée — reconnexion...")
                login(page)
        else:
            login(page)
        
        # Scraper toutes les réservations
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 3 : SCRAPING DES RÉSERVATIONS")
        print(f"{'='*70}\n")
        
        print("📋 Récupération de toutes les réservations...")
        all_reservations = get_reservations(page)
        
        # Si l'API GraphQL échoue, utiliser le fallback
        if not all_reservations:
            print("   ⚠️  API GraphQL vide, utilisation du fallback...")
            from airbnb_scraper import scrape_fallback
            all_reservations = scrape_fallback(page)
        
        if not all_reservations:
            print("❌ Aucune réservation trouvée")
            return
        
        print(f"✅ {len(all_reservations)} réservations récupérées")
        
        # Trouver la réservation cible
        target_reservation = None
        for res in all_reservations:
            if res.get("id") == target_code:
                target_reservation = res
                break
        
        if not target_reservation:
            print(f"\n❌ Réservation {target_code} non trouvée")
            print(f"\n📋 Réservations disponibles (10 premières) :")
            for res in all_reservations[:10]:
                print(f"   • {res.get('id')} - {res.get('voyageur')} - {res.get('statut')}")
            return
        
        print(f"\n✅ Réservation trouvée :")
        print(f"   • ID : {target_reservation.get('id')}")
        print(f"   • Voyageur : {target_reservation.get('voyageur')}")
        print(f"   • Statut : {target_reservation.get('statut')}")
        print(f"   • Logement : {target_reservation.get('logement')}")
        print(f"   • Montant : {target_reservation.get('montant_total')} {target_reservation.get('devise')}")
        
        # Collecter les coordonnées
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 4 : COLLECTE DES COORDONNÉES")
        print(f"{'='*70}\n")
        
        contacts = get_guest_contact_info(page, target_code)
        
        target_reservation["telephone_voyageur"] = contacts["phone"]
        target_reservation["email_voyageur"] = contacts["email"]
        
        print(f"\n✅ Coordonnées collectées :")
        print(f"   • Téléphone : {contacts['phone'] or '❌ Non trouvé'}")
        print(f"   • Email : {contacts['email'] or '❌ Non trouvé'}")
        
        # Conversion de la devise
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 5 : CONVERSION DE LA DEVISE")
        print(f"{'='*70}\n")
        
        enriched = enrich_with_currency_ratio([target_reservation])
        target_reservation = enriched[0]
        
        montant = target_reservation.get("montant_total", 0)
        devise = target_reservation.get("currency_code", "DZD")
        ratio = target_reservation.get("currency_ratio", 1.0)
        montant_dzd = montant * ratio
        
        print(f"\n✅ Conversion effectuée :")
        print(f"   • Montant original : {montant} {devise}")
        print(f"   • Taux de conversion : {ratio}")
        print(f"   • Montant en DZD : {montant_dzd:,.2f} DZD")
        
        # Afficher les données complètes
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 6 : DONNÉES COMPLÈTES")
        print(f"{'='*70}\n")
        
        print(json.dumps(target_reservation, indent=2, ensure_ascii=False))
        
        # Envoi à l'API
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 7 : ENVOI À L'API NEXT.JS")
        print(f"{'='*70}\n")
        
        response = input("Voulez-vous envoyer cette réservation à l'API Next.js ? (o/n) : ")
        
        if response.lower() == 'o':
            try:
                result = send_to_nextjs_api([target_reservation], sync_type="manual")
                
                if result.get("success"):
                    print(f"\n✅ Envoi réussi !")
                    metrics = result.get("metrics", {})
                    print(f"   • Traitées : {metrics.get('processed', 0)}")
                    print(f"   • Créées : {metrics.get('created', 0)}")
                    print(f"   • Mises à jour : {metrics.get('updated', 0)}")
                else:
                    print(f"\n❌ Échec de l'envoi")
                    print(f"   Erreur : {result.get('error', 'Unknown')}")
            except Exception as e:
                print(f"\n❌ Exception lors de l'envoi : {e}")
        else:
            print("\n⚠️  Envoi annulé")
        
        # Résumé
        print(f"\n{'='*70}")
        print(f"   ✅ TEST TERMINÉ")
        print(f"{'='*70}\n")
        
        print("📊 Résumé :")
        print(f"   • Réservation : {target_code}")
        print(f"   • Voyageur : {target_reservation.get('voyageur')}")
        print(f"   • Téléphone : {target_reservation.get('telephone_voyageur') or '❌'}")
        print(f"   • Email : {target_reservation.get('email_voyageur') or '❌'}")
        print(f"   • Montant : {montant} {devise} = {montant_dzd:,.2f} DZD")
        
    finally:
        context.close()
        browser.close()
        if not USE_CLOAKBROWSER:
            pw.stop()
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
