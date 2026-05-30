"""
Script de vérification de santé du système de synchronisation
==============================================================
Vérifie que tout fonctionne correctement
"""
import requests
import os
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(encoding='utf-8')

SUPABASE_URL = os.environ.get("NEXT_PUBLIC_SUPABASE_URL") or "https://zlpzuyctjhajdwlxzdzk.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpscHp1eWN0amhhamR3bHh6ZHprIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3OTEwMjc0NiwiZXhwIjoyMDk0Njc4NzQ2fQ.Hi6BTLkyPN-3ax18N9ssbOmTBtl-tdNoOVz4gHMMMLE"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

print("="*70)
print("🏥 VÉRIFICATION DE SANTÉ DU SYSTÈME")
print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

health_score = 0
max_score = 0

# 1. Vérifier les containers Docker
print("\n[1/6] 🐳 Containers Docker")
print("-" * 70)
max_score += 20
try:
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.sync.yml", "ps", "--format", "json"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    if result.returncode == 0:
        import json
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line:
                try:
                    containers.append(json.loads(line))
                except:
                    pass
        
        ical_watcher_up = any(c.get('Name') == 'ical-watcher' and c.get('State') == 'running' for c in containers)
        targeted_scraper_up = any(c.get('Name') == 'targeted-scraper' and c.get('State') == 'running' for c in containers)
        
        if ical_watcher_up and targeted_scraper_up:
            print("  ✅ iCal Watcher: Running")
            print("  ✅ Targeted Scraper: Running")
            health_score += 20
        elif ical_watcher_up or targeted_scraper_up:
            print(f"  {'✅' if ical_watcher_up else '❌'} iCal Watcher: {'Running' if ical_watcher_up else 'Stopped'}")
            print(f"  {'✅' if targeted_scraper_up else '❌'} Targeted Scraper: {'Running' if targeted_scraper_up else 'Stopped'}")
            health_score += 10
        else:
            print("  ❌ Aucun container en cours d'exécution")
    else:
        print("  ⚠️  Impossible de vérifier les containers")
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 2. Vérifier les URLs iCal avec token
print("\n[2/6] 🔗 URLs iCal")
print("-" * 70)
max_score += 20
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/lofts?select=airbnb_ical_url&airbnb_ical_url=not.is.null",
        headers=HEADERS,
        timeout=15,
    )
    lofts = resp.json()
    
    with_token = sum(1 for l in lofts if ('?t=' in l.get('airbnb_ical_url', '') or '?s=' in l.get('airbnb_ical_url', '') or 'calendarAccessSignature' in l.get('airbnb_ical_url', '')))
    without_token = len(lofts) - with_token
    
    percentage = (with_token / len(lofts) * 100) if lofts else 0
    
    print(f"  Total URLs: {len(lofts)}")
    print(f"  ✅ Avec token: {with_token} ({percentage:.1f}%)")
    print(f"  ⚠️  Sans token: {without_token}")
    
    if percentage >= 90:
        health_score += 20
    elif percentage >= 70:
        health_score += 15
    elif percentage >= 50:
        health_score += 10
    else:
        health_score += 5
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 3. Vérifier la queue de synchronisation
print("\n[3/6] 📋 Queue de Synchronisation")
print("-" * 70)
max_score += 20
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/sync_queue?select=status&order=created_at.desc&limit=100",
        headers=HEADERS,
        timeout=15,
    )
    queue = resp.json()
    
    pending = sum(1 for q in queue if q['status'] == 'pending')
    processing = sum(1 for q in queue if q['status'] == 'processing')
    done = sum(1 for q in queue if q['status'] == 'done')
    error = sum(1 for q in queue if q['status'] == 'error')
    
    print(f"  ⏳ Pending: {pending}")
    print(f"  🔄 Processing: {processing}")
    print(f"  ✅ Done: {done}")
    print(f"  ❌ Error: {error}")
    
    if pending + processing <= 5 and error <= 5:
        health_score += 20
    elif pending + processing <= 10 and error <= 10:
        health_score += 15
    else:
        health_score += 10
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 4. Vérifier les derniers changements détectés
print("\n[4/6] 🔍 Derniers Changements Détectés")
print("-" * 70)
max_score += 15
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/ical_hashes?select=checked_at,changed_at&order=checked_at.desc&limit=1",
        headers=HEADERS,
        timeout=15,
    )
    hashes = resp.json()
    
    if hashes:
        last_check = datetime.fromisoformat(hashes[0]['checked_at'].replace('Z', '+00:00'))
        now = datetime.now(last_check.tzinfo)
        minutes_ago = (now - last_check).total_seconds() / 60
        
        print(f"  Dernier check: il y a {minutes_ago:.0f} minutes")
        
        if minutes_ago <= 10:
            print("  ✅ Système actif")
            health_score += 15
        elif minutes_ago <= 30:
            print("  ⚠️  Dernière activité il y a plus de 10 min")
            health_score += 10
        else:
            print("  ❌ Pas d'activité récente")
            health_score += 5
    else:
        print("  ⚠️  Aucun hash trouvé")
        
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 5. Vérifier l'API Next.js
print("\n[5/6] 🌐 API Next.js")
print("-" * 70)
max_score += 15
try:
    api_url = os.environ.get("NEXTJS_API_URL", "http://localhost:3000/api/airbnb/sync")
    base_url = api_url.replace('/api/airbnb/sync', '')
    
    resp = requests.get(f"{base_url}/api/airbnb/health", timeout=5)
    
    if resp.status_code == 200:
        print(f"  ✅ API accessible ({resp.elapsed.total_seconds()*1000:.0f}ms)")
        health_score += 15
    else:
        print(f"  ⚠️  API répond avec HTTP {resp.status_code}")
        health_score += 5
        
