#!/usr/bin/env python3
"""
Tester le système de retry en ajoutant une entrée test dans sync_queue
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("🧪 Test du système de retry\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Récupérer un listing_id existant de la table reservations
    print("🔍 Recherche d'un listing_id existant...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=listing_id&limit=1",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"❌ Erreur: {response.status_code} - {response.text}")
        return
    
    reservations = response.json()
    if not reservations:
        print("❌ Aucune réservation trouvée dans la base de données")
        return
    
    listing_id = reservations[0]['listing_id']
    print(f"✅ Listing ID trouvé: {listing_id}\n")
    
    # Vérifier si ce listing a déjà une entrée pending
    print("🔍 Vérification des entrées existantes...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?listing_id=eq.{listing_id}&status=eq.pending",
        headers=headers
    )
    
    if response.status_code == 200:
        existing = response.json()
        if existing:
            print(f"⚠️  Il existe déjà {len(existing)} entrée(s) pending pour ce listing")
            print("   Vous pouvez surveiller les logs pour voir le retry en action:")
            print("   docker compose -f docker-compose.sync.yml logs -f targeted-scraper")
            return
    
    # Ajouter une entrée test dans sync_queue
    print("➕ Ajout d'une entrée test dans sync_queue...")
    entry = {
        "listing_id": listing_id,
        "status": "pending",
        "retry_count": 0,
        "hash": f"test_{datetime.now().timestamp()}",
        "source": "test_retry_system"
    }
    
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/sync_queue",
        headers=headers,
        json=entry
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Entrée ajoutée avec succès!\n")
        print("📊 PROCHAINES ÉTAPES:")
        print("="*60)
        print("1. Le Targeted Scraper détectera cette entrée dans max 30s")
        print("2. Il tentera de scraper le listing")
        print("3. Si échec réseau: retry automatique (3x max)")
        print("4. Surveillez les logs:\n")
        print("   docker compose -f docker-compose.sync.yml logs -f targeted-scraper\n")
        print("🔍 Recherchez ces messages:")
        print("   • '🔁 Tentative X/3' = retry en cours")
        print("   • '✅ X reservations trouvees' = succès")
        print("   • '❌ Echec final apres 3 tentatives' = abandon")
        print("="*60)
    else:
        print(f"❌ Erreur: {response.status_code} - {response.text}")

if __name__ == "__main__":
    main()
