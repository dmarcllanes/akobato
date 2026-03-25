-- =============================================================================
-- 03_rls.sql
-- Run third. Enables Row Level Security and sets anon-key policies.
-- The app uses the anon key, so these policies must exist or all
-- reads/writes will be silently blocked.
-- =============================================================================


ALTER TABLE players  ENABLE ROW LEVEL SECURITY;
ALTER TABLE verdicts ENABLE ROW LEVEL SECURITY;


-- players: anon can read the leaderboard and upsert/update rows
CREATE POLICY "anon can read players"
    ON players FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "anon can insert players"
    ON players FOR INSERT
    TO anon
    WITH CHECK (true);

CREATE POLICY "anon can update players"
    ON players FOR UPDATE
    TO anon
    USING (true);


-- verdicts: anon can read the Hall of Fame and insert new records
CREATE POLICY "anon can read verdicts"
    ON verdicts FOR SELECT
    TO anon
    USING (true);

CREATE POLICY "anon can insert verdicts"
    ON verdicts FOR INSERT
    TO anon
    WITH CHECK (true);
