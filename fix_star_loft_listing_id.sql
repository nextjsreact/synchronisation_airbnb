-- Corriger le airbnb_listing_id de Star loft
UPDATE lofts
SET airbnb_listing_id = '1557843210540739075'
WHERE id = '5372ab62-3a1e-46f6-bed4-3dc025ebdbfd'
  AND airbnb_listing_id = '12345678'
RETURNING id, name, airbnb_listing_id;

-- Forcer un scrape immédiat
INSERT INTO sync_queue (listing_id, status, reason)
VALUES ('1557843210540739075', 'pending', 'manual_fix_listing_id');
