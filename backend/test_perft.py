"""
PERFT (Performance Test) - Validates move generation correctness
Uses standard chess positions with known perft values
"""

from chess_board import Board, generate_legal_moves

# Standard PERFT benchmarks for initial position
PERFT_BENCHMARKS = {
    1: 20,
    2: 400,
    3: 8902,
    4: 197281,
}

def perft(board: Board, depth: int) -> int:
    """Count leaf nodes at given depth."""
    color = "white" if board.white_to_move else "black"
    moves = generate_legal_moves(board, color)

    if depth == 1:
        return len(moves)

    total = 0
    for mv in moves:
        total += perft(board.apply_move(mv), depth - 1)

    return total


def run_perft_tests():
    """Run PERFT test suite."""
    print("=" * 70)
    print("PERFT TEST SUITE - Move Generation Correctness")
    print("=" * 70)

    board = Board.initial()
    all_pass = True

    for depth, expected in PERFT_BENCHMARKS.items():
        import time
        t0 = time.time()
        result = perft(board, depth)
        elapsed = time.time() - t0

        status = "PASS" if result == expected else "FAIL"
        if status == "FAIL":
            all_pass = False

        print(f"  Depth {depth}: {result:>10,}  expected {expected:>10,}  "
              f"[{status}]  ({elapsed:.2f}s)")

    print()
    if all_pass:
        print("✓ ALL PERFT TESTS PASSED - Move generation is correct!")
    else:
        print("✗ SOME PERFT TESTS FAILED - Move generation has bugs!")

    return all_pass
