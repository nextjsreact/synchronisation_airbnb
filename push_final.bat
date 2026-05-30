@echo off
chcp 65001 >nul
echo ========================================================================
echo    🚀 PUSH VERS GITHUB (Credentials Nettoyées)
echo ========================================================================
echo.
echo Les anciennes credentials ont été supprimées.
echo Git va maintenant vous demander vos NOUVEAUX identifiants.
echo.
echo IMPORTANT :
echo   Username : nextjsreact
echo   Password : [VOTRE NOUVEAU TOKEN]
echo.
echo ⚠️  Le token ne s'affichera pas (normal pour la sécurité)
echo.
pause
echo.
echo Push en cours...
echo.
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================================
    echo ✅✅✅ PUSH RÉUSSI ! ✅✅✅
    echo ========================================================================
    echo.
    echo 🎉 Votre projet est maintenant sur GitHub !
    echo.
    echo 🔗 URL : https://github.com/nextjsreact/synchronisation_airbnb
    echo.
    echo 📋 Prochaines étapes :
    echo    1. Ouvrez le lien ci-dessus dans votre navigateur
    echo    2. Vérifiez que tous les fichiers sont présents
    echo    3. Vérifiez que le README s'affiche correctement
    echo    4. IMPORTANT : Vérifiez que .env n'est PAS visible
    echo.
    echo 💾 Les credentials sont maintenant sauvegardées dans Windows
    echo    Vous n'aurez plus besoin d'entrer le token pour les prochains push
    echo.
) else (
    echo.
    echo ========================================================================
    echo ❌ ERREUR
    echo ========================================================================
    echo.
    echo Si l'erreur persiste :
    echo   1. Vérifiez que le token est correct
    echo   2. Vérifiez que vous avez bien entré "nextjsreact" comme username
    echo   3. Vérifiez que le token a les permissions "repo"
    echo   4. Générez un nouveau token si nécessaire
    echo.
)
pause
