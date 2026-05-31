from __future__ import annotations
from typing import Dict, List, Tuple, Optional, Any
from chess_board import Board, Move, evaluate_board, is_in_check, generate_pseudo_moves

class ConceptNode:
    def __init__(self, name: str, category: str, activation: float = 0.0):
        self.name = name
        self.category = category
        self.activation = activation

    def __repr__(self) -> str:
        return f"Node({self.name}, cat={self.category}, act={self.activation:.2f})"


class KnowledgeGraph:
    def __init__(self):
        self.nodes: Dict[str, ConceptNode] = {}
        # adjacency list representation: source -> target -> (weight, relation_type)
        self.edges: Dict[str, Dict[str, Tuple[float, str]]] = {}

    def add_node(self, name: str, category: str, activation: float = 0.0):
        if name not in self.nodes:
            self.nodes[name] = ConceptNode(name, category, activation)

    def add_edge(self, source: str, target: str, weight: float, relation_type: str = "connects"):
        self.add_node(source, "inferred")
        self.add_node(target, "inferred")
        
        if source not in self.edges:
            self.edges[source] = {}
        self.edges[source][target] = (weight, relation_type)

    def set_activation(self, name: str, activation: float):
        if name in self.nodes:
            self.nodes[name].activation = activation

    def spread_activation(self, iterations: int = 1):
        """Simulates spreading activation through the knowledge graph."""
        for _ in range(iterations):
            new_activations = {name: node.activation for name, node in self.nodes.items()}
            for source, targets in self.edges.items():
                if source not in self.nodes:
                    continue
                source_act = self.nodes[source].activation
                if source_act > 0.1:
                    for target, (weight, _) in targets.items():
                        if target in new_activations:
                            # Propagate activation proportional to edge weight
                            new_activations[target] = min(1.0, new_activations[target] + source_act * weight * 0.25)
            for name, act in new_activations.items():
                self.nodes[name].activation = act

    def query_active_concepts(self, threshold: float = 0.3) -> List[Tuple[str, float]]:
        """Returns nodes with activation above a certain threshold, sorted descending."""
        active = [(name, node.activation) for name, node in self.nodes.items() if node.activation >= threshold]
        return sorted(active, key=lambda x: x[1], reverse=True)


class MicroMind:
    def __init__(self, name: str, goals: List[str]):
        self.name = name
        self.goals = goals
        self.attention_focus: float = 0.25
        self.activated_motifs: List[str] = []

    def evaluate_moves(self, board: Board, moves: List[Move], color: str, graph: KnowledgeGraph) -> Dict[str, float]:
        """Evaluates and scores a set of candidate moves. Returns Dict[str(move), score]."""
        raise NotImplementedError


class TacticalMind(MicroMind):
    def __init__(self):
        super().__init__("TacticalMind", ["Capture pieces", "Checkmate opponent", "Create double attacks"])

    def evaluate_moves(self, board: Board, moves: List[Move], color: str, graph: KnowledgeGraph) -> Dict[str, float]:
        scores = {}
        opp_color = "black" if color == "white" else "white"
        
        piece_values = {"p": 1.0, "n": 3.0, "b": 3.2, "r": 5.0, "q": 9.0, "k": 200.0}
        
        # Identify weak opponent pieces and checks
        in_check_now = is_in_check(board, opp_color)
        if in_check_now:
            graph.add_node("Opponent King Exposed", "tactical", 0.8)
            graph.add_edge("Opponent King Exposed", "Checks & Threats", 0.9, "enables")

        for mv in moves:
            score = 0.0
            mv_str = str(mv)
            
            # Simulate move
            child = board.apply_move(mv)
            
            # Is check?
            if is_in_check(child, opp_color):
                score += 1.5
                graph.add_node(f"Check {mv_str}", "tactical", 0.9)
                graph.add_edge(mv_str, f"Check {mv_str}", 0.9, "causes")
                graph.add_edge(f"Check {mv_str}", "Tactical pressure", 0.8, "increases")
                
            # Is capture?
            from_piece = board.grid[mv.from_row][mv.from_col]
            target_piece = board.grid[mv.to_row][mv.to_col]
            
            if target_piece != ".":
                val_gain = piece_values[target_piece.lower()]
                val_loss = piece_values[from_piece.lower()]
                
                # Material gain calculation
                net_gain = val_gain
                
                # Basic defender check: is target square defended by opponent?
                opp_pseudo = generate_pseudo_moves(child, opp_color)
                is_defended = any(om.to_row == mv.to_row and om.to_col == mv.to_col for om in opp_pseudo)
                if is_defended:
                    net_gain -= val_loss
                    
                score += max(0.5, net_gain + 1.0)
                graph.add_node(f"Capture {target_piece} on {mv_str[2:4]}", "tactical", 0.85)
                graph.add_edge(mv_str, f"Capture {target_piece} on {mv_str[2:4]}", 0.9, "executes")
                graph.add_edge(f"Capture {target_piece} on {mv_str[2:4]}", "Material advantage", 0.7, "supports")

            # Check if this move hangs our piece
            opp_pseudo_after = generate_pseudo_moves(child, opp_color)
            is_attacked = any(om.to_row == mv.to_row and om.to_col == mv.to_col for om in opp_pseudo_after)
            if is_attacked:
                # Basic defender check
                friendly_pseudo = generate_pseudo_moves(child, color)
                is_defended = any(fm.to_row == mv.to_row and fm.to_col == mv.to_col for fm in friendly_pseudo)
                if not is_defended:
                    score -= piece_values[from_piece.lower()]
                    graph.add_node(f"Hanging piece on {mv_str[2:4]}", "tactical", 0.9)
                    graph.add_edge(mv_str, f"Hanging piece on {mv_str[2:4]}", 0.95, "results_in")

            scores[mv_str] = score
            
        return scores


