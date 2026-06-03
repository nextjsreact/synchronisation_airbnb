-- =====================================================
-- Script: Mapping Airbnb listing IDs + création lofts archivés
-- Description: Met à jour les 4 lofts existants et crée 5 lofts
--              historiques (archivés) pour que le sync puisse mapper
--              les 11,717 lignes bloquées dans airbnb_reservations_staging
-- Date: 2026-05-24
-- =====================================================

-- =====================================================
-- ÉTAPE 0 : Nettoyage (si le script a déjà été exécuté partiellement)
-- =====================================================
-- Supprimer les lofts archivés qui auraient été insérés avant l'échec du CHECK
DELETE FROM lofts WHERE name IN ('Golf view', 'Rosina Loft', 'Rosa loft', 'Oasis loft (ancien)', 'Rayan loft')
  AND status::text = 'archived';

-- =====================================================
-- ÉTAPE 1 : Ajouter 'archived' au statut des lofts
-- =====================================================
-- 1a. Ajouter la valeur à l'enum
ALTER TYPE loft_status ADD VALUE IF NOT EXISTS 'archived';

-- 1b. Modifier la contrainte CHECK (qui bloque même si l'enum est OK)
-- On cherche dynamiquement le nom de la contrainte
DO $$
DECLARE
  cname TEXT;
BEGIN
  SELECT con.conname INTO cname
  FROM pg_constraint con
  JOIN pg_class rel ON rel.oid = con.conrelid
  WHERE rel.relname = 'lofts'
    AND con.contype = 'c'
    AND pg_get_constraintdef(con.oid) LIKE '%status%'
    AND pg_get_constraintdef(con.oid) LIKE '%available%'
  LIMIT 1;

  IF cname IS NOT NULL THEN
    EXECUTE format('ALTER TABLE lofts DROP CONSTRAINT %I', cname);
    RAISE NOTICE 'Dropped constraint: %', cname;
  END IF;
END $$;

-- Recréer la contrainte avec 'archived'
ALTER TABLE lofts ADD CONSTRAINT lofts_status_check
  CHECK (status IN ('available', 'occupied', 'maintenance', 'archived'));

-- =====================================================
-- ÉTAPE 2 : Mettre à jour les 4 lofts existants
-- =====================================================
-- Ces lofts existent dans Supabase mais n'avaient pas de airbnb_listing_id

-- Blue's loft → "Golf Loft _ Blue'78" sur Airbnb
UPDATE lofts
SET airbnb_listing_id = '617505721133092844'
WHERE name ILIKE '%blue%loft%'
  AND airbnb_listing_id IS NULL;

-- Purple's loft → "El Mouradia Loft _ Purple'78" sur Airbnb
UPDATE lofts
SET airbnb_listing_id = '617532634313236890'
WHERE name ILIKE '%purple%loft%'
  AND airbnb_listing_id IS NULL;

-- Chanel loft → "Chanel Loft _ Sidi Fredj" sur Airbnb
UPDATE lofts
SET airbnb_listing_id = '1361884360591869724'
WHERE name ILIKE '%chanel%loft%'
  AND airbnb_listing_id IS NULL;

-- El bahdja loft → "El Bahdja" sur Airbnb
UPDATE lofts
SET airbnb_listing_id = '1482835556465318279'
WHERE name ILIKE '%bahdja%'
  AND airbnb_listing_id IS NULL;


-- =====================================================
-- ÉTAPE 3 : Créer les 5 lofts historiques (archivés)
-- =====================================================
-- Ces lofts ne nous appartiennent plus, on les crée uniquement
-- pour que le sync puisse mapper les réservations historiques

-- Note: price_per_night et is_published ont des valeurs par défaut,
-- description est NOT NULL → on fournit une description minimale
-- L'index unique sur airbnb_listing_id est PARTIEL (WHERE NOT NULL),
-- donc ON CONFLICT ne fonctionne pas. On utilise une sous-requête pour éviter les doublons.

INSERT INTO lofts (name, address, description, status, airbnb_listing_id, is_published)
SELECT name, address, description, status::loft_status, airbnb_listing_id, is_published
FROM (VALUES
  ('Golf view', 'À définir', 'Loft historique — ancien bien partenaire', 'archived', '1000816997221844803', false),
  ('Rosina Loft', 'À définir', 'Loft historique — ancien bien partenaire', 'archived', '1010024176351214897', false),
  ('Rosa loft', 'À définir', 'Loft historique — ancien bien partenaire', 'archived', '1010685773931128088', false),
  ('Oasis loft (ancien)', 'À définir', 'Loft historique — ancien bien partenaire', 'archived', '1081691126719400064', false),
  ('Rayan loft', 'À définir', 'Loft historique — ancien bien partenaire', 'archived', '1084830263659814195', false)
) AS new_lofts(name, address, description, status, airbnb_listing_id, is_published)
WHERE NOT EXISTS (
  SELECT 1 FROM lofts WHERE lofts.airbnb_listing_id = new_lofts.airbnb_listing_id
);


-- =====================================================
-- ÉTAPE 4 : Vérifications
-- =====================================================

-- Vérifier que les 9 lofts ont bien leur airbnb_listing_id
SELECT name, status, airbnb_listing_id
FROM lofts
WHERE airbnb_listing_id IS NOT NULL
ORDER BY status, name;

-- Vérifier qu'il ne reste plus de lignes non mappées dans le staging
-- (après re-sync, pas maintenant)
-- SELECT listing_id, COUNT(*)
-- FROM airbnb_reservations_staging
-- WHERE mapping_status = 'failed'
-- GROUP BY listing_id;

-- =====================================================
-- ÉTAPE 5 (OPTIONNEL) : Re-lancer le sync pour mapper les lignes bloquées
-- =====================================================
-- Une fois ce script exécuté, relancer le push_existing_data.py
-- ou le sync Airbnb pour que les 11,717 lignes soient mappées.
-- Le upsert sur airbnb_id empêche les doublons.
