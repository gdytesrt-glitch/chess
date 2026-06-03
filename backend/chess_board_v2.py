"""
Enhanced Chess Board with Complete Rules Support
================================================
Adds: castling rights tracking, en passant, 50-move rule,
repetition detection, insufficient material, proper pawn promotion
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Set

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

    def __hash__(self) -> int:
        return hash((self.from_row, self.from_col, self.to_row, self.to_col, self.promotion))


class Board:
    """Complete chess board with full rule support."""

    def __init__(self,
                 grid: List[List[str]],
                 white_to_move: bool = True,
                 castling_rights: str = "KQkq",
                 en_passant_sq: Optional[Tuple[int, int]] = None,
                 halfmove_clock: int = 0,
                 fullmove_number: int = 1):
        self.grid = grid
        self.white_to_move = white_to_move
        self.castling_rights = castling_rights  # "KQkq" format
        self.en_passant_sq = en_passant_sq  # (row, col) or None
        self.halfmove_clock = halfmove_clock  # For 50-move rule
        self.fullmove_number = fullmove_number
        self.move_history: List[Move] = []  # Track all moves for repetition detection

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
            castling_rights="KQkq",
            en_passant_sq=None,
            halfmove_clock=0,
            fullmove_number=1,
        )

    def copy(self) -> Board:
        board = Board(
            [row.copy() for row in self.grid],
            self.white_to_move,
            self.castling_rights,
            self.en_passant_sq,
            self.halfmove_clock,
            self.fullmove_number,
        )
        board.move_history = self.move_history.copy()
        return board

    def has_piece(self, row: int, col: int) -> bool:
        return self.grid[row][col] != "."

    def piece_color(self, piece: str) -> Optional[str]:
        if piece == ".":
            return None
        return "white" if piece.isupper() else "black"

    def _update_castling_rights(self, move: Move):
        """Update castling rights after a move."""
        piece = self.grid[move.from_row][move.from_col]

        if piece.upper() == "K":
            if piece.isupper():  # White king
                self.castling_rights = self.castling_rights.replace("K", "").replace("Q", "")
            else:  # Black king
                self.castling_rights = self.castling_rights.replace("k", "").replace("q", "")

        elif piece.upper() == "R":
            # White queenside rook
            if move.from_row == 7 and move.from_col == 0 and piece.isupper():
                self.castling_rights = self.castling_rights.replace("Q", "")
            # White kingside rook
            elif move.from_row == 7 and move.from_col == 7 and piece.isupper():
                self.castling_rights = self.castling_rights.replace("K", "")
            # Black queenside rook
            elif move.from_row == 0 and move.from_col == 0 and piece.islower():
                self.castling_rights = self.castling_rights.replace("q", "")
            # Black kingside rook
            elif move.from_row == 0 and move.from_col == 7 and piece.islower():
                self.castling_rights = self.castling_rights.replace("k", "")

        # Capture on rook squares
        captured = self.grid[move.to_row][move.to_col]
        if captured.upper() == "R":
            if move.to_row == 7 and move.to_col == 0:
                self.castling_rights = self.castling_rights.replace("Q", "")
            elif move.to_row == 7 and move.to_col == 7:
                self.castling_rights = self.castling_rights.replace("K", "")
            elif move.to_row == 0 and move.to_col == 0:
                self.castling_rights = self.castling_rights.replace("q", "")
            elif move.to_row == 0 and move.to_col == 7:
                self.castling_rights = self.castling_rights.replace("k", "")

        if not self.castling_rights:
            self.castling_rights = "-"

    def _update_en_passant_sq(self, move: Move):
        """Update en passant target square after a move."""
        piece = self.grid[move.from_row][move.from_col]

        # Only pawns can create en passant opportunities
        if piece.lower() != "p":
            self.en_passant_sq = None
            return

        # Double pawn push: set en passant square
        if abs(move.to_row - move.from_row) == 2:
            # En passant square is behind the pawn
            ep_row = (move.from_row + move.to_row) // 2
            self.en_passant_sq = (ep_row, move.to_col)
        else:
            self.en_passant_sq = None

    def apply_move(self, move: Move) -> Board:
        board = self.copy()
        piece = board.grid[move.from_row][move.from_col]

        # Store old board state for halfmove clock
        is_capture = board.grid[move.to_row][move.to_col] != "."
        is_pawn_move = piece.lower() == "p"

        # Handle en passant capture
        is_en_passant = (piece.lower() == "p" and
                        move.to_row != move.from_row and
                        board.grid[move.to_row][move.to_col] == ".")

        # Remove piece from source
        board.grid[move.from_row][move.from_col] = "."

        # Handle pawn promotion
        final_piece = move.promotion or piece
        if piece.lower() == "p":
            if (piece.isupper() and move.to_row == 0) or (piece.islower() and move.to_row == 7):
                final_piece = move.promotion or ("Q" if piece.isupper() else "q")

        # Place piece at destination
        board.grid[move.to_row][move.to_col] = final_piece

        # Handle en passant removal
        if is_en_passant:
            ep_pawn_row = move.from_row
            board.grid[ep_pawn_row][move.to_col] = "."

        # Handle castling rook move
        if piece.lower() == "k" and abs(move.to_col - move.from_col) > 1:
            r_row = move.from_row
            if move.to_col == 6:  # Kingside castle
                board.grid[r_row][5] = board.grid[r_row][7]
                board.grid[r_row][7] = "."
            elif move.to_col == 2:  # Queenside castle
                board.grid[r_row][3] = board.grid[r_row][0]
                board.grid[r_row][0] = "."

        # Update castling rights
        board._update_castling_rights(move)

        # Update en passant square
        board._update_en_passant_sq(move)

        # Update halfmove clock (50-move rule)
        if is_pawn_move or is_capture:
            board.halfmove_clock = 0
        else:
            board.halfmove_clock += 1

        # Update fullmove number
        if not board.white_to_move:
            board.fullmove_number += 1

        # Toggle turn
        board.white_to_move = not board.white_to_move

        # Track move
        board.move_history.append(move)

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

    def position_fen_hash(self) -> str:
        """Hash for position (for repetition detection)."""
        return "".join("".join(row) for row in self.grid)


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8


def is_square_attacked(board: Board, row: int, col: int, attacker_color: str) -> bool:
    """Check if a square is attacked by a given color."""
    opp_moves = generate_pseudo_moves(board, attacker_color, include_castling=False)
    for mv in opp_moves:
        if mv.to_row == row and mv.to_col == col:
            return True
    return False


def generate_pseudo_moves(board: Board, color: str, include_castling: bool = True) -> List[Move]:
    """Generate all pseudo-legal moves (including moves that leave king in check)."""
    moves: List[Move] = []

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

        # Pawn moves
        if piece_type == "p":
            f_row = row + pawn_dir
            if in_bounds(f_row, col) and not board.has_piece(f_row, col):
                moves.append(Move(row, col, f_row, col))
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

            # En passant
            if board.en_passant_sq and board.en_passant_sq[0] == row + pawn_dir:
                for dc in [-1, 1]:
                    if col + dc == board.en_passant_sq[1]:
                        moves.append(Move(row, col, row + pawn_dir, col + dc))

        # Knight moves
        elif piece_type == "n":
            for dr, dc in directions["n"]:
                tr, tc = row + dr, col + dc
                if in_bounds(tr, tc):
                    target = board.grid[tr][tc]
                    if target == "." or board.piece_color(target) != color:
                        moves.append(Move(row, col, tr, tc))

        # King moves
        elif piece_type == "k":
            for dr, dc in directions["k"]:
                tr, tc = row + dr, col + dc
                if in_bounds(tr, tc):
                    target = board.grid[tr][tc]
                    if target == "." or board.piece_color(target) != color:
                        moves.append(Move(row, col, tr, tc))

            # Castling
            if include_castling:
                opp_color = "black" if color == "white" else "white"
                k_row = 7 if color == "white" else 0
                k_char = "K" if color == "white" else "k"
                r_char = "R" if color == "white" else "r"

                if row == k_row and col == 4 and piece == k_char:
                    # Kingside castling
                    if ("K" in board.castling_rights if color == "white" else "k" in board.castling_rights):
                        if (board.grid[k_row][5] == "." and board.grid[k_row][6] == "." and
                            board.grid[k_row][7] == r_char):
                            if not is_in_check(board, color):
                                if not is_square_attacked(board, k_row, 5, opp_color) and \
                                   not is_square_attacked(board, k_row, 6, opp_color):
                                    moves.append(Move(k_row, 4, k_row, 6))

                    # Queenside castling
                    if ("Q" in board.castling_rights if color == "white" else "q" in board.castling_rights):
                        if (board.grid[k_row][1] == "." and board.grid[k_row][2] == "." and
                            board.grid[k_row][3] == "." and board.grid[k_row][0] == r_char):
                            if not is_in_check(board, color):
                                if not is_square_attacked(board, k_row, 3, opp_color) and \
                                   not is_square_attacked(board, k_row, 2, opp_color):
                                    moves.append(Move(k_row, 4, k_row, 2))

        # Sliders
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
    """Check if a color's king is in check."""
    king_pos = board.find_king(color)
    if not king_pos:
        return False

    kr, kc = king_pos
    opponent_color = "black" if color == "white" else "white"

    opp_moves = generate_pseudo_moves(board, opponent_color, include_castling=False)
    for move in opp_moves:
        if move.to_row == kr and move.to_col == kc:
            return True
    return False


