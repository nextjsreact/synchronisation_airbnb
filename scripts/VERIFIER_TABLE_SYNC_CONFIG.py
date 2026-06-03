"""
VERIFIER_TABLE_SYNC_CONFIG.py - Vérifier la table property_sync_config
========================================================================
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

print("\n" + "="*70)
print("🔍 VÉRIFICATION DE LA TABLE property_sync_config")
print("="*70)

# Test 1: Requête simple sans paramètres
print("\n📋 Test 1: Requête simple")
try:
    url = f"{SUPABASE_URL}/rest/v1/property_sync_config"
    response = requests.get(url, headers=HEADERS, timeout=10)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {len(data)} enregistrements trouvés")
        
        if data:
            print(f"\n   📊 Premier enregistrement:")
            first = data[0]
            for key, value in first.items():
                value_str = str(value)[:50] if value else "null"
                print(f"      • {key}: {value_str}")
    else:
        print(f"   ❌ Erreur: {response.text}")
        
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 2: Avec select
print("\n📋 Test 2: Avec select")
try:
    url = f"{SUPABASE_URL}/rest/v1/property_sync_config"
    params = {"select": "*", "limit": 5}
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ {len(data)} enregistrements")
    else:
        print(f"   ❌ Erreur: {response.text}")
        
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 3: Compter les URLs iCal non nulles
print("\n📋 Test 3: Compter les URLs iCal")
try:
    url = f"{SUPABASE_URL}/rest/v1/property_sync_config"
    params = {"select": "ical_url"}
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        with_ical = [d for d in data if d.get("ical_url")]
        print(f"   ✅ Total: {len(data)} enregistrements")
        print(f"   ✅ Avec ical_url: {len(with_ical)}")
        print(f"   ⚠️  Sans ical_url: {len(data) - len(with_ical)}")
        
        if with_ical:
            print(f"\n   📊 Exemple d'URL iCal:")
            print(f"      {with_ical[0]['ical_url'][:80]}...")
    else:
        print(f"   ❌ Erreur: {response.text}")
        
except Exception as e:
    print(f"   ❌ Exception: {e}")

print("\n" + "="*70 + "\n")
