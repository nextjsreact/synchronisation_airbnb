@echo off
chcp 65001 >nul
echo ========================================================================
echo 🧪 TEST D'INTÉGRATION - Collecte des coordonnées
echo ========================================================================
echo.
echo Ce test va vérifier que l'intégration est complète :
echo.
echo 1. ✅ Code intégré dans airbnb_scraper.py
echo 2. ✅ Code intégré dans targeted_scraper.py
echo 3. ✅ Variable COLLECT_CONTACTS dans .env
echo 4. ⚠️  Test en conditions réelles (à faire manuellement)
echo.
echo ========================================================================
echo.

echo 📋 Vérification 1 : airbnb_scraper.py
echo ========================================================================
findstr /C:"enrich_with_contacts" airbnb_scraper.py >nul
if %errorlevel% equ 0 (
    echo ✅ Fonction enrich_with_contacts trouvée
) else (
    echo ❌ Fonction enrich_with_contacts NON trouvée
)

findstr /C:"COLLECT_CONTACTS" airbnb_scraper.py >nul
if %errorlevel% equ 0 (
    echo ✅ Variable COLLECT_CONTACTS trouvée
) else (
    echo ❌ Variable COLLECT_CONTACTS NON trouvée
)

findstr /C:"telephone_voyageur" airbnb_scraper.py >nul
if %errorlevel% equ 0 (
    echo ✅ Champ telephone_voyageur trouvé
) else (
    echo ❌ Champ telephone_voyageur NON trouvé
)

echo.
echo 📋 Vérification 2 : targeted_scraper.py
echo ========================================================================
findstr /C:"enrich_with_contacts" targeted_scraper.py >nul
if %errorlevel% equ 0 (
    echo ✅ Import enrich_with_contacts trouvé
) else (
    echo ❌ Import enrich_with_contacts NON trouvé
)

findstr /C:"COLLECT_CONTACTS" targeted_scraper.py >nul
if %errorlevel% equ 0 (
    echo ✅ Variable COLLECT_CONTACTS trouvée
) else (
    echo ❌ Variable COLLECT_CONTACTS NON trouvée
)

echo.
echo 📋 Vérification 3 : .env
echo ========================================================================
findstr /C:"COLLECT_CONTACTS" .env >nul
if %errorlevel% equ 0 (
    echo ✅ Variable COLLECT_CONTACTS trouvée dans .env
    findstr /C:"COLLECT_CONTACTS" .env
) else (
    echo ❌ Variable COLLECT_CONTACTS NON trouvée dans .env
)

echo.
echo 📋 Vérification 4 : .env.example
echo ========================================================================
findstr /C:"COLLECT_CONTACTS" .env.example >nul
if %errorlevel% equ 0 (
    echo ✅ Variable COLLECT_CONTACTS trouvée dans .env.example
) else (
    echo ❌ Variable COLLECT_CONTACTS NON trouvée dans .env.example
)

echo.
echo ========================================================================
echo ✅ VÉRIFICATIONS AUTOMATIQUES TERMINÉES
echo ========================================================================
echo.
echo 📋 PROCHAINES ÉTAPES (manuelles) :
echo.
echo 1. Vérifier la structure Supabase :
echo    - Table : reservations
echo    - Colonnes : guest_phone, guest_email
echo.
echo 2. Vérifier l'API Next.js :
echo    - Endpoint : /api/airbnb/sync
echo    - Mapping : telephone_voyageur → guest_phone
echo    - Mapping : email_voyageur → guest_email
echo.
echo 3. Test en conditions réelles :
echo    a. Modifier .env : COLLECT_CONTACTS=true
echo    b. Lancer : SCRAPING_COMPLET_MAINTENANT.bat
echo    c. Vérifier : output/reservations_airbnb.json
echo    d. Vérifier : Supabase (table reservations)
echo.
echo ========================================================================
pause
