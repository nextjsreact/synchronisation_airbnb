-- =====================================================
-- Schema Airbnb Scraper v2 — Tables manquantes
-- =====================================================
-- Exécuter dans Supabase SQL Editor
-- =====================================================

-- ── Table des hashes iCal (pour le watcher) ─────────────
CREATE TABLE IF NOT EXISTS public.ical_hashes (
    listing_id  TEXT PRIMARY KEY,
    hash        TEXT NOT NULL,
    checked_at  TIMESTAMPTZ DEFAULT now(),
    changed_at  TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE public.ical_hashes IS 'Hash SHA256 des calendriers iCal pour détecter les changements';

-- ── Table de la file d''attente de synchronisation ──────
CREATE TABLE IF NOT EXISTS public.sync_queue (
    id             BIGSERIAL PRIMARY KEY,
    listing_id     TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'pending',
    reason         TEXT,
    error_message  TEXT,
    created_at     TIMESTAMPTZ DEFAULT now(),
    processed_at   TIMESTAMPTZ
);

COMMENT ON TABLE public.sync_queue IS 'File d''attente pour le scraping ciblé (targeted_scraper)';

-- Index pour la lecture rapide des entrées pending
CREATE INDEX IF NOT EXISTS idx_sync_queue_pending
    ON public.sync_queue (status, created_at)
    WHERE status = 'pending';

-- ── RLS (Row Level Security) ────────────────────────────
-- Le service role bypass RLS, mais on l'active par sécurité
ALTER TABLE public.ical_hashes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sync_queue ENABLE ROW LEVEL SECURITY;

-- Politique : le service role peut tout faire
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE policyname = 'service_all' AND tablename = 'ical_hashes'
    ) THEN
        CREATE POLICY "service_all" ON public.ical_hashes
            FOR ALL USING (true) WITH CHECK (true);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE policyname = 'service_all' AND tablename = 'sync_queue'
    ) THEN
        CREATE POLICY "service_all" ON public.sync_queue
            FOR ALL USING (true) WITH CHECK (true);
    END IF;
END $$;
