@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo           🧪 TEST D'EXTRACTION DES COORDONNÉES                        
echo ========================================================================
echo.
echo Ce script va tester l'extraction des coordonnées pour UNE réservation.
echo.
echo Code de confirmation par défaut : HM4TB95HKS
echo.
echo Pour tester un autre code :
echo   TEST_CONTACT.bat VOTRE_CODE
echo.
echo ========================================================================
echo.
pause

cd /d "%~dp0"

echo.
echo [1/1] Lancement du test...

if "%1"=="" (
    python test_contact_extraction.py
) else (
    python test_contact_extraction.py %1
)

echo.
echo ========================================================================
echo                           ✅ TEST TERMINÉ                              
echo ========================================================================
echo.
echo Vérifiez les résultats ci-dessus.
echo.
echo Si le téléphone n'est pas trouvé :
echo   1. Vérifiez la capture d'écran dans output\
echo   2. Vérifiez que vous êtes bien connecté
echo   3. Vérifiez que le code de confirmation est correct
echo.
pause
