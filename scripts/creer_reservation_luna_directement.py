#!/usr/bin/env python3
"""
Créer une réservation test pour Luna loft directement dans Supabase
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

LUNA_LOFT_ID = "faf9a006-2b66-4499-a4c9-b08e3908e64f"

def main():
    print("\n" + "="*80)
    print("🎯 CRÉATION D'UNE RÉSERVATION TEST POUR LUNA LOFT")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Créer la réservation
    reservation = {
        "guest_name": "Test Luna Guest",
        "guest_email": "test@luna.com",
        "guest_phone": "+33600000000",
        "guest_count": 2,
        "loft_id": LUNA_LOFT_ID,
        "check_in_date": "2026-06-10",
        "check_out_date": "2026-06-12",
        "base_price": 15000.0,
        "cleaning_fee": 2000.0,
        "service_fee": 1000.0,
        "taxes": 500.0,
        "total_amount": 18500.0,
        "status": "confirmed",
        "payment_status": "paid",
        "currency_code": "DZD",
        "currency_ratio": 1.0,
        "price_per_night_input": 7500.0,
        "source": "airbnb",
        "airbnb_confirmation_code": "TEST_LUNA_" + datetime.now().strftime("%Y%m%d%H%M%S"),
    }
    
    print("📝 Création de la réservation...")
    print(f"   Guest: {reservation['guest_name']}")
    print(f"   Check-in: {reservation['check_in_date']}")
    print(f"   Check-out: {reservation['check_out_date']}")
    print(f"   Total: {reservation['total_amount']} {reservation['currency_code']}")
    print(f"   Code confirmation: {reservation['airbnb_confirmation_code']}\n")
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/reservations",
        json=reservation,
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        print("✅ Réservation créée avec succès!")
        
        if response.json():
            created = response.json()[0]
            print(f"\n   ID: {created.get('id')}")
            print(f"   Créée à: {created.get('created_at')}\n")
        
        print("💡 VÉRIFICATION:")
        print("   Allez dans votre application Next.js")
        print("   Vous devriez voir cette réservation pour Luna loft")
        print("   Dates: 10-12 juin 2026")
        
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   {response.text}\n")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
