/*
  # Create chess_moves table for move tracking
  
  1. New Tables
    - `chess_moves`
      - `id` (uuid, primary key)
      - `game_id` (uuid, foreign key to chess_games)
      - `move_number` (integer) - sequential move number
      - `move_notation` (text) - e.g., "e2e4"
      - `move_uci` (text) - standard UCI notation
      - `from_square` (text) - e.g., "e2"
      - `to_square` (text) - e.g., "e4"
      - `piece_moved` (text) - piece that moved
      - `is_capture` (boolean) - whether move was a capture
      - `is_check` (boolean) - whether move gives check
      - `evaluation` (float) - position evaluation after move
      - `played_by` (text) - 'player' or 'ai'
      - `created_at` (timestamp)
  
  2. Security
    - Enable RLS and allow public access for demo
    - Cascade delete when game is deleted
  
  3. Indexing
    - Index on game_id for quick lookup
    - Index on created_at for recent moves
*/

CREATE TABLE IF NOT EXISTS chess_moves (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  game_id uuid NOT NULL REFERENCES chess_games(id) ON DELETE CASCADE,
  move_number integer NOT NULL,
  move_notation text NOT NULL,
  move_uci text,
  from_square text,
  to_square text,
  piece_moved text,
  is_capture boolean DEFAULT false,
  is_check boolean DEFAULT false,
  evaluation float,
  played_by text NOT NULL CHECK (played_by IN ('player', 'ai')),
  created_at timestamptz DEFAULT now()
);

ALTER TABLE chess_moves ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view moves"
  ON chess_moves FOR SELECT
  USING (true);

CREATE POLICY "Anyone can insert moves"
  ON chess_moves FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Anyone can update moves"
  ON chess_moves FOR UPDATE
  USING (true)
  WITH CHECK (true);

CREATE POLICY "Anyone can delete moves"
  ON chess_moves FOR DELETE
  USING (true);

CREATE INDEX IF NOT EXISTS idx_chess_moves_game_id ON chess_moves(game_id);
CREATE INDEX IF NOT EXISTS idx_chess_moves_created_at ON chess_moves(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chess_moves_game_number ON chess_moves(game_id, move_number);