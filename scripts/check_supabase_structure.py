"""
Check Supabase data structure
"""
import requests
import os
import json
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("Checking reservations structure...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/reservations?select=*&limit=1",
    headers=HEADERS,
    timeout=15,
)
print("\nReservation sample:")
print(json.dumps(resp.json(), indent=2))

print("\n\nChecking reservations with lofts join...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/reservations?select=confirmation_code,guest_name,lofts(name)&limit=1",
    headers=HEADERS,
    timeout=15,
)
print("\nReservation with lofts join:")
print(json.dumps(resp.json(), indent=2))

print("\n\nChecking sync_queue structure...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/sync_queue?select=*&limit=1",
    headers=HEADERS,
    timeout=15,
)
print("\nSync queue sample:")
print(json.dumps(resp.json(), indent=2))

print("\n\nChecking sync_queue with lofts join...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/sync_queue?select=listing_id,status,lofts!inner(name,airbnb_listing_id)&limit=1",
    headers=HEADERS,
    timeout=15,
)
print("\nSync queue with lofts join:")
print(json.dumps(resp.json(), indent=2))
