from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from chess_board import Board, Move, is_in_check
from micro_mind import KnowledgeGraph
from timeline_simulator import Scenario

class MetaObserver:
    def __init__(self):
        self.uncertainties: List[str] = []
        self.meta_goals: List[str] = []
        self.errors: List[str] = []

    def reflect(self, board: Board, color: str, selected_move: Move, 
                attention_profile: Dict[str, float], graph: KnowledgeGraph,
                main_timeline: Scenario, alternatives: List[Scenario], 
                rejected: List[Scenario]) -> Dict[str, Any]:
        """
        Synthesizes information from all cognitive layers to generate 
        the unified Self-Reflection and Meta-Consciousness narrative.
        """
        self.uncertainties.clear()
        self.meta_goals.clear()
        
        # 1. Determine main goals and concerns from Attention System and Graph
        tactical_focus = attention_profile.get("tactical", 0.25)
        strategic_focus = attention_profile.get("strategic", 0.50)
        defensive_focus = attention_profile.get("defensive", 0.20)
        endgame_focus = attention_profile.get("endgame", 0.05)
        
        # Select Primary Meta Goal
        primary_goal = "Position stabilization and developmental symmetry"
        if strategic_focus > 0.4:
            primary_goal = "Rapid piece mobilization and central pawn control"
        elif tactical_focus > 0.4:
            primary_goal = "Immediate tactical strike, searching for forced material gains"
        elif defensive_focus > 0.4:
            primary_goal = "Neutralizing aggressive opponent threats and securing king safety"
        elif endgame_focus > 0.4:
            primary_goal = "Activating key endgame assets and promoting passed pawns"
            
        self.meta_goals.append(primary_goal)

        # 2. Extract Concerns
        active_concepts = graph.query_active_concepts(threshold=0.6)
        concern = "Maintaining structural balance and pieces activity"
        for name, act in active_concepts:
            if "Hanging" in name or "weak" in name.lower():
                concern = f"Vulnerability of our structural weakness: {name}"
                self.uncertainties.append(f"Is our piece on {name.split()[-1]} sufficiently protected?")
                break
            elif "Check" in name:
                concern = "Exposed king and immediate tactical checks"
                self.uncertainties.append("Can the king survive the upcoming check storm safely?")
                break

        if not self.uncertainties:
            # Generate a standard uncertainty
            self.uncertainties.append(f"Are there hidden tactical refutations in the simulated lines?")

        # 3. Confidence level
        confidence = main_timeline.confidence
        # Scale confidence based on defensive pressure
        if defensive_focus > 0.4:
            confidence = max(0.4, confidence - 0.15) # lower confidence under heavy attack
        elif tactical_focus > 0.5:
            confidence = min(0.95, confidence + 0.1) # higher confidence when striking

        # 4. Generate the conscious narrative
        mv_str = str(selected_move)
        piece = board.grid[selected_move.from_row][selected_move.from_col]
        cols = "abcdefgh"
        to_sq = f"{cols[selected_move.to_col]}{8-selected_move.to_row}"
        
        narrative = f"I have committed to playing {mv_str} ({piece} to {to_sq}). "
        
        if strategic_focus > 0.4:
            narrative += f"This decision is rooted in a long-term strategic plan: {main_timeline.description}. "
        elif tactical_focus > 0.4:
            narrative += f"This is an urgent tactical decision: {main_timeline.description}. I am prioritizing concrete material exchanges. "
        elif defensive_focus > 0.4:
            narrative += f"This is a vital defensive retreat or blocking maneuver: {main_timeline.description}. Security is paramount now. "
        else:
            narrative += f"Executing my endgame protocol: {main_timeline.description}. "
            
        # Mention Alternatives
        if alternatives:
            alt_moves = [alt.name.split()[-1] for alt in alternatives]
            narrative += f"I spent significant cognitive cycles simulating alternative timelines: {', '.join(alt_moves)}. "
            narrative += f"Specifically, {alternatives[0].name.split()[-1]} was a highly viable candidate pointing to '{alternatives[0].description}'. "
            
        # Mention Rejected Timelines
        if rejected:
            rej_moves = [rej.name.split()[-1] for rej in rejected]
            narrative += f"However, I explicitly rejected timelines like {', '.join(rej_moves)} because they led to a significant decline in stability or high king exposure."
        else:
            narrative += "No highly dangerous refutations were detected in this depth search, giving me positional security."

        return {
            "primary_goal": primary_goal,
            "concern": concern,
            "confidence": f"{confidence * 100:.1f}%",
            "uncertainties": self.uncertainties.copy(),
            "meta_goals": self.meta_goals.copy(),
            "narrative": narrative
        }
