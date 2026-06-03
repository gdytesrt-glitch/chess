"""
Performance Benchmark - Before and After Optimizations
=======================================================
Compares:
- String-based hash vs Zobrist hash
- Basic move ordering vs enhanced move ordering
- Search depth consistency
- Transposition table efficiency
"""

import time
from chess_board_v2 import Board, parse_move
from subconscious_calculator import SubconsciousCalculator as CalcV1
from subconscious_calculator_v2 import SubconsciousCalculator as CalcV2


def create_test_position(moves: list) -> Board:
    """Create a test position by applying moves from initial."""
    board = Board.initial()
    for move_str in moves:
        move = parse_move(move_str)
        if move:
            board = board.apply_move(move)
    return board


def benchmark_position(calc, board: Board, depth: int, name: str) -> dict:
    """Benchmark search at a position."""
    print(f"\n  Testing {name} (depth {depth})...")

    calc.clear_caches()
    t0 = time.time()
    move, score, diag = calc.search(board)
    elapsed = time.time() - t0

    nodes = diag.get("nodes_evaluated", 0)
    nps = nodes / elapsed if elapsed > 0 else 0
    tt_hits = diag.get("tt_hits", 0)
    tt_size = diag.get("tt_size", 0)

    return {
        "name": name,
        "depth": depth,
        "move": str(move) if move else "None",
        "score": score,
        "time": elapsed,
        "nodes": nodes,
        "nps": nps,
        "tt_hits": tt_hits,
        "tt_size": tt_size,
    }


def run_benchmarks():
    """Run comprehensive benchmark suite."""
    print("=" * 80)
    print("PERFORMANCE BENCHMARK - Before vs After Optimization")
    print("=" * 80)

    test_positions = [
        {
            "name": "Initial Position",
            "moves": [],
            "depth": 5,
        },
        {
            "name": "After 1.e4 e5 2.Nf3",
            "moves": ["e2e4", "e7e5", "g1f3"],
            "depth": 5,
        },
        {
            "name": "Open Game (5 moves each)",
            "moves": ["e2e4", "e7e5", "g1f3", "b8c6", "f1b5"],
            "depth": 4,
        },
        {
            "name": "Mid-game Position",
            "moves": ["e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4", "f3d4", "g8f6", "b1c3", "a7a6"],
            "depth": 4,
        },
    ]

    results_v1 = []
    results_v2 = []

    for test_pos in test_positions:
        board = create_test_position(test_pos["moves"])
        print(f"\n{test_pos['name']} (depth {test_pos['depth']})")
        print("-" * 80)

        # V1 benchmark
        calc_v1 = CalcV1(max_depth=test_pos["depth"])
        result_v1 = benchmark_position(calc_v1, board, test_pos["depth"], "V1 (String Hash)")
        results_v1.append(result_v1)
        print(f"    V1: {result_v1['nodes']:>10,} nodes  {result_v1['time']:>6.2f}s  "
              f"{result_v1['nps']:>8.0f} nps  TT:{result_v1['tt_hits']:>6,}")

        # V2 benchmark
        calc_v2 = CalcV2(max_depth=test_pos["depth"])
        result_v2 = benchmark_position(calc_v2, board, test_pos["depth"], "V2 (Zobrist Hash)")
        results_v2.append(result_v2)
        print(f"    V2: {result_v2['nodes']:>10,} nodes  {result_v2['time']:>6.2f}s  "
              f"{result_v2['nps']:>8.0f} nps  TT:{result_v2['tt_hits']:>6,}")

        # Calculate delta
        speedup = result_v1["time"] / result_v2["time"] if result_v2["time"] > 0 else 1.0
        print(f"    Speedup: {speedup:.2f}x faster")

    # Summary report
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)

    total_time_v1 = sum(r["time"] for r in results_v1)
    total_time_v2 = sum(r["time"] for r in results_v2)
    total_nodes_v1 = sum(r["nodes"] for r in results_v1)
    total_nodes_v2 = sum(r["nodes"] for r in results_v2)
    total_nps_v1 = total_nodes_v1 / total_time_v1 if total_time_v1 > 0 else 0
    total_nps_v2 = total_nodes_v2 / total_time_v2 if total_time_v2 > 0 else 0

    print(f"\nV1 (String Hash):")
    print(f"  Total time: {total_time_v1:.2f}s")
    print(f"  Total nodes: {total_nodes_v1:,}")
    print(f"  Avg NPS: {total_nps_v1:.0f}")

    print(f"\nV2 (Zobrist Hash):")
    print(f"  Total time: {total_time_v2:.2f}s")
    print(f"  Total nodes: {total_nodes_v2:,}")
    print(f"  Avg NPS: {total_nps_v2:.0f}")

    overall_speedup = total_time_v1 / total_time_v2 if total_time_v2 > 0 else 1.0
    print(f"\nOverall Speedup: {overall_speedup:.2f}x faster")
    print(f"NPS improvement: {(total_nps_v2 / total_nps_v1 - 1) * 100:.1f}% faster")

    # Feature comparison
    print("\n" + "=" * 80)
    print("FEATURE COMPARISON")
    print("=" * 80)

    features = {
        "Hash function": ("String-based", "Zobrist 64-bit"),
        "Hash complexity": ("O(n)", "O(1)"),
        "Move ordering": ("Basic (TT, MVV-LVA)", "Enhanced (TT, MVV-LVA, killers, history)"),
        "Quiescence": ("Basic", "With delta pruning"),
        "Depth limit": ("Unrestricted", "MAX_DEPTH=7"),
        "Node pruning": ("Standard α-β", "Enhanced with history"),
    }

    for feature, (v1_val, v2_val) in features.items():
        print(f"  {feature:<25} V1: {v1_val:<25} V2: {v2_val}")

    print("\n" + "=" * 80)
    print("✓ BENCHMARK COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    try:
        run_benchmarks()
    except Exception as e:
        print(f"Error running benchmarks: {e}")
        import traceback
        traceback.print_exc()
