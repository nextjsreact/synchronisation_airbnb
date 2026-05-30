@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:loop
cls
echo ========================================================================
echo    📊 MONITORING SYNCHRONISATION AIRBNB
echo ========================================================================
echo.

echo [1] 🐳 Status des Containers Docker
echo ------------------------------------------------------------------------
docker compose -f docker-compose.sync.yml ps
echo.

echo [2] 📥 iCal Watcher - Derniers Logs
echo ------------------------------------------------------------------------
docker logs ical-watcher --tail 8 2>&1 | findstr /V "WARNING"
echo.

echo [3] 🤖 Targeted Scraper - Derniers Logs
echo ------------------------------------------------------------------------
docker logs targeted-scraper --tail 8 2>&1 | findstr /V "WARNING"
echo.

echo [4] ⚠️  Erreurs Récentes
echo ------------------------------------------------------------------------
docker logs ical-watcher --tail 50 2>&1 | findstr /C:"HTTP 400" /C:"HTTP 404" /C:"ERREUR" /C:"ERROR" | findstr /V "WARNING"
docker logs targeted-scraper --tail 50 2>&1 | findstr /C:"ERREUR" /C:"ERROR" /C:"Exception" | findstr /V "WARNING"
echo.

echo ========================================================================
echo ⏰ Rafraîchissement dans 30 secondes...
echo 💡 Appuyez sur Ctrl+C pour arrêter
echo ========================================================================
timeout /t 30 /nobreak >nul
goto loop
