@echo off
chcp 65001 > nul
title Déclencheur de Synchronisation Airbnb Ciblée
cd /d "%~dp0"
python scripts/declencher_sync_ciblee.py
pause
