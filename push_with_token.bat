@echo off
chcp 65001 >nul
echo ========================================================================
echo    🔐 PUSH VERS GITHUB AVEC TOKEN
echo ========================================================================
echo.
echo Ce script va pousser votre projet vers GitHub en utilisant un
echo Personal Access Token pour l'authentification.
echo.
echo ⚠️  IMPORTANT : Vous devez d'abord générer un token sur GitHub :
echo    https://github.com/settings/tokens
echo.
echo    Permissions requises : repo (Full control)
echo.
pause
echo.

set /p TOKEN="Entrez votre Personal Access Token : "

if "%TOKEN%"=="" (
    echo.
    echo ❌ Erreur : Token vide
    pause
    exit /b 1
)

echo.
echo [1] Configuration du remote avec token...
echo ------------------------------------------------------------------------
git remote remove origin 2>nul
git remote add origin https://nextjsreact:%TOKEN%@github.com/nextjsreact/synchronisation_airbnb.git

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors de la configuration du remote
    pause
    exit /b 1
)

echo ✅ Remote configuré
echo.

echo [2] Push vers GitHub...
echo ------------------------------------------------------------------------
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================================
    echo ✅ PUSH RÉUSSI !
    echo ========================================================================
    echo.
    echo Votre projet est maintenant sur GitHub :
    echo https://github.com/nextjsreact/synchronisation_airbnb
    echo.
    
    echo [3] Nettoyage du token de l'URL...
    echo ------------------------------------------------------------------------
    git remote remove origin
    git remote add origin https://github.com/nextjsreact/synchronisation_airbnb.git
    echo ✅ Token supprimé de la config Git (sécurité)
    echo.
    
    echo ========================================================================
    echo 📋 PROCHAINES ÉTAPES
    echo ========================================================================
    echo.
    echo 1. Vérifiez sur GitHub que tout est bien présent
    echo 2. Vérifiez que .env n'est PAS visible
    echo 3. Ajoutez une description au repository
    echo 4. Invitez des collaborateurs si nécessaire
    echo.
) else (
    echo.
    echo ========================================================================
    echo ❌ ERREUR LORS DU PUSH
    echo ========================================================================
    echo.
    echo Causes possibles :
    echo   1. Token invalide ou expiré
    echo   2. Permissions insuffisantes (vérifiez que 'repo' est coché)
    echo   3. Repository n'existe pas ou est inaccessible
    echo.
    echo Solutions :
    echo   1. Générez un nouveau token : https://github.com/settings/tokens
    echo   2. Vérifiez que le repository existe
    echo   3. Vérifiez que vous êtes connecté avec le bon compte
    echo.
)

pause
