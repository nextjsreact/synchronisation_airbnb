@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo              🔄 REDÉMARRAGE DES SERVICES DOCKER                        
echo ========================================================================
echo.
echo Ce script va redémarrer les 2 services Docker :
echo   • ical-watcher
echo   • targeted-scraper
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/2] Arrêt des services...
docker-compose -f docker-compose.sync.yml down
if errorlevel 1 (
    echo    ⚠️  Erreur lors de l'arrêt (peut-être déjà arrêtés)
)
echo    ✅ Services arrêtés

echo.
echo [2/2] Démarrage des services...
docker-compose -f docker-compose.sync.yml up -d
if errorlevel 1 (
    echo    ❌ Erreur lors du démarrage
    pause
    exit /b 1
)
echo    ✅ Services démarrés

echo.
echo ========================================================================
echo                      ✅ SERVICES REDÉMARRÉS                            
echo ========================================================================
echo.
echo Les services Docker sont maintenant redémarrés.
echo.
echo Pour voir les logs :
echo   DOCKER_LOGS.bat
echo.
pause
