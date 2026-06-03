#!/usr/bin/env python3
"""
Vérifier TOUTES les entrées dans sync_queue et proposer des actions
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("🔍 ANALYSE COMPLÈTE DE LA SYNC_QUEUE\n")
    print("="*80)
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "count=exact"
    }
    
    # Statistiques globales
    print("\n📊 STATISTIQUES GLOBALES:")
    print("-"*80)
    
    stats = {}
    for status in ['pending', 'done', 'error']:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.{status}&select=count",
            headers=headers
        )
        if response.status_code == 200:
            count = response.headers.get('Content-Range', '').split('/')[-1]
            stats[status] = int(count) if count != '*' else 0
            
            emoji = "⏳" if status == "pending" else "✅" if status == "done" else "❌"
            print(f"   {emoji} {status.upper()}: {stats[status]}")
    
    total = sum(stats.values())
    print(f"\n   📦 TOTAL: {total} entrées dans sync_queue")
    
    # Détails des entrées PENDING
    if stats.get('pending', 0) > 0:
        print("\n" + "="*80)
        print("⏳ ENTRÉES PENDING (à traiter):")
        print("-"*80)
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.pending&select=*&order=created_at.desc&limit=50",
            headers={k: v for k, v in headers.items() if k != 'Prefer'}
        )
        
        if response.status_code == 200:
            pending = response.json()
            for i, entry in enumerate(pending, 1):
                print(f"\n   {i}. Listing ID: {entry['listing_id']}")
                print(f"      Status: {entry['status']}")
                print(f"      Retry count: {entry.get('retry_count', 0)}")
                print(f"      Créé: {entry['created_at']}")
                if entry.get('error_message'):
                    print(f"      Dernière erreur: {entry['error_message'][:80]}...")
        
        print("\n   ℹ️  Ces entrées seront traitées AUTOMATIQUEMENT par le Targeted Scraper")
        print("   ℹ️  Prochaine tentative dans max 30 secondes")
    
    # Détails des entrées ERROR (échecs définitifs)
    if stats.get('error', 0) > 0:
        print("\n" + "="*80)
        print("❌ ENTRÉES ERROR (échecs définitifs):")
        print("-"*80)
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.error&select=*&order=created_at.desc&limit=20",
            headers={k: v for k, v in headers.items() if k != 'Prefer'}
        )
        
        if response.status_code == 200:
            errors = response.json()
            for i, entry in enumerate(errors, 1):
                print(f"\n   {i}. Listing ID: {entry['listing_id']}")
                print(f"      Retry count: {entry.get('retry_count', 0)}/3")
                print(f"      Créé: {entry['created_at']}")
                if entry.get('error_message'):
                    print(f"      Erreur: {entry['error_message'][:100]}...")
    
    # Entrées DONE récentes
    if stats.get('done', 0) > 0:
        print("\n" + "="*80)
        print("✅ DERNIÈRES ENTRÉES DONE (5 plus récentes):")
        print("-"*80)
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.done&select=listing_id,created_at,retry_count&order=created_at.desc&limit=5",
            headers={k: v for k, v in headers.items() if k != 'Prefer'}
        )
        
        if response.status_code == 200:
            done = response.json()
            for i, entry in enumerate(done, 1):
                print(f"   {i}. Listing {entry['listing_id']} (retry: {entry.get('retry_count', 0)})")
    
    # RECOMMANDATIONS
    print("\n" + "="*80)
    print("💡 RECOMMANDATIONS:")
    print("="*80)
    
    if stats.get('pending', 0) > 0:
        print(f"\n✅ {stats['pending']} entrée(s) PENDING:")
        print("   → Le Targeted Scraper va les traiter automatiquement")
        print("   → AUCUNE ACTION REQUISE de votre part")
        print("   → Surveillez les logs: docker compose -f docker-compose.sync.yml logs -f targeted-scraper")
    
    if stats.get('error', 0) > 0:
        print(f"\n⚠️  {stats['error']} entrée(s) ERROR (échecs définitifs après 3 tentatives):")
        print("   → OPTIONS:")
        print("   → 1) Les laisser (anciennes entrées, probablement pas importantes)")
        print("   → 2) Les remettre en 'pending' pour réessayer (script fourni)")
        print("   → 3) Les supprimer (nettoyage)")
        print("\n   💡 CONSEIL: Vérifiez d'abord les dates. Si elles sont anciennes (>1 mois),")
        print("              vous pouvez les supprimer sans risque.")
    
    if stats.get('done', 0) > 100:
        print(f"\n🧹 {stats['done']} entrée(s) DONE (complétées):")
        print("   → Ces entrées peuvent être archivées/supprimées pour alléger la base")
        print("   → Script de nettoyage fourni")
    
    print("\n" + "="*80)
    print("🔧 SCRIPTS DISPONIBLES:")
    print("="*80)
    print("   • reset_error_entries.py - Remettre les ERROR en pending pour réessayer")
    print("   • cleanup_old_done.py - Nettoyer les anciennes entrées DONE")
    print("   • delete_all_errors.py - Supprimer toutes les entrées ERROR")
    print("="*80)
    
    print("\n✅ Analyse terminée!")

if __name__ == "__main__":
    main()
