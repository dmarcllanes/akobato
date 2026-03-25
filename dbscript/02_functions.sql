-- =============================================================================
-- 02_functions.sql
-- Run second. Creates RPC functions called by the app.
-- =============================================================================


-- Atomically increments a player's stats after each match.
-- Using a function instead of a raw UPDATE avoids race conditions
-- when two matches finish at the same time.
CREATE OR REPLACE FUNCTION increment_player_stats(
    p_username  TEXT,
    p_wins      INTEGER,
    p_losses    INTEGER,
    p_ties      INTEGER,
    p_score     INTEGER
)
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE players
    SET
        wins   = wins   + p_wins,
        losses = losses + p_losses,
        ties   = ties   + p_ties,
        score  = score  + p_score
    WHERE username = p_username;
END;
$$;
