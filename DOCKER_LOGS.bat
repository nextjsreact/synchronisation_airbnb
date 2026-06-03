@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo                 📋 LOGS DES SERVICES DOCKER                            
echo ========================================================================
echo.
echo Choisissez le service à surveiller :
echo.
echo   1. iCal Watcher (détection des changements)
echo   2. Targeted Scraper (synchronisation)
echo   3. Les 2 services (tous les logs)
echo.
echo ========================================================================
echo.

set /p choice="Votre choix (1, 2 ou 3) : "

cd /d "%~dp0"

if "%choice%"=="1" (
    echo.
    echo 📋 Logs de l'iCal Watcher (Ctrl+C pour quitter)
    echo ========================================================================
    echo.
    docker-compose -f docker-compose.sync.yml logs -f ical-watcher
) else if "%choice%"=="2" (
    echo.
    echo 📋 Logs du Targeted Scraper (Ctrl+C pour quitter)
    echo ========================================================================
    echo.
    docker-compose -f docker-compose.sync.yml logs -f targeted-scraper
) else if "%choice%"=="3" (
    echo.
    echo 📋 Logs des 2 services (Ctrl+C pour quitter)
    echo ========================================================================
    echo.
    docker-compose -f docker-compose.sync.yml logs -f
) else (
    echo.
    echo ❌ Choix invalide
    pause
    exit /b 1
)
