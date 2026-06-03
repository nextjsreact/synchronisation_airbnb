"""
Vérifier en détail les notifications et les nouvelles réservations
"""
import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*60)
print("🔍 Analyse détaillée des notifications")
print("="*60)

# 1. Structure de la table notifications
print("\n📋 Dernières 5 notifications (toutes colonnes)")
try:
    notifications = supabase.table("notifications")\
        .select("*")\
        .order("created_at", desc=True)\
        .limit(5)\
        .execute()
    
    if notifications.data:
        print(f"✅ {len(notifications.data)} notifications trouvées\n")
        for i, notif in enumerate(notifications.data, 1):
            print(f"  Notification #{i}:")
            for key, value in notif.items():
                print(f"    {key}: {value}")
            print()
    else:
        print("⚠️  Aucune notification")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 2. Notifications récentes (dernières 24h)
print("\n🔔 Notifications des dernières 24h")
try:
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    
    recent_notifs = supabase.table("notifications")\
        .select("*")\
        .gte("created_at", yesterday)\
        .order("created_at", desc=True)\
        .execute()
    
    if recent_notifs.data:
        print(f"✅ {len(recent_notifs.data)} notifications récentes")
    else:
        print("⚠️  Aucune notification dans les dernières 24h")
        print("   → Les notifications ne sont PAS créées automatiquement")
        print("   → Vérifiez le code de algerie-loft (webhook ou trigger)")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 3. Réservations récemment modifiées
print("\n📅 Réservations modifiées (dernières 24h)")
try:
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    
    # Essayer différentes colonnes possibles
    for date_col in ["updated_at", "last_sync", "created_at"]:
        try:
            reservations = supabase.table("reservations")\
                .select("*")\
                .gte(date_col, yesterday)\
                .order(date_col, desc=True)\
                .limit(5)\
                .execute()
            
            if reservations.data:
                print(f"✅ {len(reservations.data)} réservations (via {date_col})\n")
                
                for res in reservations.data[:3]:
                    print(f"  - ID: {res.get('id', 'N/A')}")
                    print(f"    Listing: {res.get('listing_id', 'N/A')}")
                    print(f"    Code: {res.get('code_reservation', res.get('reservation_code', 'N/A'))}")
                    print(f"    Statut: {res.get('statut', res.get('status', 'N/A'))}")
                    print(f"    {date_col}: {res.get(date_col, 'N/A')}")
                    print()
                break
        except Exception:
            continue
except Exception as e:
    print(f"❌ Erreur: {e}")

# 4. Vérifier s'il y a eu des NOUVELLES réservations (pas juste des mises à jour)
print("\n🆕 Vérifier les NOUVELLES réservations")
try:
    yesterday = (datetime.now() - timedelta(days=1)).isoformat()
    
    new_reservations = supabase.table("reservations")\
        .select("*")\
        .gte("created_at", yesterday)\
        .execute()
    
    if new_reservations.data:
        print(f"✅ {len(new_reservations.data)} NOUVELLES réservations créées dans les dernières 24h")
        print("\n   → C'EST NORMAL de ne pas avoir de notifications si ce sont des mises à jour")
    else:
        print("⚠️  Aucune NOUVELLE réservation dans les dernières 24h")
        print("\n   → Les changements détectés sont probablement des MODIFICATIONS")
        print("   → Les notifications ne sont envoyées QUE pour les NOUVELLES réservations")
except Exception as e:
    print(f"❌ Erreur: {e}")

# 5. Explication
print("\n" + "="*60)
print("💡 EXPLICATION")
print("="*60)
print("""
Les notifications dans algerie-loft sont envoyées UNIQUEMENT pour :
  ✅ Les NOUVELLES réservations (created_at récent)
  ❌ PAS pour les modifications de réservations existantes

Les changements détectés par l'iCal Watcher incluent :
  - Modifications de dates
  - Annulations
  - Changements de prix
  - Mises à jour de réservations existantes

👉 C'est NORMAL de ne pas recevoir de notifications si :
   - Aucune nouvelle réservation n'a été créée
   - Seulement des réservations existantes ont été modifiées
""")
print("="*60)
