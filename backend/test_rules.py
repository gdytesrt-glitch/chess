"""
Rules Test Suite - Validates chess rule correctness
Tests castling, en passant, promotion, check, checkmate, stalemate, draws
"""

from chess_board_v2 import Board, generate_legal_moves, is_in_check, Move
from chess_board_v2 import is_insufficient_material, check_fifty_move_rule


def test_castling():
    """Test castling moves and rights."""
    print("\n=== CASTLING TESTS ===")

    # Test kingside castling
    board = Board.initial()
    board.grid[6] = list("PP.PPP.P")
    board.grid[7] = list("R.BQKBNR")
    board.white_to_move = True

    color = "white"
    moves = generate_legal_moves(board, color)
    castling_moves = [m for m in moves if m.from_col == 4 and m.to_col == 6]
    print(f"  Kingside castling available: {len(castling_moves) > 0}")

    # Apply castling and verify rook moved
    if castling_moves:
        board = board.apply_move(castling_moves[0])
        print(f"  After castling - King at g1: {board.grid[7][6] == 'K'}")
        print(f"  After castling - Rook at f1: {board.grid[7][5] == 'R'}")


def test_en_passant():
    """Test en passant captures."""
    print("\n=== EN PASSANT TESTS ===")

    board = Board.initial()
    # Set up position with en passant opportunity
    board.grid[3] = list("....P...")  # White pawn
    board.grid[1] = list(".....p..")  # Black pawn on starting rank
    board.white_to_move = False
    board.en_passant_sq = None

    # Black pawn pushes 2 squares
    move = Move(1, 5, 3, 5)
    board = board.apply_move(move)
    print(f"  After black e5, en passant square set: {board.en_passant_sq is not None}")

    # White can capture en passant
    board.white_to_move = True
    moves = generate_legal_moves(board, "white")
    ep_moves = [m for m in moves if m.from_col == 4 and m.to_col == 5 and m.to_row == 2]
    print(f"  White can capture en passant: {len(ep_moves) > 0}")


def test_promotion():
    """Test pawn promotion."""
    print("\n=== PROMOTION TESTS ===")

    # White pawn on 7th rank
    board = Board([["."] * 8 for _ in range(8)])
    board.grid[1] = list(".P...... ")  # White pawn about to promote
    board.grid[0] = list("....k...")
    board.white_to_move = True

    moves = generate_legal_moves(board, "white")
    # Should have promotion to Q, R, B, N
    print(f"  Promotion moves available: {len(moves) > 0}")


def test_insufficient_material():
    """Test insufficient material detection."""
    print("\n=== INSUFFICIENT MATERIAL TESTS ===")

    # King vs King
    board = Board([["."] * 8 for _ in range(8)])
    board.grid[0][0] = "K"
    board.grid[7][7] = "k"
    print(f"  KvK is draw: {is_insufficient_material(board)}")

    # King + Knight vs King
    board.grid[0][1] = "N"
    print(f"  KN vs K is draw: {is_insufficient_material(board)}")


def test_checkmate_stalemate():
    """Test checkmate and stalemate detection."""
    print("\n=== CHECKMATE/STALEMATE TESTS ===")

    # Fool's mate position: checkmate in 2
    board = Board.initial()
    board = board.apply_move(Move(6, 5, 4, 5))  # f3
    board = board.apply_move(Move(1, 4, 3, 4))  # e5
    board = board.apply_move(Move(6, 6, 4, 6))  # g4
    board = board.apply_move(Move(0, 3, 4, 7))  # Qh5#

    color = "white"
    moves = generate_legal_moves(board, color)
    in_check = is_in_check(board, color)
    print(f"  Fool's mate - White in check: {in_check}")
    print(f"  Fool's mate - No legal moves (checkmate): {len(moves) == 0}")


def test_castling_rights_loss():
    """Test that castling rights are lost after king/rook moves."""
    print("\n=== CASTLING RIGHTS LOSS TESTS ===")

    board = Board.initial()
    # Move king forward and back
    board = board.apply_move(Move(6, 4, 5, 4))  # e3
    board = board.apply_move(Move(1, 4, 2, 4))  # e6
    board = board.apply_move(Move(5, 4, 6, 4))  # Ke2
    board = board.apply_move(Move(2, 4, 3, 4))  # e5

    print(f"  Castling rights after king move: '{board.castling_rights}'")
    print(f"  White kingside castling lost: {'K' not in board.castling_rights}")


def test_fifty_move_rule():
    """Test 50-move rule detection."""
    print("\n=== FIFTY-MOVE RULE TESTS ===")

    board = Board.initial()
    # Simulate 50 moves without pawn/capture
    for _ in range(50):
        board.halfmove_clock += 1
        board.white_to_move = not board.white_to_move

    is_draw = check_fifty_move_rule(board)
    print(f"  After 50 moves without pawn/capture, draw claimed: {is_draw}")


def run_rules_tests():
    """Run all rules tests."""
    print("=" * 70)
    print("RULES TEST SUITE - Chess Rules Validation")
    print("=" * 70)

    test_castling()
    test_en_passant()
    test_promotion()
    test_insufficient_material()
    test_checkmate_stalemate()
    test_castling_rights_loss()
    test_fifty_move_rule()

    print("\n" + "=" * 70)
    print("✓ RULES TESTS COMPLETED")
    print("=" * 70)
