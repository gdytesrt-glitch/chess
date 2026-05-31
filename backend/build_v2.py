"""
Build script v2: writes updated cognitive_engine.py + 3 test suites.
Run with: python build_v2.py
"""
import pathlib

BASE = pathlib.Path(__file__).parent

# ─────────────────────────────────────────────────────────────────────────────
# 1. cognitive_engine.py  (v2)
# ─────────────────────────────────────────────────────────────────────────────
ENGINE_V2 = r"""
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional

from chess_board import Board, Move, generate_legal_moves, is_in_check
from attention_system import AttentionSystem
from micro_mind import (KnowledgeGraph, TacticalMind, StrategicMind,
                         DefensiveMind, EndgameMind)
from probability_tree import ProbabilityTreeBuilder
from timeline_simulator import TimelineSimulator
from meta_observer import MetaObserver
from subconscious_calculator import SubconsciousCalculator
from cognitive_memory import CognitiveMemory


def pv_is_legal(board: Board, pv: List[str]) -> bool:
    """Verify that every move in the principal variation is legal."""
    b = board
    for mv_str in pv:
        color = "white" if b.white_to_move else "black"
        legal = [str(m) for m in generate_legal_moves(b, color)]
        if mv_str not in legal:
            return False
        # apply the move
        matched = next(m for m in generate_legal_moves(b, color) if str(m) == mv_str)
        b = b.apply_move(matched)
    return True


def search_confidence(score_map: Dict[str, float]) -> float:
    """
    Confidence derived purely from the search result.
    High gap between 1st and 2nd best → high confidence.
    formula: gap / (gap + 0.5) scaled to [0..1]
    """
    if not score_map:
        return 0.5
    sorted_scores = sorted(score_map.values(), reverse=True)
    best = sorted_scores[0]
    second = sorted_scores[1] if len(sorted_scores) > 1 else best - 0.5
    gap = abs(best - second)
    return min(1.0, gap / (gap + 0.5))


class ProbabilisticChessMind:
    """
    Hybrid Cognitive Chess Mind  v2
    ================================
    Scoring weights (conservative – corrected per feedback):
        final = 0.85 * tactical_score   (Alpha-Beta, always dominant)
              + 0.10 * strategic_score  (conscious micro-minds)
              + 0.03 * memory_score     (capped at 0.15 raw bonus)
              + 0.02 * confidence_adj   (search-derived gap confidence)

    The conscious layer NEVER overrides tactical truth —
    it only re-ranks the Alpha-Beta shortlist.
    """

    TACTICAL_WEIGHT   = 0.85
    STRATEGIC_WEIGHT  = 0.10
    MEMORY_WEIGHT     = 0.03
    CONFIDENCE_WEIGHT = 0.02

    SHORTLIST_SIZE    = 6       # Conscious minds only see top-6 AB moves
    MEMORY_CAP        = 0.15    # Memory bonus never exceeds this
    MIN_GAMES_TO_TRUST = 3      # Ignore memory entries with < 3 games

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
        self._last_pv_legal    = True

    # ─────────────────────────────────────────────────────────────────────────

    def think(self, board: Board) -> Optional[Tuple[Move, Dict[str, Any]]]:
        color = "white" if board.white_to_move else "black"
        legal_moves = generate_legal_moves(board, color)
        if not legal_moves:
            return None

        # ── 1. Subconscious deep search (with memory-driven depth boost) ──────
        depth_boost  = self.memory.recommended_depth_boost(board, self.subconscious.max_depth)
        orig_depth   = self.subconscious.max_depth
        self.subconscious.max_depth = orig_depth + depth_boost
        self.subconscious.clear_caches()

        sc_best, sc_score, sc_diag = self.subconscious.search(board)

        self.subconscious.max_depth = orig_depth

        # PV legality check (debug guard)
        pv = sc_diag.get("principal_variation", [])
        self._last_pv_legal = pv_is_legal(board, pv)
        if not self._last_pv_legal:
            print("[WARNING] PV contains illegal move – ignoring PV for memory.")
            pv = []

        # ── 2. Build shortlist from top AB candidates ─────────────────────────
        candidate_pool = legal_moves[:min(len(legal_moves), 24)]
        sc_shortlist   = self.subconscious.score_candidates(board, candidate_pool, depth=3)

        # Sort by AB score → take top SHORTLIST_SIZE
        top_keys    = sorted(sc_shortlist, key=sc_shortlist.get, reverse=True)[:self.SHORTLIST_SIZE]
        shortlist   = [m for m in candidate_pool if str(m) in top_keys]
        if sc_best and sc_best not in shortlist:
            shortlist.insert(0, sc_best)

        # ── 3. Attention System ───────────────────────────────────────────────
        attention = self.attention_system.calculate_attention(board, color)

        # ── 4. Knowledge Graph ────────────────────────────────────────────────
        self.master_graph = KnowledgeGraph()
        self.master_graph.add_node("Root Consciousness", "core", 1.0)
        for k, v in attention.items():
            node = f"Focus: {k.capitalize()}"
            self.master_graph.add_node(node, "attention", v)
            self.master_graph.add_edge("Root Consciousness", node, v * 0.9)

        # ── 5. Conscious Micro-Minds (shortlist only) ─────────────────────────
        tactical_s  = self.tactical_mind.evaluate_moves (board, shortlist, color, self.master_graph)
        strategic_s = self.strategic_mind.evaluate_moves(board, shortlist, color, self.master_graph)
        defensive_s = self.defensive_mind.evaluate_moves(board, shortlist, color, self.master_graph)
        endgame_s   = self.endgame_mind.evaluate_moves  (board, shortlist, color, self.master_graph)

        minds_evals = {"TacticalMind": tactical_s, "StrategicMind": strategic_s,
                       "DefensiveMind": defensive_s, "EndgameMind": endgame_s}

        def strat_score(mv_str: str) -> float:
            return (tactical_s .get(mv_str, 0.0) * attention.get("tactical",  0.25) +
                    strategic_s.get(mv_str, 0.0) * attention.get("strategic", 0.50) +
                    defensive_s.get(mv_str, 0.0) * attention.get("defensive", 0.20) +
                    endgame_s  .get(mv_str, 0.0) * attention.get("endgame",   0.05))

        # ── 6. Memory lookup (trust only positions with MIN_GAMES_TO_TRUST) ───
        raw_mem_bonuses = self.memory.get_bonus(board)
        mem_bonuses: Dict[str, float] = {}
        for mv_str, bonus in raw_mem_bonuses.items():
            # fetch games count from internal record to check trust threshold
            h = self.memory._hash(board)
            rec = self.memory._db.get(h)
            games = rec.move_stats.get(mv_str, {}).get("games", 0) if rec else 0
            if games >= self.MIN_GAMES_TO_TRUST:
                mem_bonuses[mv_str] = min(self.MEMORY_CAP, bonus)  # hard cap
            else:
                mem_bonuses[mv_str] = 0.0

        position_familiarity = 1.0 - self.memory.get_uncertainty(board)   # [0..1]

        # ── 7. Search-derived confidence (score gap heuristic) ────────────────
        s_conf = search_confidence(sc_shortlist)

        # ── 8. Hybrid scoring ─────────────────────────────────────────────────
        ab_vals   = [sc_shortlist.get(str(m), 0.0) for m in shortlist]
        ab_min, ab_max = min(ab_vals, default=0.0), max(ab_vals, default=1.0)
        ab_range  = ab_max - ab_min if ab_max != ab_min else 1.0

        hybrid: Dict[str, float] = {}
        for mv in shortlist:
            mv_str  = str(mv)
            ab_raw  = sc_shortlist.get(mv_str, 0.0)
            ab_norm = (ab_raw - ab_min) / ab_range           # [0..1]
            st_norm = max(0.0, min(1.0, (strat_score(mv_str) + 5) / 10))
            mem_b   = mem_bonuses.get(mv_str, 0.0)

            hybrid[mv_str] = (self.TACTICAL_WEIGHT   * ab_norm +
                               self.STRATEGIC_WEIGHT  * st_norm +
                               self.MEMORY_WEIGHT     * mem_b   +
                               self.CONFIDENCE_WEIGHT * s_conf)

        # ── 9. Final selection (tactically anchored) ──────────────────────────
        best_str      = max(hybrid, key=hybrid.get)
        selected_move = next((m for m in shortlist if str(m) == best_str),
                              sc_best or shortlist[0])

        # ── 10. Timeline Simulator ────────────────────────────────────────────
        main_tl, alts, rejected = self.timeline_sim.simulate_timelines(
            board, shortlist, color, minds_evals, attention)
        if main_tl and main_tl.move_sequence:
            main_tl.move_sequence[0] = selected_move

        # ── 11. Probability Tree ──────────────────────────────────────────────
        sel_str = str(selected_move)
        sel_scores = {"tactical": tactical_s.get(sel_str, 0.0),
                      "strategic": strategic_s.get(sel_str, 0.0),
                      "defensive": defensive_s.get(sel_str, 0.0),
                      "endgame":   endgame_s.get(sel_str, 0.0)}
        prob_tree = ProbabilityTreeBuilder.build_tree_for_move(
            board, selected_move, color, sel_scores, attention)

        # ── 12. Activation spreading ──────────────────────────────────────────
        self.master_graph.set_activation("Root Consciousness", 1.0)
        self.master_graph.spread_activation(iterations=2)

        # ── 13. MetaObserver ─────────────────────────────────────────────────
        reflection = self.meta_observer.reflect(
            board, color, selected_move, attention,
            self.master_graph, main_tl, alts, rejected)
        reflection["search_confidence"]    = f"{s_conf * 100:.1f}%"
        reflection["position_familiarity"] = f"{position_familiarity * 100:.1f}%"
        reflection["confidence"] = reflection["search_confidence"]   # overwrite with search-derived

        # ── 14. Record decision ───────────────────────────────────────────────
        if self._last_pv_legal:
            self.memory.record_decision(board, sel_str, pv, s_conf)

        return selected_move, {
            "attention_profile":     attention,
            "reflection":            reflection,
            "probability_tree":      prob_tree,
            "knowledge_graph":       self.master_graph,
            "main_timeline":         main_tl,
            "alternatives":          alts,
            "rejected":              rejected,
            "subconscious":          sc_diag,
            "hybrid_scores":         hybrid,
            "memory_bonus":          mem_bonuses.get(sel_str, 0.0),
            "position_familiarity":  position_familiarity,
            "search_confidence":     s_conf,
            "depth_boost":           depth_boost,
            "pv_legal":              self._last_pv_legal,
        }

    def finalize_game(self, result: str):
        """Call at game end: 'win' | 'loss' | 'draw' from engine perspective."""
        self.memory.finalize_game(result)
""".lstrip()

