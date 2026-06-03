@echo off
chcp 65001 >nul
echo ========================================================================
echo 🧪 TEST AVEC UNE SEULE RÉSERVATION
echo ========================================================================
echo.
echo Ce test va :
echo 1. Scraper toutes les réservations
echo 2. Trouver la réservation HM4TB95HKS (Hamza)
echo 3. Collecter les coordonnées (téléphone + email)
echo 4. Convertir la devise en DZD
echo 5. Proposer l'envoi à l'API Next.js
echo.
echo ⏱️  Durée estimée : 3-5 minutes
echo.
echo ========================================================================
pause

python TEST_UNE_RESERVATION.py HM4TB95HKS

echo.
echo ========================================================================
echo ✅ TEST TERMINÉ
echo ========================================================================
pause
