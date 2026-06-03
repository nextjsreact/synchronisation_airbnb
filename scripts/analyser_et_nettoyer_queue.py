#!/usr/bin/env python3
"""
Analyser et nettoyer la sync_queue
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("🔍 ANALYSE COMPLÈTE DE LA SYNC_QUEUE")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "count=exact"
    }
    
    # Compter par status
    print("📊 STATISTIQUES PAR STATUS:")
    print("-"*80)
    
    stats = {}
    for status in ['pending', 'processing', 'done', 'error']:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.{status}&select=count",
            headers=headers
        )
        if response.status_code == 200:
            count = response.headers.get('Content-Range', '').split('/')[-1]
            stats[status] = int(count) if count and count != '*' else 0
            emoji = "⏳" if status == "pending" else "🔄" if status == "processing" else "✅" if status == "done" else "❌"
            print(f"   {emoji} {status.upper()}: {stats[status]}")
    
    total = sum(stats.values())
    print(f"\n   📦 TOTAL: {total} entrées\n")
    
    # PROBLÈME: Entrées "processing" bloquées
    if stats.get('processing', 0) > 0:
        print("="*80)
        print("🚨 PROBLÈME DÉTECTÉ: Entrées PROCESSING bloquées")
        print("="*80)
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.processing&select=*&order=created_at.asc",
            headers={k: v for k, v in headers.items() if k != 'Prefer'}
        )
        
        if response.status_code == 200:
            processing = response.json()
            print(f"\n   ⚠️  {len(processing)} entrée(s) bloquées en 'processing':\n")
            
            for i, entry in enumerate(processing, 1):
                created = entry.get('created_at', 'N/A')
                processed = entry.get('processed_at', 'N/A')
                print(f"   {i}. ID: {entry.get('id')}")
                print(f"      Listing: {entry['listing_id']}")
                print(f"      Créé: {created}")
                print(f"      Dernier processed_at: {processed}")
                print(f"      Retry count: {entry.get('retry_count', 0)}")
                print()
            
            print("   💡 CES ENTRÉES SONT BLOQUÉES !")
            print("      Le status 'processing' signifie qu'elles ont été commencées")
            print("      mais jamais finalisées (crash, timeout, etc.)")
            print("\n   ✅ SOLUTION: Les remettre en 'pending' pour réessayer\n")
    
    # Entrées ERROR
    if stats.get('error', 0) > 0:
        print("="*80)
        print("❌ ENTRÉES ERROR (échecs définitifs)")
        print("="*80)
        
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.error&select=*&order=created_at.desc&limit=10",
            headers={k: v for k, v in headers.items() if k != 'Prefer'}
        )
        
        if response.status_code == 200:
            errors = response.json()
            print(f"\n   ⚠️  {stats['error']} erreur(s) (affichage des 10 dernières):\n")
            
            for i, entry in enumerate(errors, 1):
                print(f"   {i}. ID: {entry.get('id')}")
                print(f"      Listing: {entry['listing_id']}")
                print(f"      Créé: {entry.get('created_at', 'N/A')}")
                print(f"      Retry count: {entry.get('retry_count', 0)}")
                if entry.get('error_message'):
                    print(f"      Erreur: {entry['error_message'][:100]}...")
                print()
    
    # Entrées DONE anciennes
    if stats.get('done', 0) > 50:
        print("="*80)
        print("🧹 NETTOYAGE RECOMMANDÉ: Trop d'entrées DONE")
        print("="*80)
        print(f"\n   ℹ️  {stats['done']} entrées 'done' dans la table")
        print("      Ces entrées ont été traitées avec succès")
        print("      Elles peuvent être archivées ou supprimées\n")
    
    # RECOMMANDATIONS
    print("="*80)
    print("💡 ACTIONS RECOMMANDÉES:")
    print("="*80 + "\n")
    
    actions = []
    
    if stats.get('processing', 0) > 0:
        actions.append(f"1️⃣  URGENT: Débloquer {stats['processing']} entrée(s) 'processing'")
        actions.append("   → python reset_processing_to_pending.py")
    
    if stats.get('error', 0) > 0:
        actions.append(f"2️⃣  Gérer {stats['error']} erreur(s):")
        actions.append("   → Remettre en pending: python reset_error_to_pending.py")
        actions.append("   → Ou supprimer: python delete_error_entries.py")
    
    if stats.get('done', 0) > 50:
        actions.append(f"3️⃣  Nettoyer {stats['done']} entrée(s) 'done':")
        actions.append("   → Supprimer les anciennes (>7 jours): python cleanup_old_done.py")
    
    if stats.get('pending', 0) > 0:
        actions.append(f"4️⃣  {stats['pending']} entrée(s) 'pending':")
        actions.append("   → Seront traitées automatiquement par le Targeted Scraper")
        actions.append("   → Aucune action requise")
    
    if actions:
        for action in actions:
            print(action)
    else:
        print("✅ Aucune action requise - tout est normal!")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
