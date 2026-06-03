#!/usr/bin/env python3
"""
Forcer le scraping de Luna loft immédiatement
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

LUNA_LISTING_ID = "1352875010941932574"

def main():
    print("\n" + "="*80)
    print("🚀 FORCER LE SCRAPING DE LUNA LOFT")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Ajouter dans sync_queue
    payload = {
        "listing_id": LUNA_LISTING_ID,
        "status": "pending",
        "reason": "manual_force",
        "retry_count": 0,
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    }
    
    print(f"📝 Ajout de Luna loft (listing {LUNA_LISTING_ID}) dans sync_queue...")
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/sync_queue",
        json=payload,
        headers=headers
    )
    
    if response.status_code in [200, 201]:
        print("✅ Ajouté avec succès dans sync_queue!\n")
        print("💡 PROCHAINES ÉTAPES:")
        print("   • Le Targeted Scraper va détecter cette entrée dans ~30s")
        print("   • Il va scraper Luna loft en mode optimisé (upcoming uniquement)")
        print("   • Surveillez les logs:\n")
        print("     docker compose -f docker-compose.sync.yml logs -f targeted-scraper\n")
        print("🔍 Recherchez:")
        print("   • 'Queue #... — listing 1352875010941932574'")
        print("   • 'X reservations trouvees'")
        print("   • '✅ Scraping réussi'")
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}\n")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
