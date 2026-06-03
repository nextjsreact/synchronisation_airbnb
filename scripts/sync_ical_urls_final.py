"""
Script FINAL pour synchroniser les URLs iCal
=============================================
Copie les URLs depuis property_sync_config.ical_url_airbnb
vers lofts.airbnb_ical_url (nom correct du champ)
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
    "Prefer": "return=representation"
}

print("="*70)
print("SYNCHRONISATION DES URLs iCal")
print("property_sync_config.ical_url_airbnb → lofts.airbnb_ical_url")
print("="*70)

# 1. Récupérer toutes les URLs depuis property_sync_config
print("\n📥 Récupération des URLs depuis 'property_sync_config'...")
resp = requests.get(
    f"{SUPABASE_URL}/rest/v1/property_sync_config?select=loft_id,ical_url_airbnb,lofts(name)",
    headers=HEADERS,
    timeout=15,
)
configs = resp.json()
print(f"  ✅ {len(configs)} configs récupérées")

# Filtrer ceux qui ont une URL
to_update = [c for c in configs if c.get('ical_url_airbnb')]
print(f"  ✅ {len(to_update)} URLs à synchroniser")

# Statistiques
with_token = sum(1 for c in to_update if ('?t=' in c['ical_url_airbnb'] or '?s=' in c['ical_url_airbnb'] or 'calendarAccessSignature' in c['ical_url_airbnb']))
without_token = len(to_update) - with_token
print(f"  📊 {with_token} URLs avec token ✅")
print(f"  📊 {without_token} URLs sans token ⚠️")

# 2. Mettre à jour chaque loft avec son URL iCal
print("\n📤 Mise à jour de la table 'lofts' (champ: airbnb_ical_url)...")
success = 0
failed = 0

for config in to_update:
    loft_id = config['loft_id']
    ical_url = config['ical_url_airbnb']
    loft_info = config.get('lofts', {})
    loft_name = loft_info.get('name', 'N/A') if loft_info else 'N/A'
    
    try:
        # Utiliser PATCH avec le nom de champ CORRECT: airbnb_ical_url
        resp = requests.patch(
            f"{SUPABASE_URL}/rest/v1/lofts?id=eq.{loft_id}",
            json={"airbnb_ical_url": ical_url},
            headers=HEADERS,
            timeout=15,
        )
        
        # Vérifier le résultat
        if resp.status_code in (200, 204):
            success += 1
            has_token = '?t=' in ical_url or '?s=' in ical_url or 'calendarAccessSignature' in ical_url
            status = "✅" if has_token else "⚠️"
            print(f"  {status} {loft_name[:30]:30} | URL mise à jour")
        else:
            failed += 1
            print(f"  ❌ {loft_name[:30]:30} | HTTP {resp.status_code}")
            # Afficher le détail de l'erreur
            try:
                error_detail = resp.json()
                print(f"     Détail: {error_detail}")
            except:
                print(f"     Réponse: {resp.text[:100]}")
            
    except Exception as e:
        failed += 1
        print(f"  ❌ {loft_name[:30]:30} | Exception: {str(e)[:50]}")

print("\n" + "="*70)
print(f"RÉSULTAT:")
print(f"  ✅ Succès: {success}")
print(f"  ❌ Échecs: {failed}")
print("="*70)

if success > 0:
    print("\n✅ Synchronisation terminée avec succès !")
    print(f"\n{success} lofts ont maintenant leur URL iCal à jour dans le champ 'airbnb_ical_url'.")
    print(f"  - {with_token} URLs avec token valide ✅")
    print(f"  - {without_token} URLs sans token (à corriger) ⚠️")
    
    print("\n📋 Vous pouvez maintenant voir les URLs dans la table 'lofts':")
    print("   SELECT id, name, airbnb_ical_url FROM lofts WHERE airbnb_ical_url IS NOT NULL;")
elif failed > 0:
    print("\n⚠️  Toutes les mises à jour ont échoué.")
    print("\nSolution: Exécutez cette requête SQL directement dans Supabase:")
    print("\n" + "="*70)
    print("""
UPDATE lofts l
SET airbnb_ical_url = psc.ical_url_airbnb
FROM property_sync_config psc
WHERE l.id = psc.loft_id
  AND psc.ical_url_airbnb IS NOT NULL;
""")
    print("="*70)
