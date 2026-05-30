"""Script pour récupérer les infos des 3 lofts problématiques"""
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

# Les 3 listing IDs problématiques
LISTING_IDS = ["897794605927940108", "24697659", "1413064424044049516"]

print("="*70)
print("RÉCUPÉRATION DES INFOS DES 3 LOFTS PROBLÉMATIQUES")
print("="*70)

for listing_id in LISTING_IDS:
    print(f"\n📍 Listing ID: {listing_id}")
    
    # Chercher dans lofts
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?airbnb_listing_id=eq.{listing_id}&select=id,name,airbnb_listing_id,airbnb_ical_url",
        headers=HEADERS,
        timeout=15,
    )
    
    lofts = resp.json()
    if lofts:
        loft = lofts[0]
        print(f"  Nom: {loft['name']}")
        print(f"  Loft ID: {loft['id']}")
        print(f"  URL actuelle: {loft.get('airbnb_ical_url', 'N/A')[:80]}...")
        
        # Vérifier si l'URL a un token
        url = loft.get('airbnb_ical_url', '')
        has_token = '?t=' in url or '?s=' in url or 'calendarAccessSignature' in url
        print(f"  Token: {'✅ OUI' if has_token else '❌ NON'}")
    else:
        print(f"  ❌ Loft non trouvé")

print("\n" + "="*70)