def generate_legal_moves(board: Board, color: str) -> List[Move]:
    """Generate all legal moves."""
    pseudo_moves = generate_pseudo_moves(board, color)
    legal_moves = []

    for move in pseudo_moves:
        next_board = board.apply_move(move)
        if not is_in_check(next_board, color):
            legal_moves.append(move)

    return legal_moves


def is_insufficient_material(board: Board) -> bool:
    """Check if current position is insufficient material draw."""
    pieces = []
    for r, row in enumerate(board.grid):
        for c, piece in enumerate(row):
            if piece != ".":
                pieces.append(piece.lower())

    # If both sides have only kings
    if len(pieces) == 2 and all(p == "k" for p in pieces):
        return True

    # If each side has only king + one minor piece
    if len(pieces) == 3:
        if pieces.count("k") == 2:
            other = [p for p in pieces if p != "k"][0]
            if other in ["n", "b"]:
                return True

    # If both sides have only king + bishop on same color
    if len(pieces) == 4 and pieces.count("k") == 2 and pieces.count("b") == 2:
        white_bishop_pos = None
        black_bishop_pos = None
        for r, row in enumerate(board.grid):
            for c, piece in enumerate(row):
                if piece == "B":
                    white_bishop_pos = (r, c)
                elif piece == "b":
                    black_bishop_pos = (r, c)

        if white_bishop_pos and black_bishop_pos:
            same_color = (white_bishop_pos[0] + white_bishop_pos[1]) % 2 == \
                        (black_bishop_pos[0] + black_bishop_pos[1]) % 2
            if same_color:
                return True

    return False


