-- ============================================================
-- Fix retroactif Yasmine Itchir (Tulipe loft)
-- Reservation scrapee avant le fix Python -> devise manquante
-- 84 855,60 DZD / 270 (taux GBP defaut) = 314,28 GBP
-- ============================================================

WITH found_reservation AS (
  SELECT r.id
  FROM reservations r
  LEFT JOIN lofts l ON l.id = r.loft_id
  WHERE l.name LIKE '%Tulipe%'
    AND r.check_in_date = '2026-08-14'
    AND r.guest_name ILIKE '%Yasmine%'
  LIMIT 1
)
UPDATE reservations
SET 
  original_amount = 314.28,
  original_currency_code = 'GBP',
  currency_ratio = 270
WHERE id IN (SELECT id FROM found_reservation)
RETURNING id, guest_name, check_in_date, total_amount, original_amount, original_currency_code, currency_ratio;
