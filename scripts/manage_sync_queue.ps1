# =============================================================================
# Airbnb Sync Queue Manager
# =============================================================================
# A. Affiche l'etat de sync_queue (pending / processing / done / failed)
# B. Re-pousse les entrees failed (reset retry_count=0, status=pending)
# C. Affiche le SQL de nettoyage des notifs de test
# =============================================================================

$ErrorActionPreference = "Stop"

# --- 1. Charger .env ----------------------------------------------------------
$envFile = "D:\Airbnb_transfer_v2\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERREUR: .env introuvable a $envFile" -ForegroundColor Red
    exit 1
}

Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^=#][^=]*)\s*=\s*(.*?)\s*$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"').Trim("'")
        Set-Item -Path "Env:\$name" -Value $value
    }
}

$SUPABASE_URL = $env:NEXT_PUBLIC_SUPABASE_URL
$SUPABASE_KEY = $env:SUPABASE_SERVICE_ROLE_KEY

if (-not $SUPABASE_URL -or -not $SUPABASE_KEY) {
    Write-Host "ERREUR: NEXT_PUBLIC_SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY manquant dans .env" -ForegroundColor Red
    exit 1
}

$headers = @{
    "apikey"        = $SUPABASE_KEY
    "Authorization" = "Bearer $SUPABASE_KEY"
    "Content-Type"  = "application/json"
    "Prefer"        = "return=representation"
}

function Supa-Get($path) {
    Invoke-RestMethod -Uri "$SUPABASE_URL/rest/v1/$path" -Headers $headers -Method Get
}

function Supa-Patch($path, $body) {
    Invoke-RestMethod -Uri "$SUPABASE_URL/rest/v1/$path" -Headers $headers -Method Patch -Body ($body | ConvertTo-Json -Compress)
}

# --- ETAPE A : Etat de la queue ----------------------------------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ETAPE A : Etat de sync_queue (7 derniers jours)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$sevenDaysAgo = (Get-Date).AddDays(-7).ToString("yyyy-MM-ddTHH:mm:ssZ")
$allRecent = Supa-Get "sync_queue?select=id,listing_id,status,retry_count,error_message,created_at,processed_at&created_at=gt.$sevenDaysAgo&order=created_at.desc&limit=500"

$byStatus = $allRecent | Group-Object status
foreach ($g in ($byStatus | Sort-Object Name)) {
    $color = switch ($g.Name) {
        'pending'    { 'Yellow' }
        'processing' { 'Magenta' }
        'done'       { 'Green' }
        'failed'     { 'Red' }
        default      { 'Gray' }
    }
    Write-Host ("   {0,-12} : {1,4}" -f $g.Name, $g.Count) -ForegroundColor $color
}

$failedEntries = @($allRecent | Where-Object { $_.status -eq 'failed' })
$pendingEntries = @($allRecent | Where-Object { $_.status -eq 'pending' -or $_.status -eq 'processing' })

if ($failedEntries.Count -eq 0) {
    Write-Host ""
    Write-Host "   -> Aucune entree 'failed'. Rien a re-pousser." -ForegroundColor Green
}

# --- ETAPE B : Re-pousser les failed -----------------------------------------
if ($failedEntries.Count -gt 0) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  ETAPE B : Re-pousser $($failedEntries.Count) entree(s) FAILED" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan

    Write-Host ""
    Write-Host "   Listing ID        | Retry | Erreur" -ForegroundColor DarkGray
    Write-Host "   ------------------|-------|------------------------------------------------" -ForegroundColor DarkGray
    foreach ($e in $failedEntries) {
        $err = if ($e.error_message) { $e.error_message } else { '-' }
        if ($err.Length -gt 50) { $err = $err.Substring(0, 47) + "..." }
        Write-Host ("   {0,-18}| {1,5} | {2}" -f $e.listing_id, $e.retry_count, $err)
    }

    Write-Host ""
    $confirm = Read-Host "   Re-pousser ces entrees (reset retry=0, status=pending) ? (o/N)"
    if ($confirm -eq 'o' -or $confirm -eq 'O') {
        $repushCount = 0
        foreach ($e in $failedEntries) {
            $body = @{
                status         = "pending"
                retry_count    = 0
                error_message  = $null
                processed_at   = $null
            }
            try {
                Supa-Patch "sync_queue?id=eq.$($e.id)" $body | Out-Null
                Write-Host "      OK  #$($e.id) listing=$($e.listing_id)" -ForegroundColor Green
                $repushCount++
            } catch {
                Write-Host "      ERR #$($e.id) : $_" -ForegroundColor Red
            }
        }
        Write-Host ""
        Write-Host "   -> $repushCount entree(s) re-poussee(s). Le targeted-scraper va les detecter dans ~30s." -ForegroundColor Green
        Write-Host "   -> Surveille : docker compose -f docker-compose.sync.yml logs -f targeted-scraper" -ForegroundColor DarkGray
    } else {
        Write-Host "   -> Annule. Aucune modification." -ForegroundColor DarkGray
    }
}

# --- ETAPE B-bis : Lister les pending/processing stagnants -------------------
$stale = @($pendingEntries | Where-Object {
        $created = [DateTime]::Parse($_.created_at)
        $age = (Get-Date) - $created
        $age.TotalHours -gt 2
    })

if ($stale.Count -gt 0) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Yellow
    Write-Host "  ATTENTION : $($stale.Count) entree(s) pending/processing de +2h" -ForegroundColor Yellow
    Write-Host "================================================================" -ForegroundColor Yellow

    foreach ($e in $stale) {
        $age = (Get-Date) - [DateTime]::Parse($e.created_at)
        $ageStr = if ($age.TotalHours -gt 24) { "{0:0.0}j" -f ($age.TotalHours / 24) } else { "{0:0.0}h" -f $age.TotalHours }
        Write-Host ("   {0,-18} {1,-12} age={2}" -f $e.listing_id, $e.status, $ageStr) -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "   Le targeted-scraper est peut-etre bloque. Verifie les logs :`n" -ForegroundColor Yellow
    Write-Host "     docker compose -f docker-compose.sync.yml logs --tail=50 targeted-scraper" -ForegroundColor White
    Write-Host "     docker compose -f docker-compose.sync.yml ps" -ForegroundColor White
}

# --- ETAPE C : SQL de nettoyage ----------------------------------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ETAPE C : Nettoyage notifs de test (SQL a executer)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "   -- 1. Voir les notifs de test" -ForegroundColor DarkGray
Write-Host "   SELECT id, title, metadata->>'guest_name' AS guest, created_at" -ForegroundColor White
Write-Host "   FROM airbnb_notifications" -ForegroundColor White
Write-Host "   WHERE created_at > NOW() - INTERVAL '1 day'" -ForegroundColor White
Write-Host "     AND (metadata->>'guest_name' LIKE 'Test%'" -ForegroundColor White
Write-Host "       OR title LIKE '%Test%'" -ForegroundColor White
Write-Host "       OR metadata->>'test' = 'true');" -ForegroundColor White
Write-Host ""
Write-Host "   -- 2. Supprimer (verifie d'abord avec le SELECT ci-dessus)" -ForegroundColor DarkGray
Write-Host "   DELETE FROM airbnb_notifications" -ForegroundColor White
Write-Host "   WHERE metadata->>'guest_name' LIKE 'Test%'" -ForegroundColor White
Write-Host "      OR title LIKE '%Test%'" -ForegroundColor White
Write-Host "      OR metadata->>'test' = 'true';" -ForegroundColor White
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