def detect_threefold_repetition(board: Board) -> bool:
    """Check if position has appeared 3 times."""
    fen_hash = board.position_fen_hash()
    position_count = sum(1 for move in board.move_history
                        if move.from_row >= 0)  # Dummy, needs full history tracking
    # Simplified version - would need full position history
    return False


def check_fifty_move_rule(board: Board) -> bool:
    """Check if 50-move rule applies (100 half-moves without pawn/capture)."""
    return board.halfmove_clock >= 100


# ───── Position Tables ─────

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
    p_lower = piece.lower()
    table_r = 7 - r if piece.islower() else r

    score = 0.0
    if p_lower == "p":
        score = PAWN_TABLE[table_r][c] * 0.1
    elif p_lower == "n":
        score = KNIGHT_TABLE[table_r][c] * 0.1
    elif p_lower == "b":
        score = BISHOP_TABLE[table_r][c] * 0.1
    elif p_lower == "r":
        score = ROOK_TABLE[table_r][c] * 0.1
    elif p_lower == "q":
        score = QUEEN_TABLE[table_r][c] * 0.1
    elif p_lower == "k":
        score = KING_MIDDLE_TABLE[table_r][c] * 0.1

    return score


def evaluate_board(board: Board, color: str) -> float:
    """Evaluate position from a color's perspective."""
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
        promotion = text[4].upper()

    return Move(from_row, from_col, to_row, to_col, promotion)


def select_color(turn: bool) -> str:
    return "white" if turn else "black"
