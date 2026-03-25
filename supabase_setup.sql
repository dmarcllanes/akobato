-- =============================================================================
-- AKOBATO — Supabase Setup Script
-- Run each STEP in order inside the Supabase SQL Editor
-- Dashboard → SQL Editor → New Query → paste → Run
-- =============================================================================


-- =============================================================================
-- STEP 1: Players table
-- Tracks every fighter and their cumulative stats.
-- =============================================================================

CREATE TABLE IF NOT EXISTS players (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    username    TEXT        UNIQUE NOT NULL,
    score       INTEGER     DEFAULT 0,
    wins        INTEGER     DEFAULT 0,
    losses      INTEGER     DEFAULT 0,
    ties        INTEGER     DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);


-- =============================================================================
-- STEP 2: Verdicts table
-- Every completed match + the AI Judge's ruling is stored here.
-- This is the raw material for the Hall of Fame.
-- =============================================================================

CREATE TABLE IF NOT EXISTS verdicts (
    id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    match_id      TEXT        NOT NULL,
    prompt        TEXT,
    player1       TEXT,
    player2       TEXT,
    argument1     TEXT,
    argument2     TEXT,
    winner        TEXT,                  -- "Player 1", "Player 2", or "Tie"
    reasoning     TEXT,                  -- AI Judge's sassy explanation
    winning_quote TEXT,                  -- Best line from the winner
    hp1_score     INTEGER,               -- Human originality score player 1 (1-10)
    hp2_score     INTEGER,               -- Human originality score player 2 (1-10)
    created_at    TIMESTAMPTZ DEFAULT NOW()
);


-- =============================================================================
-- STEP 3: RPC function — increment_player_stats
-- Called after every match to atomically update a player's record.
-- Using a function instead of a plain UPDATE avoids race conditions
-- when two matches finish at the same time.
-- =============================================================================

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


-- =============================================================================
-- STEP 4: Row Level Security (RLS)
-- Enable RLS on both tables, then allow the anon key (used by the app)
-- to read and write freely. Tighten this later if you add auth.
-- =============================================================================

ALTER TABLE players  ENABLE ROW LEVEL SECURITY;
ALTER TABLE verdicts ENABLE ROW LEVEL SECURITY;

-- Players: anon can read the leaderboard and upsert their own row
CREATE POLICY "anon can read players"
    ON players FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "anon can upsert players"
    ON players FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "anon can update players"
    ON players FOR UPDATE
    TO anon
    USING (true);

-- Verdicts: anon can read Hall of Fame and insert new verdicts
CREATE POLICY "anon can read verdicts"
    ON verdicts FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "anon can insert verdicts"
    ON verdicts FOR INSERT
    TO anon
    WITH CHECK (true);


-- =============================================================================
-- STEP 5: Indexes (performance)
-- Speeds up the leaderboard query and verdict lookups.
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_players_score
    ON players (score DESC);

CREATE INDEX IF NOT EXISTS idx_verdicts_created
    ON verdicts (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_verdicts_match
    ON verdicts (match_id);


-- =============================================================================
-- STEP 6: Enable Google OAuth  ← DO THIS IN THE DASHBOARD, NOT SQL
-- =============================================================================
-- 1. Supabase Dashboard → Authentication → Providers → Google → Enable
-- 2. Paste your Google OAuth Client ID and Client Secret
-- 3. Copy the "Callback URL" shown by Supabase (looks like:
--      https://<project-ref>.supabase.co/auth/v1/callback)
--    Add that URL in Google Cloud Console →
--    APIs & Services → Credentials → OAuth 2.0 Client → Authorised redirect URIs
-- 4. Also add your app's callback to Supabase:
--    Dashboard → Authentication → URL Configuration → Redirect URLs → Add:
--      http://localhost:5001/auth/callback          (local dev)
--      https://yourdomain.com/auth/callback         (production)
-- 5. Set Flow Type to "PKCE" (default — leave it as-is)
-- =============================================================================


-- =============================================================================
-- STEP 7: Verify — run this after the steps above to confirm everything exists
-- =============================================================================

SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = t.table_name
       AND table_schema = 'public') AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('players', 'verdicts')
ORDER BY table_name;
