-- Migration: Remove redundant disk and network columns
-- These fields are now available through fs_data and network_data JSON columns

ALTER TABLE control.system_snapshots
DROP COLUMN disk_percent,
DROP COLUMN disk_used,
DROP COLUMN disk_total,
DROP COLUMN network_sent,
DROP COLUMN network_recv,
DROP COLUMN disk_read_bytes,
DROP COLUMN disk_write_bytes,
DROP COLUMN disk_read_count,
DROP COLUMN disk_write_count;
