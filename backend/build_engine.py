"""
Builder script: writes subconscious_calculator.py, cognitive_memory.py,
and the updated cognitive_engine.py to disk using pure Python file I/O
so we avoid every shell quoting hazard.
"""
import pathlib

BASE = pathlib.Path(__file__).parent

# ─────────────────────────────────────────────────────────────────────────────
# 1.  subconscious_calculator.py
# ─────────────────────────────────────────────────────────────────────────────
SUBCONSCIOUS = """\
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
    \"\"\"
    Subconscious Brain:
      - Negamax Alpha-Beta with Transposition Table
      - Quiescence Search (no horizon effect)
      - MVV-LVA + Killer-move ordering
      - Iterative Deepening
      - Principal Variation tracking
    \"\"\"

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
        \"\"\"Iterative deepening search. Returns (best_move, score, diagnostics).\"\"\"
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
        \"\"\"Score a shortlist of candidate moves quickly.\"\"\"
        color = "white" if board.white_to_move else "black"
        opp   = "black" if color == "white" else "white"
        out: Dict[str, float] = {}
        for mv in candidates:
            pv: List[str] = []
            score = -self._negamax(board.apply_move(mv), depth-1, NEG_INFINITY, INFINITY, opp, 1, pv)
            out[str(mv)] = score
        return out
"""

# ─────────────────────────────────────────────────────────────────────────────
# 2.  cognitive_memory.py
# ─────────────────────────────────────────────────────────────────────────────
MEMORY = """\
from __future__ import annotations
import json
import pathlib
from typing import Dict, List, Optional, Any
from chess_board import Board

MEMORY_FILE = pathlib.Path(__file__).parent / "cognitive_memory.json"


def board_hash(board: Board) -> str:
    return "".join("".join(row) for row in board.grid) + ("W" if board.white_to_move else "B")


class PositionRecord:
    \"\"\"Represents what we remember about a specific board position.\"\"\"

    def __init__(self):
        self.move_stats: Dict[str, Dict[str, Any]] = {}
        # move_stats[move_str] = {
        #   "games": int, "wins": int, "losses": int, "draws": int,
        #   "pv": [str...],          # best principal variation remembered
        #   "confidence": float,     # rolling average confidence at decision time
        # }

    def record_move(self, move_str: str, result: str, pv: List[str], confidence: float):
        \"\"\"result: 'win' | 'loss' | 'draw'\"\"\"
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
        \"\"\"Returns a bonus score [0..1] per move based on win-rate and confidence.\"\"\"
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
        \"\"\"Returns average uncertainty (1 - avg_confidence) across all known moves.\"\"\"
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
    \"\"\"
    Long-Term Learning Memory.
    Persists to cognitive_memory.json between games.
    Tracks position → move stats (wins/losses/draws/PV/confidence).
    Provides adaptive depth: low confidence → deeper search requested.
    \"\"\"

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
        \"\"\"Returns move bonus dict for the current position (empty if unknown).\"\"\"
        h = board_hash(board)
        if h in self._db:
            return self._db[h].best_move_bonus()
        return {}

    def get_uncertainty(self, board: Board) -> float:
        \"\"\"Returns positional uncertainty [0..1].  1 = completely unknown.\"\"\"
        h = board_hash(board)
        if h in self._db:
            return self._db[h].uncertainty()
        return 1.0        # unknown position → maximum uncertainty

    def recommended_depth_boost(self, board: Board, base_depth: int) -> int:
        \"\"\"
        If uncertainty is high, recommend searching deeper.
        Maps uncertainty [0..1] to depth bonus [0..2].
        \"\"\"
        unc = self.get_uncertainty(board)
        if unc > 0.75:   return 2
        if unc > 0.50:   return 1
        return 0

    # ── learning ─────────────────────────────────────────────────────────────

    def record_decision(self, board: Board, move_str: str, pv: List[str], confidence: float):
        \"\"\"Call after every decision this game to log it in the pending list.\"\"\"
        h = board_hash(board)
        self._pending.append({"hash": h, "move": move_str, "pv": pv, "confidence": confidence})

    def finalize_game(self, result: str):
        \"\"\"
        result: 'win' | 'loss' | 'draw'  (from the engine's perspective)
        Commits all pending decisions into the database and saves.
        \"\"\"
        for entry in self._pending:
            h = entry["hash"]
            if h not in self._db:
                self._db[h] = PositionRecord()
            self._db[h].record_move(entry["move"], result, entry["pv"], entry["confidence"])
        self._pending.clear()
        self.save()
        print(f"[CognitiveMemory] Saved {len(self._db)} positions to {MEMORY_FILE.name}")
"""

