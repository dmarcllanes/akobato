-- =============================================================================
-- 05_verify.sql
-- Run last to confirm everything is set up correctly.
-- =============================================================================


-- 1. Check tables exist with correct column counts
SELECT
    table_name,
    (
        SELECT COUNT(*)
        FROM information_schema.columns c
        WHERE c.table_name  = t.table_name
          AND c.table_schema = 'public'
    ) AS column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name IN ('players', 'verdicts')
ORDER BY table_name;


-- 2. Check RLS is enabled on both tables
SELECT
    tablename,
    rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('players', 'verdicts');


-- 3. Check all policies exist
SELECT
    tablename,
    policyname
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('players', 'verdicts')
ORDER BY tablename, policyname;


-- 4. Check the RPC function exists
SELECT
    routine_name,
    routine_type
FROM information_schema.routines
WHERE routine_schema = 'public'
  AND routine_name = 'increment_player_stats';


-- 5. Check indexes exist
SELECT
    indexname,
    tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('players', 'verdicts')
ORDER BY tablename, indexname;
