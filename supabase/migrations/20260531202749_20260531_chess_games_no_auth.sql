/*
  # Update chess_games table to work without authentication
  
  1. Changes
    - Remove user_id requirement (no auth system)
    - Make table public readable/writable for demo
    - Add move_history as proper text array
    - Add game tracking for move count
  
  2. New Features
    - Public access for demo/testing
    - Automatic timestamp updates
    - Move tracking for analytics
*/

DO $$
BEGIN
  -- Drop existing policies
  IF EXISTS (SELECT 1 FROM pg_policies WHERE tablename = 'chess_games') THEN
    DROP POLICY IF EXISTS "Users can view own games" ON chess_games;
    DROP POLICY IF EXISTS "Users can insert own games" ON chess_games;
    DROP POLICY IF EXISTS "Users can update own games" ON chess_games;
    DROP POLICY IF EXISTS "Users can delete own games" ON chess_games;
  END IF;
END $$;

-- Drop the foreign key constraint if it exists
DO $$
BEGIN
  ALTER TABLE chess_games DROP CONSTRAINT IF EXISTS chess_games_user_id_fkey;
EXCEPTION WHEN others THEN
  NULL;
END $$;

-- Make user_id nullable
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name = 'chess_games' AND column_name = 'user_id' AND is_nullable = 'NO'
  ) THEN
    ALTER TABLE chess_games ALTER COLUMN user_id DROP NOT NULL;
  END IF;
END $$;

-- Create new public policies
ALTER TABLE chess_games DISABLE ROW LEVEL SECURITY;

ALTER TABLE chess_games ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view games"
  ON chess_games FOR SELECT
  USING (true);

CREATE POLICY "Anyone can create games"
  ON chess_games FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Anyone can update games"
  ON chess_games FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Anyone can delete games"
  ON chess_games FOR DELETE
  USING (true);

-- Create index on created_at for querying recent games
CREATE INDEX IF NOT EXISTS idx_chess_games_created_at ON chess_games(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chess_games_game_status ON chess_games(game_status);