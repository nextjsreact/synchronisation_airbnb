# =============================================================================
# Test dedup 4 couches — insertion manuelle + sync scrape + verification
# =============================================================================
# Scenarii testes :
#   1. Insertion manuelle d'une resa (sans airbnb_confirmation_code)
#   2. Sync Airbnb envoyant la MEME resa (meme loft/nom/date) avec un id Airbnb
#   3. Verification : linked=1, pas de doublon, champs admin preserves
# =============================================================================

$ErrorActionPreference = "Stop"

# --- 1. Charger .env ---------------------------------------------------------
$envFile = "D:\Airbnb_transfer_v2\.env"
if (-not (Test-Path $envFile)) {
    Write-Host "ERREUR: .env introuvable" -ForegroundColor Red
    exit 1
}
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*([^=#][^=]*)\s*=\s*(.*?)\s*$') {
        Set-Item -Path "Env:\$($matches[1].Trim())" -Value $matches[2].Trim().Trim('"').Trim("'")
    }
}

$API_URL = $env:NEXTJS_API_URL
$API_KEY = $env:NEXTJS_API_KEY
$SUPA_URL = $env:NEXT_PUBLIC_SUPABASE_URL
$SUPA_KEY = $env:SUPABASE_SERVICE_ROLE_KEY

$HEADERS_SUPA = @{
    "apikey"        = $SUPA_KEY
    "Authorization" = "Bearer $SUPA_KEY"
    "Content-Type"  = "application/json"
    "Prefer"        = "return=representation"
}

$HEADERS_API = @{
    "Authorization" = "Bearer $API_KEY"
    "Content-Type"  = "application/json"
}

# Constantes du test
$LUNA_LOFT_ID   = "faf9a006-2b66-4499-a4c9-b08e3908e64f"
$LUNA_LISTING   = "1352875010941932574"
$GUEST_NAME     = "Test Dedup $((Get-Date).ToString('HHmmss'))"  # unique par run
$CHECK_IN       = "2026-12-01"
$CHECK_OUT      = "2026-12-05"
$AIRBNB_ID      = "TESTDEDUP$((Get-Date).ToString('HHmmss'))"

$pass = 0
$fail = 0
function Test-Assert {
    param([bool]$Cond, [string]$Msg)
    if ($Cond) {
        Write-Host "      PASS : $Msg" -ForegroundColor Green
        $script:pass++
    } else {
        Write-Host "      FAIL : $Msg" -ForegroundColor Red
        $script:fail++
    }
}

# --- 2. Nettoyage des tests precedents --------------------------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ETAPE 0 : Nettoyage" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$delUrl = "$SUPA_URL/rest/v1/reservations?or=(airbnb_confirmation_code.like.TESTDEDUP*,guest_name.like.Test Dedup*)"
try {
    $null = Invoke-RestMethod -Uri $delUrl -Headers $HEADERS_SUPA -Method Delete
    Write-Host "   Nettoyage OK" -ForegroundColor DarkGray
} catch {
    Write-Host "   (rien a nettoyer ou erreur: $_)" -ForegroundColor DarkGray
}

# --- 3. Insertion manuelle (sans airbnb_confirmation_code) -------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ETAPE 1 : Insertion manuelle (admin/employe)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   Guest      : $GUEST_NAME"
Write-Host "   Loft       : Luna ($LUNA_LOFT_ID)"
Write-Host "   Dates      : $CHECK_IN -> $CHECK_OUT"
Write-Host "   Source     : manual (PAS d'airbnb_confirmation_code)"

$manualBody = @{
    loft_id                = $LUNA_LOFT_ID
    guest_name             = $GUEST_NAME
    check_in_date          = $CHECK_IN
    check_out_date         = $CHECK_OUT
    # nights = GENERATED ALWAYS AS (check_out_date - check_in_date) → on ne le fournit pas
    guest_count            = 2
    base_price             = 40000   # NOT NULL obligatoire
    cleaning_fee           = 5000
    service_fee            = 0
    taxes                  = 0
    total_amount           = 50000
    currency_code          = "DZD"
    status                 = "confirmed"
    source                 = "manual"
    # === Champs ADMIN a preserver (smart update) ===
    special_requests       = "Demande speciale ADMIN (NE PAS ecraser)"
    guest_phone            = "+213555999888"
    guest_email            = "admin-resa@example.com"
    payment_status         = "paid"
} | ConvertTo-Json

