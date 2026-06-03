@echo off
chcp 65001 > nul
echo ========================================================================
echo                    🔍 DEBUG TARGETED SCRAPER                           
echo ========================================================================
echo.
echo Ce script va tester les deux méthodes de scraping :
echo   1. API GraphQL (rapide mais cassée)
echo   2. Fallback Pagination (lent mais fiable)
echo.
echo ⏱️  Durée estimée : 2-3 minutes
echo.
pause

cd /d "%~dp0"
python debug_targeted_scraper.py

echo.
echo ========================================================================
echo                           ✅ DEBUG TERMINÉ                             
echo ========================================================================
echo.
echo 📄 Consultez le fichier DIFFERENCE_API_GRAPHQL_VS_FALLBACK.md
echo    pour comprendre les différences entre les deux méthodes
echo.
pause
