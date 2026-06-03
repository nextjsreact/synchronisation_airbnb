#!/usr/bin/env python3
"""
Vérifier la structure et le contenu de la table ical_hashes
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION TABLE ical_hashes")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "count=exact"
    }
    
    # Compter les entrées
    print("1️⃣  Comptage des entrées...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_hashes?select=count",
        headers=headers
    )
    
    if response.status_code == 200:
        count = response.headers.get('Content-Range', '').split('/')[-1]
        print(f"   ✅ {count} entrée(s) dans ical_hashes\n")
        
        if count == '0' or count == '*':
            print("   🚨 LA TABLE EST VIDE !")
            print("   C'est pourquoi l'iCal Watcher ne détecte AUCUN changement\n")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}\n")
    
    # Lire quelques entrées
    print("2️⃣  Lecture des 10 premières entrées...")
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_hashes?select=*&limit=10",
        headers={k: v for k, v in headers.items() if k != 'Prefer'}
    )
    
    if response.status_code == 200:
        entries = response.json()
        if entries:
            print(f"   ✅ {len(entries)} entrée(s) trouvée(s):\n")
            for entry in entries[:5]:
                print(f"   • Listing: {entry.get('listing_id', 'N/A')}")
                print(f"     Hash: {entry.get('last_hash', 'N/A')[:30]}...")
                print(f"     Dernière vérif: {entry.get('last_checked', 'N/A')}")
                print()
        else:
            print("   ⚠️  TABLE VIDE - Aucune entrée\n")
    else:
        print(f"   ❌ Erreur: {response.status_code} - {response.text}\n")
    
    # Diagnostic
    print("="*80)
    print("🔬 DIAGNOSTIC:")
    print("="*80 + "\n")
    
    if count == '0' or count == '*':
        print("🚨 PROBLÈME CRITIQUE IDENTIFIÉ:")
        print("\n   La table 'ical_hashes' est VIDE !")
        print("\n   CONSÉQUENCE:")
        print("   • L'iCal Watcher ne peut PAS comparer les hash")
        print("   • AUCUN changement ne sera jamais détecté")
        print("   • Les nouvelles réservations ne seront JAMAIS synchronisées")
        print("\n   SOLUTION:")
        print("   1. L'iCal Watcher doit INITIALISER les hash au premier passage")
        print("   2. OU nous devons lancer un scraping COMPLET pour populer la table")
        print("\n   CAUSE PROBABLE:")
        print("   • L'iCal Watcher n'a jamais été exécuté avec succès")
        print("   • OU il y a un bug dans l'insertion des hash")
        print("   • OU la table a été vidée/reset")
    else:
        print("✅ La table contient des données")
        print("   Le problème est ailleurs (hash non mis à jour, bug comparaison, etc.)")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
