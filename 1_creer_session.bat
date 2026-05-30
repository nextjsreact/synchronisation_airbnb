@echo off
REM ============================================================================
REM Étape 1 : Créer la session Airbnb avec Docker + VNC
REM ============================================================================

echo.
echo ========================================================================
echo   ÉTAPE 1 : CRÉATION DE LA SESSION AIRBNB (DOCKER + VNC)
echo ========================================================================
echo.
echo Ce script va :
echo   1. Build l'image Docker (première fois : 10-15 min)
echo   2. Lancer le container avec VNC
echo   3. Vous permettre de résoudre le CAPTCHA via http://localhost:6080
echo   4. Créer le fichier output\airbnb_session.json
echo.
echo IMPORTANT :
echo   - Le navigateur Chrome sera visible dans VNC
echo   - Accédez à http://localhost:6080 dans votre navigateur
echo   - Quand le message "CAPTCHA DÉTECTÉ" apparaît dans les logs
echo   - Résolvez le CAPTCHA dans l'interface VNC
echo   - Le script continuera automatiquement
echo.
echo ========================================================================
echo.

REM Vérifier que Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas installé
    echo.
    echo Installez Docker Desktop : https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [OK] Docker est installé
echo.

REM Vérifier que HEADLESS=false
findstr /C:"HEADLESS=false" .env >nul
if errorlevel 1 (
    echo [ERREUR] HEADLESS doit être false dans .env pour voir le navigateur dans VNC
    echo.
    echo Voulez-vous que je le configure automatiquement ? (O/N)
    set /p choice="> "
    if /i "%choice%"=="O" (
        powershell -Command "(Get-Content .env) -replace 'HEADLESS=true', 'HEADLESS=false' | Set-Content .env"
        echo [OK] HEADLESS=false configuré
    ) else (
        pause
        exit /b 1
    )
)

echo [OK] HEADLESS=false configuré
echo.

echo ========================================================================
echo   BUILD DE L'IMAGE DOCKER
echo ========================================================================
echo.
echo [INFO] Vérification de l'image Docker...
echo.

REM Vérifier si l'image existe déjà
docker images airbnb_transfer_v2-airbnb-scraper -q >nul 2>&1
if errorlevel 1 (
    echo [INFO] Image non trouvée, build en cours...
    echo [INFO] Durée estimée : 10-15 minutes (première fois)
    echo.
    docker compose build
    if errorlevel 1 (
        echo.
        echo [ERREUR] Le build Docker a échoué
        pause
        exit /b 1
    )
    echo.
    echo [OK] Image Docker créée avec succès
) else (
    echo [OK] Image Docker déjà présente
)

echo.
echo ========================================================================
echo   LANCEMENT DU CONTAINER DOCKER
echo ========================================================================
echo.
echo [INFO] Lancement du container avec VNC...
echo.
echo INSTRUCTIONS :
echo   1. Attendez que les logs affichent "CAPTCHA DÉTECTÉ"
echo   2. Ouvrez votre navigateur sur : http://localhost:6080
echo   3. Vous verrez Chrome avec Airbnb dans l'interface VNC
echo   4. Résolvez le CAPTCHA Arkose
echo   5. Le script continuera automatiquement
echo.
echo ========================================================================
echo.
echo Appuyez sur une touche pour lancer le container...
pause >nul

echo.
echo [INFO] Container en cours de démarrage...
echo [INFO] Interface VNC disponible sur : http://localhost:6080
echo.

REM Lancer le container
docker compose up

REM Vérifier que la session a été créée
echo.
echo ========================================================================
echo   VÉRIFICATION DE LA SESSION
echo ========================================================================
echo.

if exist output\airbnb_session.json (
    echo.
    echo ========================================================================
    echo   ✅ SUCCÈS : SESSION CRÉÉE
    echo ========================================================================
    echo.
    echo Le fichier output\airbnb_session.json a été créé avec succès.
    echo.
    echo Prochaine étape : Collecter les URLs iCal
    echo   Lancez : 2_collecter_ical.bat
    echo.
) else (
    echo.
    echo ========================================================================
    echo   ❌ ERREUR : SESSION NON CRÉÉE
    echo ========================================================================
    echo.
    echo Le fichier output\airbnb_session.json n'a pas été créé.
    echo.
    echo Causes possibles :
    echo   - Le CAPTCHA n'a pas été résolu
    echo   - La connexion a échoué
    echo   - Le container s'est arrêté avant la fin
    echo.
    echo Relancez ce script et assurez-vous de :
    echo   1. Accéder à http://localhost:6080
    echo   2. Résoudre le CAPTCHA dans l'interface VNC
    echo.
)

pause
