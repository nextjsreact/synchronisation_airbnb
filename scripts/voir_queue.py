"""
Voir l'état de la sync_queue
"""
import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("=" * 70)
print("📋 ÉTAT DE LA SYNC QUEUE")
print("=" * 70)

# Statistiques
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/sync_queue?select=id,status",
    headers=HEADERS,
    timeout=15,
)
queue = resp.json()

total = len(queue)
pending = sum(1 for q in queue if q.get('status') == 'pending')
processing = sum(1 for q in queue if q.get('status') == 'processing')
done = sum(1 for q in queue if q.get('status') == 'done')
error = sum(1 for q in queue if q.get('status') == 'error')

print(f"\n📊 Statistiques :")
print(f"   Total : {total}")
print(f"   En attente (pending) : {pending}")
print(f"   En cours (processing) : {processing}")
print(f"   Terminées (done) : {done}")
print(f"   Erreurs : {error}")

# Dernières entrées
print(f"\n📋 Dernières Entrées :")
print("-" * 70)

resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/sync_queue?select=*&order=created_at.desc&limit=10",
    headers=HEADERS,
    timeout=15,
)
entries = resp.json()

# Get lofts mapping
lofts_resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/lofts?select=airbnb_listing_id,name",
    headers=HEADERS,
    timeout=15,
)
lofts_map = {l['airbnb_listing_id']: l['name'] for l in lofts_resp.json() if l.get('airbnb_listing_id')}

for i, entry in enumerate(entries, 1):
    listing_id = entry.get('listing_id')
    loft_name = lofts_map.get(listing_id, f"Listing {listing_id}")
    
    status_icon = {
        'pending': '⏳',
        'processing': '🔄',
        'done': '✅',
        'error': '❌'
    }.get(entry.get('status'), '❓')
    
    created = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00'))
    time_ago = datetime.now(created.tzinfo) - created
    
    if time_ago.days > 0:
        time_str = f"il y a {time_ago.days}j"
    elif time_ago.seconds > 3600:
        time_str = f"il y a {time_ago.seconds // 3600}h"
    else:
        time_str = f"il y a {time_ago.seconds // 60}min"
    
    print(f"\n  [{i}] {status_icon} {loft_name}")
    print(f"      Status: {entry.get('status')}")
    print(f"      Raison: {entry.get('reason')}")
    print(f"      Créé: {time_str}")
    if entry.get('error_message'):
        print(f"      Erreur: {entry['error_message'][:80]}")

print("\n" + "=" * 70)

if pending > 0:
    print(f"\n✅ {pending} tâches en attente de traitement par le Targeted Scraper")
    print(f"   Vérifiez la fenêtre 'Targeted Scraper' pour voir le traitement")
elif processing > 0:
    print(f"\n🔄 {processing} tâche(s) en cours de traitement")
    print(f"   Durée estimée : 30-40 minutes par tâche avec le fallback")
elif total == 0:
    print(f"\n⚠️  Queue vide - iCal Watcher n'a rien détecté")
else:
    print(f"\n✅ Toutes les tâches sont traitées")

print("=" * 70)
