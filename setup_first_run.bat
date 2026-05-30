@echo off
REM ============================================================================
REM Script de première connexion - Résolution du CAPTCHA
REM ============================================================================

echo.
echo ========================================================================
echo   AIRBNB SCRAPER - PREMIERE CONNEXION
echo ========================================================================
echo.
echo Ce script va :
echo   1. Verifier que HEADLESS=false dans .env
echo   2. Lancer le scraper en mode local
echo   3. Vous permettre de resoudre le CAPTCHA manuellement
echo   4. Creer la session dans output/airbnb_session.json
echo.
echo Apres cette etape, vous pourrez passer en mode Docker production.
echo.
echo ========================================================================
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Installez Python 3.11+ depuis https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python est installe
echo.

REM Vérifier que le fichier .env existe
if not exist .env (
    echo [ERREUR] Le fichier .env n'existe pas
    echo.
    echo Copiez .env.example vers .env et configurez vos identifiants
    pause
    exit /b 1
)

echo [OK] Fichier .env trouve
echo.

REM Vérifier que HEADLESS=false
findstr /C:"HEADLESS=false" .env >nul
if errorlevel 1 (
    echo [ATTENTION] HEADLESS n'est pas configure a false dans .env
    echo.
    echo Voulez-vous que je le configure automatiquement ? (O/N)
    set /p choice="> "
    if /i "%choice%"=="O" (
        powershell -Command "(Get-Content .env) -replace 'HEADLESS=true', 'HEADLESS=false' | Set-Content .env"
        echo [OK] HEADLESS=false configure
    ) else (
        echo.
        echo Veuillez configurer manuellement HEADLESS=false dans .env
        pause
        exit /b 1
    )
)

echo [OK] HEADLESS=false configure
echo.

REM Créer le dossier output s'il n'existe pas
if not exist output mkdir output

echo ========================================================================
echo   LANCEMENT DU SCRAPER
echo ========================================================================
echo.
echo Le navigateur Chrome va s'ouvrir.
echo.
echo IMPORTANT :
echo   - Quand le message "CAPTCHA DETECTE" apparait
echo   - Regardez le navigateur Chrome
echo   - Resolvez le CAPTCHA Arkose manuellement
echo   - Le script continuera automatiquement
echo.
echo Appuyez sur une touche pour continuer...
pause >nul

echo.
echo [INFO] Lancement du scraper...
echo.

REM Lancer le scraper
python airbnb_scraper.py

REM Vérifier le code de sortie
if errorlevel 1 (
    echo.
    echo ========================================================================
    echo   ERREUR LORS DE L'EXECUTION
    echo ========================================================================
    echo.
    echo Le scraper a rencontre une erreur.
    echo.
    echo Verifiez :
    echo   - Vos identifiants dans .env
    echo   - Votre connexion internet
    echo   - Les logs ci-dessus pour plus de details
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   VERIFICATION DE LA SESSION
echo ========================================================================
echo.

REM Vérifier que la session a été créée
if exist output\airbnb_session.json (
    echo [OK] Session creee avec succes : output\airbnb_session.json
    echo.
    echo ========================================================================
    echo   PROCHAINE ETAPE : MODE PRODUCTION DOCKER
    echo ========================================================================
    echo.
    echo Maintenant que la session est creee, vous pouvez passer en mode Docker :
    echo.
    echo   1. Changez HEADLESS=true dans .env
    echo   2. Lancez : docker compose build
    echo   3. Lancez : docker compose up
    echo.
    echo Plus de CAPTCHA ! La session sera reutilisee.
    echo.
    echo Voulez-vous lancer le script de passage en production ? (O/N)
    set /p choice="> "
    if /i "%choice%"=="O" (
        call setup_docker_production.bat
    )
) else (
    echo [ATTENTION] Le fichier output\airbnb_session.json n'a pas ete cree
    echo.
    echo Causes possibles :
    echo   - Le CAPTCHA n'a pas ete resolu
    echo   - La connexion a echoue
    echo   - Une erreur s'est produite
    echo.
    echo Relancez ce script et assurez-vous de resoudre le CAPTCHA.
)

echo.
pause
