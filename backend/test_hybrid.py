import sys, time
sys.path.insert(0, '.')
from chess_board import Board, parse_move
from cognitive_engine import ProbabilisticChessMind

board = Board.initial()
board = board.apply_move(parse_move('e2e4'))
board = board.apply_move(parse_move('e7e5'))
board = board.apply_move(parse_move('g1f3'))

mind = ProbabilisticChessMind()
t0 = time.time()
res = mind.think(board)
elapsed = time.time() - t0

if res:
    move, diag = res
    sc = diag['subconscious']
    hybrid_top = sorted(diag['hybrid_scores'].items(), key=lambda x: -x[1])[:3]
    pv = " > ".join(sc['principal_variation'][:5])
    print("CHOSEN MOVE   :", move)
    print("HYBRID TOP 3  :", hybrid_top)
    print("DEPTH REACHED :", sc['depth_reached'], " (boost +%d)" % diag['depth_boost'])
    print("NODES EVAL    :", f"{sc['nodes_evaluated']:,}")
    print("TT HITS       :", f"{sc['tt_hits']:,}")
    print("PV            :", pv)
    print("UNCERTAINTY   :", f"{diag['uncertainty']*100:.1f}%")
    print("MEMORY BONUS  :", f"{diag['memory_bonus']*100:.1f}%")
    print("CONFIDENCE    :", diag['reflection']['confidence'])
    print("TIME          :", f"{elapsed:.2f}s")
else:
    print("NO MOVE FOUND")
