@echo off
chcp 65001 > nul
cls
echo.
echo ========================================================================
echo           🧪 TEST D'EXTRACTION - Code HM4TB95HKS                      
echo ========================================================================
echo.
echo Ce test va extraire les coordonnées de la réservation HM4TB95HKS
echo (l'exemple que vous avez fourni avec Hamza)
echo.
echo Attendu : +213 793 86 24 94
echo.
echo ========================================================================
echo.

cd /d "%~dp0"

python test_contact_extraction.py HM4TB95HKS

pause