# ─────────────────────────────────────────────────────────────────────────────
# 3.  cognitive_engine.py  (updated)
# ─────────────────────────────────────────────────────────────────────────────
ENGINE = """\
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional

from chess_board import Board, Move, generate_legal_moves
from attention_system import AttentionSystem
from micro_mind import (KnowledgeGraph, TacticalMind, StrategicMind,
                         DefensiveMind, EndgameMind)
from probability_tree import ProbabilityTreeBuilder
from timeline_simulator import TimelineSimulator
from meta_observer import MetaObserver
from subconscious_calculator import SubconsciousCalculator
from cognitive_memory import CognitiveMemory


class ProbabilisticChessMind:
    \"\"\"
    Hybrid Cognitive Chess Mind
    ===========================
    Scoring formula per move:
        final = 0.75 * tactical_score   (Alpha-Beta subconscious)
              + 0.15 * strategic_score  (conscious micro-minds)
              + 0.05 * memory_score     (long-term learning)
              + 0.05 * confidence_adj   (positional certainty)

    The conscious layer ONLY ranks moves that the subconscious has already
    validated — it can never push a tactically unsound move to the top.
    \"\"\"

    TACTICAL_WEIGHT    = 0.75
    STRATEGIC_WEIGHT   = 0.15
    MEMORY_WEIGHT      = 0.05
    CONFIDENCE_WEIGHT  = 0.05

    # Number of top Alpha-Beta candidates the conscious layer may re-rank
    SHORTLIST_SIZE = 8

    def __init__(self):
        self.attention_system  = AttentionSystem()
        self.meta_observer     = MetaObserver()
        self.timeline_sim      = TimelineSimulator()
        self.tactical_mind     = TacticalMind()
        self.strategic_mind    = StrategicMind()
        self.defensive_mind    = DefensiveMind()
        self.endgame_mind      = EndgameMind()
        self.subconscious      = SubconsciousCalculator(max_depth=5)
        self.memory            = CognitiveMemory()
        self.master_graph      = KnowledgeGraph()

    # ─────────────────────────────────────────────────────────────────────────

    def think(self, board: Board) -> Optional[Tuple[Move, Dict[str, Any]]]:
        color = "white" if board.white_to_move else "black"
        legal_moves = generate_legal_moves(board, color)
        if not legal_moves:
            return None

        # ── 1. Subconscious: deep Alpha-Beta search ───────────────────────
        # Query memory to decide if we should search deeper
        depth_boost = self.memory.recommended_depth_boost(board, self.subconscious.max_depth)
        original_depth = self.subconscious.max_depth
        self.subconscious.max_depth = original_depth + depth_boost

        sc_best_move, sc_best_score, sc_diag = self.subconscious.search(board)

        self.subconscious.max_depth = original_depth   # restore

        # Build the shortlist: top SHORTLIST_SIZE moves scored by subconscious
        shortlist_scores = self.subconscious.score_candidates(
            board, legal_moves[:min(len(legal_moves), 20)], depth=3)
        shortlist = sorted(shortlist_scores.keys(),
                           key=lambda k: shortlist_scores[k], reverse=True)[:self.SHORTLIST_SIZE]
        shortlist_moves = [m for m in legal_moves if str(m) in shortlist]
        if sc_best_move and sc_best_move not in shortlist_moves:
            shortlist_moves.insert(0, sc_best_move)

        # ── 2. Attention System ───────────────────────────────────────────
        attention = self.attention_system.calculate_attention(board, color)

        # ── 3. Master Knowledge Graph ─────────────────────────────────────
        self.master_graph = KnowledgeGraph()
        self.master_graph.add_node("Root Consciousness", "core", 1.0)
        for key, val in attention.items():
            self.master_graph.add_node(f"Focus: {key.capitalize()}", "attention", val)
            self.master_graph.add_edge("Root Consciousness", f"Focus: {key.capitalize()}", val * 0.9)

        # ── 4. Conscious Micro-Minds ─────────────────────────────────────
        tactical_s  = self.tactical_mind.evaluate_moves(board, shortlist_moves, color, self.master_graph)
        strategic_s = self.strategic_mind.evaluate_moves(board, shortlist_moves, color, self.master_graph)
        defensive_s = self.defensive_mind.evaluate_moves(board, shortlist_moves, color, self.master_graph)
        endgame_s   = self.endgame_mind.evaluate_moves(board, shortlist_moves, color, self.master_graph)

        minds_evals = {
            "TacticalMind":  tactical_s,
            "StrategicMind": strategic_s,
            "DefensiveMind": defensive_s,
            "EndgameMind":   endgame_s,
        }

        # Combined conscious strategic score for each move
        def strategic_score(mv_str: str) -> float:
            return (
                tactical_s.get(mv_str, 0.0)  * attention.get("tactical", 0.25) +
                strategic_s.get(mv_str, 0.0) * attention.get("strategic", 0.50) +
                defensive_s.get(mv_str, 0.0) * attention.get("defensive", 0.20) +
                endgame_s.get(mv_str, 0.0)   * attention.get("endgame", 0.05)
            )

        # ── 5. Memory Lookup ─────────────────────────────────────────────
        mem_bonuses  = self.memory.get_bonus(board)
        uncertainty  = self.memory.get_uncertainty(board)
        confidence_adj = 1.0 - uncertainty   # [0..1] higher = more certain

        # ── 6. Hybrid Scoring ────────────────────────────────────────────
        # Normalize Alpha-Beta scores to [0..1] range over the shortlist
        ab_vals = [shortlist_scores.get(str(m), 0.0) for m in shortlist_moves]
        ab_min, ab_max = min(ab_vals, default=0), max(ab_vals, default=1)
        ab_range = ab_max - ab_min if ab_max != ab_min else 1.0

        hybrid_scores: Dict[str, float] = {}
        for mv in shortlist_moves:
            mv_str = str(mv)
            ab_raw  = shortlist_scores.get(mv_str, 0.0)
            ab_norm = (ab_raw - ab_min) / ab_range          # [0..1]

            strat   = strategic_score(mv_str)
            strat_n = max(0.0, min(1.0, (strat + 5) / 10))  # rough norm

            mem_b   = mem_bonuses.get(mv_str, 0.0)

            hybrid  = (self.TACTICAL_WEIGHT   * ab_norm +
                       self.STRATEGIC_WEIGHT  * strat_n +
                       self.MEMORY_WEIGHT     * mem_b   +
                       self.CONFIDENCE_WEIGHT * confidence_adj)
            hybrid_scores[mv_str] = hybrid

        # ── 7. Final Move Selection (tactically anchored) ─────────────────
        # The BEST Alpha-Beta move is always in the pool; hybrid only re-ranks
        best_mv_str = max(hybrid_scores, key=hybrid_scores.get)
        selected_move = next((m for m in shortlist_moves if str(m) == best_mv_str),
                             sc_best_move or shortlist_moves[0])

        # ── 8. Timeline Simulator ─────────────────────────────────────────
        main_tl, alts, rejected = self.timeline_sim.simulate_timelines(
            board, shortlist_moves, color, minds_evals, attention)

        # Override main timeline move with our hybrid selection
        if main_tl and main_tl.move_sequence:
            main_tl.move_sequence[0] = selected_move

        # ── 9. Probability Tree ───────────────────────────────────────────
        sel_str = str(selected_move)
        sel_mind_scores = {
            "tactical":  tactical_s.get(sel_str, 0.0),
            "strategic": strategic_s.get(sel_str, 0.0),
            "defensive": defensive_s.get(sel_str, 0.0),
            "endgame":   endgame_s.get(sel_str, 0.0),
        }
        prob_tree = ProbabilityTreeBuilder.build_tree_for_move(
            board, selected_move, color, sel_mind_scores, attention)

        # ── 10. Activation spreading ──────────────────────────────────────
        self.master_graph.set_activation("Root Consciousness", 1.0)
        self.master_graph.spread_activation(iterations=2)

        # ── 11. Meta Observer Reflection ─────────────────────────────────
        overall_confidence = hybrid_scores.get(sel_str, 0.5)
        reflection = self.meta_observer.reflect(
            board, color, selected_move, attention,
            self.master_graph, main_tl, alts, rejected)
        # Inject hybrid confidence
        reflection["confidence"] = f"{overall_confidence * 100:.1f}%"

        # ── 12. Record decision in memory ─────────────────────────────────
        pv = sc_diag.get("principal_variation", [])
        self.memory.record_decision(board, sel_str, pv, overall_confidence)

        # ── Build diagnostics ─────────────────────────────────────────────
        diagnostics = {
            "attention_profile":    attention,
            "reflection":           reflection,
            "probability_tree":     prob_tree,
            "knowledge_graph":      self.master_graph,
            "main_timeline":        main_tl,
            "alternatives":         alts,
            "rejected":             rejected,
            "subconscious":         sc_diag,
            "hybrid_scores":        hybrid_scores,
            "memory_bonus":         mem_bonuses.get(sel_str, 0.0),
            "uncertainty":          uncertainty,
            "depth_boost":          depth_boost,
        }
        return selected_move, diagnostics

    def finalize_game(self, result: str):
        \"\"\"Call at game end with 'win', 'loss', or 'draw' (engine's perspective).\"\"\"
        self.memory.finalize_game(result)
"""

# ─────────────────────────────────────────────────────────────────────────────
# Write files
# ─────────────────────────────────────────────────────────────────────────────
files = {
    "subconscious_calculator.py": SUBCONSCIOUS,
    "cognitive_memory.py":        MEMORY,
    "cognitive_engine.py":        ENGINE,
}

for name, code in files.items():
    p = BASE / name
    p.write_text(code, encoding="utf-8")
    print(f"Written: {p}")

print("All files written successfully.")
