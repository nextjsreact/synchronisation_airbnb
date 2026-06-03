#!/usr/bin/env python3
"""
Remettre les entrées 'processing' en 'pending' pour qu'elles soient retraitées
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("🔄 DÉBLOCAGE DES ENTRÉES 'PROCESSING'")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Récupérer les entrées 'processing'
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.processing&select=*",
        headers={k: v for k, v in headers.items() if k != 'Prefer'}
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur lecture: {response.status_code} - {response.text}")
        return
    
    processing_entries = response.json()
    
    if not processing_entries:
        print("✅ Aucune entrée 'processing' trouvée - tout est OK!\n")
        return
    
    print(f"📋 {len(processing_entries)} entrée(s) bloquée(s) en 'processing':\n")
    
    for i, entry in enumerate(processing_entries, 1):
        print(f"   {i}. ID {entry['id']} - Listing {entry['listing_id']}")
        print(f"      Créé: {entry.get('created_at', 'N/A')}")
        print(f"      Dernier traitement: {entry.get('processed_at', 'N/A')}")
        print()
    
    # Demander confirmation
    print("-"*80)
    confirmation = input("❓ Voulez-vous remettre ces entrées en 'pending' ? (oui/non): ").strip().lower()
    
    if confirmation not in ['oui', 'o', 'yes', 'y']:
        print("\n❌ Annulé - aucune modification effectuée\n")
        return
    
    print("\n🔄 Remise en 'pending' en cours...\n")
    
    # Mettre à jour chaque entrée
    success_count = 0
    for entry in processing_entries:
        update_data = {
            "status": "pending",
            "error_message": None,
            "retry_count": entry.get('retry_count', 0)  # Conserver retry_count
        }
        
        response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/sync_queue?id=eq.{entry['id']}",
            headers=headers,
            json=update_data
        )
        
        if response.status_code in [200, 204]:
            print(f"   ✅ ID {entry['id']} (Listing {entry['listing_id']}) → pending")
            success_count += 1
        else:
            print(f"   ❌ ID {entry['id']} - Erreur: {response.status_code}")
    
    print(f"\n✅ {success_count}/{len(processing_entries)} entrée(s) remise(s) en 'pending'")
    print("\n💡 PROCHAINES ÉTAPES:")
    print("   • Le Targeted Scraper détectera ces entrées dans max 30s")
    print("   • Elles seront retraitées avec le système de retry (3 tentatives)")
    print("   • Surveillez les logs: docker compose -f docker-compose.sync.yml logs -f targeted-scraper")
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
