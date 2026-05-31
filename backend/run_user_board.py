from chess_board import Board, Move, generate_legal_moves, parse_move

# Reconstruct board state
grid = [
    [".", ".", ".", ".", ".", ".", ".", "."],  # Row 8
    [".", ".", "p", ".", ".", ".", "k", "p"],  # Row 7 (c7, g7, h7)
    ["p", ".", ".", "B", ".", ".", ".", "."],  # Row 6 (a6, d6 - White Bishop!)
    [".", ".", "p", "Q", ".", "B", ".", "."],  # Row 5 (c5, d5 - White Queen!, f5 - White Bishop!)
    [".", ".", ".", ".", ".", ".", ".", "."],  # Row 4
    ["P", ".", ".", ".", ".", ".", ".", "."],  # Row 3 (a3)
    [".", "P", ".", ".", ".", "P", "P", "P"],  # Row 2 (b2, f2, g2, h2)
    ["R", ".", ".", ".", ".", ".", "K", "."]   # Row 1 (a1, g1)
]

board = Board(grid, white_to_move=True)

# List all legal moves for White
legal_white = generate_legal_moves(board, "white")
print("LEGAL WHITE MOVES:")
for m in legal_white:
    print(str(m))
