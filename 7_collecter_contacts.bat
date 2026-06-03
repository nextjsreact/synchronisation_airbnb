@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo           📞 COLLECTE DES COORDONNÉES DES VOYAGEURS                   
echo ========================================================================
echo.
echo Ce script va :
echo   1. Charger les réservations existantes
echo   2. Filtrer les réservations actives (à venir + en cours)
echo   3. Pour chaque réservation :
echo      • Ouvrir la page de détails
echo      • Extraire le numéro de téléphone
echo      • Extraire l'email
echo   4. Sauvegarder dans reservations_avec_contacts.json
echo.
echo ⏱️  Durée estimée : ~5 secondes par réservation
echo.
echo ⚠️  IMPORTANT :
echo   • Nécessite d'avoir lancé le scraping complet avant
echo   • Les coordonnées ne sont disponibles que pour les réservations actives
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/1] Lancement de la collecte...
python scrape_guest_contacts.py

echo.
echo ========================================================================
echo                           ✅ COLLECTE TERMINÉE                         
echo ========================================================================
echo.
echo 📁 Fichier créé : output\reservations_avec_contacts.json
echo.
echo Pour voir les données :
echo   • Ouvrez le fichier JSON
echo   • Ou importez-le dans votre application
echo.
pause
