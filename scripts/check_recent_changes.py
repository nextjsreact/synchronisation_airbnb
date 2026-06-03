"""
Vérifier les changements récents dans Supabase
"""
import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Variables d'environnement manquantes")
    exit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*60)
print("🔍 Vérification des changements récents dans Supabase")
print("="*60)

# 1. Vérifier la sync_queue
print("\n📋 Sync Queue (dernières entrées)")
try:
    queue = supabase.table("sync_queue")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    if queue.data:
        print(f"✅ {len(queue.data)} entrées dans la queue\n")
        for entry in queue.data[:5]:
            print(f"  - Listing: {entry['listing_id']}")
            print(f"    Status: {entry['status']}")
            print(f"    Raison: {entry['reason']}")
            print(f"    Créé: {entry['created_at']}")
            print(f"    Traité: {entry.get('processed_at', 'N/A')}")
            print()
    else:
        print("⚠️  Queue vide")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 2. Vérifier les réservations récentes (dernières 24h)
print("\n📅 Réservations récentes (dernières 24h)")
try:
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    
    # Réservations créées/modifiées récemment
    reservations = supabase.table("reservations")\
        .select("*")\
        .gte("updated_at", yesterday)\
        .order("updated_at", desc=True)\
        .limit(10)\
        .execute()
    
    if reservations.data:
        print(f"✅ {len(reservations.data)} réservations modifiées/créées\n")
        for res in reservations.data[:5]:
            print(f"  - Code: {res['confirmation_code']}")
            print(f"    Listing: {res['listing_id']}")
            print(f"    Check-in: {res['check_in']}")
            print(f"    Statut: {res['status']}")
            print(f"    Modifié: {res['updated_at']}")
            print()
    else:
        print("⚠️  Aucune réservation récente")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 3. Vérifier les notifications
print("\n🔔 Notifications récentes")
try:
    notifications = supabase.table("notifications")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(10)\
        .execute()
    
    if notifications.data:
        print(f"✅ {len(notifications.data)} notifications\n")
        for notif in notifications.data[:5]:
            print(f"  - Type: {notif.get('type', 'N/A')}")
            print(f"    Titre: {notif.get('title', 'N/A')}")
            print(f"    Lu: {notif.get('read', False)}")
            print(f"    Créé: {notif['created_at']}")
            print()
    else:
        print("⚠️  Aucune notification")
except Exception as e:
    print(f"❌ Erreur (table 'notifications' n'existe peut-être pas): {e}")

# 4. Statistiques générales
print("\n📊 Statistiques générales")
try:
    total_res = supabase.table("reservations")\
        .select("*", count="exact")\
        .execute()
    
    upcoming_res = supabase.table("reservations")\
        .select("*", count="exact")\
        .gte("check_in", datetime.now().date().isoformat())\
        .execute()
    
    print(f"  Total réservations: {total_res.count}")
    print(f"  Réservations futures: {upcoming_res.count}")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("\n" + "="*60)
