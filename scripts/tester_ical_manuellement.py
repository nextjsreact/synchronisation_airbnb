#!/usr/bin/env python3
"""
Tester manuellement les URLs iCal pour voir s'il y a des changements
"""

import os
import requests
import hashlib
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("🔍 TEST MANUEL DES URLS iCAL")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Récupérer les URLs iCal depuis property_sync_config
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/property_sync_config?select=loft_id,ical_url_airbnb,is_active&is_active=eq.true&limit=10",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur lecture config: {response.status_code}")
        return
    
    configs = response.json()
    
    if not configs:
        print("❌ Aucune config trouvée")
        return
    
    print(f"📋 {len(configs)} URL(s) iCal actives trouvées\n")
    
    # Récupérer les hash actuels depuis ical_hashes
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_hashes?select=listing_id,last_hash,last_checked",
        headers=headers
    )
    
    current_hashes = {}
    if response.status_code == 200:
        for entry in response.json():
            current_hashes[entry['listing_id']] = entry.get('last_hash')
    
    # Tester chaque URL
    changes_detected = 0
    
    for i, config in enumerate(configs, 1):
        url = config.get('ical_url_airbnb')
        if not url:
            continue
        
        # Extraire le listing_id de l'URL
        listing_id = url.split('/ical/')[1].split('.ics')[0] if '/ical/' in url else 'unknown'
        
        print(f"{i}. Listing: {listing_id[:20]}...")
        print(f"   URL: {url[:60]}...")
        
        # Fetch l'iCal
        try:
            ical_response = requests.get(url, timeout=10)
            
            if ical_response.status_code == 200:
                content = ical_response.text
                new_hash = hashlib.md5(content.encode()).hexdigest()
                old_hash = current_hashes.get(listing_id)
                
                print(f"   Hash actuel DB: {old_hash[:20] if old_hash else 'N/A'}...")
                print(f"   Hash nouveau  : {new_hash[:20]}...")
                
                if old_hash and old_hash != new_hash:
                    print(f"   🚨 CHANGEMENT DÉTECTÉ ! Hash différent")
                    changes_detected += 1
                    
                    # Compter les événements
                    event_count = content.count('BEGIN:VEVENT')
                    print(f"   📅 {event_count} événement(s) dans l'iCal")
                elif old_hash == new_hash:
                    print(f"   ✅ Pas de changement (hash identique)")
                else:
                    print(f"   ⚠️  Pas de hash en DB (nouveau listing?)")
                
            else:
                print(f"   ❌ Erreur HTTP {ical_response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)[:50]}")
        
        print()
    
    print("="*80)
    print(f"📊 RÉSULTAT: {changes_detected} changement(s) détecté(s)")
    print("="*80)
    
    if changes_detected > 0:
        print("\n🚨 PROBLÈME CONFIRMÉ !")
        print("   Des changements existent MAIS l'iCal Watcher ne les détecte pas !")
        print("\n💡 CAUSES POSSIBLES:")
        print("   1. Bug dans le code de l'iCal Watcher")
        print("   2. Problème de lecture de la base de données")
        print("   3. Erreur dans la comparaison des hash")
        print("   4. Logs ne montrent pas les vrais changements")
    else:
        print("\n✅ Aucun changement détecté manuellement")
        print("   Si vous voyez des nouvelles réservations, vérifiez:")
        print("   1. Sont-elles sur des listings surveillés ?")
        print("   2. Airbnb a-t-il mis à jour l'iCal ?")
        print("   3. Délai normal de 1-5 minutes après création")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
