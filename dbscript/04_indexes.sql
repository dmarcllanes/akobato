-- =============================================================================
-- 04_indexes.sql
-- Run fourth. Adds indexes for leaderboard and verdict queries.
-- Safe to re-run (IF NOT EXISTS).
-- =============================================================================


-- Leaderboard sorts by score descending
CREATE INDEX IF NOT EXISTS idx_players_score
    ON players (score DESC);

-- Hall of Fame sorts by newest first
CREATE INDEX IF NOT EXISTS idx_verdicts_created
    ON verdicts (created_at DESC);

-- Verdict lookups by match ID
CREATE INDEX IF NOT EXISTS idx_verdicts_match
    ON verdicts (match_id);
