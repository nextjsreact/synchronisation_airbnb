"""
Script pour synchroniser les URLs iCal de property_sync_config vers lofts
==========================================================================
Copie les URLs iCal depuis property_sync_config.ical_url_airbnb 
vers lofts.ical_url_airbnb
"""
import requests
import os
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

print("="*70)
print("SYNCHRONISATION DES URLs iCal : property_sync_config → lofts")
print("="*70)

# 1. Récupérer toutes les URLs depuis property_sync_config
print("\n📥 Récupération des URLs depuis 'property_sync_config'...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/property_sync_config?select=loft_id,ical_url_airbnb",
    headers=HEADERS,
    timeout=15,
)
configs = resp.json()
print(f"  ✅ {len(configs)} configs récupérées")

# Créer un mapping loft_id -> ical_url
url_mapping = {}
for c in configs:
    if c.get('ical_url_airbnb'):
        url_mapping[c['loft_id']] = c['ical_url_airbnb']

print(f"  ✅ {len(url_mapping)} URLs à synchroniser")

# Statistiques
with_token = sum(1 for url in url_mapping.values() if ('?t=' in url or '?s=' in url or 'calendarAccessSignature' in url))
without_token = len(url_mapping) - with_token
print(f"  📊 {with_token} URLs avec token ✅")
print(f"  📊 {without_token} URLs sans token ⚠️")

# 2. Mettre à jour chaque loft avec son URL iCal
print("\n📤 Mise à jour de la table 'lofts'...")
success = 0
failed = 0
skipped = 0

for loft_id, ical_url in url_mapping.items():
    try:
        # Vérifier si le loft existe
        check_resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/lofts?id=eq.{loft_id}&select=id,name",
            headers=HEADERS,
            timeout=15,
        )
        
        if not check_resp.json():
            print(f"  ⏭️  Loft {loft_id[:8]}... n'existe pas - skip")
            skipped += 1
            continue
        
        loft_name = check_resp.json()[0].get('name', 'N/A')
        
        # Mettre à jour l'URL iCal
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/lofts?id=eq.{loft_id}",
            json={"ical_url_airbnb": ical_url},
            headers=HEADERS,
            timeout=15,
        )
        
        if resp.status_code in (200, 204):
            success += 1
            has_token = '?t=' in ical_url or '?s=' in ical_url or 'calendarAccessSignature' in ical_url
            status = "✅" if has_token else "⚠️"
            print(f"  {status} {loft_name[:30]:30} | {ical_url[:50]}...")
        else:
            failed += 1
            print(f"  ❌ Erreur pour {loft_name}: HTTP {resp.status_code}")
            
    except Exception as e:
        failed += 1
        print(f"  ❌ Erreur pour {loft_id[:8]}...: {e}")

print("\n" + "="*70)
print(f"RÉSULTAT:")
print(f"  ✅ Succès: {success}")
print(f"  ❌ Échecs: {failed}")
print(f"  ⏭️  Skipped: {skipped}")
print("="*70)

if success > 0:
    print("\n✅ Synchronisation terminée avec succès !")
    print(f"\n{success} lofts ont maintenant leur URL iCal à jour.")
    print(f"  - {with_token} URLs avec token valide ✅")
    print(f"  - {without_token} URLs sans token (à corriger) ⚠️")
    
    print("\n📋 Vous pouvez maintenant voir les URLs dans la table 'lofts':")
    print("   SELECT id, name, ical_url_airbnb FROM lofts WHERE ical_url_airbnb IS NOT NULL;")
