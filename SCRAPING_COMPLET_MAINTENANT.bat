@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo              🔥 SCRAPING COMPLET IMMÉDIAT (TOUTES LES RÉSERVATIONS)   
echo ========================================================================
echo.
echo ⚠️  Ce script va :
echo.
echo   1. Lancer un scraping COMPLET de toutes les réservations Airbnb
echo   2. Utiliser le fallback (30-40 minutes)
echo   3. Synchroniser TOUT dans Supabase
echo.
echo 💡 Utilisez ce script pour :
echo   - Récupérer toutes les nouvelles réservations MAINTENANT
echo   - Faire une synchronisation complète
echo   - Tester que le fallback fonctionne
echo.
echo ⏱️  Durée : 30-40 minutes
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo 🚀 Lancement du scraping complet...
echo.
echo ========================================================================
echo                         📊 LOGS EN DIRECT                              
echo ========================================================================
echo.

python airbnb_scraper.py

echo.
echo ========================================================================
echo                      ✅ SCRAPING TERMINÉ                               
echo ========================================================================
echo.
echo Pour voir les réservations synchronisées :
echo   python view_reservations.py
echo.
pause
