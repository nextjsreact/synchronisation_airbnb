@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   🚨 SOLUTION URGENTE
echo   Récupérer la nouvelle réservation
echo ========================================
echo.
echo Le Targeted Scraper échoue à cause de timeouts réseau.
echo.
echo On va lancer un SCRAPING COMPLET pour récupérer
echo la nouvelle réservation immédiatement.
echo.
echo Durée estimée: ~30 minutes
echo.
pause
echo.
echo ⏳ Lancement du scraping complet...
echo.
python airbnb_scraper.py
echo.
echo ========================================
echo   ✅ Scraping terminé !
echo ========================================
echo.
echo Vérifiez maintenant votre application Next.js.
echo La nouvelle réservation devrait apparaître.
echo.
pause
