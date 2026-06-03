@echo off
chcp 65001 > nul
echo ========================================================================
echo              🔥 MISE À JOUR À CHAUD DU SCRAPER                         
echo ========================================================================
echo.
echo Cette méthode copie le nouveau code directement dans le container
echo sans avoir à reconstruire l'image Docker (plus rapide).
echo.
pause

cd /d "%~dp0"

echo.
echo [1/2] Copie du nouveau targeted_scraper.py dans le container...
docker cp targeted_scraper.py targeted-scraper:/app/targeted_scraper.py

echo.
echo [2/2] Redémarrage du container...
docker-compose -f docker-compose.sync.yml restart targeted-scraper

echo.
echo ========================================================================
echo                           ✅ TERMINÉ                                   
echo ========================================================================
echo.
echo Le container utilise maintenant le nouveau code avec le fallback !
echo.
echo Pour voir les logs :
echo   docker-compose -f docker-compose.sync.yml logs -f targeted-scraper
echo.
echo Vous devriez voir :
echo   "⚠️  API GraphQL vide ou cassée, utilisation du fallback..."
echo.
pause
