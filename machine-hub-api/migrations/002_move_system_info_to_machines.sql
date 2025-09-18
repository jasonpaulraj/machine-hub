-- Migration: Move system info columns from system_snapshots to machines
-- Description: Add os_name, os_version columns to machines

-- Add system info columns to machines table (before created_at)
-- Note: hostname already exists, only add os_name and os_version
ALTER TABLE machines ADD COLUMN os_name VARCHAR(100) NULL AFTER last_seen;
ALTER TABLE machines ADD COLUMN os_version VARCHAR(100) NULL AFTER os_name;

-- Migrate data from system_snapshots to machines
UPDATE machines AS m
INNER JOIN (
    SELECT
        machine_id,
        os_name,
        os_version,
        hostname,
        ROW_NUMBER() OVER (
            PARTITION BY machine_id ORDER BY created_at DESC
        ) AS rn
    FROM system_snapshots
    WHERE
        os_name IS NOT NULL
        OR os_version IS NOT NULL
        OR hostname IS NOT NULL
) AS latest ON m.id = latest.machine_id AND latest.rn = 1
SET
    m.os_name = COALESCE(m.os_name, latest.os_name),
    m.os_version = COALESCE(m.os_version, latest.os_version),
    m.hostname = COALESCE(m.hostname, latest.hostname);

-- Remove system info columns from system_snapshots table
ALTER TABLE system_snapshots DROP COLUMN os_name;
ALTER TABLE system_snapshots DROP COLUMN os_version;
ALTER TABLE system_snapshots DROP COLUMN hostname;
