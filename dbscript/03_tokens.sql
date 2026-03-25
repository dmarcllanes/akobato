-- =============================================================================
-- 03_tokens.sql
-- Run third. Adds token/energy system to players.
-- Dashboard → SQL Editor → New Query → paste → Run
-- =============================================================================

-- Add tokens column (safe to run multiple times)
ALTER TABLE players ADD COLUMN IF NOT EXISTS tokens INTEGER DEFAULT 5;

-- Give all existing players 5 tokens
UPDATE players SET tokens = 5 WHERE tokens IS NULL;

-- Function: restore 1 token after a match (capped at 5)
CREATE OR REPLACE FUNCTION restore_player_token(p_username TEXT)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE players
    SET tokens = LEAST(tokens + 1, 5)
    WHERE username = p_username;
END;
$$;

-- Function: deduct 1 token before joining a match (floor at 0)
CREATE OR REPLACE FUNCTION deduct_player_token(p_username TEXT)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE players
    SET tokens = GREATEST(tokens - 1, 0)
    WHERE username = p_username;
END;
$$;
