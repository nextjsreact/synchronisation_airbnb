@echo off
REM ============================================================================
REM Étape 3 : Lancer la synchronisation automatique (Docker)
REM ============================================================================

echo.
echo ========================================================================
echo   ÉTAPE 3 : LANCEMENT DE LA SYNCHRONISATION AUTOMATIQUE (DOCKER)
echo ========================================================================
echo.

echo Ce script va lancer 2 services Docker en arrière-plan :
echo.
echo   1. ical_watcher.py (surveillance des calendriers iCal)
echo      - Poll les URLs iCal toutes les 5 minutes
echo      - Détecte les changements via hash SHA256
echo      - Pousse dans la queue de synchronisation
echo      - RAM : ~50MB
echo.
echo   2. targeted_scraper.py (scraping ciblé)
echo      - Lit la queue toutes les 30 secondes
echo      - Scrape uniquement les listings qui ont changé
echo      - Envoie à l'API Next.js
echo      - RAM : ~2GB
echo.
echo Mode : Docker avec containers persistants
echo.
echo ========================================================================
echo.

echo Voulez-vous continuer ? (O/N)
set /p choice="> "

if /i not "%choice%"=="O" (
    echo.
    echo Opération annulée.
    pause
    exit /b 0
)

echo.
echo ========================================================================
echo   CHANGEMENT DE CONFIGURATION
echo ========================================================================
echo.

REM Changer HEADLESS=true pour mode automatique
findstr /C:"HEADLESS=true" .env >nul
if errorlevel 1 (
    echo [INFO] Configuration de HEADLESS=true pour mode automatique...
    powershell -Command "(Get-Content .env) -replace 'HEADLESS=false', 'HEADLESS=true' | Set-Content .env"
    echo [OK] HEADLESS=true configuré
) else (
    echo [OK] HEADLESS=true déjà configuré
)

echo.

echo ========================================================================
echo   VÉRIFICATION DES FICHIERS
echo ========================================================================
echo.

REM Vérifier si ical_watcher.py existe
if not exist ical_watcher.py (
    echo [ERREUR] Le fichier ical_watcher.py n'existe pas
    echo.
    echo Ce fichier est nécessaire pour la synchronisation automatique.
    pause
    exit /b 1
)

echo [OK] ical_watcher.py trouvé
echo.

REM Vérifier si targeted_scraper.py existe
if not exist targeted_scraper.py (
    echo [ATTENTION] Le fichier targeted_scraper.py n'existe pas encore
    echo.
    echo Pour l'instant, seul le watcher sera lancé.
    echo Le watcher détectera les changements et les mettra dans la queue.
    echo.
    echo Vous pourrez lancer le targeted scraper plus tard quand il sera disponible.
    echo.
    set TARGETED_EXISTS=false
) else (
    echo [OK] targeted_scraper.py trouvé
    set TARGETED_EXISTS=true
)

echo.

echo ========================================================================
echo   CRÉATION DU DOCKER-COMPOSE POUR LA SYNCHRONISATION
echo ========================================================================
echo.

REM Créer docker-compose.sync.yml
echo [INFO] Création de docker-compose.sync.yml...

(
echo services:
echo   # Watcher iCal
echo   ical-watcher:
echo     build:
echo       context: .
echo       dockerfile: Dockerfile
echo     container_name: ical-watcher
echo     env_file:
echo       - .env
echo     volumes:
echo       - ./output:/app/output
echo     restart: unless-stopped
echo     command: python ical_watcher.py
echo.
if "%TARGETED_EXISTS%"=="true" (
echo   # Targeted scraper
echo   targeted-scraper:
echo     build:
echo       context: .
echo       dockerfile: Dockerfile
echo     container_name: targeted-scraper
echo     env_file:
echo       - .env
echo     volumes:
echo       - ./output:/app/output
echo     shm_size: "2gb"
echo     mem_limit: "4g"
echo     restart: unless-stopped
echo     command: python targeted_scraper.py
)
) > docker-compose.sync.yml

echo [OK] docker-compose.sync.yml créé
echo.

echo ========================================================================
echo   LANCEMENT DES SERVICES DOCKER
echo ========================================================================
echo.
echo [INFO] Lancement des containers en arrière-plan...
echo.

REM Lancer les services
docker compose -f docker-compose.sync.yml up -d

if errorlevel 1 (
    echo.
    echo [ERREUR] Le lancement des services a échoué
    pause
    exit /b 1
)

echo.
echo [OK] Services lancés avec succès
echo.

timeout /t 3 /nobreak >nul

echo ========================================================================
echo   ✅ SYNCHRONISATION AUTOMATIQUE ACTIVE
echo ========================================================================
echo.
echo Les services Docker sont maintenant actifs en arrière-plan :
echo.
echo   ✅ ical-watcher : Surveille les calendriers toutes les 5 minutes
if "%TARGETED_EXISTS%"=="true" (
    echo   ✅ targeted-scraper : Scrape les changements toutes les 30 secondes
) else (
    echo   ⏳ targeted-scraper : Pas encore disponible
)
echo.
echo Pour voir les logs :
echo   docker compose -f docker-compose.sync.yml logs -f
echo.
echo Pour voir les logs d'un service spécifique :
echo   docker compose -f docker-compose.sync.yml logs -f ical-watcher
if "%TARGETED_EXISTS%"=="true" (
    echo   docker compose -f docker-compose.sync.yml logs -f targeted-scraper
)
echo.
echo Pour arrêter les services :
echo   docker compose -f docker-compose.sync.yml down
echo.
echo Pour redémarrer les services :
echo   docker compose -f docker-compose.sync.yml restart
echo.
echo Pour voir l'état des containers :
echo   docker compose -f docker-compose.sync.yml ps
echo.

pause
