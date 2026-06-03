"""
TEST_RAPIDE_UNE_RESERVATION.py - Test rapide avec une réservation
==================================================================
Ce script teste rapidement avec une réservation existante :
1. Charge les données depuis le CSV
2. Collecte les coordonnées (téléphone + email)
3. Conversion de la devise
4. Envoi à l'API Next.js

Usage :
    python TEST_RAPIDE_UNE_RESERVATION.py [CODE_CONFIRMATION]
"""

import os
import sys
import json
import csv
from datetime import datetime

# Forcer UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
load_dotenv(encoding='utf-8')

# Imports
from airbnb_scraper import login, is_logged_in, SESSION_FILE
from currency_converter import enrich_with_currency_ratio
from airbnb_api_client import send_to_nextjs_api

# CloakBrowser
try:
    from cloakbrowser import launch as cloak_launch
    USE_CLOAKBROWSER = True
except ImportError:
    USE_CLOAKBROWSER = False

HEADLESS = os.environ.get("HEADLESS", "false").lower() == "true"
PROXY_URL = os.environ.get("PROXY_URL", "")


def get_guest_contact_info(page, confirmation_code):
    """Récupère les coordonnées d'un voyageur."""
    print(f"\n📞 Récupération des coordonnées pour {confirmation_code}...")
    
    try:
        url = f"https://fr.airbnb.com/hosting/stay/{confirmation_code}?tab=upcoming"
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        
        phone = None
        email = None
        page_content = page.content()
        
        import re
        
        # Chercher le téléphone
        phone_pattern = r'Numéro de téléphone[:\s]*[^+\n]*\n?\s*(\+?\d[\d\s\-\(\)]{8,})'
        match = re.search(phone_pattern, page_content, re.IGNORECASE)
        if match:
            phone = match.group(1).strip()
            print(f"   ✅ Téléphone trouvé : {phone}")
        
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


def load_reservation_from_csv(target_code):
    """Charge une réservation depuis le CSV."""
    csv_file = "output/reservations_airbnb.csv"
    
    if not os.path.exists(csv_file):
        print(f"❌ Fichier {csv_file} introuvable")
        return None
    
    print(f"📂 Chargement depuis {csv_file}...")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('id') == target_code:
                # Convertir les types
                row['montant_total'] = float(row['montant_total'])
                row['nb_voyageurs'] = int(row['nb_voyageurs'])
                row['nb_nuits'] = int(row['nb_nuits']) if row.get('nb_nuits') else 0
                return row
    
    return None