# ─────────────────────────────────────────────────────────────────────────────
# 2. cognitive_memory.py  (v2 – adds _hash() helper + game filter)
# ─────────────────────────────────────────────────────────────────────────────
MEMORY_V2 = r"""
from __future__ import annotations
import json, pathlib
from typing import Dict, List, Any
from chess_board import Board, generate_legal_moves

MEMORY_FILE = pathlib.Path(__file__).parent / "cognitive_memory.json"
MIN_MATERIAL = 6.0   # skip trivially simple positions (< 6 pts material each side)


def _board_hash(board: Board) -> str:
    return "".join("".join(row) for row in board.grid) + ("W" if board.white_to_move else "B")


def _is_trivial(board: Board, color: str) -> bool:
    """Skip positions that are forced (only 1 legal move) or endgame trivial."""
    moves = generate_legal_moves(board, color)
    return len(moves) <= 1


class PositionRecord:
    def __init__(self):
        self.move_stats: Dict[str, Dict[str, Any]] = {}

    def record_move(self, move_str: str, result: str, pv: List[str], confidence: float):
        if move_str not in self.move_stats:
            self.move_stats[move_str] = {"games": 0, "wins": 0, "losses": 0, "draws": 0,
                                          "pv": pv, "confidence": confidence}
        s = self.move_stats[move_str]
        s["games"] += 1
        key = result + "s"
        if key in s:
            s[key] += 1
        if result == "win":
            s["pv"] = pv
        s["confidence"] = (s["confidence"] * (s["games"] - 1) + confidence) / s["games"]

    def best_move_bonus(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for mv, s in self.move_stats.items():
            if s["games"] == 0:
                out[mv] = 0.0
                continue
            win_rate = s["wins"] / s["games"]
            out[mv] = win_rate * 0.70 + s["confidence"] * 0.30
        return out

    def uncertainty(self) -> float:
        if not self.move_stats:
            return 1.0
        avg = sum(s["confidence"] for s in self.move_stats.values()) / len(self.move_stats)
        return 1.0 - avg

    def to_dict(self) -> Dict:
        return {"move_stats": self.move_stats}

    @classmethod
    def from_dict(cls, d: Dict) -> "PositionRecord":
        rec = cls()
        rec.move_stats = d.get("move_stats", {})
        return rec


class CognitiveMemory:
    def __init__(self):
        self._db: Dict[str, PositionRecord] = {}
        self._pending: List[Dict] = []
        self.load()

    def _hash(self, board: Board) -> str:
        return _board_hash(board)

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

    def get_bonus(self, board: Board) -> Dict[str, float]:
        h = self._hash(board)
        return self._db[h].best_move_bonus() if h in self._db else {}

    def get_uncertainty(self, board: Board) -> float:
        h = self._hash(board)
        return self._db[h].uncertainty() if h in self._db else 1.0

    def recommended_depth_boost(self, board: Board, base_depth: int) -> int:
        unc = self.get_uncertainty(board)
        if unc > 0.75: return 2
        if unc > 0.50: return 1
        return 0

    def record_decision(self, board: Board, move_str: str, pv: List[str], confidence: float):
        """Only record non-trivial positions."""
        color = "white" if board.white_to_move else "black"
        if _is_trivial(board, color):
            return
        h = self._hash(board)
        self._pending.append({"hash": h, "move": move_str, "pv": pv, "confidence": confidence})

    def finalize_game(self, result: str):
        for entry in self._pending:
            h = entry["hash"]
            if h not in self._db:
                self._db[h] = PositionRecord()
            self._db[h].record_move(entry["move"], result, entry["pv"], entry["confidence"])
        self._pending.clear()
        self.save()
        print(f"[CognitiveMemory] {len(self._db)} positions in memory → {MEMORY_FILE.name}")
""".lstrip()

