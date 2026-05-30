@echo off
REM ============================================================================
REM Script de passage en mode production Docker
REM ============================================================================

echo.
echo ========================================================================
echo   AIRBNB SCRAPER - MODE PRODUCTION DOCKER
echo ========================================================================
echo.

REM Vérifier que Docker est installé
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Docker n'est pas installe ou pas lance
    echo.
    echo Installez Docker Desktop depuis https://www.docker.com/products/docker-desktop
    echo Puis lancez Docker Desktop avant de relancer ce script
    pause
    exit /b 1
)

echo [OK] Docker est installe et lance
echo.

REM Vérifier que la session existe
if not exist output\airbnb_session.json (
    echo [ERREUR] Le fichier output\airbnb_session.json n'existe pas
    echo.
    echo Vous devez d'abord creer la session en mode local :
    echo   1. Lancez : setup_first_run.bat
    echo   2. Resolvez le CAPTCHA manuellement
    echo   3. Relancez ce script
    echo.
    pause
    exit /b 1
)

echo [OK] Session trouvee : output\airbnb_session.json
echo.

REM Vérifier que HEADLESS=true
findstr /C:"HEADLESS=true" .env >nul
if errorlevel 1 (
    echo [ATTENTION] HEADLESS n'est pas configure a true dans .env
    echo.
    echo Pour le mode production Docker, HEADLESS doit etre true.
    echo Voulez-vous que je le configure automatiquement ? (O/N)
    set /p choice="> "
    if /i "%choice%"=="O" (
        powershell -Command "(Get-Content .env) -replace 'HEADLESS=false', 'HEADLESS=true' | Set-Content .env"
        echo [OK] HEADLESS=true configure
    ) else (
        echo.
        echo Veuillez configurer manuellement HEADLESS=true dans .env
        pause
        exit /b 1
    )
)

echo [OK] HEADLESS=true configure
echo.

echo ========================================================================
echo   CONSTRUCTION DE L'IMAGE DOCKER
echo ========================================================================
echo.
echo Cette etape peut prendre 5-10 minutes (premiere fois seulement).
echo Docker va telecharger environ 500MB de dependances.
echo.
echo Appuyez sur une touche pour continuer...
pause >nul

echo.
echo [INFO] Construction de l'image Docker...
echo.

docker compose build

if errorlevel 1 (
    echo.
    echo [ERREUR] La construction de l'image a echoue
    echo.
    echo Verifiez :
    echo   - Que Docker Desktop est bien lance
    echo   - Votre connexion internet
    echo   - Les logs ci-dessus pour plus de details
    echo.
    pause
    exit /b 1
)

echo.
echo [OK] Image Docker construite avec succes
echo.

echo ========================================================================
echo   LANCEMENT DU SCRAPER EN MODE PRODUCTION
echo ========================================================================
echo.
echo Le scraper va maintenant s'executer dans un container Docker.
echo.
echo IMPORTANT :
echo   - Le navigateur sera en mode headless (invisible)
echo   - La session sera reutilisee (plus de CAPTCHA)
echo   - Les fichiers seront sauvegardes dans output/
echo.
echo Appuyez sur une touche pour continuer...
pause >nul

echo.
echo [INFO] Lancement du container Docker...
echo.

docker compose up

if errorlevel 1 (
    echo.
    echo [ERREUR] Le container a rencontre une erreur
    echo.
    echo Verifiez les logs ci-dessus pour plus de details.
    echo.
    echo Pour voir les logs :
    echo   docker compose logs
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   SUCCES !
echo ========================================================================
echo.
echo Le scraper a termine avec succes.
echo.
echo Fichiers generes :
echo   - output/reservations_airbnb.csv
echo   - output/reservations_airbnb.json
echo.
echo Pour relancer :
echo   docker compose up
echo.
echo Pour lancer en arriere-plan :
echo   docker compose up -d
echo.
echo Pour voir les logs :
echo   docker compose logs -f
echo.
echo Pour arreter :
echo   docker compose down
echo.
pause
