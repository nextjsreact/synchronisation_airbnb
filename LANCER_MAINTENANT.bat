@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo           🚀 LANCEMENT DES 2 SERVICES (WATCHER + SCRAPER)             
echo ========================================================================
echo.
echo ⚠️  IMPORTANT : Ce script va lancer 2 fenêtres :
echo.
echo   Fenêtre 1 : iCal Watcher (détecte les changements toutes les 5 min)
echo   Fenêtre 2 : Targeted Scraper (traite la queue toutes les 30 sec)
echo.
echo ⏱️  Les deux doivent rester ouverts en permanence !
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/3] Arrêt des containers Docker...
docker-compose -f docker-compose.sync.yml down 2>nul
if errorlevel 1 (
    echo    ℹ️  Containers déjà arrêtés ou Docker non démarré
) else (
    echo    ✅ Containers arrêtés
)

echo.
echo [2/3] Lancement de l'iCal Watcher dans une nouvelle fenêtre...
start "iCal Watcher" cmd /k "cd /d %~dp0 && python ical_watcher.py"
timeout /t 2 /nobreak >nul
echo    ✅ iCal Watcher lancé

echo.
echo [3/3] Lancement du Targeted Scraper dans une nouvelle fenêtre...
start "Targeted Scraper" cmd /k "cd /d %~dp0 && python targeted_scraper.py"
timeout /t 2 /nobreak >nul
echo    ✅ Targeted Scraper lancé

echo.
echo ========================================================================
echo                           ✅ SERVICES LANCÉS                           
echo ========================================================================
echo.
echo 2 fenêtres ont été ouvertes :
echo   1. iCal Watcher (détection des changements)
echo   2. Targeted Scraper (traitement de la queue)
echo.
echo ⚠️  NE FERMEZ PAS ces fenêtres !
echo.
echo Pour arrêter les services :
echo   - Fermez les 2 fenêtres
echo   - Ou lancez : docker-compose -f docker-compose.sync.yml down
echo.
echo Pour voir les réservations :
echo   python view_reservations.py
echo.
pause
