-- Migration: Add source column to system_snapshots table
-- This migration adds a 'source' column to track whether data came from
-- API polling or webhook

ALTER TABLE system_snapshots
ADD COLUMN `source` VARCHAR(10) NOT NULL DEFAULT 'api'
AFTER machine_id;

-- Update existing records to have 'api' as default source
UPDATE system_snapshots SET `source` = 'api'
WHERE `source` IS NULL;

-- Add index for better query performance on source column
CREATE INDEX idx_system_snapshots_source ON system_snapshots (`source`);

-- Add index for combined queries on machine_id and source
CREATE INDEX idx_system_snapshots_machine_source ON system_snapshots (
    machine_id, `source`
);
