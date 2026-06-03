$body = @{
    reservations = @(
        @{
            airbnb_confirmation_code = "TEST_LUNA"
            guest_name = "Test Luna"
            loft_id = "faf9a006-2b66-4499-a4c9-b08e3908e64f"
            check_in_date = "2026-06-03"
            check_out_date = "2026-06-05"
            total_amount = 100
            currency_code = "EUR"
            status = "confirmed"
            source = "airbnb"
        }
    )
} | ConvertTo-Json -Depth 10

Write-Host "Envoi de la réservation test pour Luna loft..."
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri "http://localhost:3000/api/airbnb/sync" -Method POST -ContentType "application/json" -Body $body -UseBasicParsing
    
    Write-Host "✅ Succès!"
    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Response:"
    Write-Host $response.Content
}
catch {
    Write-Host "❌ Erreur: $($_.Exception.Message)"
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Détails: $responseBody"
    }
}
