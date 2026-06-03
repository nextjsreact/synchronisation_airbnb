#!/usr/bin/env python3
"""
Script pour ajouter la colonne retry_count à la table sync_queue
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

def main():
    print("🔧 Ajout de la colonne retry_count à sync_queue...")
    
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # SQL pour ajouter la colonne retry_count
    sql = """
    ALTER TABLE sync_queue 
    ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;
    """
    
    try:
        # Exécuter via RPC si disponible, sinon on devra le faire manuellement
        print("⚠️  Cette modification nécessite l'accès SQL direct à Supabase.")
        print("\n📋 Exécutez cette requête SQL dans Supabase SQL Editor:")
        print("\n" + "="*60)
        print(sql)
        print("="*60)
        
        print("\n✅ Après avoir exécuté la requête, la colonne retry_count sera disponible.")
        print("   Valeur par défaut: 0")
        print("   Type: INTEGER")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
