@echo off
chcp 65001 >nul
echo ========================================================================
echo 🐳 SCRAPING COMPLET AVEC DOCKER
echo ========================================================================
echo.
echo Ce script va :
echo 1. Lancer le conteneur Docker
echo 2. Exécuter le scraping complet (30-40 min)
echo 3. Convertir les devises automatiquement
echo 4. Envoyer les données à l'API Next.js
echo 5. Arrêter le conteneur
echo.
echo ⏱️  Durée estimée : 30-40 minutes
echo.
echo 📊 Configuration :
echo    • COLLECT_CONTACTS : false (pas de collecte coordonnées)
echo    • Conversion devises : activée
echo    • API Next.js : activée
echo.
echo ========================================================================
pause

echo.
echo [1/4] Vérification de Docker...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker n'est pas installé ou n'est pas lancé
    echo    Lancez Docker Desktop et réessayez
    pause
    exit /b 1
)
echo ✅ Docker est disponible

echo.
echo [2/4] Construction de l'image Docker...
docker-compose build airbnb-scraper
if %errorlevel% neq 0 (
    echo ❌ Échec de la construction de l'image
    pause
    exit /b 1
)
echo ✅ Image construite

echo.
echo [3/4] Lancement du scraping complet...
echo ⏳ Cela peut prendre 30-40 minutes...
echo.
docker-compose run --rm airbnb-scraper python airbnb_scraper.py

if %errorlevel% neq 0 (
    echo.
    echo ❌ Le scraping a échoué
    echo.
    echo 📋 Actions recommandées :
    echo    1. Vérifier les logs ci-dessus
    echo    2. Vérifier que l'API Next.js est lancée
    echo    3. Vérifier la session Airbnb (1_creer_session.bat)
    echo.
    pause
    exit /b 1
)

echo.
echo [4/4] Nettoyage...
docker-compose down

echo.
echo ========================================================================
echo ✅ SCRAPING COMPLET TERMINÉ
echo ========================================================================
echo.
echo 📊 Résultats :
echo    • Fichiers : output/reservations_airbnb.csv et .json
echo    • Données envoyées à l'API Next.js
echo    • Devises converties automatiquement
echo.
echo 📋 Prochaines étapes :
echo    1. Vérifier les données dans Supabase
echo    2. Vérifier l'affichage côté frontend
echo    3. (Optionnel) Collecter les coordonnées : 7_collecter_contacts.bat
echo.
echo ========================================================================
pause
