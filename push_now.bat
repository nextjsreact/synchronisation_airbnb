@echo off
chcp 65001 >nul
echo ========================================================================
echo    🚀 PUSH VERS GITHUB
echo ========================================================================
echo.
echo Lors du push, Git va vous demander vos identifiants :
echo.
echo   Username : nextjsreact
echo   Password : [COLLEZ VOTRE TOKEN ICI]
echo.
echo ⚠️  Le token ne s'affichera pas quand vous le collez (normal)
echo.
pause
echo.
echo Push en cours...
echo.
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================================
    echo ✅ PUSH RÉUSSI !
    echo ========================================================================
    echo.
    echo Votre projet est maintenant sur GitHub :
    echo https://github.com/nextjsreact/synchronisation_airbnb
    echo.
    echo Vérifiez que :
    echo   1. Tous les fichiers sont présents
    echo   2. Le README s'affiche correctement
    echo   3. Le fichier .env n'est PAS visible
    echo.
) else (
    echo ========================================================================
    echo ❌ ERREUR
    echo ========================================================================
    echo.
    echo Vérifiez que :
    echo   1. Le token est correct
    echo   2. Vous avez entré "nextjsreact" comme username
    echo   3. Le token a les permissions "repo"
    echo.
)
pause
