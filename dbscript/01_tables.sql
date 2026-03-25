-- =============================================================================
-- 01_tables.sql
-- Run first. Creates the core tables.
-- Dashboard → SQL Editor → New Query → paste → Run
-- =============================================================================


-- Players: one row per fighter, cumulative stats across all matches
CREATE TABLE IF NOT EXISTS players (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    username    TEXT        UNIQUE NOT NULL,
    score       INTEGER     DEFAULT 0,
    wins        INTEGER     DEFAULT 0,
    losses      INTEGER     DEFAULT 0,
    ties        INTEGER     DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);


-- Verdicts: every completed match + the AI Judge's full ruling
CREATE TABLE IF NOT EXISTS verdicts (
    id            UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    match_id      TEXT        NOT NULL,
    prompt        TEXT,
    player1       TEXT,
    player2       TEXT,
    argument1     TEXT,
    argument2     TEXT,
    winner        TEXT,        -- "Player 1", "Player 2", or "Tie"
    reasoning     TEXT,        -- AI Judge's sassy explanation
    winning_quote TEXT,        -- Best line from the winner
    hp1_score     INTEGER,     -- Human originality score p1 (1-10)
    hp2_score     INTEGER,     -- Human originality score p2 (1-10)
    created_at    TIMESTAMPTZ DEFAULT NOW()
);