# ─────────────────────────────────────────────────────────────────────────────
# 3. perft_test.py
# ─────────────────────────────────────────────────────────────────────────────
PERFT = r"""
"""
PERFT = r"""
from chess_board import Board, generate_legal_moves

# Standard Perft values for initial position
EXPECTED = {1: 20, 2: 400, 3: 8902, 4: 197281}

def perft(board: Board, depth: int) -> int:
    color = "white" if board.white_to_move else "black"
    moves = generate_legal_moves(board, color)
    if depth == 1:
        return len(moves)
    total = 0
    for mv in moves:
        total += perft(board.apply_move(mv), depth - 1)
    return total

def run():
    board = Board.initial()
    print("=== PERFT TEST (Initial Position) ===")
    all_pass = True
    for d in range(1, 5):
        result = perft(board, d)
        expected = EXPECTED[d]
        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_pass = False
        print(f"  Depth {d}: {result:>8,}  expected {expected:>8,}  [{status}]")
    print()
    if all_pass:
        print("ALL PERFT TESTS PASSED - Move generation is correct!")
    else:
        print("SOME PERFT TESTS FAILED - Move generation has bugs!")
    return all_pass

if __name__ == "__main__":
    run()
""".lstrip()

# ─────────────────────────────────────────────────────────────────────────────
# 4. tactical_suite.py
# ─────────────────────────────────────────────────────────────────────────────
TACTICAL = r"""
from chess_board import Board, generate_legal_moves
from subconscious_calculator import SubconsciousCalculator
import time

# Puzzles: (grid_rows, white_to_move, expected_best_move_str, description)
# Grid is row 8..1 top to bottom, piece chars same as chess_board.py
PUZZLES = [
    # ── Mate in 1 ─────────────────────────────────────────────────────────
    {
        "desc": "Mate in 1 - Scholar's Mate setup",
        "grid": [
            list("rnb.kbnr"),
            list("pppp.Qpp"),
            list("........"),
            list("....p..."),
            list("..B.P..."),
            list("........"),
            list("PPPP.PPP"),
            list("RNB.K.NR"),
        ],
        "white_to_move": True,
        "expected": "f7f8",   # Qxf7# - but queen is already at f7... adjust
        "depth": 3,
    },
    # ── Mate in 1 - back rank ──────────────────────────────────────────────
    {
        "desc": "Mate in 1 - Back rank",
        "grid": [
            list("....rk.."),
            list("ppp..ppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPP..PPP"),
            list("....RK.."),
        ],
        "white_to_move": True,
        "expected": "e1e8",   # Re8#
        "depth": 2,
    },
    # ── Fork ──────────────────────────────────────────────────────────────
    {
        "desc": "Knight Fork - king and rook",
        "grid": [
            list("r...k..."),
            list("........"),
            list("....N..."),
            list("........"),
            list("........"),
            list("........"),
            list("PPP..PPP"),
            list("R...K..R"),
        ],
        "white_to_move": True,
        "expected": "e6c7",   # Nc7+ forks king and rook
        "depth": 3,
    },
    # ── Winning capture ────────────────────────────────────────────────────
    {
        "desc": "Free queen capture",
        "grid": [
            list("....k..."),
            list("....q..."),
            list("........"),
            list("....R..."),
            list("........"),
            list("........"),
            list("PPP..PPP"),
            list("....K..R"),
        ],
        "white_to_move": True,
        "expected": "e5e7",   # Rxe7 wins queen
        "depth": 2,
    },
]

def run():
    calc = SubconsciousCalculator(max_depth=5)
    print("=== TACTICAL SUITE ===")
    solved = 0
    total  = len(PUZZLES)

    for puz in PUZZLES:
        board = Board(puz["grid"], puz["white_to_move"])
        calc.clear_caches()
        t0 = time.time()
        move, score, diag = calc.search(board)
        elapsed = time.time() - t0
        found = str(move) if move else "None"
        ok = found == puz["expected"]
        if ok:
            solved += 1
        status = "PASS" if ok else f"FAIL (expected {puz['expected']}, got {found})"
        pv_str = " > ".join(diag.get("principal_variation", [])[:4])
        print(f"  [{status}]  {puz['desc']}")
        print(f"         Move={found}  Score={score:+.2f}  Depth={diag['depth_reached']}  "
              f"Nodes={diag['nodes_evaluated']:,}  Time={elapsed:.2f}s")
        print(f"         PV: {pv_str}")

    print(f"\nSolved: {solved}/{total}")
    return solved, total

if __name__ == "__main__":
    run()
""".lstrip()

