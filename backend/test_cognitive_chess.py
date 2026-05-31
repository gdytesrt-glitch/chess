from __future__ import annotations
import unittest
from chess_board import Board, Move, generate_legal_moves, evaluate_board
from attention_system import AttentionSystem
from micro_mind import KnowledgeGraph, TacticalMind, StrategicMind, DefensiveMind, EndgameMind
from timeline_simulator import TimelineSimulator
from meta_observer import MetaObserver
from cognitive_engine import ProbabilisticChessMind

class TestCognitiveChessEngine(unittest.TestCase):
    def setUp(self):
        self.board = Board.initial()

    def test_board_initialization(self):
        self.assertEqual(len(self.board.grid), 8)
        self.assertEqual(len(self.board.grid[0]), 8)
        self.assertTrue(self.board.white_to_move)
        
    def test_initial_move_generation(self):
        # White should have exactly 20 legal moves at start
        # Pawns: 8 pawns * 2 moves = 16 moves
        # Knights: 2 knights * 2 moves = 4 moves
        # Total = 20 moves
        legal = generate_legal_moves(self.board, "white")
        self.assertEqual(len(legal), 20)

    def test_attention_system(self):
        system = AttentionSystem()
        profile = system.calculate_attention(self.board, "white")
        self.assertIn("tactical", profile)
        self.assertIn("strategic", profile)
        self.assertIn("defensive", profile)
        self.assertIn("endgame", profile)
        
        # Verify normalization
        total_focus = sum(profile.values())
        self.assertAlmostEqual(total_focus, 1.0, places=3)

    def test_minds_evaluations(self):
        graph = KnowledgeGraph()
        tactical = TacticalMind()
        strategic = StrategicMind()
        
        legal = generate_legal_moves(self.board, "white")
        candidates = legal[:10]
        
        t_scores = tactical.evaluate_moves(self.board, candidates, "white", graph)
        s_scores = strategic.evaluate_moves(self.board, candidates, "white", graph)
        
        self.assertEqual(len(t_scores), len(candidates))
        self.assertEqual(len(s_scores), len(candidates))
        
        # Strategic score for e2e4 (index 12 in full list, let's just assert keys are str of moves)
        for mv in candidates:
            self.assertIn(str(mv), t_scores)
            self.assertIn(str(mv), s_scores)

    def test_timeline_simulator(self):
        simulator = TimelineSimulator()
        legal = generate_legal_moves(self.board, "white")
        candidates = legal[:12]
        
        attention_profile = {
            "tactical": 0.25,
            "strategic": 0.50,
            "defensive": 0.20,
            "endgame": 0.05
        }
        
        minds_evaluations = {
            "TacticalMind": {str(m): 0.1 for m in candidates},
            "StrategicMind": {str(m): 0.5 for m in candidates},
            "DefensiveMind": {str(m): 0.2 for m in candidates},
            "EndgameMind": {str(m): 0.0 for m in candidates}
        }
        
        main_tl, alts, rejs = simulator.simulate_timelines(
            self.board, candidates, "white", minds_evaluations, attention_profile
        )
        
        self.assertIsNotNone(main_tl)
        self.assertTrue(len(main_tl.move_sequence) > 0)
        self.assertIsInstance(alts, list)
        self.assertIsInstance(rejs, list)

    def test_meta_observer(self):
        observer = MetaObserver()
        graph = KnowledgeGraph()
        graph.add_node("Root Consciousness", "core", 1.0)
        
        attention_profile = {
            "tactical": 0.25,
            "strategic": 0.50,
            "defensive": 0.20,
            "endgame": 0.05
        }
        
        from timeline_simulator import Scenario
        main_tl = Scenario("Main", [Move(6, 4, 4, 4)], 1.5, 0.8, "center pawn push")
        alts = [Scenario("Alt", [Move(6, 3, 4, 3)], 1.2, 0.7, "queen pawn push")]
        rejs = []
        
        reflection = observer.reflect(
            self.board, "white", Move(6, 4, 4, 4), attention_profile, graph,
            main_tl, alts, rejs
        )
        
        self.assertIn("primary_goal", reflection)
        self.assertIn("concern", reflection)
        self.assertIn("confidence", reflection)
        self.assertIn("narrative", reflection)

    def test_unified_mind(self):
        mind = ProbabilisticChessMind()
        res = mind.think(self.board)
        self.assertIsNotNone(res)
        
        chosen_move, diagnostics = res
        self.assertIsInstance(chosen_move, Move)
        self.assertIn("attention_profile", diagnostics)
        self.assertIn("reflection", diagnostics)
        self.assertIn("probability_tree", diagnostics)
        self.assertIn("knowledge_graph", diagnostics)

if __name__ == "__main__":
    unittest.main()
