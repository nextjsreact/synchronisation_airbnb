#!/usr/bin/env python3
"""
Lister TOUTES les entrées dans sync_queue sans aucun filtre
"""

import os
import requests
from dotenv import load_dotenv
from collections import Counter

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("📦 ANALYSE BRUTE DE SYNC_QUEUE (sans filtre)")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Récupérer TOUT sans filtre
    all_entries = []
    offset = 0
    limit = 1000
    
    while True:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?select=*&order=id.desc&limit={limit}&offset={offset}",
            headers=headers
        )
        
        if response.status_code in [200, 206]:  # 206 = Partial Content
            data = response.json()
            if not data:
                break
            all_entries.extend(data)
            print(f"   Récupéré {len(data)} entrées (offset {offset})...")
            offset += limit
            
            # Si moins que limit, c'est la dernière page
            if len(data) < limit:
                break
        else:
            print(f"   ❌ Erreur: {response.status_code} - {response.text[:200]}")
            break
    
    print(f"\n✅ Total récupéré: {len(all_entries)} entrées\n")
    
    if not all_entries:
        print("❌ La table est vraiment vide\n")
        return
    
    # Analyser les status
    statuses = Counter(entry.get('status', 'NULL') for entry in all_entries)
    
    print("="*80)
    print("📊 RÉPARTITION PAR STATUS:")
    print("="*80 + "\n")
    
    for status, count in statuses.most_common():
        emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'done': '✅',
            'error': '❌',
            'NULL': '❓'
        }.get(status, '❔')
        print(f"   {emoji} {status or 'NULL'}: {count}")
    
    # Détails des entrées problématiques
    processing = [e for e in all_entries if e.get('status') == 'processing']
    errors = [e for e in all_entries if e.get('status') == 'error']
    pending = [e for e in all_entries if e.get('status') == 'pending']
    
    if processing:
        print("\n" + "="*80)
        print(f"🚨 {len(processing)} ENTRÉES BLOQUÉES EN 'PROCESSING':")
        print("="*80 + "\n")
        
        for i, entry in enumerate(processing[:10], 1):
            print(f"   {i}. ID: {entry.get('id')} | Listing: {entry['listing_id']}")
            print(f"      Créé: {entry.get('created_at', 'N/A')}")
            print(f"      Dernier traitement: {entry.get('processed_at', 'N/A')}")
            print(f"      Retry: {entry.get('retry_count', 0)}")
            print()
        
        if len(processing) > 10:
            print(f"   ... et {len(processing) - 10} autre(s)\n")
    
    if errors:
        print("="*80)
        print(f"❌ {len(errors)} ENTRÉES EN ERREUR:")
        print("="*80 + "\n")
        
        for i, entry in enumerate(errors[:5], 1):
            print(f"   {i}. ID: {entry.get('id')} | Listing: {entry['listing_id']}")
            print(f"      Créé: {entry.get('created_at', 'N/A')}")
            print(f"      Retry: {entry.get('retry_count', 0)}")
            if entry.get('error_message'):
                print(f"      Erreur: {entry['error_message'][:80]}...")
            print()
        
        if len(errors) > 5:
            print(f"   ... et {len(errors) - 5} autre(s)\n")
    
    if pending:
        print("="*80)
        print(f"⏳ {len(pending)} ENTRÉES PENDING (seront traitées auto):")
        print("="*80 + "\n")
        
        for i, entry in enumerate(pending[:5], 1):
            print(f"   {i}. ID: {entry.get('id')} | Listing: {entry['listing_id']}")
            print(f"      Créé: {entry.get('created_at', 'N/A')}")
            print(f"      Retry: {entry.get('retry_count', 0)}")
            print()
    
    # RECOMMANDATIONS
    print("="*80)
    print("💡 QUE FAIRE ?")
    print("="*80 + "\n")
    
    if processing:
        print(f"1️⃣  URGENT: {len(processing)} entrées 'processing' sont BLOQUÉES")
        print("   Ces entrées ne seront JAMAIS traitées automatiquement")
        print("   ✅ SOLUTION: Les remettre en 'pending'")
        print("   📝 Commande: python reset_processing_to_pending.py\n")
    
    if errors:
        print(f"2️⃣  {len(errors)} entrées en 'error'")
        print("   Ces entrées ont échoué après plusieurs tentatives")
        print("   OPTIONS:")
        print("   • Les remettre en 'pending' pour réessayer")
        print("   • Les supprimer si elles sont anciennes\n")
    
    done_count = statuses.get('done', 0)
    if done_count > 50:
        print(f"3️⃣  {done_count} entrées 'done' (complétées)")
        print("   Recommandation: Nettoyer les entrées > 7 jours")
        print("   📝 Commande: python cleanup_old_done.py\n")
    
    if pending:
        print(f"4️⃣  {len(pending)} entrées 'pending'")
        print("   ✅ NORMAL: Seront traitées automatiquement par le Targeted Scraper\n")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
