@echo off
chcp 65001 >nul
echo ========================================================================
echo    📦 PUSH VERS GITHUB
echo ========================================================================
echo.

echo [1] Vérification des fichiers sensibles...
echo ------------------------------------------------------------------------
git status | findstr /C:".env" /C:"airbnb_session.json" /C:"*.json"
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ⚠️  ATTENTION : Des fichiers sensibles sont détectés !
    echo    Vérifiez que .env et les fichiers JSON ne sont pas trackés.
    echo.
    pause
    exit /b 1
)
echo ✅ Aucun fichier sensible détecté
echo.

echo [2] Statut Git actuel
echo ------------------------------------------------------------------------
git status
echo.

echo [3] Configuration du remote GitHub
echo ------------------------------------------------------------------------
echo.
echo Entrez l'URL de votre repository GitHub :
echo Exemple : https://github.com/votre-username/airbnb-sync.git
echo.
set /p GITHUB_URL="URL GitHub : "

if "%GITHUB_URL%"=="" (
    echo ❌ URL vide, abandon.
    pause
    exit /b 1
)

echo.
echo Configuration du remote 'origin'...
git remote remove origin 2>nul
git remote add origin %GITHUB_URL%

if %ERRORLEVEL% NEQ 0 (
    echo ❌ Erreur lors de l'ajout du remote
    pause
    exit /b 1
)

echo ✅ Remote configuré
git remote -v
echo.

echo [4] Push vers GitHub
echo ------------------------------------------------------------------------
echo.
echo Renommage de la branche en 'main'...
git branch -M main

echo.
echo Push vers GitHub...
git push -u origin main

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Erreur lors du push
    echo.
    echo Solutions possibles :
    echo   1. Vérifiez vos credentials GitHub
    echo   2. Utilisez un Personal Access Token
    echo   3. Configurez SSH
    echo.
    echo Pour générer un token :
    echo   https://github.com/settings/tokens
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo ✅ PUSH RÉUSSI !
echo ========================================================================
echo.
echo Votre projet est maintenant sur GitHub : %GITHUB_URL%
echo.
echo Prochaines étapes :
echo   1. Vérifiez sur GitHub que tout est bien présent
echo   2. Vérifiez que .env n'est PAS visible
echo   3. Ajoutez des collaborateurs si nécessaire
echo   4. Configurez les GitHub Actions (optionnel)
echo.
pause