Write-Host "   Body envoye : $manualBody"

try {
    $manualInsert = Invoke-RestMethod `
        -Uri "$SUPA_URL/rest/v1/reservations" `
        -Headers $HEADERS_SUPA -Method Post -Body $manualBody
} catch {
    Write-Host "   ERREUR Supabase insert:" -ForegroundColor Red
    Write-Host "   HTTP Status: $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    $reader = $_.Exception.Response.GetResponseStream()
    if ($reader) {
        $reader.Position = 0
        $body = (New-Object System.IO.StreamReader($reader)).ReadToEnd()
        Write-Host "   Body: $body" -ForegroundColor Red
    }
    throw
}

$manualId = $manualInsert[0].id
Write-Host "   -> Resa manuelle creee : $manualId" -ForegroundColor Green
Write-Host ""

# --- 4. Sync Airbnb (meme loft/nom/date, mais avec un airbnb_id) -------------
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ETAPE 2 : Sync Airbnb (simulation scraping)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   airbnb_confirmation_code = $AIRBNB_ID"
Write-Host "   Meme guest, meme dates, mais :"
Write-Host "     - total_amount different  : 55000 (au lieu de 50000)"
Write-Host "     - special_requests differt : 'Demande Airbnb' (devrait etre ignoree)"
Write-Host "     - guest_phone differt     : '+213000000000' (devrait etre preserve)"

$syncBody = @{
    reservations = @(
        @{
            id            = $AIRBNB_ID
            listing_id    = $LUNA_LISTING
            statut        = "Confirmée"
            voyageur      = $GUEST_NAME
            nb_voyageurs  = 2
            date_arrivee  = $CHECK_IN
            date_depart   = $CHECK_OUT
            nb_nuits      = 4
            montant_total = 55000
            devise        = "DZD"
            guest_phone   = "+213000000000"
            guest_email   = "airbnb@example.com"
            special_requests = "Demande Airbnb (devrait etre ignoree par smart update)"
        }
    )
    sync_metadata = @{
        sync_type       = "manual"
        timestamp       = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        script_version  = "test_dedup_4couches_v1"
    }
} | ConvertTo-Json -Depth 10

$syncResp = Invoke-RestMethod `
    -Uri $API_URL `
    -Headers $HEADERS_API -Method Post -Body $syncBody

Write-Host ""
Write-Host "   Reponse API :"
Write-Host "     processed : $($syncResp.metrics.processed)"
Write-Host "     created   : $($syncResp.metrics.created)"
Write-Host "     updated   : $($syncResp.metrics.updated)"
Write-Host "     linked    : $($syncResp.metrics.linked)"
Write-Host "     failed    : $($syncResp.metrics.failed)"
Write-Host "     conflicts : $($syncResp.metrics.conflicts)"

# --- 5. Verifications --------------------------------------------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ETAPE 3 : Verification des assertions" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 5a. Metriques API
Write-Host ""
Write-Host "   5a. Metriques de l'API" -ForegroundColor Yellow
Test-Assert ($syncResp.metrics.linked -eq 1) "linked = 1 (fuzzy match detecte)"
Test-Assert ($syncResp.metrics.created -eq 0) "created = 0 (pas de doublon cree)"
Test-Assert ($syncResp.metrics.updated -eq 0) "updated = 0 (pas d'update exact)"
Test-Assert ($syncResp.metrics.failed -eq 0) "failed = 0"

# 5b. Pas de doublon
Write-Host ""
Write-Host "   5b. Pas de doublon en base" -ForegroundColor Yellow
$allRows = Invoke-RestMethod `
    -Uri "$SUPA_URL/rest/v1/reservations?guest_name=eq.$([uri]::EscapeDataString($GUEST_NAME))&select=id,airbnb_confirmation_code,total_amount,status,source,matched_via" `
    -Headers $HEADERS_SUPA -Method Get
Test-Assert ($allRows.Count -eq 1) "Exactement 1 ligne en base (pas de doublon)"

# 5c. airbnb_confirmation_code renseigne
$row = $allRows[0]
Test-Assert ($row.airbnb_confirmation_code -eq $AIRBNB_ID) "airbnb_confirmation_code = $AIRBNB_ID (lie avec succes)"
Test-Assert ($row.id -eq $manualId) "ID de la ligne = ID de l'entree manuelle (meme row, pas cree)"

