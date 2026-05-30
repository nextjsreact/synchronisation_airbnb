"""Script pour vérifier la structure des tables et les URLs iCal"""
import requests
import os
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("="*70)
print("VÉRIFICATION DE LA STRUCTURE DE LA BASE DE DONNÉES")
print("="*70)

# 1. Vérifier la table lofts
print("\n📋 Table 'lofts':")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/lofts?select=id,name,airbnb_listing_id&limit=3",
    headers=HEADERS,
    timeout=15,
)
lofts = resp.json()
print(f"  Colonnes disponibles: {list(lofts[0].keys()) if lofts else 'Aucune donnée'}")
print(f"  Exemple:")
for loft in lofts[:2]:
    print(f"    - {loft.get('name')}: listing_id={loft.get('airbnb_listing_id')}")

# Vérifier si la colonne ical_url_airbnb existe dans lofts
print("\n  🔍 Vérification de la colonne 'ical_url_airbnb' dans 'lofts':")
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=id,ical_url_airbnb&limit=1",
        headers=HEADERS,
        timeout=15,
    )
    if resp.status_code == 200:
        data = resp.json()
        if data and 'ical_url_airbnb' in data[0]:
            print(f"    ✅ La colonne existe dans 'lofts'")
            print(f"    Valeur: {data[0].get('ical_url_airbnb', 'NULL')[:80]}...")
        else:
            print(f"    ❌ La colonne n'existe PAS dans 'lofts'")
    else:
        print(f"    ❌ Erreur: {resp.status_code}")
except Exception as e:
    print(f"    ❌ La colonne 'ical_url_airbnb' n'existe PAS dans 'lofts'")
    print(f"    Erreur: {str(e)[:100]}")

# 2. Vérifier la table property_sync_config
print("\n📋 Table 'property_sync_config':")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/property_sync_config?select=*&limit=3",
    headers=HEADERS,
    timeout=15,
)
configs = resp.json()
print(f"  Colonnes disponibles: {list(configs[0].keys()) if configs else 'Aucune donnée'}")
print(f"  Exemples:")
for config in configs[:2]:
    url = config.get('ical_url_airbnb', 'N/A')
    has_token = '?t=' in url or '?s=' in url or 'calendarAccessSignature' in url
    token_status = "✅ avec token" if has_token else "❌ sans token"
    print(f"    - loft_id={config.get('loft_id')[:8]}...")
    print(f"      URL: {url[:60]}... {token_status}")

# 3. Vérifier la relation entre les tables
print("\n🔗 Relation entre 'lofts' et 'property_sync_config':")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/property_sync_config?select=loft_id,ical_url_airbnb,lofts(name,airbnb_listing_id)&limit=3",
    headers=HEADERS,
    timeout=15,
)
relations = resp.json()
print(f"  Exemples de jointure:")
for rel in relations[:2]:
    loft_info = rel.get('lofts', {})
    url = rel.get('ical_url_airbnb', 'N/A')
    has_token = '?t=' in url or '?s=' in url or 'calendarAccessSignature' in url
    print(f"    - {loft_info.get('name', 'N/A')} (listing: {loft_info.get('airbnb_listing_id', 'N/A')})")
    print(f"      URL iCal: {url[:60]}... {'✅' if has_token else '❌'}")

# 4. Statistiques
print("\n📊 Statistiques:")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/property_sync_config?select=loft_id,ical_url_airbnb",
    headers=HEADERS,
    timeout=15,
)
all_configs = resp.json()
with_url = [c for c in all_configs if c.get("ical_url_airbnb")]
with_token = [c for c in with_url if ('?t=' in c['ical_url_airbnb'] or '?s=' in c['ical_url_airbnb'] or 'calendarAccessSignature' in c['ical_url_airbnb'])]

print(f"  Total configs: {len(all_configs)}")
print(f"  Avec URL: {len(with_url)}")
print(f"  Avec token valide: {len(with_token)} ✅")
print(f"  Sans token: {len(with_url) - len(with_token)} ⚠️")

print("\n" + "="*70)
print("CONCLUSION:")
print("="*70)
print("Les URLs iCal sont stockées dans 'property_sync_config', pas dans 'lofts'.")
print("C'est une table séparée qui fait référence à 'lofts' via 'loft_id'.")
print("\nSi vous voulez voir les URLs iCal dans la table 'lofts', vous devez:")
print("  1. Ajouter une colonne 'ical_url_airbnb' dans 'lofts'")
print("  2. Copier les URLs depuis 'property_sync_config' vers 'lofts'")
print("  3. OU utiliser une jointure SQL pour voir les deux tables ensemble")
print("="*70)
