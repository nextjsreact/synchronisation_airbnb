#!/usr/bin/env python3
"""
Nettoyer les anciennes entrées 'done' (> 7 jours)
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
    print("🧹 NETTOYAGE DES ENTRÉES 'DONE' ANCIENNES")
    print("="*80 + "\n")
    
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }
    
    # Date limite: 7 jours en arrière
    cutoff_date = (datetime.utcnow() - timedelta(days=7)).isoformat()
    
    print(f"📅 Suppression des entrées 'done' créées avant: {cutoff_date}\n")
    
    # Compter les entrées à supprimer
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.done&created_at=lt.{cutoff_date}&select=count",
        headers={**headers, "Prefer": "count=exact"}
    )
    
    if response.status_code == 200:
        count = response.headers.get('Content-Range', '').split('/')[-1]
        count_int = int(count) if count and count != '*' else 0
        
        if count_int == 0:
            print("✅ Aucune entrée 'done' ancienne à supprimer\n")
            return
        
        print(f"📊 {count_int} entrée(s) 'done' de plus de 7 jours trouvée(s)\n")
        
        # Demander confirmation
        confirmation = input(f"❓ Voulez-vous supprimer ces {count_int} entrées ? (oui/non): ").strip().lower()
        
        if confirmation not in ['oui', 'o', 'yes', 'y']:
            print("\n❌ Annulé - aucune suppression effectuée\n")
            return
        
        print("\n🗑️  Suppression en cours...\n")
        
        # Supprimer
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/sync_queue?status=eq.done&created_at=lt.{cutoff_date}",
            headers=headers
        )
        
        if response.status_code in [200, 204]:
            print(f"✅ {count_int} entrée(s) supprimée(s) avec succès!")
            print("\n💾 Base de données allégée!")
        else:
            print(f"❌ Erreur: {response.status_code} - {response.text}")
    else:
        print(f"❌ Erreur lecture: {response.status_code} - {response.text}")
    
    print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    main()
