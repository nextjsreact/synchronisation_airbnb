@echo off
chcp 65001 > nul
echo.
echo ========================================
echo   Vérifier les notifications
echo ========================================
echo.
python check_notifications_detail.py
echo.
pause