# 5d. matched_via = fuzzy_manual
Test-Assert ($row.matched_via -eq "fuzzy_manual") "matched_via = 'fuzzy_manual' (fuzzy match, pas exact)"

# 5e. Champs Airbnb ecrases
Test-Assert ($row.total_amount -eq 55000) "total_amount = 55000 (depuis Airbnb)"

# 5f. Champs admin PRESERVES
Write-Host ""
Write-Host "   5c. Champs admin PRESERVES (smart update)" -ForegroundColor Yellow
$fullRow = Invoke-RestMethod `
    -Uri "$SUPA_URL/rest/v1/reservations?id=eq.$manualId&select=*" `
    -Headers $HEADERS_SUPA -Method Get
$full = $fullRow[0]
Test-Assert ($full.special_requests -eq "Demande speciale ADMIN (NE PAS ecraser)") "special_requests preserve"
Test-Assert ($full.guest_phone -eq "+213555999888") "guest_phone preserve (admin)"
Test-Assert ($full.payment_status -eq "paid") "payment_status preserve"
Test-Assert ($full.guest_email -eq "admin-resa@example.com") "guest_email preserve (admin)"

# 5g. Test NOTIFICATION (la cloche doit avoir une entree 'updated' avec matched_via=fuzzy_manual)
Write-Host ""
Write-Host "   5d. Notification de linkage" -ForegroundColor Yellow
$notifs = Invoke-RestMethod `
    -Uri "$SUPA_URL/rest/v1/airbnb_notifications?reservation_id=eq.$manualId&order=created_at.desc&limit=1" `
    -Headers $HEADERS_SUPA -Method Get
if ($notifs.Count -gt 0) {
    $n = $notifs[0]
    Test-Assert ($n.metadata.matched_via -eq "fuzzy_manual") "Notification metadata.matched_via = 'fuzzy_manual'"
    # PowerShell -like n'est PAS accent-insensitive : utiliser un pattern sans accent
    Test-Assert ($n.metadata.admin_alert -like "*automatiquement*") "Notification contient admin_alert"
} else {
    Test-Assert $false "Une notification doit avoir ete creee pour le linkage"
}

# --- 6. Test inverse : vraie nouvelle resa (pas de doublon, doit creer) ------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  ETAPE 4 : Test inverse - vraie nouvelle resa (doit creer)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$newGuest = "Test Nouvelle $((Get-Date).ToString('HHmmss'))"
$newAirbnbId = "TESTNEW$((Get-Date).ToString('HHmmss'))"
$syncBody2 = @{
    reservations = @(
        @{
            id            = $newAirbnbId
            listing_id    = $LUNA_LISTING
            statut        = "Confirmée"
            voyageur      = $newGuest
            nb_voyageurs  = 1
            date_arrivee  = "2026-12-15"
            date_depart   = "2026-12-18"
            nb_nuits      = 3
            montant_total = 30000
            devise        = "DZD"
        }
    )
    sync_metadata = @{
        sync_type       = "manual"
        timestamp       = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
        script_version  = "test_dedup_v1"
    }
} | ConvertTo-Json -Depth 10

$syncResp2 = Invoke-RestMethod -Uri $API_URL -Headers $HEADERS_API -Method Post -Body $syncBody2
Write-Host "   created = $($syncResp2.metrics.created), linked = $($syncResp2.metrics.linked)"
Test-Assert ($syncResp2.metrics.created -eq 1) "Vraie nouvelle resa → created=1"
Test-Assert ($syncResp2.metrics.linked -eq 0) "Vraie nouvelle resa → linked=0"

# --- 7. Bilan final ----------------------------------------------------------
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  BILAN : $pass PASS / $fail FAIL" -ForegroundColor $(if ($fail -eq 0) { 'Green' } else { 'Red' })
Write-Host "================================================================" -ForegroundColor Cyan

if ($fail -gt 0) {
    Write-Host ""
    Write-Host "  Verifie les logs Next.js pour les details" -ForegroundColor Yellow
    Write-Host "  Logs fuzzy match cherchees : 'FUZZY MATCH: ...'" -ForegroundColor Yellow
    exit 1
}
exit 0
