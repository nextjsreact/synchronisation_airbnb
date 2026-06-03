@echo off
echo ========================================
echo Verifier l'etat de la sync_queue
echo ========================================
echo.

python check_sync_queue.py

echo.
echo Appuyez sur une touche pour fermer...
pause > nul
