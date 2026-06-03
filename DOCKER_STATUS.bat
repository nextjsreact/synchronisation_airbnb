@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo                 📊 ÉTAT DES SERVICES DOCKER                            
echo ========================================================================
echo.

cd /d "%~dp0"

echo État des conteneurs :
echo.
docker-compose -f docker-compose.sync.yml ps

echo.
echo ========================================================================
echo.
echo Légende :
echo   • Up X minutes/hours : Service en cours d'exécution
echo   • Exit 0             : Service arrêté normalement
echo   • Exit 1             : Service arrêté avec erreur
echo   • Restarting         : Service en cours de redémarrage
echo.
echo Pour voir les logs :
echo   DOCKER_LOGS.bat
echo.
pause
