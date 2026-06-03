"""
Optimized Subconscious Calculator with Zobrist Hashing
======================================================
Improvements:
- 64-bit Zobrist hash instead of string (O(1) vs O(n))
- Delta pruning in quiescence search
- Enhanced move ordering
- Configurable depth limits
- Better transposition table management
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from chess_board_v2 import Board, Move, generate_legal_moves, evaluate_board, is_in_check
from zobrist_hash import compute_zobrist_hash

INFINITY = float("inf")
NEG_INFINITY = float("-inf")
TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

PIECE_VALUES = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}
MAX_DEPTH_LIMIT = 7  # Prevent search explosion


def material_count(board: Board, color: str) -> float:
    """Count material for a color (for delta pruning)."""
    material = 0.0
    for r, row in enumerate(board.grid):
        for c, piece in enumerate(row):
            if piece != "." and (piece.isupper() == (color == "white")):
                material += PIECE_VALUES.get(piece.lower(), 0)
    return material


class TTEntry:
    """Transposition table entry."""
    __slots__ = ["score", "depth", "flag", "best_move", "pv"]

    def __init__(self, score: float, depth: int, flag: int, best_move: Optional[Move], pv: List[str]):
        self.score = score
        self.depth = depth
        self.flag = flag
        self.best_move = best_move
        self.pv = pv


class SubconsciousCalculator:
    """
    Optimized search engine with Zobrist hashing.

    Features:
    - Negamax with alpha-beta pruning
    - Zobrist 64-bit transposition table
    - Quiescence search with delta pruning
    - Move ordering (TT, MVV-LVA, killers)
    - Iterative deepening
    - Principal variation tracking
    """

    def __init__(self, max_depth: int = 5):
        self.max_depth = min(max_depth, MAX_DEPTH_LIMIT)
        self.tt: Dict[int, TTEntry] = {}
        self.nodes_evaluated = 0
        self.tt_hits = 0
        self.tt_cutoffs = 0
        self.killers: List[List] = [[None, None] for _ in range(64)]
        self.history: Dict[str, int] = {}  # Move history heuristic

    def clear_caches(self):
        """Clear transposition table and stats."""
        self.tt.clear()
        self.nodes_evaluated = 0
        self.tt_hits = 0
        self.tt_cutoffs = 0
        self.killers = [[None, None] for _ in range(64)]
        self.history.clear()

    def _mvv_lva(self, board: Board, move: Move, ply: int) -> int:
        """Most Valuable Victim - Least Valuable Attacker move ordering."""
        tgt = board.grid[move.to_row][move.to_col]
        src = board.grid[move.from_row][move.from_col]

        # Captures: prioritize by victim value
        if tgt != ".":
            victim_val = PIECE_VALUES.get(tgt.lower(), 0) * 10
            attacker_val = PIECE_VALUES.get(src.lower(), 0)
            return 1000 + victim_val - attacker_val

        # Killer moves: moves that caused cutoffs
        if ply < len(self.killers):
            if move == self.killers[ply][0]:
                return 900
            if move == self.killers[ply][1]:
                return 800

        # History heuristic: moves that led to good positions
        move_str = str(move)
        return self.history.get(move_str, 0)

    def _order_moves(self, board: Board, moves: List[Move], ply: int, tt_best: Optional[Move]) -> List[Move]:
        """Order moves for better alpha-beta pruning."""
        def key(m):
            if tt_best and m == tt_best:
                return 10000
            return self._mvv_lva(board, m, ply)

        return sorted(moves, key=key, reverse=True)

    def _qsearch(self, board: Board, alpha: float, beta: float, color: str, ply: int) -> float:
        """Quiescence search: only evaluate capture sequences.

        Delta pruning: if stand pat + max material gain < alpha, prune.
        """
        sp = evaluate_board(board, color)

        # Stand pat: can we prune by not capturing?
        if sp >= beta:
            return beta
        if sp > alpha:
            alpha = sp

        # Delta pruning: if position + max piece can't reach alpha, prune
        max_material_gain = material_count(board, "black" if color == "white" else "white")
        if sp + max_material_gain + 100 < alpha:  # 100 = safety margin
            return alpha

        opp = "black" if color == "white" else "white"
        moves = generate_legal_moves(board, color)
        captures = [m for m in moves if board.grid[m.to_row][m.to_col] != "."]

        if not captures:
            return sp

        captures = self._order_moves(board, captures, ply, None)

        for mv in captures:
            score = -self._qsearch(board.apply_move(mv), -beta, -alpha, opp, ply + 1)
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def _negamax(self, board: Board, depth: int, alpha: float, beta: float,
                 color: str, ply: int, pv: List[str]) -> float:
        """Negamax with alpha-beta pruning."""
        self.nodes_evaluated += 1
        a0 = alpha

        # Zobrist hash lookup
        h = compute_zobrist_hash(board)

        # Transposition table lookup
        te = self.tt.get(h)
        tt_best = None
        if te and te.depth >= depth:
            self.tt_hits += 1
            if te.flag == TT_EXACT:
                pv[:] = te.pv
                return te.score
            elif te.flag == TT_LOWER:
                alpha = max(alpha, te.score)
            elif te.flag == TT_UPPER:
                beta = min(beta, te.score)
            if alpha >= beta:
                self.tt_cutoffs += 1
                pv[:] = te.pv
                return te.score
            tt_best = te.best_move

        # Reached depth 0: quiescence search
        if depth == 0:
            return self._qsearch(board, alpha, beta, color, ply)

        opp = "black" if color == "white" else "white"
        moves = generate_legal_moves(board, color)

        # Terminal node: checkmate or stalemate
        if not moves:
            if is_in_check(board, color):
                return -50000 + ply  # Checkmate (penalize delay)
            else:
                return 0  # Stalemate

        # Order moves for better pruning
        moves = self._order_moves(board, moves, ply, tt_best)
        best_score = NEG_INFINITY
        best_move = None
        child_pv: List[str] = []

        for mv in moves:
            cpv: List[str] = []
            score = -self._negamax(board.apply_move(mv), depth - 1, -beta, -alpha, opp, ply + 1, cpv)

            if score > best_score:
                best_score = score
                best_move = mv
                child_pv = cpv

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Beta cutoff: record killer move
                if board.grid[mv.to_row][mv.to_col] == "." and ply < len(self.killers):
                    self.killers[ply][1] = self.killers[ply][0]
                    self.killers[ply][0] = mv

                # Record in history heuristic
                move_str = str(mv)
                self.history[move_str] = self.history.get(move_str, 0) + depth * depth

                break

        # Build principal variation
        new_pv = ([str(best_move)] + child_pv) if best_move else []
        pv[:] = new_pv

        # Store in transposition table
        flag = TT_EXACT
        if best_score <= a0:
            flag = TT_UPPER
        elif best_score >= beta:
            flag = TT_LOWER

        if h not in self.tt or self.tt[h].depth <= depth:
            self.tt[h] = TTEntry(best_score, depth, flag, best_move, new_pv)

        return best_score

    def search(self, board: Board) -> Tuple[Optional[Move], float, Dict]:
        """Iterative deepening search."""
        color = "white" if board.white_to_move else "black"
        self.nodes_evaluated = 0
        self.tt_hits = 0
        self.tt_cutoffs = 0

        best_move = None
        best_score = NEG_INFINITY
        best_pv: List[str] = []
        depth_reached = 0

        # Iterative deepening
        for depth in range(1, self.max_depth + 1):
            moves = generate_legal_moves(board, color)
            if not moves:
                break

            ordered = self._order_moves(board, moves, 0, best_move)
            cb, cs, cpv = None, NEG_INFINITY, []
            alpha, beta = NEG_INFINITY, INFINITY
            opp = "black" if color == "white" else "white"

            # Search root level moves
            for mv in ordered:
                mpv: List[str] = []
                score = -self._negamax(board.apply_move(mv), depth - 1, -beta, -alpha, opp, 1, mpv)

                if score > cs:
                    cs, cb = score, mv
                    cpv = [str(mv)] + mpv

                alpha = max(alpha, score)

            if cb:
                best_move, best_score, best_pv = cb, cs, cpv
                depth_reached = depth

        return best_move, best_score, {
            "depth_reached": depth_reached,
            "nodes_evaluated": self.nodes_evaluated,
            "tt_hits": self.tt_hits,
            "tt_cutoffs": self.tt_cutoffs,
            "tt_size": len(self.tt),
            "best_score": best_score,
            "principal_variation": best_pv,
        }

    def score_candidates(self, board: Board, candidates: List[Move], depth: int = 3) -> Dict[str, float]:
        """Score a shortlist of candidate moves."""
        color = "white" if board.white_to_move else "black"
        opp = "black" if color == "white" else "white"
        out: Dict[str, float] = {}

        for mv in candidates:
            pv: List[str] = []
            score = -self._negamax(board.apply_move(mv), depth - 1, NEG_INFINITY, INFINITY, opp, 1, pv)
            out[str(mv)] = score

        return out
