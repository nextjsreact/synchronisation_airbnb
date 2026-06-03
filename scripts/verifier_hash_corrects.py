#!/usr/bin/env python3
"""
Vérifier les hash avec les BONS noms de colonnes (hash, checked_at)
"""

import os
import requests
import hashlib
import re
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION DES HASH AVEC LES BONS NOMS DE COLONNES")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Lire avec les BONS noms de colonnes
    print("1️⃣  Lecture de ical_hashes (colonnes: hash, checked_at, changed_at)...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_hashes?select=listing_id,hash,checked_at,changed_at&limit=10",
        headers=headers
    )
    
    if response.status_code == 200:
        entries = response.json()
        print(f"   ✅ {len(entries)} entrée(s) trouvée(s):\n")
        
        hash_count = sum(1 for e in entries if e.get('hash'))
        
        for i, entry in enumerate(entries[:5], 1):
            print(f"   {i}. Listing: {entry.get('listing_id', 'N/A')}")
            print(f"      Hash: {entry.get('hash', 'N/A')[:30] if entry.get('hash') else 'NULL'}...")
            print(f"      Checked: {entry.get('checked_at', 'N/A')}")
            print(f"      Changed: {entry.get('changed_at', 'N/A')}")
            print()
        
        print(f"   📊 {hash_count}/{len(entries)} ont un hash valide\n")
        
        if hash_count == 0:
            print("   🚨 AUCUN HASH STOCKÉ !")
            print("      L'iCal Watcher n'a jamais réussi à stocker les hash")
            print("      OU il y a un problème d'insertion dans la base\n")
        elif hash_count < len(entries):
            print(f"   ⚠️  {len(entries) - hash_count} entrée(s) sans hash")
            print("      Ces listings ne peuvent pas être surveillés\n")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}\n")
        return
    
    # Tester un fetch iCal et comparer
    print("="*80)
    print("2️⃣  TEST: Fetch un iCal et comparer avec la DB...")
    print("="*80 + "\n")
    
    # Récupérer une config
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/property_sync_config?select=ical_url_airbnb,lofts!inner(airbnb_listing_id)&is_active=eq.true&limit=1",
        headers=headers
    )
    
    if response.status_code == 200 and response.json():
        config = response.json()[0]
        ical_url = config.get('ical_url_airbnb')
        listing_id = config['lofts']['airbnb_listing_id']
        
        print(f"   Listing: {listing_id}")
        print(f"   URL: {ical_url[:60]}...\n")
        
        # Fetch l'iCal
        try:
            ical_resp = requests.get(ical_url, timeout=10)
            if ical_resp.status_code == 200:
                content = ical_resp.text
                
                # Calculer le hash (même méthode que l'iCal Watcher)
                cleaned = re.sub(r"DTSTAMP:[^\n\r]*\r?\n?", "", content)
                new_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
                
                # Récupérer le hash en DB
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/ical_hashes?listing_id=eq.{listing_id}&select=hash,checked_at",
                    headers=headers
                )
                
                if response.status_code == 200 and response.json():
                    db_entry = response.json()[0]
                    db_hash = db_entry.get('hash')
                    
                    print(f"   Hash DB    : {db_hash[:30] if db_hash else 'NULL'}...")
                    print(f"   Hash actuel: {new_hash[:30]}...")
                    
                    if not db_hash:
                        print(f"\n   🚨 HASH NULL EN DB !")
                        print("      L'iCal Watcher n'a jamais stocké de hash pour ce listing")
                    elif db_hash == new_hash:
                        print(f"\n   ✅ Hash identique - Pas de changement")
                        print(f"      L'iCal Watcher fonctionne correctement pour ce listing")
                    else:
                        print(f"\n   🚨 CHANGEMENT DÉTECTÉ !")
                        print(f"      Ce changement DEVRAIT être dans sync_queue")
                        print(f"      Si ce n'est pas le cas, l'iCal Watcher a un bug")
                else:
                    print("   ⚠️  Pas d'entrée en DB pour ce listing")
            else:
                print(f"   ❌ Erreur HTTP {ical_resp.status_code}")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
