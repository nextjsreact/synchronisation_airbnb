@echo off
echo ========================================
echo Verifier/Ajouter colonne retry_count
echo ========================================
echo.

python execute_migration.py

echo.
echo Appuyez sur une touche pour fermer...
pause > nul
