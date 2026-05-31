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
    """
    Hybrid Cognitive Chess Mind
    ===========================
    Scoring formula per move:
        final = 0.75 * tactical_score   (Alpha-Beta subconscious)
              + 0.15 * strategic_score  (conscious micro-minds)
              + 0.05 * memory_score     (long-term learning)
              + 0.05 * confidence_adj   (positional certainty)

    The conscious layer ONLY ranks moves that the subconscious has already
    validated — it can never push a tactically unsound move to the top.
    """

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
        """Call at game end with 'win', 'loss', or 'draw' (engine's perspective)."""
        self.memory.finalize_game(result)
