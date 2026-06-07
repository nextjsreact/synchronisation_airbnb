-- =====================================================================
-- FIX 2 RÉSAS EXISTANTES : Sabrina Ouacel (Éden loft) + Ghada Touahria (Chanel loft)
-- Taux utilisé : 270 DZD/GBP (défaut code, cf. currency_converter.py:109)
-- Hypothèse : conversion a bien été appliquée (montant_total en DZD)
-- =====================================================================

-- ── 1) AVANT : vérif rapide ──────────────────────────────────────
SELECT id, guest_name, total_amount, currency_code, currency_ratio,
       original_currency_code, original_amount
FROM reservations
WHERE id IN (
  '94b811e0-217e-40d3-9180-5e39ed30220e',  -- Sabrina
  'b9b49453-d400-4bdf-ae58-7fecb94d3d1a'   -- Ghada
);

-- ── 2) UPDATE Sabrina Ouacel (Éden loft, 3 nuits) ────────────────
-- 23 957.10 DZD ÷ 270 = 88.73 GBP
UPDATE reservations
SET original_currency_code = 'GBP',
    original_amount        = 88.73,
    currency_ratio         = 270.0
WHERE id = '94b811e0-217e-40d3-9180-5e39ed30220e'
  AND original_currency_code IS NULL;

-- ── 3) UPDATE Ghada Touahria (Chanel loft, 14 nuits) ─────────────
-- 188 451.90 DZD ÷ 270 = 697.97 GBP
UPDATE reservations
SET original_currency_code = 'GBP',
    original_amount        = 697.97,
    currency_ratio         = 270.0
WHERE id = 'b9b49453-d400-4bdf-ae58-7fecb94d3d1a'
  AND original_currency_code IS NULL;

-- ── 4) APRÈS : vérif ─────────────────────────────────────────────
SELECT id, guest_name, total_amount, currency_code, currency_ratio,
       original_currency_code, original_amount
FROM reservations
WHERE id IN (
  '94b811e0-217e-40d3-9180-5e39ed30220e',
  'b9b49453-d400-4bdf-ae58-7fecb94d3d1a'
);

-- ── 5) Recap prix/nuit ───────────────────────────────────────────
SELECT guest_name, loft_id,
       total_amount AS da_total,
       original_amount AS gbp_total,
       ROUND(original_amount / nights, 2) AS gbp_per_night,
       nights,
       check_in_date, check_out_date
FROM reservations
WHERE id IN (
  '94b811e0-217e-40d3-9180-5e39ed30220e',
  'b9b49453-d400-4bdf-ae58-7fecb94d3d1a'
);
