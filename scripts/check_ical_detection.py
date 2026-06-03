"""
Vérifier que l'iCal détecte bien les changements
"""
import requests
import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("=" * 70)
print("🔍 VÉRIFICATION : L'iCal Détecte-t-il les Changements ?")
print("=" * 70)

# 1. Vérifier les derniers changements détectés
print("\n[1] 📊 Derniers Changements Détectés par iCal Watcher")
print("-" * 70)
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=*&order=created_at.desc&limit=10",
        headers=HEADERS,
        timeout=15,
    )
    queue = resp.json()
    
    if isinstance(queue, list) and queue:
        # Get lofts mapping
        lofts_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/lofts?select=airbnb_listing_id,name",
            headers=HEADERS,
            timeout=15,
        )
        lofts_map = {l['airbnb_listing_id']: l['name'] for l in lofts_resp.json() if l.get('airbnb_listing_id')}
        
        for i, entry in enumerate(queue, 1):
            listing_id = entry.get('listing_id')
            loft_name = lofts_map.get(listing_id, f"Listing {listing_id}")
            created = datetime.fromisoformat(entry['created_at'].replace('Z', '+00:00'))
            time_ago = datetime.now(created.tzinfo) - created
            
            if time_ago.days > 0:
                time_str = f"il y a {time_ago.days} jour(s)"
            elif time_ago.seconds > 3600:
                time_str = f"il y a {time_ago.seconds // 3600} heure(s)"
            else:
                time_str = f"il y a {time_ago.seconds // 60} minute(s)"
            
            status_icon = "✅" if entry['status'] == 'done' else "⏳" if entry['status'] == 'processing' else "❌"
            
            print(f"\n  [{i}] {status_icon} {loft_name}")
            print(f"      Raison: {entry.get('reason', 'N/A')}")
            print(f"      Status: {entry.get('status', 'N/A')}")
            print(f"      Détecté: {time_str}")
            if entry.get('error_message'):
                print(f"      Erreur: {entry['error_message'][:100]}")
    else:
        print("  ❌ Aucun changement détecté récemment")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 2. Vérifier les hash iCal
print("\n[2] 🔐 Hash iCal Stockés (Preuve de Surveillance)")
print("-" * 70)
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_hashes?select=*&order=last_checked.desc&limit=5",
        headers=HEADERS,
        timeout=15,
    )
    hashes = resp.json()
    
    if isinstance(hashes, list) and hashes:
        # Get lofts mapping
        lofts_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/lofts?select=airbnb_listing_id,name",
            headers=HEADERS,
            timeout=15,
        )
        lofts_map = {l['airbnb_listing_id']: l['name'] for l in lofts_resp.json() if l.get('airbnb_listing_id')}
        
        for i, h in enumerate(hashes, 1):
            listing_id = h.get('listing_id')
            loft_name = lofts_map.get(listing_id, f"Listing {listing_id}")
            
            if h.get('last_checked'):
                checked = datetime.fromisoformat(h['last_checked'].replace('Z', '+00:00'))
                time_ago = datetime.now(checked.tzinfo) - checked
                
                if time_ago.days > 0:
                    time_str = f"il y a {time_ago.days} jour(s)"
                elif time_ago.seconds > 3600:
                    time_str = f"il y a {time_ago.seconds // 3600} heure(s)"
                else:
                    time_str = f"il y a {time_ago.seconds // 60} minute(s)"
            else:
                time_str = "Jamais"
            
            print(f"\n  [{i}] {loft_name}")
            print(f"      Hash: {h.get('hash', 'N/A')[:16]}...")
            print(f"      Dernière vérification: {time_str}")
    else:
        print("  ❌ Aucun hash iCal trouvé")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 3. Tester un iCal en direct
print("\n[3] 🌐 Test d'un iCal en Direct")
print("-" * 70)
try:
    # Get one iCal URL
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=name,airbnb_ical_url&limit=1",
        headers=HEADERS,
        timeout=15,
    )
    lofts = resp.json()
    
    if isinstance(lofts, list) and lofts and lofts[0].get('airbnb_ical_url'):
        loft = lofts[0]
        ical_url = loft['airbnb_ical_url']
        
        print(f"  Loft: {loft['name']}")
        print(f"  URL: {ical_url[:60]}...")
        
        # Fetch iCal
        ical_resp = requests.get(ical_url, timeout=10)
        
        if ical_resp.status_code == 200:
            content = ical_resp.text
            hash_value = hashlib.sha256(content.encode()).hexdigest()
            
            # Count events
            event_count = content.count('BEGIN:VEVENT')
            
            print(f"\n  ✅ iCal accessible")
            print(f"  📊 Nombre d'événements: {event_count}")
            print(f"  🔐 Hash actuel: {hash_value[:16]}...")
            print(f"  📏 Taille: {len(content)} caractères")
            
            # Show sample event
            if 'BEGIN:VEVENT' in content:
                start = content.find('BEGIN:VEVENT')
                end = content.find('END:VEVENT', start) + len('END:VEVENT')
                sample = content[start:end]
                print(f"\n  📄 Exemple d'événement:")
                for line in sample.split('\n')[:8]:
                    if line.strip():
                        print(f"     {line[:70]}")
        else:
            print(f"  ❌ Erreur HTTP {ical_resp.status_code}")
    else:
        print("  ❌ Aucune URL iCal trouvée")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 4. Statistiques globales
print("\n[4] 📈 Statistiques Globales")
print("-" * 70)
try:
    # Total entries in sync_queue
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=id",
        headers=HEADERS,
        timeout=15,
    )
    total_queue = len(resp.json())
    
    # Entries today
    today = datetime.now().date().isoformat()
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=id&created_at=gte.{today}T00:00:00",
        headers=HEADERS,
        timeout=15,
    )
    today_queue = len(resp.json())
    
    # Done entries
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=id&status=eq.done",
        headers=HEADERS,
        timeout=15,
    )
    done_queue = len(resp.json())
    
    # Pending entries
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=id&status=eq.pending",
        headers=HEADERS,
        timeout=15,
    )
    pending_queue = len(resp.json())
    
    print(f"  Total changements détectés: {total_queue}")
    print(f"  Changements aujourd'hui: {today_queue}")
    print(f"  Traités avec succès: {done_queue}")
    print(f"  En attente: {pending_queue}")
    
    if total_queue > 0:
        success_rate = (done_queue / total_queue) * 100
        print(f"\n  ✅ Taux de succès: {success_rate:.1f}%")
        
        if success_rate > 90:
            print(f"  🎉 Excellent ! L'iCal watcher fonctionne parfaitement")
        elif success_rate > 70:
            print(f"  👍 Bon ! Quelques erreurs mais globalement OK")
        else:
            print(f"  ⚠️  Attention ! Beaucoup d'erreurs de traitement")
    
except Exception as e:
    print(f"  ❌ Erreur: {e}")

print("\n" + "=" * 70)
print("📊 CONCLUSION")
print("=" * 70)
print("""
Si vous voyez des changements détectés ci-dessus, cela signifie que :

✅ L'iCal watcher FONCTIONNE (détecte les changements)
✅ Les entrées sont ajoutées dans sync_queue
✅ Le targeted-scraper traite ces entrées

❌ MAIS le scraping échouait à récupérer les données (API GraphQL cassée)

Maintenant avec le fallback automatique, le scraping devrait réussir !
""")
print("=" * 70)
