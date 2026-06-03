#!/usr/bin/env python3
"""
Investigation complète sur Luna loft
"""

import os
import requests
import hashlib
import re
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("🔍 INVESTIGATION: LUNA LOFT")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # 1. Trouver Luna loft dans la base
    print("1️⃣  Recherche de Luna loft dans la base...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?name=ilike.%luna%&select=id,name,airbnb_listing_id",
        headers=headers
    )
    
    if response.status_code != 200 or not response.json():
        print("   ❌ Luna loft non trouvé dans la base 'lofts'")
        return
    
    loft = response.json()[0]
    loft_id = loft['id']
    loft_name = loft['name']
    listing_id = loft.get('airbnb_listing_id')
    
    print(f"   ✅ Trouvé: {loft_name}")
    print(f"   ID Loft: {loft_id}")
    print(f"   Listing ID: {listing_id}\n")
    
    if not listing_id:
        print("   ❌ Pas de listing_id Airbnb associé!")
        return
    
    # 2. Vérifier la config iCal
    print("="*80)
    print("2️⃣  Vérification de la configuration iCal...")
    print("="*80 + "\n")
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/property_sync_config?loft_id=eq.{loft_id}&select=*",
        headers=headers
    )
    
    if response.status_code != 200 or not response.json():
        print("   ❌ Aucune config iCal pour Luna loft!")
        print("      → Ce listing n'est PAS surveillé par l'iCal Watcher")
        return
    
    config = response.json()[0]
    ical_url = config.get('ical_url_airbnb')
    is_active = config.get('is_active')
    
    print(f"   URL iCal: {ical_url[:70] if ical_url else 'N/A'}...")
    print(f"   Actif: {'✅ Oui' if is_active else '❌ Non'}")
    
    if not is_active:
        print("\n   🚨 PROBLÈME: Config désactivée!")
        print("      → L'iCal Watcher ignore ce listing")
        return
    
    if not ical_url:
        print("\n   🚨 PROBLÈME: Pas d'URL iCal!")
        return
    
    print("   ✅ Configuration OK\n")
    
    # 3. Vérifier le hash actuel en DB
    print("="*80)
    print("3️⃣  Vérification du hash en base de données...")
    print("="*80 + "\n")
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_hashes?listing_id=eq.{listing_id}&select=*",
        headers=headers
    )
    
    db_hash = None
    checked_at = None
    changed_at = None
    
    if response.status_code == 200 and response.json():
        hash_entry = response.json()[0]
        db_hash = hash_entry.get('hash')
        checked_at = hash_entry.get('checked_at')
        changed_at = hash_entry.get('changed_at')
        
        print(f"   Hash DB: {db_hash[:40] if db_hash else 'NULL'}...")
        print(f"   Dernière vérif: {checked_at}")
        print(f"   Dernier changement: {changed_at}\n")
    else:
        print("   ⚠️  Aucun hash en DB pour ce listing\n")
    
    # 4. Fetch l'iCal actuel et comparer
    print("="*80)
    print("4️⃣  Fetch de l'iCal actuel depuis Airbnb...")
    print("="*80 + "\n")
    
    try:
        ical_response = requests.get(ical_url, timeout=15)
        
        if ical_response.status_code != 200:
            print(f"   ❌ Erreur HTTP {ical_response.status_code}")
            return
        
        content = ical_response.text
        
        # Calculer le hash (même méthode que iCal Watcher)
        cleaned = re.sub(r"DTSTAMP:[^\n\r]*\r?\n?", "", content)
        current_hash = hashlib.sha256(cleaned.encode("utf-8")).hexdigest()
        
        # Compter les événements
        event_count = content.count('BEGIN:VEVENT')
        
        print(f"   ✅ iCal téléchargé")
        print(f"   Hash actuel: {current_hash[:40]}...")
        print(f"   Événements: {event_count}\n")
        
        # Comparer avec DB
        print("="*80)
        print("5️⃣  COMPARAISON:")
        print("="*80 + "\n")
        
        if not db_hash:
            print("   🚨 PAS DE HASH EN DB!")
            print("      → L'iCal Watcher n'a jamais traité ce listing")
            print("      → Ou le listing vient d'être ajouté\n")
            print("   💡 SOLUTION: Le prochain cycle va initialiser le hash")
        elif db_hash == current_hash:
            print("   ✅ Hash IDENTIQUE")
            print("      → Aucun changement depuis la dernière vérification")
            print(f"      → Dernière vérif: {checked_at}\n")
            print("   💡 CONCLUSION:")
            print("      • Si vous voyez une nouvelle réservation")
            print("      • Mais iCal n'a pas changé")
            print("      • C'est que Airbnb n'a pas encore mis à jour l'iCal")
            print("      • Délai normal: 1-5 minutes\n")
        else:
            print("   🚨 CHANGEMENT DÉTECTÉ !")
            print("      → Le hash a changé depuis la dernière vérification\n")
            print("   💡 Ce changement DEVRAIT être détecté au prochain cycle")
            print(f"      Prochain cycle: ~{5 - ((datetime.utcnow().minute % 5))} min\n")
            
            # Vérifier si dans sync_queue
            response = requests.get(
                f"{SUPABASE_URL}/rest/v1/sync_queue?listing_id=eq.{listing_id}&status=eq.pending&select=*",
                headers=headers
            )
            
            if response.status_code == 200 and response.json():
                print("   ✅ Entrée PENDING dans sync_queue")
                print("      → Sera traitée dans ~30 secondes")
            else:
                print("   ⚠️  Pas encore dans sync_queue")
                print("      → Sera ajoutée au prochain cycle iCal Watcher")
    
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 6. Vérifier les réservations existantes
    print("\n" + "="*80)
    print("6️⃣  Réservations actuelles dans la base...")
    print("="*80 + "\n")
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?listing_id=eq.{listing_id}&select=guest_name,checkin_date,checkout_date,status,created_at&order=created_at.desc&limit=5",
        headers=headers
    )
    
    if response.status_code == 200:
        reservations = response.json()
        if reservations:
            print(f"   ✅ {len(reservations)} dernière(s) réservation(s):\n")
            for i, res in enumerate(reservations, 1):
                print(f"   {i}. {res.get('guest_name', 'N/A')}")
                print(f"      Check-in: {res.get('checkin_date')} → {res.get('checkout_date')}")
                print(f"      Status: {res.get('status')}")
                print(f"      Créée: {res.get('created_at')}")
                print()
        else:
            print("   ⚠️  Aucune réservation dans la base pour Luna loft\n")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
