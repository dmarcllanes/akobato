-- =============================================================================
-- 06_alias.sql
-- Adds alias column to players for anonymous identity in leaderboard.
-- Run in: Dashboard → SQL Editor → New Query → paste → Run
-- =============================================================================

ALTER TABLE players ADD COLUMN IF NOT EXISTS alias TEXT;
