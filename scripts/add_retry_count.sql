-- Migration: Ajouter la colonne retry_count à sync_queue
-- Date: 2026-06-02
-- Description: Permet le système de retry automatique après échec réseau

-- Ajouter la colonne retry_count (si elle n'existe pas déjà)
ALTER TABLE sync_queue 
ADD COLUMN IF NOT EXISTS retry_count INTEGER DEFAULT 0;

-- Mettre à jour les valeurs existantes à 0
UPDATE sync_queue 
SET retry_count = 0 
WHERE retry_count IS NULL;

-- Vérifier que la colonne a été ajoutée
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'sync_queue' AND column_name = 'retry_count';
