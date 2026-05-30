"""
test_with_sample_data.py - Test du système avec des données fictives réalistes
===============================================================================
Version  : 1.0.0
Date     : Mai 2026

Ce script teste l'intégration complète sans scraper Airbnb.
Utile pour valider que tout fonctionne avant le scraping réel.
"""

import sys
import os

# Ajouter le chemin pour importer airbnb_api_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  python-dotenv non installé")

from airbnb_api_client import send_to_nextjs_api

# Données de test réalistes (comme si elles venaient d'Airbnb)
sample_reservations = [
    {
        "id": "HM2026001",
        "listing_id": "12345678",
        "statut": "Confirmee",
        "voyageur": "Marie Dubois",
        "nb_voyageurs": 2,
        "date_arrivee": "2026-06-15",
        "date_depart": "2026-06-20",
        "nb_nuits": 5,
        "montant_total": 75000.00,
        "devise": "DZD",
        "base_price": 65000.00,
        "cleaning_fee": 5000.00,
        "service_fee": 3000.00,
        "taxes": 2000.00,
        "guest_email": "marie.dubois@example.fr",
        "guest_phone": "+33612345678",
        "guest_nationality": "FR",
        "special_requests": "Arrivée tardive vers 22h"
    },
    {
        "id": "HM2026002",
        "listing_id": "12345678",
        "statut": "Confirmee",
        "voyageur": "Ahmed Mansouri",
        "nb_voyageurs": 4,
        "date_arrivee": "2026-07-01",
        "date_depart": "2026-07-10",
        "nb_nuits": 9,
        "montant_total": 135000.00,
        "devise": "DZD",
        "base_price": 120000.00,
        "cleaning_fee": 7000.00,
        "service_fee": 5000.00,
        "taxes": 3000.00,
        "guest_email": "ahmed.mansouri@example.dz",
        "guest_phone": "+213555123456",
        "guest_nationality": "DZ",
        "special_requests": ""
    },
    {
        "id": "HM2026003",
        "listing_id": "87654321",
        "statut": "En attente",
        "voyageur": "John Smith",
        "nb_voyageurs": 3,
        "date_arrivee": "2026-08-05",
        "date_depart": "2026-08-12",
        "nb_nuits": 7,
        "montant_total": 105000.00,
        "devise": "DZD",
        "base_price": 95000.00,
        "cleaning_fee": 5000.00,
        "service_fee": 3500.00,
        "taxes": 1500.00,
        "guest_email": "john.smith@example.com",
        "guest_phone": "+14155551234",
        "guest_nationality": "US",
        "special_requests": "Besoin d'un lit bébé"
    }
]

def main():
    print("=" * 70)
    print("   Test du système avec données fictives réalistes")
    print("=" * 70)
    print()
    
    print(f"📋 {len(sample_reservations)} réservations de test")
    print()
    
    for i, res in enumerate(sample_reservations, 1):
        print(f"   {i}. {res['id']} - {res['voyageur']}")
        print(f"      {res['date_arrivee']} → {res['date_depart']} ({res['nb_nuits']} nuits)")
        print(f"      {res['montant_total']:,.0f} {res['devise']}")
        print(f"      📧 {res['guest_email']}")
        print(f"      📱 {res['guest_phone']}")
        print()
    
    print("☁️  Envoi vers l'API Next.js...")
    print()
    
    try:
        result = send_to_nextjs_api(sample_reservations, sync_type="manual")
        
        print()
        print("=" * 70)
        print("✅ Test réussi!")
        print("=" * 70)
        print()
        print("Prochaines étapes:")
        print("  1. Vérifiez les données dans Supabase")
        print("  2. Mappez les listing_id aux lofts")
        print("  3. Lancez le scraper Airbnb réel")
        print()
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ Test échoué!")
        print("=" * 70)
        print(f"Erreur: {e}")
        print()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
