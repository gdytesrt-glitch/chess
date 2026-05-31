from __future__ import annotations
from typing import List, Dict, Optional, Any
from chess_board import Board, Move, generate_pseudo_moves, is_in_check

class ProbabilityNode:
    def __init__(self, name: str, probability: float = 0.0):
        self.name = name
        self.probability = probability
        self.children: List[ProbabilityNode] = []

    def add_child(self, child: ProbabilityNode):
        self.children.append(child)

    def print_tree(self, indent: str = "") -> str:
        """Beautifully formats the probability tree node and its children recursively."""
        res = f"{indent}├── {self.name} ({self.probability*100:.1f}%)\n"
        child_indent = indent + "│   "
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                # Last child formatting
                res += child.print_tree_last(child_indent)
            else:
                res += child.print_tree(child_indent)
        return res

    def print_tree_last(self, indent: str = "") -> str:
        # Re-verify indent prefix
        clean_indent = indent[:-4] + "    " if len(indent) >= 4 else indent
        res = f"{clean_indent}└── {self.name} ({self.probability*100:.1f}%)\n"
        child_indent = clean_indent + "│   "
        for i, child in enumerate(self.children):
            if i == len(self.children) - 1:
                res += child.print_tree_last(child_indent)
            else:
                res += child.print_tree(child_indent)
        return res


class ProbabilityTreeBuilder:
    @staticmethod
    def build_tree_for_move(board: Board, move: Move, color: str, mind_scores: Dict[str, float], attention_profile: Dict[str, float]) -> ProbabilityNode:
        """
        Builds a hierarchical probability classification tree for a candidate move.
        Intention probabilities are weighted by BOTH the attention of the mind and the evaluation scores.
        """
        mv_str = str(move)
        root = ProbabilityNode(name=mv_str, probability=1.0)
        
        # Extract individual mind scores for this specific move
        tactical_score = max(0.0, mind_scores.get("tactical", 0.0))
        strategic_score = max(0.0, mind_scores.get("strategic", 0.0))
        defensive_score = max(0.0, mind_scores.get("defensive", 0.0))
        endgame_score = max(0.0, mind_scores.get("endgame", 0.0))

        # Weight scores by current attention focus weights
        tactical_weighted = tactical_score * attention_profile.get("tactical", 0.25)
        strategic_weighted = strategic_score * attention_profile.get("strategic", 0.25)
        defensive_weighted = defensive_score * attention_profile.get("defensive", 0.25)
        endgame_weighted = endgame_score * attention_profile.get("endgame", 0.25)

        total_weighted = tactical_weighted + strategic_weighted + defensive_weighted + endgame_weighted
        if total_weighted == 0:
            total_weighted = 1.0

        # Calculate category probabilities
        p_tactical = tactical_weighted / total_weighted
        p_strategic = strategic_weighted / total_weighted
        p_defensive = defensive_weighted / total_weighted
        p_endgame = endgame_weighted / total_weighted

        piece = board.grid[move.from_row][move.from_col]
        piece_lower = piece.lower()
        opp_color = "black" if color == "white" else "white"

        # 1. Tactical Node & Sub-nodes
        if p_tactical > 0.05:
            tactical_node = ProbabilityNode("Tactical Intent", p_tactical)
            
            # Sub-categories
            has_sub = False
            # Check capture
            if board.grid[move.to_row][move.to_col] != ".":
                captured = board.grid[move.to_row][move.to_col]
                tactical_node.add_child(ProbabilityNode(f"Capture {captured}", 0.7))
                has_sub = True
                
            # Check check
            child_board = board.apply_move(move)
            if is_in_check(child_board, opp_color):
                tactical_node.add_child(ProbabilityNode("King Check Threat", 0.6 if has_sub else 1.0))
                has_sub = True

            if not has_sub:
                tactical_node.add_child(ProbabilityNode("Tactical Mobilization", 1.0))

            # Normalize children
            tot_c = sum(c.probability for c in tactical_node.children)
            for c in tactical_node.children:
                c.probability = (c.probability / tot_c) * p_tactical

            root.add_child(tactical_node)

        # 2. Strategic Node & Sub-nodes
        if p_strategic > 0.05:
            strategic_node = ProbabilityNode("Strategic Intent", p_strategic)
            
            has_sub = False
            # Development
            back_rank = 7 if color == "white" else 0
            if piece_lower in ["n", "b"] and move.from_row == back_rank:
                strategic_node.add_child(ProbabilityNode("Piece Development", 0.8))
                has_sub = True
                
            # Center Control
            center_squares = [(3,3), (3,4), (4,3), (4,4)]
            if (move.to_row, move.to_col) in center_squares:
                strategic_node.add_child(ProbabilityNode("Center Occupation", 0.7 if has_sub else 1.0))
                has_sub = True
            elif any(abs(move.to_row - cr) <= 1 and abs(move.to_col - cc) <= 1 for cr, cc in center_squares):
                strategic_node.add_child(ProbabilityNode("Center Support", 0.5 if has_sub else 0.8))
                has_sub = True

            if not has_sub:
                strategic_node.add_child(ProbabilityNode("Positional Improvement", 1.0))

            # Normalize children
            tot_c = sum(c.probability for c in strategic_node.children)
            for c in strategic_node.children:
                c.probability = (c.probability / tot_c) * p_strategic

            root.add_child(strategic_node)

        # 3. Defensive Node & Sub-nodes
        if p_defensive > 0.05:
            defensive_node = ProbabilityNode("Defensive Intent", p_defensive)
            
            has_sub = False
            # Save piece
            opp_pseudo_before = generate_pseudo_moves(board, opp_color)
            attacked_before = set((om.to_row, om.to_col) for om in opp_pseudo_before)
            
            if (move.from_row, move.from_col) in attacked_before:
                defensive_node.add_child(ProbabilityNode("Evacuate Attacked Piece", 0.8))
                has_sub = True

            # King safety
            in_check_now = is_in_check(board, color)
            if in_check_now:
                defensive_node.add_child(ProbabilityNode("Escape Check", 0.9 if has_sub else 1.0))
                has_sub = True
                
            if piece_lower == "k" and abs(move.to_col - move.from_col) > 1:
                defensive_node.add_child(ProbabilityNode("Castle Protection", 0.8 if has_sub else 1.0))
                has_sub = True

            if not has_sub:
                defensive_node.add_child(ProbabilityNode("Defensive Fortification", 1.0))

            # Normalize children
            tot_c = sum(c.probability for c in defensive_node.children)
            for c in defensive_node.children:
                c.probability = (c.probability / tot_c) * p_defensive

            root.add_child(defensive_node)

        # 4. Endgame Node & Sub-nodes
        if p_endgame > 0.05:
            endgame_node = ProbabilityNode("Endgame Intent", p_endgame)
            
            has_sub = False
            if piece_lower == "p":
                endgame_node.add_child(ProbabilityNode("Pawn Push Promotion", 0.9))
                has_sub = True
            if piece_lower == "k":
                endgame_node.add_child(ProbabilityNode("King Activation", 0.8 if has_sub else 1.0))
                has_sub = True

            if not has_sub:
                endgame_node.add_child(ProbabilityNode("Endgame Material Conversion", 1.0))

            # Normalize children
            tot_c = sum(c.probability for c in endgame_node.children)
            for c in endgame_node.children:
                c.probability = (c.probability / tot_c) * p_endgame

            root.add_child(endgame_node)

        return root
