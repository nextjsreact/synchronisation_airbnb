"""
Script pour voir les réservations synchronisées
================================================
Affiche les dernières réservations depuis Supabase
"""
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("="*70)
print("📊 RÉSERVATIONS AIRBNB SYNCHRONISÉES")
print("="*70)

# 1. Statistiques globales
print("\n[1] 📈 Statistiques Globales")
print("-" * 70)
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=id,created_at",
        headers=HEADERS,
        timeout=15,
    )
    total = len(resp.json())
    
    # Réservations d'aujourd'hui
    today = datetime.now().date().isoformat()
    resp_today = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=id&created_at=gte.{today}T00:00:00",
        headers=HEADERS,
        timeout=15,
    )
    today_count = len(resp_today.json())
    
    # Réservations des 7 derniers jours
    week_ago = (datetime.now() - timedelta(days=7)).date().isoformat()
    resp_week = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=id&created_at=gte.{week_ago}T00:00:00",
        headers=HEADERS,
        timeout=15,
    )
    week_count = len(resp_week.json())
    
    print(f"  Total réservations : {total}")
    print(f"  Synchronisées aujourd'hui : {today_count}")
    print(f"  Synchronisées cette semaine : {week_count}")
    
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 2. Dernières réservations synchronisées
print("\n[2] 🆕 Dernières Réservations Synchronisées")
print("-" * 70)
try:
    # Get reservations with loft info
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=airbnb_confirmation_code,guest_name,check_in_date,check_out_date,status,created_at,loft_id&order=created_at.desc&limit=10",
        headers=HEADERS,
        timeout=15,
    )
    reservations = resp.json()
    
    # Get lofts mapping
    lofts_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=id,name",
        headers=HEADERS,
        timeout=15,
    )
    lofts_map = {l['id']: l['name'] for l in lofts_resp.json()}
    
    if isinstance(reservations, list) and reservations:
        for i, r in enumerate(reservations, 1):
            loft_name = lofts_map.get(r.get('loft_id'), 'N/A')
            created = datetime.fromisoformat(r['created_at'].replace('Z', '+00:00'))
            time_ago = datetime.now(created.tzinfo) - created
            
            if time_ago.days > 0:
                time_str = f"il y a {time_ago.days} jour(s)"
            elif time_ago.seconds > 3600:
                time_str = f"il y a {time_ago.seconds // 3600} heure(s)"
            else:
                time_str = f"il y a {time_ago.seconds // 60} minute(s)"
            
            print(f"\n  [{i}] {loft_name}")
            print(f"      Code: {r.get('airbnb_confirmation_code', 'N/A')}")
            print(f"      Guest: {r.get('guest_name', 'N/A')}")
            print(f"      Check-in: {r.get('check_in_date', 'N/A')}")
            print(f"      Check-out: {r.get('check_out_date', 'N/A')}")
            print(f"      Statut: {r.get('status', 'N/A')}")
            print(f"      Synchronisé: {time_str}")
    else:
        print("  Aucune réservation trouvée")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 3. Réservations par loft
print("\n[3] 🏠 Réservations par Loft")
print("-" * 70)
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/reservations?select=loft_id",
        headers=HEADERS,
        timeout=15,
    )
    reservations = resp.json()
    
    # Get lofts mapping
    lofts_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=id,name",
        headers=HEADERS,
        timeout=15,
    )
    lofts_map = {l['id']: l['name'] for l in lofts_resp.json()}
    
    # Compter par loft
    loft_counts = {}
    if isinstance(reservations, list):
        for r in reservations:
            loft_id = r.get('loft_id')
            if loft_id and loft_id in lofts_map:
                loft_name = lofts_map[loft_id]
                loft_counts[loft_name] = loft_counts.get(loft_name, 0) + 1
    
    # Trier par nombre de réservations
    sorted_lofts = sorted(loft_counts.items(), key=lambda x: x[1], reverse=True)
    
    for loft_name, count in sorted_lofts[:10]:
        print(f"  {loft_name:30} : {count} réservation(s)")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 4. Dernières synchronisations
print("\n[4] 🔄 Dernières Synchronisations")
print("-" * 70)
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=listing_id,status,reason,processed_at&status=eq.done&order=processed_at.desc&limit=10",
        headers=HEADERS,
        timeout=15,
    )
    syncs = resp.json()
    
    # Get lofts mapping by airbnb_listing_id
    lofts_resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=airbnb_listing_id,name",
        headers=HEADERS,
        timeout=15,
    )
    lofts_map = {l['airbnb_listing_id']: l['name'] for l in lofts_resp.json() if l.get('airbnb_listing_id')}
    
    if isinstance(syncs, list) and syncs:
        for i, s in enumerate(syncs, 1):
            listing_id = s.get('listing_id')
            loft_name = lofts_map.get(listing_id, f"Listing {listing_id}")
            
            if s.get('processed_at'):
                processed = datetime.fromisoformat(s['processed_at'].replace('Z', '+00:00'))
                time_ago = datetime.now(processed.tzinfo) - processed
                
                if time_ago.days > 0:
                    time_str = f"il y a {time_ago.days} jour(s)"
                elif time_ago.seconds > 3600:
                    time_str = f"il y a {time_ago.seconds // 3600} heure(s)"
                else:
                    time_str = f"il y a {time_ago.seconds // 60} minute(s)"
            else:
                time_str = "N/A"
            
            print(f"  [{i}] {loft_name} - {s.get('reason', 'N/A')} - {time_str}")
    else:
        print("  Aucune synchronisation récente")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

print("\n" + "="*70)
print("💡 Pour voir plus de détails, connectez-vous à Supabase :")
print("   https://supabase.com")
print("="*70)
