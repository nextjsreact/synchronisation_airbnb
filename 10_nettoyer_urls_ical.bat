@echo off
chcp 65001 >nul
echo.
echo ========================================
echo 🧹 NETTOYAGE DES URLs iCAL INVALIDES
echo ========================================
echo.

python NETTOYER_URLS_ICAL.py

echo.
pause
