-- =====================================================================
-- DIAGNOSTIC APPROFONDI : pourquoi 0 rows pour Camomille ?
-- =====================================================================

-- 1) Liste TOUS les lofts avec "Camomille" dans le nom (peut-être y'a un trailing space)
SELECT id, name, LENGTH(name) AS name_length
FROM lofts
WHERE name ILIKE '%camomille%';

-- 2) Toutes les résas des 7 derniers jours (toutes sources)
SELECT
  r.id,
  r.guest_name,
  r.loft_id,
  l.name AS loft_name,
  LENGTH(l.name) AS loft_name_length,
  r.check_in_date,
  r.check_out_date,
  r.status,
  r.total_amount,
  r.airbnb_confirmation_code,
  r.source,
  r.created_at
FROM reservations r
LEFT JOIN lofts l ON l.id = r.loft_id
WHERE r.created_at > NOW() - INTERVAL '7 days'
ORDER BY r.created_at DESC
LIMIT 50;

-- 3) Cherche spécifiquement "Mohamed Karim Redjem" partout
SELECT
  r.id,
  r.guest_name,
  l.name AS loft_name,
  r.check_in_date,
  r.check_out_date,
  r.status,
  r.total_amount,
  r.airbnb_confirmation_code,
  r.source,
  r.created_at
FROM reservations r
LEFT JOIN lofts l ON l.id = r.loft_id
WHERE r.guest_name ILIKE '%mohamed%'
   OR r.guest_name ILIKE '%karim%'
   OR r.guest_name ILIKE '%redjem%';

-- 4) Cherche les résas avec un guest_name qui ressemble à un téléphone (+346...)
SELECT
  r.id,
  r.guest_name,
  l.name AS loft_name,
  r.check_in_date,
  r.check_out_date,
  r.status,
  r.airbnb_confirmation_code,
  r.created_at
FROM reservations r
LEFT JOIN lofts l ON l.id = r.loft_id
WHERE r.guest_name ~ '^[+\d\s\-\(\)]+$'  -- nom = que des chiffres/+/-/espaces
ORDER BY r.created_at DESC
LIMIT 20;
