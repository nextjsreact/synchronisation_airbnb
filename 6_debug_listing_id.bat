@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo           🔍 DEBUG LISTING_ID - Diagnostic du problème                
echo ========================================================================
echo.
echo Ce script va :
echo   1. Scraper 1 page de réservations Airbnb
echo   2. Afficher la structure JSON complète
echo   3. Identifier où se trouve le listing_id
echo   4. Tester le parsing actuel
echo.
echo ⏱️  Durée estimée : 2-3 minutes
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/1] Lancement du diagnostic...
python debug_listing_id.py

echo.
echo ========================================================================
echo                           ✅ DIAGNOSTIC TERMINÉ                        
echo ========================================================================
echo.
echo 📋 Fichiers créés :
echo   - debug_api_response_1.json (structure complète de l'API)
echo   - debug_api_response_2.json (si plusieurs réponses)
echo.
echo 🔍 Prochaines étapes :
echo   1. Ouvrez les fichiers JSON pour voir la structure
echo   2. Cherchez le champ qui contient le listing_id
echo   3. Corrigez _parse_reservation_node() dans airbnb_scraper.py
echo.
pause
