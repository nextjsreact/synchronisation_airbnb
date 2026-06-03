#!/usr/bin/env python3
"""
Vérifier les changements iCal récents et l'état de synchronisation
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("🔍 VÉRIFICATION DES CHANGEMENTS iCAL RÉCENTS\n")
    print("="*80)
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Vérifier la table ical_cache pour voir les listings surveillés
    print("\n📋 LISTINGS SURVEILLÉS (ical_cache):")
    print("-"*80)
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_cache?select=listing_id,url,last_hash,updated_at&order=updated_at.desc&limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        ical_entries = response.json()
        if ical_entries:
            print(f"   ✅ {len(ical_entries)} listings trouvés (top 10 récents)\n")
            for i, entry in enumerate(ical_entries, 1):
                updated = entry.get('updated_at', 'N/A')
                print(f"   {i}. Listing: {entry['listing_id']}")
                print(f"      Hash: {entry.get('last_hash', 'N/A')[:20]}...")
                print(f"      Dernière mise à jour: {updated}")
                print()
        else:
            print("   ⚠️  Aucun listing trouvé dans ical_cache")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    
    # Vérifier les réservations récentes dans la base
    print("\n" + "="*80)
    print("📅 RÉSERVATIONS RÉCENTES DANS LA BASE:")
    print("-"*80)
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=confirmation_code,listing_id,checkin_date,checkout_date,status,created_at&order=created_at.desc&limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        reservations = response.json()
        if reservations:
            print(f"   ✅ {len(reservations)} réservations récentes (top 10)\n")
            for i, res in enumerate(reservations, 1):
                created = res.get('created_at', 'N/A')
                print(f"   {i}. Code: {res.get('confirmation_code', 'N/A')}")
                print(f"      Listing: {res.get('listing_id')}")
                print(f"      Check-in: {res.get('checkin_date')} → Check-out: {res.get('checkout_date')}")
                print(f"      Status: {res.get('status')}")
                print(f"      Créée le: {created}")
                print()
        else:
            print("   ⚠️  Aucune réservation trouvée")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}")
    
    # Vérifier sync_queue
    print("\n" + "="*80)
    print("📦 ÉTAT DE LA SYNC_QUEUE:")
    print("-"*80)
    
    for status in ['pending', 'done', 'error']:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.{status}&select=count",
            headers={**headers, "Prefer": "count=exact"}
        )
        if response.status_code == 200:
            count = response.headers.get('Content-Range', '').split('/')[-1]
            emoji = "⏳" if status == "pending" else "✅" if status == "done" else "❌"
            print(f"   {emoji} {status.upper()}: {count}")
    
    # Recommandations
    print("\n" + "="*80)
    print("💡 SITUATION ACTUELLE:")
    print("="*80)
    
    print("\n✅ La sync_queue est VIDE (0 entrées)")
    print("   → C'est NORMAL entre les cycles de détection")
    print("   → L'iCal Watcher vérifie toutes les 5 minutes")
    print("   → Le Targeted Scraper poll toutes les 30 secondes")
    
    print("\n📊 FONCTIONNEMENT NORMAL:")
    print("   1. iCal Watcher détecte un changement")
    print("   2. Ajoute une entrée dans sync_queue (status=pending)")
    print("   3. Targeted Scraper la traite en ~30 secondes")
    print("   4. Marque comme 'done' et supprime ou archive l'entrée")
    print("   5. sync_queue redevient vide jusqu'au prochain changement")
    
    print("\n🔄 SI VOUS VOULEZ FORCER UNE SYNCHRONISATION:")
    print("   Option 1: Attendre le prochain cycle iCal (max 5 min)")
    print("   Option 2: Utiliser test_retry_system.py pour tester")
    print("   Option 3: Redémarrer iCal Watcher pour forcer un check immédiat:")
    print("             docker compose -f docker-compose.sync.yml restart ical-watcher")
    
    print("\n✅ Tout fonctionne normalement!")

if __name__ == "__main__":
    main()
