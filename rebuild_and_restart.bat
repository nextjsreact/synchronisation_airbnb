@echo off
chcp 65001 > nul
echo ========================================================================
echo           🔄 RECONSTRUCTION ET REDÉMARRAGE DU SCRAPER                  
echo ========================================================================
echo.
echo Ce script va :
echo   1. Arrêter les containers actuels
echo   2. Reconstruire l'image Docker avec le nouveau code
echo   3. Redémarrer les containers
echo.
echo ⏱️  Durée estimée : 2-3 minutes
echo.
pause

cd /d "%~dp0"

echo.
echo [1/3] Arrêt des containers...
docker-compose -f docker-compose.sync.yml down

echo.
echo [2/3] Reconstruction de l'image Docker...
docker-compose -f docker-compose.sync.yml build --no-cache

echo.
echo [3/3] Redémarrage des containers...
docker-compose -f docker-compose.sync.yml up -d

echo.
echo ========================================================================
echo                           ✅ TERMINÉ                                   
echo ========================================================================
echo.
echo Pour voir les logs en temps réel :
echo   docker-compose -f docker-compose.sync.yml logs -f targeted-scraper
echo.
echo Vous devriez maintenant voir le message :
echo   "⚠️  API GraphQL cassée, utilisation du fallback..."
echo.
pause
