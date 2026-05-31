from __future__ import annotations
import json
import pathlib
from typing import Dict, List, Optional, Any
from chess_board import Board

MEMORY_FILE = pathlib.Path(__file__).parent / "cognitive_memory.json"


def board_hash(board: Board) -> str:
    return "".join("".join(row) for row in board.grid) + ("W" if board.white_to_move else "B")


class PositionRecord:
    """Represents what we remember about a specific board position."""

    def __init__(self):
        self.move_stats: Dict[str, Dict[str, Any]] = {}
        # move_stats[move_str] = {
        #   "games": int, "wins": int, "losses": int, "draws": int,
        #   "pv": [str...],          # best principal variation remembered
        #   "confidence": float,     # rolling average confidence at decision time
        # }

    def record_move(self, move_str: str, result: str, pv: List[str], confidence: float):
        """result: 'win' | 'loss' | 'draw'"""
        if move_str not in self.move_stats:
            self.move_stats[move_str] = {"games": 0, "wins": 0, "losses": 0, "draws": 0,
                                          "pv": pv, "confidence": confidence}
        s = self.move_stats[move_str]
        s["games"] += 1
        s[result + "s"] += 1
        # Update PV if we won
        if result == "win":
            s["pv"] = pv
        # Rolling average confidence
        s["confidence"] = (s["confidence"] * (s["games"] - 1) + confidence) / s["games"]

    def best_move_bonus(self) -> Dict[str, float]:
        """Returns a bonus score [0..1] per move based on win-rate and confidence."""
        bonuses: Dict[str, float] = {}
        for mv, s in self.move_stats.items():
            if s["games"] == 0:
                bonuses[mv] = 0.0
                continue
            win_rate   = s["wins"] / s["games"]
            confidence = s["confidence"]
            # Scale: win-rate is 70%, remembered confidence is 30%
            bonuses[mv] = win_rate * 0.70 + confidence * 0.30
        return bonuses

    def uncertainty(self) -> float:
        """Returns average uncertainty (1 - avg_confidence) across all known moves."""
        if not self.move_stats:
            return 1.0
        avg_conf = sum(s["confidence"] for s in self.move_stats.values()) / len(self.move_stats)
        return 1.0 - avg_conf

    def to_dict(self) -> Dict:
        return {"move_stats": self.move_stats}

    @classmethod
    def from_dict(cls, d: Dict) -> "PositionRecord":
        rec = cls()
        rec.move_stats = d.get("move_stats", {})
        return rec


class CognitiveMemory:
    """
    Long-Term Learning Memory.
    Persists to cognitive_memory.json between games.
    Tracks position → move stats (wins/losses/draws/PV/confidence).
    Provides adaptive depth: low confidence → deeper search requested.
    """

    def __init__(self):
        self._db: Dict[str, PositionRecord] = {}
        self._pending: List[Dict] = []   # moves played this game awaiting outcome
        self.load()

    # ── persistence ──────────────────────────────────────────────────────────

    def load(self):
        if MEMORY_FILE.exists():
            try:
                raw = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
                for h, d in raw.items():
                    self._db[h] = PositionRecord.from_dict(d)
            except Exception:
                self._db = {}

    def save(self):
        raw = {h: rec.to_dict() for h, rec in self._db.items()}
        MEMORY_FILE.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")

    # ── querying ─────────────────────────────────────────────────────────────

    def get_bonus(self, board: Board) -> Dict[str, float]:
        """Returns move bonus dict for the current position (empty if unknown)."""
        h = board_hash(board)
        if h in self._db:
            return self._db[h].best_move_bonus()
        return {}

    def get_uncertainty(self, board: Board) -> float:
        """Returns positional uncertainty [0..1].  1 = completely unknown."""
        h = board_hash(board)
        if h in self._db:
            return self._db[h].uncertainty()
        return 1.0        # unknown position → maximum uncertainty

    def recommended_depth_boost(self, board: Board, base_depth: int) -> int:
        """
        If uncertainty is high, recommend searching deeper.
        Maps uncertainty [0..1] to depth bonus [0..2].
        """
        unc = self.get_uncertainty(board)
        if unc > 0.75:   return 2
        if unc > 0.50:   return 1
        return 0

    # ── learning ─────────────────────────────────────────────────────────────

    def record_decision(self, board: Board, move_str: str, pv: List[str], confidence: float):
        """Call after every decision this game to log it in the pending list."""
        h = board_hash(board)
        self._pending.append({"hash": h, "move": move_str, "pv": pv, "confidence": confidence})

    def finalize_game(self, result: str):
        """
        result: 'win' | 'loss' | 'draw'  (from the engine's perspective)
        Commits all pending decisions into the database and saves.
        """
        for entry in self._pending:
            h = entry["hash"]
            if h not in self._db:
                self._db[h] = PositionRecord()
            self._db[h].record_move(entry["move"], result, entry["pv"], entry["confidence"])
        self._pending.clear()
        self.save()
        print(f"[CognitiveMemory] Saved {len(self._db)} positions to {MEMORY_FILE.name}")
