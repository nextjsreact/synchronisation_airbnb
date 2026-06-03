# =============================================================================
# Re-pousse TOUS les lofts Airbnb pour collecter les coordonnees (phone/email)
# Necessite COLLECT_CONTACTS=true dans .env et container targeted-scraper
# redemarre avec le nouveau .env.
# =============================================================================

$ErrorActionPreference = "Stop"

$envFile = "D:\Airbnb_transfer_v2\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERREUR: .env introuvable" -ForegroundColor Red; exit 1
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^=#][^=]*)\s*=\s*(.*?)\s*$') {
        Set-Item -Path "Env:\$($matches[1].Trim())" -Value $matches[2].Trim().Trim('"').Trim("'")
    }
}

$headers = @{
    "apikey"        = $env:SUPABASE_SERVICE_ROLE_KEY
    "Authorization" = "Bearer $env:SUPABASE_SERVICE_ROLE_KEY"
    "Content-Type"  = "application/json"
    "Prefer"        = "return=representation"
}

Write-Host ""
Write-Host "Recuperation des lofts Airbnb actifs..." -ForegroundColor Cyan

# Lofts avec un airbnb_listing_id non nul
$lofts = Invoke-RestMethod `
    -Uri "$($env:NEXT_PUBLIC_SUPABASE_URL)/rest/v1/lofts?select=id,name,airbnb_listing_id&airbnb_listing_id=not.is.null&order=name" `
    -Headers $headers -Method Get

Write-Host ("   {0} loft(s) avec airbnb_listing_id" -f $lofts.Count) -ForegroundColor Green
Write-Host ""

$now = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
$queued = 0
$skipped = 0

foreach ($loft in $lofts) {
    $body = @{
        listing_id   = $loft.airbnb_listing_id
        status       = "pending"
        reason       = "collect_contacts_$(Get-Date -Format 'yyyyMMddHHmmss')"
        retry_count  = 0
        error_message = $null
        created_at   = $now
    } | ConvertTo-Json -Compress

    try {
        Invoke-RestMethod `
            -Uri "$($env:NEXT_PUBLIC_SUPABASE_URL)/rest/v1/sync_queue" `
            -Headers $headers -Method Post -Body $body | Out-Null
        Write-Host ("   + {0,-30} {1}" -f $loft.name, $loft.airbnb_listing_id) -ForegroundColor Green
        $queued++
    } catch {
        Write-Host ("   ! {0,-30} ERREUR: {1}" -f $loft.name, $_) -ForegroundColor Red
        $skipped++
    }
}

Write-Host ""
Write-Host ("=== {0} loft(s) re-pousse(s), {1} erreur(s) ===" -f $queued, $skipped) -ForegroundColor Cyan
Write-Host ""
Write-Host "Le targeted-scraper va les traiter dans ~30s (1 loft toutes les ~20-40s avec contacts)." -ForegroundColor DarkGray
Write-Host "Surveillance : docker compose -f D:\Airbnb_transfer_v2\docker-compose.sync.yml logs -f targeted-scraper" -ForegroundColor DarkGray
Write-Host ""
