"""
Stockfish Trainer Module
========================
Connects to Stockfish UCI engine to generate training datasets.
Useful for supervised learning and position labeling.

Requirements:
  pip install python-chess stockfish

Usage:
  trainer = StockfishTrainer(stockfish_path="/path/to/stockfish")
  eval_score = trainer.evaluate_fen(fen_string)
  best_move = trainer.get_best_move(fen_string)
  dataset = trainer.generate_dataset_from_pgn("games.pgn")
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
import json
import pathlib
from dataclasses import dataclass, asdict


@dataclass
class PositionLabel:
    """Training label for a chess position."""
    fen: str
    best_move: str
    evaluation: float
    depth_searched: int
    nodes_evaluated: int


class StockfishTrainer:
    """UCI protocol interface to Stockfish for training."""

    def __init__(self, stockfish_path: Optional[str] = None, depth: int = 20, time_limit_ms: int = 5000):
        """
        Initialize Stockfish trainer.

        Args:
            stockfish_path: Path to stockfish executable
            depth: Search depth for analysis
            time_limit_ms: Time limit in milliseconds
        """
        self.stockfish_path = stockfish_path or self._find_stockfish()
        self.depth = depth
        self.time_limit_ms = time_limit_ms
        self.process = None
        self._connect()

    @staticmethod
    def _find_stockfish() -> str:
        """Find Stockfish executable in system PATH."""
        import shutil
        stockfish_exe = "stockfish.exe" if __import__("sys").platform == "win32" else "stockfish"
        path = shutil.which(stockfish_exe)
        if not path:
            raise FileNotFoundError(
                f"Stockfish not found. Install with: pip install stockfish "
                f"or download from https://stockfishchess.org/download/"
            )
        return path

    def _connect(self):
        """Connect to Stockfish via UCI protocol."""
        try:
            import subprocess
            self.process = subprocess.Popen(
                [self.stockfish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1
            )
            # Initialize UCI
            self._send_command("uci")
            self._read_until("uciok")
            self._send_command("isready")
            self._read_until("readyok")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Stockfish: {e}")

    def _send_command(self, cmd: str):
        """Send command to Stockfish."""
        if self.process:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()

    def _read_until(self, target: str) -> List[str]:
        """Read output until target string found."""
        lines = []
        if not self.process:
            return lines
        while True:
            line = self.process.stdout.readline().strip()
            lines.append(line)
            if target in line:
                break
        return lines

    def evaluate_fen(self, fen: str) -> float:
        """
        Evaluate a position (in centipawns).

        Args:
            fen: FEN string of position

        Returns:
            Evaluation score (positive = white winning)
        """
        if not self.process:
            return 0.0

        try:
            self._send_command(f"position fen {fen}")
            self._send_command(f"go depth {self.depth}")

            lines = self._read_until("bestmove")
            for line in lines:
                if "score cp" in line:
                    score_str = line.split("score cp")[1].split()[0]
                    return float(score_str)
                elif "score mate" in line:
                    mate_str = line.split("score mate")[1].split()[0]
                    # Convert mate in N to large score
                    return 30000 if int(mate_str) > 0 else -30000

            return 0.0
        except Exception as e:
            print(f"Error evaluating position: {e}")
            return 0.0

    def get_best_move(self, fen: str) -> Optional[str]:
        """
        Get best move for a position.

        Args:
            fen: FEN string of position

        Returns:
            Best move in UCI notation (e.g., "e2e4")
        """
        if not self.process:
            return None

        try:
            self._send_command(f"position fen {fen}")
            self._send_command(f"go movetime {self.time_limit_ms}")

            lines = self._read_until("bestmove")
            for line in lines:
                if line.startswith("bestmove"):
                    move = line.split()[1]
                    return move if move != "(none)" else None

            return None
        except Exception as e:
            print(f"Error getting best move: {e}")
            return None

    def get_top_moves(self, fen: str, num_moves: int = 5) -> List[Tuple[str, float]]:
        """
        Get top N moves with scores.

        Args:
            fen: FEN string
            num_moves: Number of top moves to return

        Returns:
            List of (move, score) tuples
        """
        if not self.process:
            return []

        try:
            self._send_command(f"position fen {fen}")
            self._send_command(f"go depth {self.depth}")

            moves_dict = {}
            lines = self._read_until("bestmove")

            for line in lines:
                if "pv" in line:
                    parts = line.split()
                    pv_idx = parts.index("pv")
                    if pv_idx + 1 < len(parts):
                        move = parts[pv_idx + 1]
                        score = 0.0
                        if "score cp" in line:
                            score = float(line.split("score cp")[1].split()[0])
                        elif "score mate" in line:
                            score = 30000
                        moves_dict[move] = score

            return sorted(moves_dict.items(), key=lambda x: abs(x[1]), reverse=True)[:num_moves]
        except Exception as e:
            print(f"Error getting top moves: {e}")
            return []

    def generate_dataset_from_pgn(self, pgn_path: str, max_positions: int = 1000) -> List[PositionLabel]:
        """
        Generate training dataset from PGN file.

        Args:
            pgn_path: Path to PGN file
            max_positions: Maximum positions to extract

        Returns:
            List of labeled positions
        """
        dataset = []

        try:
            import chess
            import chess.pgn
        except ImportError:
            print("Error: python-chess required. Install with: pip install python-chess")
            return dataset

        pgn_file = pathlib.Path(pgn_path)
        if not pgn_file.exists():
            print(f"PGN file not found: {pgn_path}")
            return dataset

        try:
            with open(pgn_file) as f:
                game_num = 0
                while True:
                    game = chess.pgn.read_game(f)
                    if not game:
                        break

                    game_num += 1
                    board = game.board()
                    move_num = 0

                    for move in game.mainline_moves():
                        move_num += 1

                        # Skip first 3 moves (opening, too much memorization)
                        if move_num < 4:
                            board.push(move)
                            continue

                        # Stop if dataset is full
                        if len(dataset) >= max_positions:
                            break

                        fen = board.fen()
                        best_move = self.get_best_move(fen)
                        eval_score = self.evaluate_fen(fen)

                        if best_move:
                            label = PositionLabel(
                                fen=fen,
                                best_move=best_move,
                                evaluation=eval_score,
                                depth_searched=self.depth,
                                nodes_evaluated=0
                            )
                            dataset.append(label)

                        board.push(move)

                    if len(dataset) >= max_positions:
                        break

                    if game_num % 10 == 0:
                        print(f"  Processed {game_num} games, extracted {len(dataset)} positions")

        except Exception as e:
            print(f"Error processing PGN: {e}")

        return dataset

    def export_dataset(self, dataset: List[PositionLabel], output_path: str, fmt: str = "json"):
        """
        Export training dataset.

        Args:
            dataset: List of position labels
            output_path: Output file path
            fmt: Format ("json" or "csv")
        """
        output_file = pathlib.Path(output_path)

        if fmt == "json":
            data = [asdict(label) for label in dataset]
            output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"Exported {len(dataset)} positions to {output_path}")

        elif fmt == "csv":
            import csv
            with open(output_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["fen", "best_move", "evaluation", "depth_searched"])
                for label in dataset:
                    writer.writerow([
                        label.fen,
                        label.best_move,
                        label.evaluation,
                        label.depth_searched
                    ])
            print(f"Exported {len(dataset)} positions to {output_path}")

    def cleanup(self):
        """Disconnect from Stockfish."""
        if self.process:
            try:
                self._send_command("quit")
                self.process.wait(timeout=2)
            except Exception:
                pass
            finally:
                self.process = None

    def __del__(self):
        """Cleanup on deletion."""
        self.cleanup()


# Example usage
if __name__ == "__main__":
    print("Stockfish Trainer Example")
    print("=" * 50)

    try:
        trainer = StockfishTrainer()

        # Evaluate initial position
        initial_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        score = trainer.evaluate_fen(initial_fen)
        print(f"Initial position evaluation: {score} cp")

        # Get best move
        best_move = trainer.get_best_move(initial_fen)
        print(f"Best move for initial position: {best_move}")

        # Get top moves
        top_moves = trainer.get_top_moves(initial_fen, num_moves=5)
        print(f"Top 5 moves:")
        for move, score in top_moves:
            print(f"  {move}: {score:+.0f} cp")

        # Generate dataset from PGN (if file exists)
        # dataset = trainer.generate_dataset_from_pgn("games.pgn", max_positions=100)
        # trainer.export_dataset(dataset, "training_data.json")

        trainer.cleanup()

    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: This requires Stockfish to be installed.")
        print("Download from: https://stockfishchess.org/download/")