except requests.Timeout:
    print("  ⚠️  API timeout (>5s)")
except requests.ConnectionError:
    print("  ⚠️  API non accessible (optionnel)")
    health_score += 10  # Pas critique
except Exception as e:
    print(f"  ⚠️  Erreur: {e}")
    health_score += 10  # Pas critique

# 6. Vérifier les erreurs récentes dans les logs
print("\n[6/6] 📝 Logs Récents")
print("-" * 70)
max_score += 10
try:
    result = subprocess.run(
        ["docker", "logs", "ical-watcher", "--tail", "50"],
        capture_output=True,
        text=True,
        timeout=10
    )
    
    http_400_count = result.stdout.count("HTTP 400")
    http_404_count = result.stdout.count("HTTP 404")
    error_count = result.stdout.count("ERREUR") + result.stdout.count("ERROR")
    
    print(f"  HTTP 400: {http_400_count}")
    print(f"  HTTP 404: {http_404_count}")
    print(f"  Erreurs: {error_count}")
    
    if http_400_count <= 10 and error_count == 0:
        print("  ✅ Pas d'erreurs critiques")
        health_score += 10
    elif http_400_count <= 20 and error_count <= 5:
        print("  ⚠️  Quelques erreurs")
        health_score += 7
    else:
        print("  ❌ Beaucoup d'erreurs")
        health_score += 3
        
except Exception as e:
    print(f"  ⚠️  Impossible de lire les logs: {e}")

# Score final
print("\n" + "="*70)
percentage = (health_score / max_score * 100) if max_score > 0 else 0
print(f"🏥 SCORE DE SANTÉ: {health_score}/{max_score} ({percentage:.0f}%)")
print("="*70)

if percentage >= 90:
    print("✅ EXCELLENT - Système en parfait état")
    exit_code = 0
elif percentage >= 70:
    print("⚠️  BON - Quelques points à surveiller")
    exit_code = 0
elif percentage >= 50:
    print("⚠️  MOYEN - Plusieurs problèmes à corriger")
    exit_code = 1
else:
    print("❌ CRITIQUE - Intervention nécessaire")
    exit_code = 2

print("\n💡 Pour plus de détails:")
print("   docker logs -f ical-watcher")
print("   docker logs -f targeted-scraper")
print("   python check_all_without_token.py")

exit(exit_code)
