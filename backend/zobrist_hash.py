"""
Zobrist Hash for Transposition Tables
======================================
Replaces slow string-based hashing with 64-bit Zobrist hash for O(1) TT lookups
"""

import random

# Initialize Zobrist hash tables
random.seed(42)  # Deterministic for reproducibility

ZOBRIST_PIECES = {}  # [piece_type][square] -> random 64-bit number
ZOBRIST_SIDE = random.getrandbits(64)  # XOR if black to move
ZOBRIST_CASTLING = [random.getrandbits(64) for _ in range(16)]  # 4 bits of castling rights
ZOBRIST_EP = [random.getrandbits(64) for _ in range(8)]  # En passant file (0-7)

# Initialize piece table
for piece_char in "pnbrqkPNBRQK":
    ZOBRIST_PIECES[piece_char] = [random.getrandbits(64) for _ in range(64)]


def castling_rights_to_bits(castling_str: str) -> int:
    """Convert "KQkq" format to 4-bit integer."""
    bits = 0
    if "K" in castling_str:
        bits |= 1
    if "Q" in castling_str:
        bits |= 2
    if "k" in castling_str:
        bits |= 4
    if "q" in castling_str:
        bits |= 8
    return bits


def compute_zobrist_hash(board) -> int:
    """Compute 64-bit Zobrist hash for a board position."""
    h = 0

    # Piece placement
    for r in range(8):
        for c in range(8):
            piece = board.grid[r][c]
            if piece != ".":
                sq = r * 8 + c
                h ^= ZOBRIST_PIECES[piece][sq]

    # Side to move
    if not board.white_to_move:
        h ^= ZOBRIST_SIDE

    # Castling rights
    castling_bits = castling_rights_to_bits(board.castling_rights)
    h ^= ZOBRIST_CASTLING[castling_bits]

    # En passant
    if board.en_passant_sq:
        ep_file = board.en_passant_sq[1]
        h ^= ZOBRIST_EP[ep_file]

    return h & ((1 << 64) - 1)  # Ensure 64-bit
