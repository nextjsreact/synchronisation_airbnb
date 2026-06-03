#!/usr/bin/env python3
"""
Voir TOUTES les entrées dans sync_queue sans filtre
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("📦 TOUTES LES ENTRÉES DANS SYNC_QUEUE (sans filtre)")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "count=exact"
    }
    
    # Récupérer TOUTES les entrées
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=*&order=created_at.desc&limit=100",
        headers=headers
    )
    
    if response.status_code == 200:
        entries = response.json()
        total = response.headers.get('Content-Range', '').split('/')[-1]
        
        print(f"📊 TOTAL: {total} entrée(s) dans la table\n")
        
        if entries:
            # Grouper par status
            by_status = {}
            for entry in entries:
                status = entry.get('status', 'UNKNOWN')
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(entry)
            
            # Afficher par status
            for status, items in sorted(by_status.items()):
                emoji = "⏳" if status == "pending" else "✅" if status == "done" else "❌" if status == "error" else "❓"
                print(f"{emoji} {status.upper()}: {len(items)} entrée(s)")
                print("-"*80)
                
                for i, entry in enumerate(items[:20], 1):  # Max 20 par status
                    print(f"\n   {i}. ID: {entry.get('id', 'N/A')}")
                    print(f"      Listing ID: {entry['listing_id']}")
                    print(f"      Status: {entry.get('status', 'N/A')}")
                    print(f"      Retry count: {entry.get('retry_count', 0)}")
                    print(f"      Hash: {entry.get('hash', 'N/A')[:30]}...")
                    print(f"      Source: {entry.get('source', 'N/A')}")
                    print(f"      Créé: {entry.get('created_at', 'N/A')}")
                    if entry.get('error_message'):
                        print(f"      Erreur: {entry['error_message'][:100]}...")
                
                if len(items) > 20:
                    print(f"\n   ... et {len(items) - 20} autre(s) entrée(s) {status}")
                print()
        else:
            print("❌ La table est vraiment vide")
    
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
    
    # Proposer des actions
    print("\n" + "="*80)
    print("💡 ACTIONS POSSIBLES:")
    print("="*80)
    print("""
1️⃣  ENTRÉES PENDING:
   → Le Targeted Scraper les traitera automatiquement (dans 30s max)
   → AUCUNE action requise

2️⃣  ENTRÉES DONE:
   → Déjà traitées avec succès
   → Peuvent être supprimées pour nettoyer la base
   → Script: python cleanup_done_entries.py

3️⃣  ENTRÉES ERROR (échecs après 3 tentatives):
   → Option A: Les laisser (pour historique)
   → Option B: Les remettre en 'pending' pour réessayer
              Script: python reset_error_to_pending.py
   → Option C: Les supprimer
              Script: python delete_error_entries.py

4️⃣  Autres statuts:
   → Vérifier manuellement selon le cas
""")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
