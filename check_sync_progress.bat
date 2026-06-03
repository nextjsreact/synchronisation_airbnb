@echo off
chcp 65001 >nul
:loop
cls
echo ========================================================================
echo    📊 PROGRESSION DE LA SYNCHRONISATION
echo ========================================================================
echo.
echo [1] Dernières lignes du scraper
echo ------------------------------------------------------------------------
docker logs airbnb-scraper --tail 10 2>&1 | findstr /V "WARNING"
echo.
echo [2] Statistiques Supabase
echo ------------------------------------------------------------------------
python -c "import requests, os; from dotenv import load_dotenv; load_dotenv(encoding='utf-8'); SUPABASE_URL = os.environ.get('NEXT_PUBLIC_SUPABASE_URL') or 'https://zlpzuyctjhajdwlxzdzk.supabase.co'; SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY'); resp = requests.get(f'{SUPABASE_URL}/rest/v1/reservations?select=id,created_at', headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}, timeout=15); from datetime import datetime; today = datetime.now().date().isoformat(); resp_today = requests.get(f'{SUPABASE_URL}/rest/v1/reservations?select=id&created_at=gte.{today}T00:00:00', headers={'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}, timeout=15); print(f'Total: {len(resp.json())} | Aujourdhui: {len(resp_today.json())}')"
echo.
echo ========================================================================
echo Rafraîchissement dans 10 secondes... (Ctrl+C pour arrêter)
timeout /t 10 /nobreak >nul
goto loop
