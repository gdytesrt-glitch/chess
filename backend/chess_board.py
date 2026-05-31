from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class Move:
    from_row: int
    from_col: int
    to_row: int
    to_col: int
    promotion: Optional[str] = None

    def __str__(self) -> str:
        cols = "abcdefgh"
        move = f"{cols[self.from_col]}{8-self.from_row}{cols[self.to_col]}{8-self.to_row}"
        if self.promotion:
            move += self.promotion.lower()
        return move

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Move):
            return False
        return (self.from_row == other.from_row and 
                self.from_col == other.from_col and 
                self.to_row == other.to_row and 
                self.to_col == other.to_col and 
                self.promotion == other.promotion)


class Board:
    def __init__(self, grid: List[List[str]], white_to_move: bool = True):
        self.grid = grid
        self.white_to_move = white_to_move

    @classmethod
    def initial(cls) -> Board:
        return cls(
            [
                list("rnbqkbnr"),
                list("pppppppp"),
                list("........"),
                list("........"),
                list("........"),
                list("........"),
                list("PPPPPPPP"),
                list("RNBQKBNR"),
            ],
            white_to_move=True,
        )

    def copy(self) -> Board:
        return Board([row.copy() for row in self.grid], self.white_to_move)

    def has_piece(self, row: int, col: int) -> bool:
        return self.grid[row][col] != "."

    def piece_color(self, piece: str) -> Optional[str]:
        if piece == ".":
            return None
        return "white" if piece.isupper() else "black"

    def apply_move(self, move: Move) -> Board:
        board = self.copy()
        piece = board.grid[move.from_row][move.from_col]
        board.grid[move.from_row][move.from_col] = "."
        
        # Auto-promote to Queen if pawn reaches the end
        final_piece = move.promotion or piece
        if piece.lower() == "p":
            if (piece.isupper() and move.to_row == 0) or (not piece.isupper() and move.to_row == 7):
                final_piece = "Q" if piece.isupper() else "q"

        board.grid[move.to_row][move.to_col] = final_piece
        
        # Move Rook during Castling
        if piece.lower() == "k" and abs(move.to_col - move.from_col) > 1:
            r_row = move.from_row
            # Kingside castle
            if move.to_col == 6:
                board.grid[r_row][5] = board.grid[r_row][7]
                board.grid[r_row][7] = "."
            # Queenside castle
            elif move.to_col == 2:
                board.grid[r_row][3] = board.grid[r_row][0]
                board.grid[r_row][0] = "."

        board.white_to_move = not board.white_to_move
        return board


    def list_pieces(self, color: str) -> List[Tuple[int, int, str]]:
        pieces = []
        for r, row in enumerate(self.grid):
            for c, square in enumerate(row):
                if square != "." and self.piece_color(square) == color:
                    pieces.append((r, c, square))
        return pieces

    def find_king(self, color: str) -> Optional[Tuple[int, int]]:
        king_char = "K" if color == "white" else "k"
        for r, row in enumerate(self.grid):
            for c, square in enumerate(row):
                if square == king_char:
                    return r, c
        return None


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8


def is_square_attacked(board: Board, row: int, col: int, attacker_color: str) -> bool:
    opp_moves = generate_pseudo_moves(board, attacker_color, include_castling=False)
    for mv in opp_moves:
        if mv.to_row == row and mv.to_col == col:
            return True
    return False


