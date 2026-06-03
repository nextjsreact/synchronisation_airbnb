"""Script pour trouver TOUS les lofts sans token"""
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
print("RECHERCHE DES LOFTS SANS TOKEN")
print("="*70)

# Récupérer tous les lofts avec URL
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/lofts?select=id,name,airbnb_listing_id,airbnb_ical_url&airbnb_ical_url=not.is.null",
    headers=HEADERS,
    timeout=15,
)

lofts = resp.json()
print(f"\n📋 {len(lofts)} lofts avec URL iCal")

# Filtrer ceux sans token
without_token = []
for loft in lofts:
    url = loft.get('airbnb_ical_url', '')
    has_token = '?t=' in url or '?s=' in url or 'calendarAccessSignature' in url
    if not has_token:
        without_token.append(loft)

print(f"\n⚠️  {len(without_token)} lofts SANS TOKEN:")
print("="*70)

for loft in without_token:
    print(f"\n📍 {loft['name']}")
    print(f"  Loft ID: {loft['id']}")
    print(f"  Listing ID: {loft['airbnb_listing_id']}")
    print(f"  URL: {loft['airbnb_ical_url'][:80]}...")

print("\n" + "="*70)
print("Ces lofts doivent être corrigés pour avoir un token valide.")
print("="*70)
