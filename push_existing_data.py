"""
push_existing_data.py
Envoie les données JSON existantes à l'API Next.js par batches de 100.
Évite de rescrap depuis Airbnb (~48 min économisées).
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from airbnb_api_client import send_to_nextjs_api

JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "reservations_airbnb.json")


def main():
    # 1. Lire le JSON
    print(f"Lecture de {JSON_PATH}...")
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        reservations = json.load(f)
    print(f"   {len(reservations)} reservations chargees")

    # 2. Ajouter les champs manquants pour la validation Supabase
    for r in reservations:
        r["listing_id"] = str(r.get("listing_id", ""))
        r["guest_email"] = f"{r.get('id', 'unknown')}@reservations.airbnb.local"
        r["guest_nationality"] = ""
        # Montants négatifs (remboursements d'annulations) → 0 pour passer la validation Zod
        if isinstance(r.get("montant_total"), (int, float)) and r["montant_total"] < 0:
            r["montant_total"] = 0

    # 3. Envoyer par batches
    result = send_to_nextjs_api(reservations, sync_type="manual", script_version="2.0.1")

    # 4. Resume
    metrics = result.get("metrics", {})
    print(f"\nResume final:")
    print(f"   Traitees : {metrics.get('processed', 0)}")
    print(f"   Creees   : {metrics.get('created', 0)}")
    print(f"   Erreurs  : {metrics.get('failed', 0)}")
    if result.get("errors"):
        print(f"   Premier  : {result['errors'][0]}")


if __name__ == "__main__":
    main()
