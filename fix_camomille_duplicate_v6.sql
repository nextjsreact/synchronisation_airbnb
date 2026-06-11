-- =====================================================================
-- FIX DOUBLON Camomille loft (v6 - ID direct, plus de lookup par nom)
-- =====================================================================
-- La manuelle a l'UUID : ec39cb7c-13c8-4bd5-ae68-52e9e0294c5f
-- La scrapée (à garder) : 58aa8b0a-48d5-426e-be98-86b0deb3d8b4

-- ── 1) VÉRIF AVANT : voir la manuelle à supprimer ──────────────────
SELECT
  r.id, r.guest_name, r.guest_phone, r.guest_email,
  r.check_in_date, r.check_out_date, r.status,
  r.total_amount, r.airbnb_confirmation_code, r.source, r.created_at,
  (SELECT COUNT(*) FROM reservation_payments p WHERE p.reservation_id = r.id) AS fk_payments,
  (SELECT COUNT(*) FROM airbnb_notifications n WHERE n.reservation_id = r.id) AS fk_notifs,
  (SELECT COUNT(*) FROM airbnb_conflicts c WHERE c.reservation_1_id = r.id OR c.reservation_2_id = r.id) AS fk_conflicts,
  (SELECT COUNT(*) FROM airbnb_reservations_staging s WHERE s.reservation_id = r.id) AS fk_staging
FROM reservations r
WHERE r.id = 'ec39cb7c-13c8-4bd5-ae68-52e9e0294c5f';

-- ── 2) DELETE avec gestion FK ──────────────────────────────────────
DO $$
DECLARE
  v_manual_id UUID := 'ec39cb7c-13c8-4bd5-ae68-52e9e0294c5f';
  v_count INT;
BEGIN
  RAISE NOTICE '🔍 Suppression résa manuelle : %', v_manual_id;

  -- 1) reservation_payments
  DELETE FROM reservation_payments WHERE reservation_id = v_manual_id;
  GET DIAGNOSTICS v_count = ROW_COUNT;
  IF v_count > 0 THEN RAISE NOTICE '   ✓ % payments supprimés', v_count; END IF;

  -- 2) airbnb_notifications
  DELETE FROM airbnb_notifications WHERE reservation_id = v_manual_id;
  GET DIAGNOSTICS v_count = ROW_COUNT;
  IF v_count > 0 THEN RAISE NOTICE '   ✓ % notifications supprimées', v_count; END IF;

  -- 3) airbnb_conflicts (NOT NULL sur les 2 colonnes)
  DELETE FROM airbnb_conflicts WHERE reservation_1_id = v_manual_id;
  GET DIAGNOSTICS v_count = ROW_COUNT;
  IF v_count > 0 THEN RAISE NOTICE '   ✓ % conflits (side 1) supprimés', v_count; END IF;

  DELETE FROM airbnb_conflicts WHERE reservation_2_id = v_manual_id;
  GET DIAGNOSTICS v_count = ROW_COUNT;
  IF v_count > 0 THEN RAISE NOTICE '   ✓ % conflits (side 2) supprimés', v_count; END IF;

  -- 4) airbnb_reservations_staging
  DELETE FROM airbnb_reservations_staging WHERE reservation_id = v_manual_id;
  GET DIAGNOSTICS v_count = ROW_COUNT;
  IF v_count > 0 THEN RAISE NOTICE '   ✓ % staging records supprimés', v_count; END IF;

  -- 5) DELETE la résa
  DELETE FROM reservations WHERE id = v_manual_id;
  RAISE NOTICE '✅ Résa manuelle supprimée';
EXCEPTION
  WHEN foreign_key_violation THEN
    RAISE NOTICE '❌ ERREUR FK : % (SQLSTATE: %)', SQLERRM, SQLSTATE;
  WHEN OTHERS THEN
    RAISE NOTICE '❌ ERREUR : % (SQLSTATE: %)', SQLERRM, SQLSTATE;
END $$;

-- ── 3) VÉRIF FINALE : il ne doit rester QUE Mohamed Karim Redjem ───
SELECT
  r.id, r.guest_name, r.check_in_date, r.check_out_date,
  r.status, r.total_amount, r.airbnb_confirmation_code, r.source
FROM reservations r
WHERE r.loft_id = 'aa064685-6852-450e-8a04-39c638e44fd7'  -- Camomille loft UUID
  AND r.check_in_date = '2026-06-06'
  AND r.check_out_date = '2026-06-07'
ORDER BY r.created_at;
-- Attendu : 1 seule ligne (Mohamed Karim Redjem, source=airbnb_scraper)

-- ── 4) Vérifier que Sabrina + Ghada ont toujours besoin du fix GBP ──
SELECT id, guest_name, total_amount, currency_code, original_currency_code, original_amount
FROM reservations
WHERE id IN (
  '94b811e0-217e-40d3-9180-5e39ed30220e',  -- Sabrina
  'b9b49453-d400-4bdf-ae58-7fecb94d3d1a'   -- Ghada
);