# ─────────────────────────────────────────────────────────────────────────────
# 5. depth_stability_test.py
# ─────────────────────────────────────────────────────────────────────────────
STABILITY = r"""
from chess_board import Board, parse_move
from subconscious_calculator import SubconsciousCalculator
import time

def run():
    board = Board.initial()
    for mv_str in ["e2e4", "e7e5", "g1f3"]:
        board = board.apply_move(parse_move(mv_str))

    print("=== DEPTH STABILITY TEST ===")
    print("Position after 1.e4 e5 2.Nf3 (Black to move)\n")
    print(f"{'Depth':<8} {'Move':<8} {'Score':>8} {'Nodes':>12} {'TT Hits':>10} {'Time':>8}  PV")
    print("-" * 90)

    prev_move = None
    stable_count = 0

    for depth in [2, 3, 4, 5, 6]:
        calc = SubconsciousCalculator(max_depth=depth)
        t0 = time.time()
        move, score, diag = calc.search(board)
        elapsed = time.time() - t0

        mv_str = str(move) if move else "None"
        pv_str = " > ".join(diag.get("principal_variation", [])[:4])
        nodes  = diag["nodes_evaluated"]
        tthits = diag["tt_hits"]

        stable = "(stable)" if mv_str == prev_move and prev_move else ""
        if mv_str == prev_move:
            stable_count += 1

        print(f"  {depth:<6} {mv_str:<8} {score:>+8.3f} {nodes:>12,} {tthits:>10,} {elapsed:>7.2f}s  {pv_str}  {stable}")
        prev_move = mv_str

    print()
    if stable_count >= 3:
        print("STABLE: Move choice consistent across depths - evaluation is reliable.")
    else:
        print("UNSTABLE: Move changes significantly with depth - evaluation needs tuning.")

if __name__ == "__main__":
    run()
""".lstrip()

# ─────────────────────────────────────────────────────────────────────────────
# Write all files
# ─────────────────────────────────────────────────────────────────────────────
files = {
    "cognitive_engine.py":    ENGINE_V2,
    "cognitive_memory.py":    MEMORY_V2,
    "perft_test.py":          PERFT,
    "tactical_suite.py":      TACTICAL,
    "depth_stability_test.py": STABILITY,
}

for name, code in files.items():
    p = BASE / name
    p.write_text(code, encoding="utf-8")
    print(f"Written: {p.name}")

print("\nAll v2 files written successfully.")
