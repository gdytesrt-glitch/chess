"""
Tactical Test Suite - Validates search engine correctness
Tests ability to find checkmates, captures, forks, pins
"""

from chess_board import Board, generate_legal_moves
from subconscious_calculator import SubconsciousCalculator
import time

TACTICAL_PUZZLES = [
    {
        "name": "Mate in 1 - Back Rank",
        "grid": [
            list("....rk.."),
            list("ppp..ppp"),
            list("........"),
            list("........"),
            list("........"),
            list("........"),
            list("PPP..PPP"),
            list("....RK.."),
        ],
        "white_to_move": True,
        "expected_move": "e1e8",
        "depth": 2,
    },
    {
        "name": "Free Queen",
        "grid": [
            list("....k..."),
            list("....q..."),
            list("........"),
            list("....R..."),
            list("........"),
            list("........"),
            list("PPP..PPP"),
            list("....K..R"),
        ],
        "white_to_move": True,
        "expected_move": "e5e7",
        "depth": 2,
    },
    {
        "name": "Knight Fork",
        "grid": [
            list("r...k..."),
            list("........"),
            list("....N..."),
            list("........"),
            list("........"),
            list("........"),
            list("PPP..PPP"),
            list("R...K..R"),
        ],
        "white_to_move": True,
        "expected_move": "e6c7",
        "depth": 3,
    },
    {
        "name": "Simple Capture",
        "grid": [
            list("r...k..."),
            list("....q..."),
            list("....R..."),
            list("........"),
            list("........"),
            list("........"),
            list("PPP..PPP"),
            list("....K..R"),
        ],
        "white_to_move": True,
        "expected_move": "e6e7",
        "depth": 1,
    },
]


def run_tactical_tests():
    """Run tactical test suite."""
    print("=" * 70)
    print("TACTICAL TEST SUITE - Search Engine Correctness")
    print("=" * 70)

    calc = SubconsciousCalculator(max_depth=5)
    solved = 0

    for puzzle in TACTICAL_PUZZLES:
        board = Board(puzzle["grid"], puzzle["white_to_move"])
        calc.clear_caches()

        t0 = time.time()
        move, score, diag = calc.search(board)
        elapsed = time.time() - t0

        found = str(move) if move else "None"
        is_correct = found == puzzle["expected_move"]
        status = "PASS" if is_correct else "FAIL"

        if is_correct:
            solved += 1

        pv_str = " > ".join(diag.get("principal_variation", [])[:3])
        print(f"  [{status}] {puzzle['name']}")
        print(f"         Expected: {puzzle['expected_move']}, Found: {found}")
        print(f"         Score: {score:+.2f}  Depth: {diag['depth_reached']}  "
              f"Nodes: {diag['nodes_evaluated']:,}  Time: {elapsed:.2f}s")
        print(f"         PV: {pv_str}\n")

    total = len(TACTICAL_PUZZLES)
    print(f"Solved: {solved}/{total}")
    return solved, total
