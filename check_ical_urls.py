"""Script rapide pour vérifier les URLs iCal dans Supabase"""
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

# Récupérer toutes les configs
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/property_sync_config?select=loft_id,ical_url_airbnb",
    headers=HEADERS,
    timeout=15,
)

configs = resp.json()

# Analyser
total = len(configs)
with_url = [c for c in configs if c.get("ical_url_airbnb")]
with_token = [c for c in with_url if ('?t=' in c['ical_url_airbnb'] or '?s=' in c['ical_url_airbnb'] or 'calendarAccessSignature' in c['ical_url_airbnb'])]
without_token = [c for c in with_url if c not in with_token]

print(f"📊 Statistiques URLs iCal:")
print(f"  Total configs: {total}")
print(f"  Avec URL: {len(with_url)}")
print(f"  Avec token valide: {len(with_token)}")
print(f"  Sans token: {len(without_token)}")

if with_token:
    print(f"\n✅ Exemples avec token:")
    for c in with_token[:3]:
        url = c['ical_url_airbnb']
        token_type = "?t=" if "?t=" in url else ("?s=" if "?s=" in url else "calendarAccessSignature")
        print(f"  {c['loft_id']}: {url[:80]}... (token: {token_type})")

if without_token:
    print(f"\n⚠️  URLs sans token:")
    for c in without_token:
        print(f"  {c['loft_id']}: {c['ical_url_airbnb'][:80]}...")
