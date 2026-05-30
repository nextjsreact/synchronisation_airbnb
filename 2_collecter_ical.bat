@echo off
REM ============================================================================
REM Étape 2 : Collecter les URLs iCal avec token (Docker)
REM ============================================================================

echo.
echo ========================================================================
echo   ÉTAPE 2 : COLLECTE DES URLs iCal (DOCKER)
echo ========================================================================
echo.

REM Vérifier que la session existe
if not exist output\airbnb_session.json (
    echo [ERREUR] Le fichier output\airbnb_session.json n'existe pas
    echo.
    echo Vous devez d'abord créer la session :
    echo   Lancez : 1_creer_session.bat
    echo.
    pause
    exit /b 1
)

echo [OK] Session trouvée : output\airbnb_session.json
echo.

echo Ce script va :
echo   1. Tester la collecte sur 3 lofts (5-10 minutes)
echo   2. Si succès, proposer de collecter les 54 lofts (2-3 heures)
echo.
echo Mode : Docker avec VNC (http://localhost:6080)
echo.
echo ========================================================================
echo.

echo Voulez-vous lancer le test sur 3 lofts ? (O/N)
set /p choice="> "

if /i not "%choice%"=="O" (
    echo.
    echo Opération annulée.
    pause
    exit /b 0
)

echo.
echo ========================================================================
echo   TEST : COLLECTE SUR 3 LOFTS
echo ========================================================================
echo.
echo [INFO] Lancement du container Docker pour la collecte test...
echo [INFO] Interface VNC disponible sur : http://localhost:6080
echo.

REM Lancer la collecte test dans Docker
docker compose run --rm airbnb-scraper ./collect_ical.sh

if errorlevel 1 (
    echo.
    echo [ERREUR] La collecte test a échoué
    echo.
    echo Vérifiez les logs ci-dessus pour plus de détails.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   RÉSULTAT DU TEST
echo ========================================================================
echo.

REM Vérifier le résultat
echo Voulez-vous maintenant collecter les 54 lofts ? (O/N)
echo (Durée estimée : 2-3 heures)
set /p choice2="> "

if /i not "%choice2%"=="O" (
    echo.
    echo Opération annulée.
    echo.
    echo Pour relancer la collecte complète plus tard :
    echo   docker compose run --rm airbnb-scraper python collect_ical_urls.py --all
    echo.
    pause
    exit /b 0
)

echo.
echo ========================================================================
echo   COLLECTE COMPLÈTE : 54 LOFTS
echo ========================================================================
echo.
echo [INFO] Lancement de la collecte complète dans Docker...
echo [INFO] Durée estimée : 2-3 heures
echo [INFO] Interface VNC : http://localhost:6080
echo [INFO] Vous pouvez minimiser cette fenêtre
echo.

REM Lancer la collecte complète dans Docker
docker compose run --rm airbnb-scraper ./collect_ical.sh --all

if errorlevel 1 (
    echo.
    echo [ERREUR] La collecte complète a échoué
    echo.
    echo Vérifiez les logs ci-dessus pour plus de détails.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   ✅ COLLECTE TERMINÉE
echo ========================================================================
echo.
echo Prochaine étape : Lancer la synchronisation automatique
echo   Lancez : 3_lancer_sync.bat
echo.

pause
