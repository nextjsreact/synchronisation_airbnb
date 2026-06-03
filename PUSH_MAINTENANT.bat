@echo off
chcp 65001 >nul
cls
echo.
echo ========================================================================
echo                    🚀 PUSH VERS GITHUB
echo ========================================================================
echo.
echo Ce script va pousser votre projet vers GitHub.
echo.
echo Repository : https://github.com/nextjsreact/synchronisation_airbnb
echo.
echo ========================================================================
echo.
echo Git va vous demander vos identifiants :
echo.
echo   👤 Username : nextjsreact
echo   🔑 Password : [VOTRE TOKEN GITHUB]
echo.
echo ⚠️  IMPORTANT :
echo    - Le token ne s'affichera PAS quand vous le tapez (normal)
echo    - Collez-le avec Ctrl+V ou clic droit
echo    - Appuyez sur Entrée après avoir collé
echo.
echo ========================================================================
echo.
pause
echo.
echo 📤 Push en cours vers GitHub...
echo.

git push -u origin main

echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================================
    echo.
    echo            ✅✅✅ SUCCÈS ! ✅✅✅
    echo.
    echo ========================================================================
    echo.
    echo 🎉 Votre projet est maintenant sur GitHub !
    echo.
    echo 🔗 Lien : https://github.com/nextjsreact/synchronisation_airbnb
    echo.
    echo ========================================================================
    echo 📋 VÉRIFICATIONS À FAIRE :
    echo ========================================================================
    echo.
    echo 1. Ouvrez le lien ci-dessus dans votre navigateur
    echo 2. Vérifiez que le README s'affiche correctement
    echo 3. Vérifiez que tous les fichiers sont présents (85 fichiers)
    echo 4. ⚠️  IMPORTANT : Vérifiez que .env n'est PAS visible
    echo.
    echo ========================================================================
    echo 💾 POUR LES PROCHAINS PUSH :
    echo ========================================================================
    echo.
    echo Les credentials sont sauvegardées dans Windows.
    echo Pour les prochaines modifications :
    echo.
    echo   git add .
    echo   git commit -m "votre message"
    echo   git push
    echo.
    echo Vous n'aurez plus besoin d'entrer le token !
    echo.
    echo ========================================================================
    echo.
) else (
    echo ========================================================================
    echo.
    echo            ❌ ERREUR
    echo.
    echo ========================================================================
    echo.
    echo Causes possibles :
    echo   1. Token incorrect ou expiré
    echo   2. Username incorrect (doit être : nextjsreact)
    echo   3. Permissions insuffisantes sur le token
    echo.
    echo Solutions :
    echo   1. Vérifiez que vous avez bien copié le token complet
    echo   2. Générez un nouveau token si nécessaire
    echo   3. Vérifiez que le token a les permissions "repo"
    echo.
    echo ========================================================================
    echo.
)

pause