class StrategicMind(MicroMind):
    def __init__(self):
        super().__init__("StrategicMind", ["Control the center", "Develop pieces", "Open files for rooks"])

    def evaluate_moves(self, board: Board, moves: List[Move], color: str, graph: KnowledgeGraph) -> Dict[str, float]:
        scores = {}
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        
        for mv in moves:
            score = 0.0
            mv_str = str(mv)
            piece = board.grid[mv.from_row][mv.from_col]
            piece_lower = piece.lower()
            
            # 1. Piece Development
            # Moving a minor piece (knight/bishop) from back rank is strategic development
            back_rank = 7 if color == "white" else 0
            if piece_lower in ["n", "b"] and mv.from_row == back_rank:
                score += 1.0
                graph.add_node("Piece Development", "strategic", 0.75)
                graph.add_edge(mv_str, "Piece Development", 0.85, "causes")
                
            # 2. Center Control
            # Moving to center or attacking the center
            if (mv.to_row, mv.to_col) in center_squares:
                score += 1.2
                graph.add_node("Center Occupation", "strategic", 0.8)
                graph.add_edge(mv_str, "Center Occupation", 0.9, "achieves")
                
            # Castling preparation / King safety preparation
            if piece_lower == "k" and abs(mv.to_col - mv.from_col) > 1:
                score += 1.5
                graph.add_node("Castling King", "strategic", 0.9)
                graph.add_edge(mv_str, "Castling King", 0.95, "executes")
                graph.add_edge("Castling King", "King Safety", 0.8, "secures")
                
            # Rook on open file
            if piece_lower == "r":
                # Check if file has no pawns
                file_has_pawn = False
                for r in range(8):
                    if board.grid[r][mv.to_col].lower() == "p":
                        file_has_pawn = True
                        break
                if not file_has_pawn:
                    score += 0.8
                    graph.add_node("Rook on Open File", "strategic", 0.7)
                    graph.add_edge(mv_str, "Rook on Open File", 0.8, "achieves")

            # Positional Tables Difference
            child = board.apply_move(mv)
            # Evaluate board scores from positional tables
            base_score = evaluate_board(child, color) - evaluate_board(board, color)
            # Add positional table difference to strategic score
            score += max(-2.0, min(base_score, 2.0))

            scores[mv_str] = score
            
        return scores


