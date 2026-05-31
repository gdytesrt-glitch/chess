from __future__ import annotations
from typing import List, Dict, Tuple, Optional
from chess_board import Board, Move, evaluate_board, generate_legal_moves

class Scenario:
    def __init__(self, name: str, move_sequence: List[Move], score: float, confidence: float, description: str):
        self.name = name
        self.move_sequence = move_sequence
        self.score = score
        self.confidence = confidence
        self.description = description

    def __repr__(self) -> str:
        seq_str = " -> ".join(str(m) for m in self.move_sequence)
        return f"Scenario({self.name}, seq=[{seq_str}], score={self.score:.2f}, conf={self.confidence*100:.1f}%)"


class TimelineSimulator:
    def __init__(self):
        self.main_timeline: Optional[Scenario] = None
        self.alternatives: List[Scenario] = []
        self.rejected: List[Scenario] = []

    def simulate_timelines(self, board: Board, candidate_moves: List[Move], color: str, 
                           minds_evaluations: Dict[str, Dict[str, float]], 
                           attention_profile: Dict[str, float]) -> Tuple[Scenario, List[Scenario], List[Scenario]]:
        """
        Simulates shallow future outcomes for candidates and groups them into 
        Main, Alternative, and Rejected timelines.
        """
        self.alternatives.clear()
        self.rejected.clear()
        
        opp_color = "black" if color == "white" else "white"
        scored_candidates: List[Tuple[Move, float, List[Move], float]] = []

        # We will look ahead depth=2 (our move, opponent's best response)
        for move in candidate_moves:
            mv_str = str(move)
            
            # Combine individual mind scores weighted by attention
            move_mind_score = 0.0
            for mind_name, scores in minds_evaluations.items():
                w = attention_profile.get(mind_name, 0.25)
                # Map mind_name to base profile key
                key = mind_name.replace("Mind", "").lower()
                if key == "endgame":
                    key = "endgame"
                move_mind_score += scores.get(mv_str, 0.0) * w
                
            # Apply move
            child = board.apply_move(move)
            
            # Evaluate immediate state
            base_score = evaluate_board(child, color)
            
            # Lookahead: simulate opponent response (minimax style)
            opp_moves = generate_legal_moves(child, opp_color)
            best_opp_response: Optional[Move] = None
            worst_outcome_score = base_score
            
            if opp_moves:
                # Opponent wants to maximize their score (minimize our score)
                worst_outcome_score = float('inf')
                for om in opp_moves[:12]: # limit search branching
                    grandchild = child.apply_move(om)
                    g_score = evaluate_board(grandchild, color)
                    if g_score < worst_outcome_score:
                        worst_outcome_score = g_score
                        best_opp_response = om
            
            # Final combined lookahead score
            final_move_score = worst_outcome_score + move_mind_score
            
            # Sequence
            seq = [move]
            if best_opp_response:
                seq.append(best_opp_response)
                
            # Confidence is based on stability (difference between immediate score and worst lookahead score)
            stability = 1.0 - min(1.0, abs(base_score - worst_outcome_score) / 5.0)
            
            scored_candidates.append((move, final_move_score, seq, stability))

        # Sort candidate moves by final lookahead score in descending order
        scored_candidates.sort(key=lambda x: x[1], reverse=True)

        if not scored_candidates:
            # Handle empty candidates gracefully
            dummy_move = Move(0,0,0,0)
            self.main_timeline = Scenario("Main Timeline", [dummy_move], 0.0, 1.0, "No moves available")
            return self.main_timeline, [], []

        # 1. Main Timeline (First choice)
        best_mv, best_score, best_seq, best_stability = scored_candidates[0]
        main_desc = self.generate_description(best_mv, board)
        self.main_timeline = Scenario("Main Timeline", best_seq, best_score, best_stability, main_desc)

        # 2. Alternative & Rejected Timelines
        # Alternatives are top runners up (up to 3) with solid scores
        # Rejected are moves that initially seemed okay but score very poorly on lookahead (e.g. stability drops rapidly or major score drops)
        
        for mv, score, seq, stability in scored_candidates[1:]:
            desc = self.generate_description(mv, board)
            
            # If the lookahead resulted in a massive score drop compared to current position evaluation (e.g. drop > 1.5)
            # then it is a rejected timeline (severe refutation or tactical risk!)
            curr_score = evaluate_board(board, color)
            if (score - curr_score) < -2.0 or stability < 0.35:
                # Rejection reason
                rejection_reason = "exposes severe tactical refutations or piece danger"
                if stability < 0.35:
                    rejection_reason = "leads to highly volatile and unstable board configurations"
                
                self.rejected.append(Scenario(
                    name=f"Rejected: {str(mv)}",
                    move_sequence=seq,
                    score=score,
                    confidence=stability,
                    description=f"Discarded because it {rejection_reason}"
                ))
            else:
                if len(self.alternatives) < 3:
                    self.alternatives.append(Scenario(
                        name=f"Alt: {str(mv)}",
                        move_sequence=seq,
                        score=score,
                        confidence=stability,
                        description=desc
                    ))

        return self.main_timeline, self.alternatives, self.rejected[:3]

    def generate_description(self, move: Move, board: Board) -> str:
        piece = board.grid[move.from_row][move.from_col]
        target = board.grid[move.to_row][move.to_col]
        cols = "abcdefgh"
        
        from_sq = f"{cols[move.from_col]}{8-move.from_row}"
        to_sq = f"{cols[move.to_col]}{8-move.to_row}"
        
        desc = ""
        p_lower = piece.lower()
        if p_lower == "p":
            if target != ".":
                desc = f"pawn strike capturing {target} on {to_sq}"
            else:
                desc = f"pawn push to {to_sq} aiming to gain space"
        elif p_lower == "n":
            desc = f"knight maneuver {from_sq} to {to_sq} aiming for central outpost"
        elif p_lower == "b":
            desc = f"bishop development along diagonal to {to_sq}"
        elif p_lower == "r":
            desc = f"rook activation transferring to {to_sq}"
        elif p_lower == "q":
            desc = f"queen mobilization to active square {to_sq}"
        elif p_lower == "k":
            if abs(move.to_col - move.from_col) > 1:
                desc = "castling maneuver to secure king safety"
            else:
                desc = f"king safety positioning to {to_sq}"
        return desc
