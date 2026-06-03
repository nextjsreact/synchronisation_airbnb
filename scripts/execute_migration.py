#!/usr/bin/env python3
"""
Script pour ajouter la colonne retry_count à la table sync_queue via API Supabase
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("🔧 Vérification de la colonne retry_count...")
    
    # Tester d'abord si la colonne existe en faisant une requête
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json"
    }
    
    # Essayer de lire avec retry_count pour voir si ça fonctionne
    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/sync_queue?limit=1&select=id,retry_count",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ La colonne retry_count existe déjà!")
            data = response.json()
            if data:
                print(f"   Exemple: retry_count = {data[0].get('retry_count', 'NULL')}")
            return True
        else:
            print(f"⚠️  Erreur {response.status_code}: {response.text}")
            print("\n❌ La colonne retry_count n'existe pas encore.")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "="*80)
    print("📋 INSTRUCTIONS POUR AJOUTER LA COLONNE:")
    print("="*80)
    print("\n1. Allez sur Supabase: https://supabase.com/dashboard")
    print("2. Sélectionnez votre projet")
    print("3. Allez dans 'SQL Editor' (menu de gauche)")
    print("4. Créez une nouvelle requête et collez ceci:\n")
    print("-" * 80)
    print("""
ALTER TABLE sync_queue 
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

UPDATE sync_queue 
SET retry_count = 0 
WHERE retry_count IS NULL;

SELECT 'Migration terminée!' as status;
""")
    print("-" * 80)
    print("\n5. Cliquez sur 'Run' (ou Ctrl+Enter)")
    print("6. Relancez ce script pour vérifier que ça fonctionne")
    print("\n✅ Une fois fait, le système de retry sera opérationnel!")
    
    return False

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n⏳ En attente de la migration...")
