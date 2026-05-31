from __future__ import annotations
from typing import Dict, Any, List
from chess_board import Board, generate_pseudo_moves, is_in_check, generate_legal_moves

class AttentionSystem:
    def __init__(self):
        self.last_profile: Dict[str, float] = {
            "tactical": 0.25,
            "strategic": 0.50,
            "defensive": 0.20,
            "endgame": 0.05
        }

    def calculate_attention(self, board: Board, color: str) -> Dict[str, float]:
        """
        Dynamically calculates the cognitive focus profile based on board state.
        Returns a normalized profile with keys: 'tactical', 'strategic', 'defensive', 'endgame'.
        """
        opp_color = "black" if color == "white" else "white"
        
        # 1. Threat Score: How many pieces are under threat or hanging?
        opp_pseudo_moves = generate_pseudo_moves(board, opp_color)
        my_threatened_values = 0.0
        hanging_count = 0
        
        piece_values = {"p": 1.0, "n": 3.0, "b": 3.2, "r": 5.0, "q": 9.0, "k": 20.0}
        
        # Track target squares attacked by opponent
        attacked_squares = set()
        for mv in opp_pseudo_moves:
            attacked_squares.add((mv.to_row, mv.to_col))
            
        for r, row in enumerate(board.grid):
            for c, sq in enumerate(row):
                if sq != "." and board.piece_color(sq) == color:
                    if (r, c) in attacked_squares:
                        val = piece_values[sq.lower()]
                        my_threatened_values += val
                        hanging_count += 1
                        
        threat_score = min(my_threatened_values / 20.0, 1.0) # Cap at 1.0

        # 2. King Safety: Check if king is exposed or currently checked
        king_safety = 1.0
        in_check = is_in_check(board, color)
        if in_check:
            king_safety -= 0.5
            
        # Check files in front of king
        king_pos = board.find_king(color)
        if king_pos:
            kr, kc = king_pos
            # Exposure check: if there is no pawn in the same column or adjacent column
            pawn_found = False
            pawn_char = "P" if color == "white" else "p"
            for offset in [-1, 0, 1]:
                check_c = kc + offset
                if 0 <= check_c < 8:
                    for check_r in range(max(0, kr-2), min(8, kr+3)):
                        if board.grid[check_r][check_c] == pawn_char:
                            pawn_found = True
                            break
            if not pawn_found:
                king_safety -= 0.3 # Exposed king!
                
        king_safety = max(0.1, king_safety)
        defense_needed = 1.0 - king_safety

        # 3. Material Imbalance: Count active major pieces to determine if endgame is reached
        my_pieces = board.list_pieces(color)
        opp_pieces = board.list_pieces(opp_color)
        
        def material_score(pieces: List[Any]) -> float:
            tot = 0.0
            for r, c, p in pieces:
                if p.lower() not in ["p", "k"]:
                    tot += piece_values[p.lower()]
            return tot
            
        my_material = material_score(my_pieces)
        opp_material = material_score(opp_pieces)
        total_major_material = my_material + opp_material
        
        # If total major piece material is less than 15, we are definitely entering/in the endgame
        endgame_trigger = 0.0
        if total_major_material < 16.0:
            endgame_trigger = (16.0 - total_major_material) / 16.0 # Scale up to 1.0

        # 4. Center Pressure
        center_squares = [(3,3), (3,4), (4,3), (4,4)]
        opp_center_control = 0
        for sq_r, sq_c in center_squares:
            if (sq_r, sq_c) in attacked_squares:
                opp_center_control += 1
            if board.grid[sq_r][sq_c] != "." and board.piece_color(board.grid[sq_r][sq_c]) == opp_color:
                opp_center_control += 2
                
        center_pressure = min(opp_center_control / 6.0, 1.0)

        # 5. Piece Activity: Friendly piece mobility
        my_legal = generate_legal_moves(board, color)
        activity_score = min(len(my_legal) / 30.0, 1.0)
        low_activity_need = 1.0 - activity_score

        # Combine inputs to compute dynamic weights
        # Base weights
        tactical = 0.2 + 0.6 * threat_score
        defensive = 0.15 + 0.5 * defense_needed + 0.1 * center_pressure
        strategic = 0.35 + 0.3 * low_activity_need - 0.2 * threat_score
        endgame = 0.05 + 0.6 * endgame_trigger
        
        # Enforce sanity limits
        tactical = max(0.1, tactical)
        defensive = max(0.1, defensive)
        strategic = max(0.1, strategic)
        endgame = max(0.02, endgame)
        
        # Normalize weights so they sum to 1.0
        total = tactical + defensive + strategic + endgame
        profile = {
            "tactical": round(tactical / total, 3),
            "strategic": round(strategic / total, 3),
            "defensive": round(defensive / total, 3),
            "endgame": round(endgame / total, 3)
        }
        
        # Re-verify normalize due to float rounding
        total = sum(profile.values())
        if total != 1.0:
            # Adjust the biggest value slightly
            key = max(profile, key=profile.get)
            profile[key] = round(profile[key] + (1.0 - total), 3)

        self.last_profile = profile.copy()
        return profile
