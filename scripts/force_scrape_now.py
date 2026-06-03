"""
Forcer un scraping immédiat avec diagnostic détaillé
"""
import os
import sys
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Variables d'environnement manquantes")
    sys.exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*60)
print("🔍 Diagnostic : Nouvelle réservation non synchronisée")
print("="*60)

# 1. Vérifier la sync_queue
print("\n📋 État de la sync_queue")
try:
    queue = supabase.table("sync_queue")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    if queue.data:
        print(f"✅ {len(queue.data)} entrées récentes\n")
        
        pending = [q for q in queue.data if q['status'] == 'pending']
        processing = [q for q in queue.data if q['status'] == 'processing']
        done = [q for q in queue.data if q['status'] == 'done']
        error = [q for q in queue.data if q['status'] == 'error']
        
        print(f"  Pending: {len(pending)}")
        print(f"  Processing: {len(processing)}")
        print(f"  Done: {len(done)}")
        print(f"  Error: {len(error)}")
        
        if error:
            print(f"\n  ⚠️  Erreurs détectées:")
            for e in error[:3]:
                print(f"    - Listing {e['listing_id']}: {e.get('error_message', 'N/A')}")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 2. Vérifier les réservations "upcoming" (futures)
print("\n📅 Réservations futures dans Supabase")
try:
    today = datetime.now().date().isoformat()
    
    upcoming = supabase.table("reservations")\
        .select("*", count="exact")\
        .gte("date_arrivee", today)\
        .execute()
    
    print(f"✅ {upcoming.count} réservations futures en base")
    
    # Dernière réservation future
    if upcoming.data:
        latest = supabase.table("reservations")\
            .select("*")\
            .gte("date_arrivee", today)\
            .order("created_at", desc=True)\
            .limit(1)\
            .execute()
        
        if latest.data:
            res = latest.data[0]
            print(f"\n  Dernière réservation future:")
            print(f"    ID: {res.get('id')}")
            print(f"    Listing: {res.get('listing_id', 'N/A')}")
            print(f"    Arrivée: {res.get('date_arrivee', 'N/A')}")
            print(f"    Créée: {res.get('created_at', 'N/A')}")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 3. Vérifier les URLs iCal
print("\n🔗 URLs iCal collectées")
try:
    urls = supabase.table("ical_urls")\
        .select("*", count="exact")\
        .execute()
    
    print(f"✅ {urls.count} URLs iCal en base")
    
    if urls.count == 0:
        print("\n  ⚠️  PROBLÈME : Aucune URL iCal collectée!")
        print("  → Lancer: .\\2_collecter_ical.bat")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 4. Proposer des solutions
print("\n" + "="*60)
print("💡 SOLUTIONS")
print("="*60)
print("""
Le Targeted Scraper échoue à cause de timeouts réseau.

Option 1 : SCRAPING COMPLET (recommandé)
  → Lance un scraping complet qui contournera le problème
  → Commande: .\\3_lancer_sync.bat
  → Durée: ~30 minutes (scrape TOUT)
  
Option 2 : Attendre que le réseau se stabilise
  → Le système réessaiera automatiquement
  → Risque: peut prendre plusieurs heures
  
Option 3 : Redémarrer les services Docker
  → Peut résoudre les problèmes de connexion
  → Commandes:
     docker compose -f docker-compose.sync.yml restart
     
⚠️  RECOMMANDATION: Lance le scraping complet (.\\3_lancer_sync.bat)
   pour être sûr de récupérer la nouvelle réservation immédiatement.
""")
print("="*60)
