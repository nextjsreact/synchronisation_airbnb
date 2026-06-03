#!/usr/bin/env python3
"""
Voir le format exact des réservations existantes
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("📋 FORMAT DES RÉSERVATIONS EXISTANTES")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Récupérer une réservation existante
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=*&limit=1",
        headers=headers
    )
    
    if response.status_code == 200 and response.json():
        reservation = response.json()[0]
        
        print("📊 Structure d'une réservation existante:\n")
        print(json.dumps(reservation, indent=2, ensure_ascii=False))
        
        print("\n" + "="*80)
        print("🔑 COLONNES DANS LA TABLE:")
        print("="*80 + "\n")
        
        for key, value in reservation.items():
            value_type = type(value).__name__
            value_str = str(value)[:50] if value else "NULL"
            print(f"   • {key:30} ({value_type:10}): {value_str}")
        
    else:
        print("❌ Impossible de récupérer une réservation")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
