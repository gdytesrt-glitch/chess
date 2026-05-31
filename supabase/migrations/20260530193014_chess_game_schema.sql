/*
  # Chess Game Schema

  1. New Tables
    - `chess_games`
      - `id` (uuid, primary key)
      - `user_id` (uuid, references auth.users)
      - `board_state` (jsonb) - current board grid and turn
      - `move_history` (jsonb array) - list of all moves
      - `game_status` (text) - 'active', 'checkmate', 'stalemate', 'resigned'
      - `difficulty` (integer) - AI search depth (1-5)
      - `player_color` (text) - 'white' or 'black'
      - `ai_cognitive_data` (jsonb) - cognitive thinking data
      - `result` (text) - 'win', 'loss', 'draw', null
      - `created_at` (timestamp)
      - `updated_at` (timestamp)

  2. Security
    - Enable RLS on `chess_games` table
    - Users can only access their own games
*/

CREATE TABLE IF NOT EXISTS chess_games (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  board_state jsonb NOT NULL DEFAULT '{}'::jsonb,
  move_history jsonb DEFAULT '[]'::jsonb,
  game_status text NOT NULL DEFAULT 'active',
  difficulty integer NOT NULL DEFAULT 3,
  player_color text NOT NULL DEFAULT 'white',
  ai_cognitive_data jsonb DEFAULT '{}'::jsonb,
  result text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE chess_games ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own games"
  ON chess_games FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own games"
  ON chess_games FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own games"
  ON chess_games FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own games"
  ON chess_games FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

CREATE INDEX IF NOT EXISTS idx_chess_games_user_id ON chess_games(user_id);
CREATE INDEX IF NOT EXISTS idx_chess_games_status ON chess_games(game_status);