from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from chess_board import Board, Move, generate_legal_moves, evaluate_board, is_in_check

INFINITY     = float("inf")
NEG_INFINITY = float("-inf")
TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2

PIECE_VALUES = {"p": 1, "n": 3, "b": 3, "r": 5, "q": 9, "k": 0}


def board_hash(board: Board) -> str:
    return "".join("".join(row) for row in board.grid) + ("W" if board.white_to_move else "B")


class TTEntry:
    __slots__ = ["score", "depth", "flag", "best_move", "pv"]
    def __init__(self, score, depth, flag, best_move, pv):
        self.score     = score
        self.depth     = depth
        self.flag      = flag
        self.best_move = best_move
        self.pv        = pv   # principal variation list[str]


class SubconsciousCalculator:
    """
    Subconscious Brain:
      - Negamax Alpha-Beta with Transposition Table
      - Quiescence Search (no horizon effect)
      - MVV-LVA + Killer-move ordering
      - Iterative Deepening
      - Principal Variation tracking
    """

    def __init__(self, max_depth: int = 5):
        self.max_depth = max_depth
        self.tt: Dict[str, TTEntry] = {}
        self.nodes_evaluated  = 0
        self.tt_hits          = 0
        self.killers: List[List] = [[None, None] for _ in range(64)]

    def clear_caches(self):
        self.tt.clear()
        self.nodes_evaluated = 0
        self.tt_hits = 0
        self.killers = [[None, None] for _ in range(64)]

    # ── move ordering ────────────────────────────────────────────────────────

    def _mvv_lva(self, board: Board, move: Move, ply: int) -> int:
        tgt = board.grid[move.to_row][move.to_col]
        src = board.grid[move.from_row][move.from_col]
        if tgt != ".":
            return 1000 + PIECE_VALUES.get(tgt.lower(), 0) * 10 - PIECE_VALUES.get(src.lower(), 0)
        if ply < len(self.killers):
            if move == self.killers[ply][0]: return 900
            if move == self.killers[ply][1]: return 800
        return 0

    def _order(self, board: Board, moves: List[Move], ply: int, tt_best) -> List[Move]:
        def key(m):
            if tt_best and m == tt_best: return 10000
            return self._mvv_lva(board, m, ply)
        return sorted(moves, key=key, reverse=True)

    # ── quiescence ───────────────────────────────────────────────────────────

    def _qsearch(self, board: Board, alpha: float, beta: float, color: str) -> float:
        sp = evaluate_board(board, color)
        if sp >= beta: return beta
        if sp > alpha: alpha = sp
        opp  = "black" if color == "white" else "white"
        caps = [m for m in generate_legal_moves(board, color)
                if board.grid[m.to_row][m.to_col] != "."]
        for mv in self._order(board, caps, 0, None):
            score = -self._qsearch(board.apply_move(mv), -beta, -alpha, opp)
            if score >= beta: return beta
            if score > alpha: alpha = score
        return alpha

    # ── negamax ──────────────────────────────────────────────────────────────

    def _negamax(self, board: Board, depth: int, alpha: float, beta: float,
                 color: str, ply: int, pv: List[str]) -> float:
        self.nodes_evaluated += 1
        a0 = alpha
        h  = board_hash(board)

        # TT lookup
        te = self.tt.get(h)
        tt_best = None
        if te and te.depth >= depth:
            self.tt_hits += 1
            if te.flag == TT_EXACT:
                pv[:] = te.pv
                return te.score
            elif te.flag == TT_LOWER: alpha = max(alpha, te.score)
            elif te.flag == TT_UPPER: beta  = min(beta,  te.score)
            if alpha >= beta:
                pv[:] = te.pv
                return te.score
            tt_best = te.best_move

        if depth == 0:
            return self._qsearch(board, alpha, beta, color)

        opp   = "black" if color == "white" else "white"
        moves = generate_legal_moves(board, color)
        if not moves:
            return (-50000 + ply) if is_in_check(board, color) else 0

        moves = self._order(board, moves, ply, tt_best)
        best_score = NEG_INFINITY
        best_move  = None
        child_pv: List[str] = []

        for mv in moves:
            cpv: List[str] = []
            score = -self._negamax(board.apply_move(mv), depth-1, -beta, -alpha, opp, ply+1, cpv)
            if score > best_score:
                best_score = score
                best_move  = mv
                child_pv   = cpv
            if score > alpha:
                alpha = score
            if alpha >= beta:
                # killer
                if board.grid[mv.to_row][mv.to_col] == "." and ply < len(self.killers):
                    self.killers[ply][1] = self.killers[ply][0]
                    self.killers[ply][0] = mv
                break

        # build PV for this node
        new_pv = ([str(best_move)] + child_pv) if best_move else []
        pv[:] = new_pv

        # TT store
        flag = TT_EXACT
        if best_score <= a0:    flag = TT_UPPER
        elif best_score >= beta: flag = TT_LOWER
        if h not in self.tt or self.tt[h].depth <= depth:
            self.tt[h] = TTEntry(best_score, depth, flag, best_move, new_pv)

        return best_score

    # ── public API ───────────────────────────────────────────────────────────

    def search(self, board: Board) -> Tuple[Optional[Move], float, Dict]:
        """Iterative deepening search. Returns (best_move, score, diagnostics)."""
        color = "white" if board.white_to_move else "black"
        self.nodes_evaluated = 0
        self.tt_hits = 0

        best_move  = None
        best_score = NEG_INFINITY
        best_pv: List[str] = []
        depth_reached = 0

        for depth in range(1, self.max_depth + 1):
            moves = generate_legal_moves(board, color)
            if not moves: break
            ordered = self._order(board, moves, 0, best_move)
            cb, cs, cpv = None, NEG_INFINITY, []
            alpha, beta = NEG_INFINITY, INFINITY
            opp = "black" if color == "white" else "white"

            for mv in ordered:
                mpv: List[str] = []
                score = -self._negamax(board.apply_move(mv), depth-1, -beta, -alpha, opp, 1, mpv)
                if score > cs:
                    cs, cb = score, mv
                    cpv = [str(mv)] + mpv
                alpha = max(alpha, score)

            if cb:
                best_move, best_score, best_pv = cb, cs, cpv
                depth_reached = depth

        return best_move, best_score, {
            "depth_reached":    depth_reached,
            "nodes_evaluated":  self.nodes_evaluated,
            "tt_hits":          self.tt_hits,
            "tt_size":          len(self.tt),
            "best_score":       best_score,
            "principal_variation": best_pv,
        }

    def score_candidates(self, board: Board, candidates: List[Move], depth: int = 3) -> Dict[str, float]:
        """Score a shortlist of candidate moves quickly."""
        color = "white" if board.white_to_move else "black"
        opp   = "black" if color == "white" else "white"
        out: Dict[str, float] = {}
        for mv in candidates:
            pv: List[str] = []
            score = -self._negamax(board.apply_move(mv), depth-1, NEG_INFINITY, INFINITY, opp, 1, pv)
            out[str(mv)] = score
        return out
