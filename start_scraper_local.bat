@echo off
chcp 65001 > nul
echo ========================================================================
echo              🚀 LANCEMENT DU SCRAPER EN LOCAL                          
echo ========================================================================
echo.
echo Ce script va :
echo   1. Arrêter les containers Docker (s'ils sont en cours)
echo   2. Lancer le targeted-scraper en local avec le NOUVEAU code
echo.
echo ⚠️  IMPORTANT : Gardez cette fenêtre ouverte !
echo.
echo Vous devriez voir le message :
echo   "⚠️  API GraphQL cassée, utilisation du fallback..."
echo.
pause

cd /d "%~dp0"

echo.
echo [1/2] Arrêt des containers Docker...
docker-compose -f docker-compose.sync.yml down 2>nul

echo.
echo [2/2] Lancement du scraper en local...
echo.
echo ========================================================================
echo                    📊 LOGS DU SCRAPER                                  
echo ========================================================================
echo.

python targeted_scraper.py

echo.
echo ========================================================================
echo                    ⚠️  SCRAPER ARRÊTÉ                                  
echo ========================================================================
echo.
pause
