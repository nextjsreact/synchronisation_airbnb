@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo              🚀 DÉMARRAGE COMPLET DU SYSTÈME                           
echo ========================================================================
echo.
echo Ce script va :
echo   1. Vérifier la configuration
echo   2. Lancer les 2 services (iCal Watcher + Targeted Scraper)
echo.
echo ⏱️  Durée : 2 minutes
echo.
pause

cd /d "%~dp0"

echo.
echo ========================================================================
echo [1/2] 🔍 DIAGNOSTIC
echo ========================================================================
echo.

python -c "
import os
import sys
from dotenv import load_dotenv
import requests

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv(encoding='utf-8')

# Vérifier variables essentielles
required = ['AIRBNB_EMAIL', 'AIRBNB_PASSWORD', 'NEXT_PUBLIC_SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
missing = [v for v in required if not os.environ.get(v)]

if missing:
    print(f'❌ Variables manquantes dans .env: {', '.join(missing)}')
    sys.exit(1)

print('✅ Configuration .env OK')

# Vérifier Supabase
SUPABASE_URL = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
HEADERS = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}

try:
    resp = requests.get(f'{SUPABASE_URL}/rest/v1/lofts?select=id&limit=1', headers=HEADERS, timeout=10)
    resp.raise_for_status()
    print('✅ Connexion Supabase OK')
except Exception as e:
    print(f'❌ Erreur Supabase: {e}')
    sys.exit(1)

# Vérifier URLs iCal
try:
    resp = requests.get(f'{SUPABASE_URL}/rest/v1/lofts?select=airbnb_ical_url', headers=HEADERS, timeout=10)
    lofts = resp.json()
    with_token = sum(1 for l in lofts if l.get('airbnb_ical_url') and ('?t=' in l.get('airbnb_ical_url', '') or '?s=' in l.get('airbnb_ical_url', '') or 'calendarAccessSignature' in l.get('airbnb_ical_url', '')))
    
    if with_token == 0:
        print(f'⚠️  Aucune URL iCal avec token')
        print(f'   Lancez: python collect_ical_urls.py')
        print()
        choice = input('Continuer quand même ? (o/n): ')
        if choice.lower() != 'o':
            sys.exit(1)
    else:
        print(f'✅ {with_token} URLs iCal avec token')
except Exception as e:
    print(f'⚠️  Impossible de vérifier les URLs iCal: {e}')

print()
print('✅ Diagnostic terminé - Système prêt')
"

if errorlevel 1 (
    echo.
    echo ========================================================================
    echo ❌ DIAGNOSTIC ÉCHOUÉ
    echo ========================================================================
    echo.
    echo Corrigez les erreurs ci-dessus avant de continuer.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo [2/2] 🚀 LANCEMENT DES SERVICES
echo ========================================================================
echo.

echo Arrêt des containers Docker...
docker-compose -f docker-compose.sync.yml down 2>nul

echo.
echo Lancement de l'iCal Watcher...
start "iCal Watcher" cmd /k "cd /d %~dp0 && echo ======================================================================== && echo                    iCAL WATCHER (Détection des changements)            && echo ======================================================================== && echo. && python ical_watcher.py"
timeout /t 2 /nobreak >nul

echo Lancement du Targeted Scraper...
start "Targeted Scraper" cmd /k "cd /d %~dp0 && echo ======================================================================== && echo                 TARGETED SCRAPER (Traitement de la queue)             && echo ======================================================================== && echo. && python targeted_scraper.py"
timeout /t 2 /nobreak >nul

echo.
echo ========================================================================
echo                           ✅ SYSTÈME DÉMARRÉ                           
echo ========================================================================
echo.
echo 2 fenêtres ont été ouvertes :
echo.
echo   📡 iCal Watcher
echo      - Vérifie les iCal toutes les 5 minutes
echo      - Détecte les changements
echo      - Alimente sync_queue
echo.
echo   🤖 Targeted Scraper
echo      - Lit sync_queue toutes les 30 secondes
echo      - Scrape les listings modifiés
echo      - Synchronise dans Supabase
echo.
echo ⚠️  NE FERMEZ PAS ces 2 fenêtres !
echo.
echo ========================================================================
echo.
echo 📊 Pour voir les réservations :
echo    python view_reservations.py
echo.
echo 🔍 Pour voir le diagnostic complet :
echo    DIAGNOSTIC_COMPLET.bat
echo.
echo 🔥 Pour forcer un scraping complet :
echo    SCRAPING_COMPLET_MAINTENANT.bat
echo.
pause
