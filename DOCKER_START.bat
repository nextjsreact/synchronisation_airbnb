@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo           🐳 DÉMARRAGE DES SERVICES DOCKER (ARRIÈRE-PLAN)             
echo ========================================================================
echo.
echo Ce script va :
echo   1. Arrêter les services Docker existants (si lancés)
echo   2. Construire les images Docker (si nécessaire)
echo   3. Lancer les 2 services en arrière-plan :
echo      • iCal Watcher (détection des changements)
echo      • Targeted Scraper (synchronisation)
echo.
echo ✅ Avantages :
echo   • Pas de fenêtres ouvertes
echo   • Redémarrage automatique en cas d'erreur
echo   • Tourne en arrière-plan 24/7
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/3] Arrêt des services existants...
docker-compose -f docker-compose.sync.yml down 2>nul
if errorlevel 1 (
    echo    ℹ️  Aucun service à arrêter
) else (
    echo    ✅ Services arrêtés
)

echo.
echo [2/3] Construction des images Docker...
echo    ⏳ Cela peut prendre 2-3 minutes la première fois...
docker-compose -f docker-compose.sync.yml build
if errorlevel 1 (
    echo    ❌ Erreur lors de la construction
    echo    ℹ️  Vérifiez que Docker Desktop est lancé
    pause
    exit /b 1
)
echo    ✅ Images construites

echo.
echo [3/3] Démarrage des services en arrière-plan...
docker-compose -f docker-compose.sync.yml up -d
if errorlevel 1 (
    echo    ❌ Erreur lors du démarrage
    pause
    exit /b 1
)
echo    ✅ Services démarrés

echo.
echo ========================================================================
echo                        ✅ SERVICES LANCÉS                              
echo ========================================================================
echo.
echo Les 2 services tournent maintenant en arrière-plan :
echo   • ical-watcher (détection toutes les 5 min)
echo   • targeted-scraper (traitement toutes les 30 sec)
echo.
echo 📋 Commandes utiles :
echo   • Voir les logs       : DOCKER_LOGS.bat
echo   • Arrêter les services: DOCKER_STOP.bat
echo   • Redémarrer          : DOCKER_RESTART.bat
echo   • Voir l'état         : docker-compose -f docker-compose.sync.yml ps
echo.
echo ℹ️  Les services redémarrent automatiquement en cas d'erreur
echo.
pause
