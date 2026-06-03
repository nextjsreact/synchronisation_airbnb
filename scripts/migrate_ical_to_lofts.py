"""
Script pour migrer les URLs iCal de property_sync_config vers lofts
====================================================================
Ce script va:
1. Vérifier si la colonne ical_url_airbnb existe dans lofts
2. Si non, l'ajouter (nécessite des permissions ALTER TABLE)
3. Copier les URLs depuis property_sync_config vers lofts
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
print("MIGRATION DES URLs iCal VERS LA TABLE 'lofts'")
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
url_mapping = {c['loft_id']: c.get('ical_url_airbnb') for c in configs if c.get('ical_url_airbnb')}
print(f"  ✅ {len(url_mapping)} URLs à migrer")

# 2. Vérifier si la colonne existe dans lofts
print("\n🔍 Vérification de la colonne 'ical_url_airbnb' dans 'lofts'...")
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=id,ical_url_airbnb&limit=1",
        headers=HEADERS,
        timeout=15,
    )
    if resp.status_code == 200:
        print("  ✅ La colonne existe déjà")
        column_exists = True
    else:
        print("  ❌ La colonne n'existe pas")
        column_exists = False
except Exception:
    print("  ❌ La colonne n'existe pas")
    column_exists = False

# 3. Si la colonne n'existe pas, on ne peut pas la créer via l'API REST
if not column_exists:
    print("\n⚠️  ATTENTION:")
    print("  La colonne 'ical_url_airbnb' n'existe pas dans la table 'lofts'.")
    print("  Pour l'ajouter, vous devez exécuter cette requête SQL dans Supabase:")
    print("\n" + "="*70)
    print("ALTER TABLE lofts ADD COLUMN ical_url_airbnb TEXT;")
    print("="*70)
    print("\nAprès avoir ajouté la colonne, relancez ce script.")
    exit(1)

# 4. Mettre à jour chaque loft avec son URL iCal
print("\n📤 Mise à jour des lofts avec les URLs iCal...")
success = 0
failed = 0

for loft_id, ical_url in url_mapping.items():
    try:
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
            print(f"  {status} Loft {loft_id[:8]}... mis à jour")
        else:
            failed += 1
            print(f"  ❌ Erreur pour {loft_id[:8]}...: {resp.status_code}")
    except Exception as e:
        failed += 1
        print(f"  ❌ Erreur pour {loft_id[:8]}...: {e}")

print("\n" + "="*70)
print(f"RÉSULTAT: {success} succès, {failed} échecs")
print("="*70)

if success > 0:
    print("\n✅ Migration terminée avec succès !")
    print("Les URLs iCal sont maintenant disponibles dans la table 'lofts'.")
    print("\nVous pouvez vérifier avec:")
    print("  SELECT id, name, ical_url_airbnb FROM lofts LIMIT 5;")