def main():
    print("="*70)
    print("   🧪 TEST RAPIDE AVEC UNE RÉSERVATION")
    print("="*70)
    print(f"\n   Date : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # Code de confirmation
    if len(sys.argv) > 1:
        target_code = sys.argv[1]
    else:
        target_code = "HM4TB95HKS"
    
    print(f"   Code : {target_code}")
    
    # Charger depuis le CSV
    print(f"\n{'='*70}")
    print(f"   ÉTAPE 1 : CHARGEMENT DES DONNÉES")
    print(f"{'='*70}\n")
    
    reservation = load_reservation_from_csv(target_code)
    
    if not reservation:
        print(f"❌ Réservation {target_code} non trouvée dans le CSV")
        return
    
    print(f"✅ Réservation trouvée :")
    print(f"   • ID : {reservation.get('id')}")
    print(f"   • Voyageur : {reservation.get('voyageur')}")
    print(f"   • Statut : {reservation.get('statut')}")
    print(f"   • Logement : {reservation.get('logement')}")
    print(f"   • Montant : {reservation.get('montant_total')} {reservation.get('devise')}")
    
    # Lancer le navigateur
    print(f"\n{'='*70}")
    print(f"   ÉTAPE 2 : LANCEMENT DU NAVIGATEUR")
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
    
    ctx_opts = {"viewport": {"width": 1280, "height": 800}, "locale": "fr-FR"}
    if os.path.exists(SESSION_FILE):
        print(f"   💾 Session trouvée : chargement...")
        ctx_opts["storage_state"] = SESSION_FILE
    
    context = browser.new_context(**ctx_opts)
    page = context.new_page()
    
    try:
        # Login
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 3 : CONNEXION À AIRBNB")
        print(f"{'='*70}\n")
        
        if os.path.exists(SESSION_FILE):
            if is_logged_in(page):
                print("   ✅ Session valide — connexion automatique !")
            else:
                print("   ⚠️  Session expirée — reconnexion...")
                login(page)
        else:
            login(page)
        
        # Collecter les coordonnées
        print(f"\n{'='*70}")
        print(f"   ÉTAPE 4 : COLLECTE DES COORDONNÉES")
        print(f"{'='*70}")
        
        contacts = get_guest_contact_info(page, target_code)
        
        reservation["telephone_voyageur"] = contacts["phone"]
        reservation["email_voyageur"] = contacts["email"]
        
        print(f"\n✅ Coordonnées collectées :")
        print(f"   • Téléphone : {contacts['phone'] or '❌ Non trouvé'}")
        print(f"   • Email : {contacts['email'] or '❌ Non trouvé'}")
        
    finally:
        context.close()
        browser.close()
        if not USE_CLOAKBROWSER:
            pw.stop()
    
    # Conversion de la devise
    print(f"\n{'='*70}")
    print(f"   ÉTAPE 5 : CONVERSION DE LA DEVISE")
    print(f"{'='*70}\n")
    
    enriched = enrich_with_currency_ratio([reservation])
    reservation = enriched[0]
    
    montant = reservation.get("montant_total", 0)
    devise = reservation.get("currency_code", "DZD")
    ratio = reservation.get("currency_ratio", 1.0)
    montant_dzd = montant * ratio
    
    print(f"✅ Conversion effectuée :")
    print(f"   • Montant original : {montant} {devise}")
    print(f"   • Taux : {ratio}")
    print(f"   • Montant en DZD : {montant_dzd:,.2f} DZD")
    
    # Afficher les données
    print(f"\n{'='*70}")
    print(f"   ÉTAPE 6 : DONNÉES COMPLÈTES")
    print(f"{'='*70}\n")
    
    print(json.dumps(reservation, indent=2, ensure_ascii=False))
    
    # Envoi à l'API
    print(f"\n{'='*70}")
    print(f"   ÉTAPE 7 : ENVOI À L'API")
    print(f"{'='*70}\n")
    
    response = input("Envoyer à l'API Next.js ? (o/n) : ")
    
    if response.lower() == 'o':
        try:
            result = send_to_nextjs_api([reservation], sync_type="manual")
            
            if result.get("success"):
                print(f"\n✅ Envoi réussi !")
                metrics = result.get("metrics", {})
                print(f"   • Traitées : {metrics.get('processed', 0)}")
                print(f"   • Créées : {metrics.get('created', 0)}")
                print(f"   • Mises à jour : {metrics.get('updated', 0)}")
            else:
                print(f"\n❌ Échec")
                print(f"   Erreur : {result.get('error', 'Unknown')}")
        except Exception as e:
            print(f"\n❌ Exception : {e}")
    else:
        print("\n⚠️  Envoi annulé")
    
    # Résumé
    print(f"\n{'='*70}")
    print(f"   ✅ TEST TERMINÉ")
    print(f"{'='*70}\n")
    
    print("📊 Résumé :")
    print(f"   • Réservation : {target_code}")
    print(f"   • Voyageur : {reservation.get('voyageur')}")
    print(f"   • Téléphone : {reservation.get('telephone_voyageur') or '❌'}")
    print(f"   • Email : {reservation.get('email_voyageur') or '❌'}")
    print(f"   • Montant : {montant} {devise} = {montant_dzd:,.2f} DZD")
    
    print(f"\n{'='*70}\n")


if __name__ == "__main__":
    main()
