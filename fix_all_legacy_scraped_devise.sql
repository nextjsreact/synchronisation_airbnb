-- ============================================================
-- Batch fix : Reservations scrapees legacy sans devise
-- Identifie toutes les reservations airbnb_scraper avec
-- original_amount NULL et remplit les champs devise manquants
-- en utilisant les taux de conversion Airbnb defaut :
--   GBP = 270, EUR = 250, USD = 250
-- ============================================================

-- ETAPE 1 : DIAGNOSTIC - Lister toutes les reservations concernees
SELECT 
  r.id,
  l.name AS loft_name,
  r.guest_name,
  r.check_in_date,
  r.check_out_date,
  r.total_amount,
  r.currency_code,
  r.original_amount,
  r.original_currency_code,
  r.currency_ratio,
  r.airbnb_confirmation_code,
  r.source,
  -- Heuristique : si total_amount divise proprement par 270, c'est probablement GBP
  CASE 
    WHEN r.total_amount > 0 AND r.total_amount % 270 = 0 THEN 'GBP probable'
    WHEN r.total_amount > 0 AND r.total_amount % 250 = 0 THEN 'EUR/USD probable'
    ELSE 'A verifier manuellement'
  END AS devise_inferree
FROM reservations r
LEFT JOIN lofts l ON l.id = r.loft_id
WHERE r.source = 'airbnb_scraper'
  AND r.original_amount IS NULL
  AND r.currency_code = 'DZD'
ORDER BY r.created_at DESC;


-- ETAPE 2 : FIX AUTO pour les reservations GBP (total_amount divisible par 270)
-- ATTENTION : execute ETAPE 1 d'abord pour verifier les resultats
UPDATE reservations
SET 
  original_amount = ROUND(total_amount / 270.0, 2),
  original_currency_code = 'GBP',
  currency_ratio = 270
WHERE source = 'airbnb_scraper'
  AND original_amount IS NULL
  AND currency_code = 'DZD'
  AND total_amount > 0
  AND total_amount % 270 = 0;

-- ETAPE 3 : FIX AUTO pour les reservations EUR/USD (total_amount divisible par 250)
-- Remarque : GBP et EUR/USD ont des taux differents (270 vs 250) donc pas d'ambiguïté
-- Si total_amount % 270 != 0 ET total_amount % 250 = 0, c'est EUR ou USD
UPDATE reservations
SET 
  original_amount = ROUND(total_amount / 250.0, 2),
  original_currency_code = 'EUR',
  currency_ratio = 250
WHERE source = 'airbnb_scraper'
  AND original_amount IS NULL
  AND currency_code = 'DZD'
  AND total_amount > 0
  AND total_amount % 270 != 0
  AND total_amount % 250 = 0;


-- ETAPE 4 : VERIFICATION - Compter les reservations non corrigees
SELECT COUNT(*) AS reservations_a_verifier_manuellement
FROM reservations
WHERE source = 'airbnb_scraper'
  AND original_amount IS NULL
  AND currency_code = 'DZD'
  AND total_amount > 0;
