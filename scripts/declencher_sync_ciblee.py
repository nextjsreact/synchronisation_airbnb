import os
import sys
import requests

# Supabase URL and Key (directly from config/env)
SUPABASE_URL = "https://mhngbluefyucoesgcjoy.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1obmdibHVlZnl1Y29lc2djam95Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjEzMTcyMiwiZXhwIjoyMDYxNzA3NzIyfQ.GWP_COePfH8YlwuEX7zRc55U5p4XSlCJE5hJehGIurw"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

def main():
    print("=" * 60)
    print("🚀 Déclencheur de Synchronisation Airbnb Ciblée")
    print("=" * 60)
    
    # 1. Récupérer la liste des lofts actifs
    print("📥 Récupération des lofts depuis Supabase...")
    try:
        resp = requests.get(f"{SUPABASE_URL}/rest/v1/lofts?select=id,title,airbnb_listing_id", headers=headers, timeout=15)
        resp.raise_for_status()
        lofts = resp.json()
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des lofts : {e}")
        return

    # Filtrer les lofts qui ont un listing_id Airbnb valide
    valid_lofts = [l for l in lofts if l.get('airbnb_listing_id')]
    if not valid_lofts:
        print("❌ Aucun loft actif avec un Airbnb Listing ID valide n'a été trouvé.")
        return

    # Trier par titre
    valid_lofts.sort(key=lambda x: x.get('title', ''))

    print(f"
📋 Lofts disponibles ({len(valid_lofts)}) :")
    for idx, loft in enumerate(valid_lofts, 1):
        print(f"  [{idx:2d}] {loft['title']} (Listing: {loft['airbnb_listing_id']})")

    # 2. Demander la saisie utilisateur
    try:
        choice = input("
👉 Choisissez un numéro de loft ou entrez directement un Listing ID Airbnb : ").strip()
        if not choice:
            print("❌ Opération annulée.")
            return

        selected_listing_id = None
        selected_title = "Manuel"

        # Si l'utilisateur a choisi un index de la liste
        if choice.isdigit() and int(choice) <= len(valid_lofts):
            selected_loft = valid_lofts[int(choice) - 1]
            selected_listing_id = selected_loft['airbnb_listing_id']
            selected_title = selected_loft['title']
        else:
            # Sinon c'est un Listing ID direct
            selected_listing_id = choice
            # Chercher si ce listing correspond à un loft connu
            for l in valid_lofts:
                if str(l['airbnb_listing_id']) == str(selected_listing_id):
                    selected_title = l['title']
                    break

        if not selected_listing_id:
            print("❌ Saisie invalide.")
            return

        print(f"
⏳ Planification de la synchronisation pour : {selected_title} ({selected_listing_id})...")

        # 3. Insérer la tâche dans la sync_queue de Supabase
        payload = {
            "listing_id": int(selected_listing_id),
            "status": "pending",
            "reason": f"Manual trigger via CLI for loft {selected_title}",
            "retry_count": 0
        }

        resp = requests.post(f"{SUPABASE_URL}/rest/v1/sync_queue", headers=headers, json=payload, timeout=15)
        if resp.status_code in [200, 201]:
            print(f"✅ Succès ! La tâche a été ajoutée à la queue en attente ('pending').")
            print("ℹ️  Le 'targeted-scraper' en cours d'exécution va la traiter dans les 30 prochaines secondes.")
        else:
            print(f"❌ Échec de l'insertion dans la queue : {resp.status_code} - {resp.text}")

    except KeyboardInterrupt:
        print("
❌ Opération annulée.")
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")

if __name__ == '__main__':
    main()
