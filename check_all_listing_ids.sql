-- Vérifier tous les airbnb_listing_id suspects
SELECT id, name, airbnb_listing_id,
  CASE
    WHEN airbnb_listing_id IS NULL THEN 'NULL'
    WHEN airbnb_listing_id = '' THEN 'VIDE'
    WHEN airbnb_listing_id = '0' THEN 'ZERO'
    WHEN airbnb_listing_id = '12345678' THEN 'PLACEHOLDER'
    WHEN LENGTH(airbnb_listing_id) < 10 THEN 'TROP COURT'
    WHEN airbnb_listing_id !~ '^\d+$' THEN 'NON NUMERIQUE'
    ELSE 'OK'
  END AS statut
FROM lofts
WHERE airbnb_listing_id IS NULL
   OR airbnb_listing_id = ''
   OR airbnb_listing_id = '0'
   OR airbnb_listing_id = '12345678'
   OR LENGTH(airbnb_listing_id) < 10
   OR airbnb_listing_id !~ '^\d+$'
ORDER BY name;

-- Tous les lofts avec leur statut complet
SELECT id, name, airbnb_listing_id,
  CASE
    WHEN airbnb_listing_id IS NULL THEN '❌ NULL'
    WHEN airbnb_listing_id = '' THEN '❌ VIDE'
    WHEN airbnb_listing_id = '0' THEN '❌ ZERO'
    WHEN airbnb_listing_id = '12345678' THEN '❌ PLACEHOLDER'
    WHEN LENGTH(airbnb_listing_id) < 10 THEN '❌ TROP COURT'
    WHEN airbnb_listing_id !~ '^\d+$' THEN '❌ NON NUMERIQUE'
    ELSE '✅'
  END AS statut
FROM lofts
ORDER BY statut, name;
