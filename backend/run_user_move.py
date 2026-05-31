from chess_board import Board, Move, parse_move
from cognitive_engine import ProbabilisticChessMind

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

# 1. Apply White's check move: d5f7
white_move = parse_move("d5f7")
board_after_white = board.apply_move(white_move)

# 2. Trigger cognitive engine for Black
mind = ProbabilisticChessMind()
res = mind.think(board_after_white)
if res:
    move, diagnostics = res
    print("CHOSEN_MOVE:", move)
    print("NARRATIVE:", diagnostics["reflection"]["narrative"])
    print("GOAL:", diagnostics["reflection"]["primary_goal"])
    print("CONCERN:", diagnostics["reflection"]["concern"])
    print("CONFIDENCE:", diagnostics["reflection"]["confidence"])
    print("UNCERTAINTIES:", diagnostics["reflection"]["uncertainties"])
    print("ALTS:", [alt.name for alt in diagnostics["alternatives"]])
    print("REJECTED:", [rej.name for rej in diagnostics["rejected"]])
    print("TREE:\n" + diagnostics["probability_tree"].print_tree())
else:
    print("NO MOVE FOUND")