def generate_pseudo_moves(board: Board, color: str, include_castling: bool = True) -> List[Move]:
    moves: List[Move] = []
    
    # Directions for different pieces
    # Pawns: move directions are different for White (-1) vs Black (+1)
    pawn_dir = -1 if color == "white" else 1
    pawn_start_row = 6 if color == "white" else 1
    
    directions = {
        "n": [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
        "k": [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
        "b": [(-1, -1), (-1, 1), (1, -1), (1, 1)],
        "r": [(-1, 0), (1, 0), (0, -1), (0, 1)],
        "q": [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    }

    for row, col, piece in board.list_pieces(color):
        piece_type = piece.lower()
        
        # 1. Pawn Moves
        if piece_type == "p":
            # 1 step forward
            f_row = row + pawn_dir
            if in_bounds(f_row, col) and not board.has_piece(f_row, col):
                moves.append(Move(row, col, f_row, col))
                # 2 steps forward from initial rank
                double_row = row + 2 * pawn_dir
                if row == pawn_start_row and not board.has_piece(double_row, col):
                    moves.append(Move(row, col, double_row, col))
            
            # Diagonal captures
            for dc in [-1, 1]:
                c_row, c_col = row + pawn_dir, col + dc
                if in_bounds(c_row, c_col) and board.has_piece(c_row, c_col):
                    target_piece = board.grid[c_row][c_col]
                    if board.piece_color(target_piece) != color:
                        moves.append(Move(row, col, c_row, c_col))
                        
        # 2. Knight Moves
        elif piece_type == "n":
            for dr, dc in directions["n"]:
                tr, tc = row + dr, col + dc
                if in_bounds(tr, tc):
                    target = board.grid[tr][tc]
                    if target == "." or board.piece_color(target) != color:
                        moves.append(Move(row, col, tr, tc))

        # 3. King Moves
        elif piece_type == "k":
            for dr, dc in directions["k"]:
                tr, tc = row + dr, col + dc
                if in_bounds(tr, tc):
                    target = board.grid[tr][tc]
                    if target == "." or board.piece_color(target) != color:
                        moves.append(Move(row, col, tr, tc))
            
            # Castling moves
            if include_castling:
                opp_color = "black" if color == "white" else "white"
                k_row = 7 if color == "white" else 0
                k_char = "K" if color == "white" else "k"
                r_char = "R" if color == "white" else "r"
                
                # Verify King position
                if row == k_row and col == 4 and piece == k_char:
                    # Kingside Castling (O-O)
                    if board.grid[k_row][7] == r_char:
                        if board.grid[k_row][5] == "." and board.grid[k_row][6] == ".":
                            if not is_in_check(board, color):
                                if not is_square_attacked(board, k_row, 5, opp_color) and not is_square_attacked(board, k_row, 6, opp_color):
                                    moves.append(Move(k_row, 4, k_row, 6))
                                    
                    # Queenside Castling (O-O-O)
                    if board.grid[k_row][0] == r_char:
                        if board.grid[k_row][1] == "." and board.grid[k_row][2] == "." and board.grid[k_row][3] == ".":
                            if not is_in_check(board, color):
                                if not is_square_attacked(board, k_row, 3, opp_color) and not is_square_attacked(board, k_row, 2, opp_color):
                                    moves.append(Move(k_row, 4, k_row, 2))

        # 4. Sliders (Bishop, Rook, Queen)
        elif piece_type in ["b", "r", "q"]:
            dirs = directions[piece_type]
            for dr, dc in dirs:
                dist = 1
                while True:
                    tr, tc = row + dr * dist, col + dc * dist
                    if not in_bounds(tr, tc):
                        break
                    target = board.grid[tr][tc]
                    if target == ".":
                        moves.append(Move(row, col, tr, tc))
                    else:
                        if board.piece_color(target) != color:
                            moves.append(Move(row, col, tr, tc))
                        break
                    dist += 1
    return moves


def is_in_check(board: Board, color: str) -> bool:
    king_pos = board.find_king(color)
    if not king_pos:
        return False
    
    kr, kc = king_pos
    opponent_color = "black" if color == "white" else "white"
    
    # Generate all pseudo moves for opponent and see if any targets king_pos
    opp_moves = generate_pseudo_moves(board, opponent_color, include_castling=False)
    for move in opp_moves:
        if move.to_row == kr and move.to_col == kc:
            return True
    return False



def generate_legal_moves(board: Board, color: str) -> List[Move]:
    pseudo_moves = generate_pseudo_moves(board, color)
    legal_moves = []
    
    for move in pseudo_moves:
        # Check if the move resolves/doesn't cause check
        next_board = board.apply_move(move)
        # Note: apply_move switches the turn, so we check check on the player who just moved
        if not is_in_check(next_board, color):
            legal_moves.append(move)
            
    return legal_moves


# Dynamic Evaluation Position Tables (Relative to White)
# Flip rows for Black evaluation
PAWN_TABLE = [
    [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
    [5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0],
    [1.0,  1.0,  2.0,  3.0,  3.0,  2.0,  1.0,  1.0],
    [0.5,  0.5,  1.0,  2.5,  2.5,  1.0,  0.5,  0.5],
    [0.0,  0.0,  0.0,  2.0,  2.0,  0.0,  0.0,  0.0],
    [0.5, -0.5, -1.0,  0.0,  0.0, -1.0, -0.5,  0.5],
    [0.5,  1.0, 1.0,  -2.0, -2.0,  1.0,  1.0,  0.5],
    [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0]
]

KNIGHT_TABLE = [
    [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0],
    [-4.0, -2.0,  0.0,  0.0,  0.0,  0.0, -2.0, -4.0],
    [-3.0,  0.0,  1.0,  1.5,  1.5,  1.0,  0.0, -3.0],
    [-3.0,  0.5,  1.5,  2.0,  2.0,  1.5,  0.5, -3.0],
    [-3.0,  0.0,  1.5,  2.0,  2.0,  1.5,  0.0, -3.0],
    [-3.0,  0.5,  1.0,  1.5,  1.5,  1.0,  0.5, -3.0],
    [-4.0, -2.0,  0.0,  0.5,  0.5,  0.0, -2.0, -4.0],
    [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0]
]

BISHOP_TABLE = [
    [-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0],
    [-1.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -1.0],
    [-1.0,  0.0,  0.5,  1.0,  1.0,  0.5,  0.0, -1.0],
    [-1.0,  0.5,  0.5,  1.0,  1.0,  0.5,  0.5, -1.0],
    [-1.0,  0.0,  1.0,  1.0,  1.0,  1.0,  0.0, -1.0],
    [-1.0,  1.0,  1.0,  1.0,  1.0,  1.0,  1.0, -1.0],
    [-1.0,  0.5,  0.0,  0.0,  0.0,  0.0,  0.5, -1.0],
    [-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0]
]

ROOK_TABLE = [
    [ 0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
    [ 0.5,  1.0,  1.0,  1.0,  1.0,  1.0,  1.0,  0.5],
    [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
    [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
    [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
    [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
    [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
    [ 0.0,  0.0,  0.0,  0.5,  0.5,  0.0,  0.0,  0.0]
]

QUEEN_TABLE = [
    [-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0],
    [-1.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -1.0],
    [-1.0,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -1.0],
    [-0.5,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -0.5],
    [ 0.0,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -0.5],
    [-1.0,  0.5,  0.5,  0.5,  0.5,  0.5,  0.0, -1.0],
    [-1.0,  0.0,  0.5,  0.0,  0.0,  0.5,  0.0, -1.0],
    [-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0]
]

KING_MIDDLE_TABLE = [
    [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
    [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
    [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
    [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
    [-2.0, -3.0, -3.0, -4.0, -4.0, -3.0, -3.0, -2.0],
    [-1.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -1.0],
    [ 2.0,  2.0,  0.0,  0.0,  0.0,  0.0,  2.0,  2.0],
    [ 2.0,  3.0,  1.0,  0.0,  0.0,  1.0,  3.0,  2.0]
]

def get_piece_square_score(piece: str, r: int, c: int) -> float:
    # Get raw score from White's perspective
    p_lower = piece.lower()
    
    # If Black, flip the row for relative table index
    table_r = 7 - r if piece.islower() else r
    table_c = c
    
    score = 0.0
    if p_lower == "p":
        score = PAWN_TABLE[table_r][table_c] * 0.1
    elif p_lower == "n":
        score = KNIGHT_TABLE[table_r][table_c] * 0.1
    elif p_lower == "b":
        score = BISHOP_TABLE[table_r][table_c] * 0.1
    elif p_lower == "r":
        score = ROOK_TABLE[table_r][table_c] * 0.1
    elif p_lower == "q":
        score = QUEEN_TABLE[table_r][table_c] * 0.1
    elif p_lower == "k":
        score = KING_MIDDLE_TABLE[table_r][table_c] * 0.1
        
    return score


def evaluate_board(board: Board, color: str) -> float:
    values = {
        "p": 1.0,
        "n": 3.0,
        "b": 3.2,
        "r": 5.0,
        "q": 9.0,
        "k": 200.0,
    }
    score = 0.0
    for r, row in enumerate(board.grid):
        for c, square in enumerate(row):
            if square == ".":
                continue
            
            p_val = values[square.lower()]
            p_sq = get_piece_square_score(square, r, c)
            
            total_val = p_val + p_sq
            
            # Check color match
            if square.isupper() == (color == "white"):
                score += total_val
            else:
                score -= total_val
    return score


def parse_move(text: str) -> Optional[Move]:
    cols = "abcdefgh"
    text = text.strip().lower()
    if len(text) < 4:
        return None
    try:
        from_col = cols.index(text[0])
        from_row = 8 - int(text[1])
        to_col = cols.index(text[2])
        to_row = 8 - int(text[3])
    except ValueError:
        return None
    
    promotion = None
    if len(text) == 5:
        promotion = text[4]
        
    return Move(from_row, from_col, to_row, to_col, promotion)


def select_color(turn: bool) -> str:
    return "white" if turn else "black"

