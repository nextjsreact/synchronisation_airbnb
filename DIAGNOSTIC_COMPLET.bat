@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo                    🔍 DIAGNOSTIC COMPLET DU SYSTÈME                    
echo ========================================================================
echo.
echo Ce script va vérifier :
echo   1. Configuration (.env)
echo   2. URLs iCal dans Supabase
echo   3. Table ical_hashes
echo   4. Sync queue
echo   5. Réservations
echo.
pause

cd /d "%~dp0"

echo.
echo ========================================================================
echo                    📊 RÉSULTATS DU DIAGNOSTIC                          
echo ========================================================================
echo.

python -c "
import os
import sys
from dotenv import load_dotenv
import requests

# Forcer UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(encoding='utf-8')

print('=' * 70)
print('[1] 🔧 CONFIGURATION')
print('=' * 70)

# Vérifier .env
required_vars = [
    'AIRBNB_EMAIL',
    'AIRBNB_PASSWORD',
    'NEXT_PUBLIC_SUPABASE_URL',
    'SUPABASE_SERVICE_ROLE_KEY'
]

missing = []
for var in required_vars:
    value = os.environ.get(var)
    if value:
        if 'KEY' in var or 'PASSWORD' in var:
            print(f'  ✅ {var}: {value[:10]}...')
        else:
            print(f'  ✅ {var}: {value}')
    else:
        print(f'  ❌ {var}: MANQUANT')
        missing.append(var)

if missing:
    print(f'\n  ⚠️  Variables manquantes: {', '.join(missing)}')
else:
    print(f'\n  ✅ Toutes les variables sont configurées')

# Vérifier Supabase
print('\n' + '=' * 70)
print('[2] 🗄️  SUPABASE - URLs iCal')
print('=' * 70)

SUPABASE_URL = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('  ❌ Clés Supabase manquantes dans .env')
    sys.exit(1)

HEADERS = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
}

try:
    # Vérifier lofts avec URLs iCal
    resp = requests.get(
        f'{SUPABASE_URL}/rest/v1/lofts?select=id,name,airbnb_listing_id,airbnb_ical_url',
        headers=HEADERS,
        timeout=15,
    )
    lofts = resp.json()
    
    total = len(lofts)
    with_ical = sum(1 for l in lofts if l.get('airbnb_ical_url'))
    with_token = sum(1 for l in lofts if l.get('airbnb_ical_url') and ('?t=' in l.get('airbnb_ical_url', '') or '?s=' in l.get('airbnb_ical_url', '') or 'calendarAccessSignature' in l.get('airbnb_ical_url', '')))
    
    print(f'  Total lofts: {total}')
    print(f'  Avec URL iCal: {with_ical}')
    print(f'  Avec token valide: {with_token}')
    
    if with_token == 0:
        print(f'\n  ❌ PROBLÈME: Aucune URL iCal avec token !')
        print(f'  ➤ Lancez: python collect_ical_urls.py')
    elif with_token < total:
        print(f'\n  ⚠️  {total - with_token} lofts sans token')
    else:
        print(f'\n  ✅ Tous les lofts ont des URLs iCal avec token')
    
except Exception as e:
    print(f'  ❌ Erreur: {e}')

# Vérifier ical_hashes
print('\n' + '=' * 70)
print('[3] 🔐 TABLE ical_hashes')
print('=' * 70)

try:
    resp = requests.get(
        f'{SUPABASE_URL}/rest/v1/ical_hashes?select=id',
        headers=HEADERS,
        timeout=15,
    )
    hashes = resp.json()
    
    if isinstance(hashes, dict) and 'code' in hashes:
        print(f'  ❌ Table ical_hashes n\'existe pas')
        print(f'  ➤ Créez la table dans Supabase')
    else:
        print(f'  ✅ Table existe avec {len(hashes)} entrées')
    
except Exception as e:
    print(f'  ❌ Erreur: {e}')

# Vérifier sync_queue
print('\n' + '=' * 70)
print('[4] 📋 SYNC QUEUE')
print('=' * 70)

try:
    resp = requests.get(
        f'{SUPABASE_URL}/rest/v1/sync_queue?select=id,status',
        headers=HEADERS,
        timeout=15,
    )
    queue = resp.json()
    
    if isinstance(queue, dict) and 'code' in queue:
        print(f'  ❌ Table sync_queue n\'existe pas')
    else:
        total = len(queue)
        pending = sum(1 for q in queue if q.get('status') == 'pending')
        done = sum(1 for q in queue if q.get('status') == 'done')
        
        print(f'  Total entrées: {total}')
        print(f'  En attente: {pending}')
        print(f'  Terminées: {done}')
        
        if pending > 0:
            print(f'\n  ✅ {pending} tâches en attente de traitement')
        elif total == 0:
            print(f'\n  ⚠️  Queue vide - ical_watcher n\'a rien détecté')
        else:
            print(f'\n  ℹ️  Toutes les tâches sont traitées')
    
except Exception as e:
    print(f'  ❌ Erreur: {e}')

# Vérifier réservations
print('\n' + '=' * 70)
print('[5] 📊 RÉSERVATIONS')
print('=' * 70)

try:
    resp = requests.get(
        f'{SUPABASE_URL}/rest/v1/reservations?select=id,created_at',
        headers=HEADERS,
        timeout=15,
    )
    reservations = resp.json()
    
    total = len(reservations)
    
    from datetime import datetime, timedelta
    today = datetime.now().date().isoformat()
    resp_today = requests.get(
        f'{SUPABASE_URL}/rest/v1/reservations?select=id&created_at=gte.{today}T00:00:00',
        headers=HEADERS,
        timeout=15,
    )
    today_count = len(resp_today.json())
    
    print(f'  Total réservations: {total}')
    print(f'  Synchronisées aujourd\'hui: {today_count}')
    
    if today_count == 0:
        print(f'\n  ⚠️  Aucune réservation synchronisée aujourd\'hui')
        print(f'  ➤ Lancez: SCRAPING_COMPLET_MAINTENANT.bat')
    else:
        print(f'\n  ✅ {today_count} nouvelles réservations aujourd\'hui')
    
except Exception as e:
    print(f'  ❌ Erreur: {e}')

print('\n' + '=' * 70)
print('📊 RÉSUMÉ')
print('=' * 70)
print()
print('Pour résoudre les problèmes :')
print('  1. URLs iCal manquantes → python collect_ical_urls.py')
print('  2. Queue vide → Lancez LANCER_MAINTENANT.bat')
print('  3. Pas de réservations → Lancez SCRAPING_COMPLET_MAINTENANT.bat')
print('=' * 70)
"

echo.
pause
