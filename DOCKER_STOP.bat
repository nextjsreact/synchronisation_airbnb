@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo              🛑 ARRÊT DES SERVICES DOCKER                              
echo ========================================================================
echo.
echo Ce script va arrêter les 2 services Docker :
echo   • ical-watcher
echo   • targeted-scraper
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/1] Arrêt des services...
docker-compose -f docker-compose.sync.yml down
if errorlevel 1 (
    echo    ❌ Erreur lors de l'arrêt
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo                        ✅ SERVICES ARRÊTÉS                             
echo ========================================================================
echo.
echo Les services Docker sont maintenant arrêtés.
echo.
echo Pour les relancer :
echo   DOCKER_START.bat
echo.
pause
