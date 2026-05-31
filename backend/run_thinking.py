from chess_board import Board, Move, parse_move
from cognitive_engine import ProbabilisticChessMind

# Setup game state
board = Board.initial()

# 1. e4 e5
board = board.apply_move(parse_move("e2e4"))
board = board.apply_move(parse_move("e7e5"))
# 2. Nf3 Nc6
board = board.apply_move(parse_move("g1f3"))
board = board.apply_move(parse_move("b8c6"))
# 3. Bb5 Nf6
board = board.apply_move(parse_move("f1b5"))
board = board.apply_move(parse_move("g8f6"))
# 4. O-O
board = board.apply_move(parse_move("e1g1"))

# Trigger mind
mind = ProbabilisticChessMind()
res = mind.think(board)
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