class DefensiveMind(MicroMind):
    def __init__(self):
        super().__init__("DefensiveMind", ["Protect the King", "Defend hanging pieces", "Blockade attacks"])

    def evaluate_moves(self, board: Board, moves: List[Move], color: str, graph: KnowledgeGraph) -> Dict[str, float]:
        scores = {}
        opp_color = "black" if color == "white" else "white"
        
        piece_values = {"p": 1.0, "n": 3.0, "b": 3.2, "r": 5.0, "q": 9.0, "k": 200.0}
        
        # Calculate attacked squares by opponent BEFORE making our move
        opp_pseudo_before = generate_pseudo_moves(board, opp_color)
        attacked_squares_before = set((om.to_row, om.to_col) for om in opp_pseudo_before)
        
        # Find which of our valuable pieces are currently attacked
        threatened_pieces = []
        for r, row in enumerate(board.grid):
            for c, sq in enumerate(row):
                if sq != "." and board.piece_color(sq) == color:
                    if (r, c) in attacked_squares_before:
                        threatened_pieces.append((r, c, sq))
                        
        in_check_now = is_in_check(board, color)
        if in_check_now:
            graph.add_node("King in Check", "defensive", 0.95)
            graph.add_edge("King in Check", "Immediate defense", 0.9, "demands")

        for mv in moves:
            score = 0.0
            mv_str = str(mv)
            piece = board.grid[mv.from_row][mv.from_col]
            
            # If in check, moves that get us out of check are vital (all legal moves do this, but evaluate safety)
            if in_check_now:
                # Give a high defense bonus to getting out of check safely
                child = board.apply_move(mv)
                if not is_in_check(child, color):
                    score += 2.0
                    
            # 1. Defending attacked pieces: Does this move move an attacked piece to safety?
            is_moving_attacked = any(tp[0] == mv.from_row and tp[1] == mv.from_col for tp in threatened_pieces)
            if is_moving_attacked:
                # Is the target square safe?
                child = board.apply_move(mv)
                opp_pseudo_after = generate_pseudo_moves(child, opp_color)
                is_safe_after = not any(om.to_row == mv.to_row and om.to_col == mv.to_col for om in opp_pseudo_after)
                if is_safe_after:
                    score += piece_values[piece.lower()] # High value for saving piece!
                    graph.add_node(f"Save {piece} from attack", "defensive", 0.85)
                    graph.add_edge(mv_str, f"Save {piece} from attack", 0.9, "achieves")
                    
            # 2. Guarding attacked squares / blocking lines
            # If the destination blockades or defends a threatened piece
            for tr_r, tr_c, tr_p in threatened_pieces:
                if tr_r == mv.to_row and tr_c == mv.to_col:
                    continue # handled above
                # Does moving there defend the target?
                child = board.apply_move(mv)
                friendly_pseudo = generate_pseudo_moves(child, color)
                is_defended = any(fm.to_row == tr_r and fm.to_col == tr_c for fm in friendly_pseudo)
                if is_defended:
                    score += piece_values[tr_p.lower()] * 0.5
                    graph.add_node(f"Defend {tr_p} on {tr_r},{tr_c}", "defensive", 0.8)
                    graph.add_edge(mv_str, f"Defend {tr_p} on {tr_r},{tr_c}", 0.85, "implements")

            scores[mv_str] = score
            
        return scores


class EndgameMind(MicroMind):
    def __init__(self):
        super().__init__("EndgameMind", ["Push passed pawns", "Activate the King", "Promote pawns"])

    def evaluate_moves(self, board: Board, moves: List[Move], color: str, graph: KnowledgeGraph) -> Dict[str, float]:
        scores = {}
        
        for mv in moves:
            score = 0.0
            mv_str = str(mv)
            piece = board.grid[mv.from_row][mv.from_col]
            piece_lower = piece.lower()
            
            # 1. Pawn Push & Promotion
            if piece_lower == "p":
                # Pushing pawn forward
                steps_remaining = mv.to_row if color == "white" else (7 - mv.to_row)
                push_bonus = 2.0 - (steps_remaining * 0.25)
                score += push_bonus
                graph.add_node("Push Passed Pawn", "endgame", 0.8)
                graph.add_edge(mv_str, "Push Passed Pawn", 0.85, "furthers")
                
                # High score if promoting
                if (color == "white" and mv.to_row == 0) or (color == "black" and mv.to_row == 7):
                    score += 5.0
                    graph.add_node("Pawn Promotion", "endgame", 0.95)
                    graph.add_edge(mv_str, "Pawn Promotion", 0.95, "causes")

            # 2. King Activation
            # Moving king towards center
            if piece_lower == "k":
                center_r, center_c = 3.5, 3.5
                dist_before = abs(mv.from_row - center_r) + abs(mv.from_col - center_c)
                dist_after = abs(mv.to_row - center_r) + abs(mv.to_col - center_c)
                if dist_after < dist_before:
                    score += 1.0
                    graph.add_node("Activate King", "endgame", 0.75)
                    graph.add_edge(mv_str, "Activate King", 0.85, "achieves")

            scores[mv_str] = score
            
        return scores
