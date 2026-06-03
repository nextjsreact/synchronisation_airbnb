#!/usr/bin/env python3
"""
Vérifier l'état de la queue de synchronisation
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("🔍 Vérification de la sync_queue...\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Vérifier les entrées pending
    print("📋 Entrées PENDING (à traiter):")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.pending&select=*&order=retry_count.desc,created_at.asc&limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        pending = response.json()
        if pending:
            print(f"   ✅ {len(pending)} entrée(s) en attente:\n")
            for entry in pending:
                print(f"   • Listing ID: {entry['listing_id']}")
                print(f"     Status: {entry['status']}")
                print(f"     Retry count: {entry.get('retry_count', 0)}")
                print(f"     Créé: {entry['created_at']}")
                if entry.get('error_message'):
                    print(f"     Erreur: {entry['error_message'][:100]}...")
                print()
        else:
            print("   ✅ Aucune entrée pending\n")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}\n")
    
    # Vérifier les entrées en erreur
    print("❌ Entrées ERROR (échecs définitifs):")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.error&select=*&order=updated_at.desc&limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        errors = response.json()
        if errors:
            print(f"   ⚠️  {len(errors)} entrée(s) en erreur:\n")
            for entry in errors:
                print(f"   • Listing ID: {entry['listing_id']}")
                print(f"     Retry count: {entry.get('retry_count', 0)}")
                print(f"     Mis à jour: {entry['updated_at']}")
                if entry.get('error_message'):
                    print(f"     Erreur: {entry['error_message'][:100]}...")
                print()
        else:
            print("   ✅ Aucune entrée en erreur\n")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}\n")
    
    # Vérifier les entrées done
    print("✅ Entrées DONE (complétées):")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.done&select=*&order=updated_at.desc&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        done = response.json()
        if done:
            print(f"   ✅ {len(done)} entrée(s) récentes complétées:\n")
            for entry in done:
                print(f"   • Listing ID: {entry['listing_id']}")
                print(f"     Retry count: {entry.get('retry_count', 0)}")
                print(f"     Mis à jour: {entry['updated_at']}")
                print()
        else:
            print("   ⚠️  Aucune entrée complétée\n")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}\n")
    
    # Statistiques
    print("📊 STATISTIQUES GLOBALES:")
    for status in ['pending', 'done', 'error']:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.{status}&select=count",
            headers={**headers, "Prefer": "count=exact"}
        )
        if response.status_code == 200:
            count = response.headers.get('Content-Range', '').split('/')[-1]
            print(f"   • {status.upper()}: {count}")
    
    print("\n✅ Vérification terminée!")

if __name__ == "__main__":
    main()
