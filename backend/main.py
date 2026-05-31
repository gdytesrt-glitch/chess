from __future__ import annotations
import os
import sys
import time

# Force UTF-8 encoding on standard output to prevent Windows console crashes
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from chess_board import Board, generate_legal_moves, parse_move, evaluate_board, select_color, is_in_check
from cognitive_engine import ProbabilisticChessMind


# ANSI Color Codes for Premium Console Styling
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
GRAY = "\033[90m"

BG_DARK = "\033[40m"

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def draw_progress_bar(value: float, max_val: float = 1.0, length: int = 12, color: str = GREEN) -> str:
    fraction = min(1.0, max(0.0, value / max_val))
    filled_len = int(fraction * length)
    unfilled_len = length - filled_len
    bar = f"{color}" + "█" * filled_len + f"{GRAY}" + "░" * unfilled_len + f"{RESET}"
    return f"[{bar}] {value*100:.1f}%"

def print_banner():
    banner = f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════════╗
║               PROBABILISTIC COGNITIVE CHESS MIND                 ║
║        البنية الإدراكية الاحتمالية لمحرك الشطرنج التفاعلي         ║
╚══════════════════════════════════════════════════════════════════╝{RESET}
"""
    print(banner)

def print_board(board: Board):
    # Unicode Chess Symbols for maximum premium aesthetics
    unicode_symbols = {
        "R": "♜", "N": "♞", "B": "♝", "Q": "♛", "K": "♚", "P": "♟",
        "r": "♖", "n": "♘", "b": "♗", "q": "♕", "k": "♔", "p": "♙",
        ".": "·"
    }

    cols = "   a   b   c   d   e   f   g   h"
    print(f"{BOLD}{BLUE}  ╔═══╤═══╤═══╤═══╤═══╤═══╤═══╤═══╗{RESET}")
    
    for r in range(8):
        row_str = f"{BOLD}{BLUE}{8 - r} ║{RESET}"
        for c in range(8):
            piece = board.grid[r][c]
            symbol = unicode_symbols[piece]
            
            # Highlight piece colors
            if piece.isupper():
                styled_piece = f" {BOLD}{YELLOW}{symbol}{RESET} "
            elif piece.islower():
                styled_piece = f" {BOLD}{CYAN}{symbol}{RESET} "
            else:
                styled_piece = f" {GRAY}{symbol}{RESET} "
                
            # Border separators
            sep = f"{BLUE}│{RESET}" if c < 7 else f"{BOLD}{BLUE}║{RESET}"
            row_str += styled_piece + sep
            
        print(row_str)
        if r < 7:
            print(f"{BLUE}  ╟───┼───┼───┼───┼───┼───┼───┼───╢{RESET}")
            
    print(f"{BOLD}{BLUE}  ╚═══╧═══╧═══╧═══╧═══╧═══╧═══╧═══╝{RESET}")
    print(f"{BOLD}{BLUE}{cols}{RESET}\n")

def display_diagnostics(diagnostics: dict, color: str):
    profile = diagnostics["attention_profile"]
    reflection = diagnostics["reflection"]
    tree = diagnostics["probability_tree"]
    graph = diagnostics["knowledge_graph"]
    main_tl = diagnostics["main_timeline"]
    alternatives = diagnostics["alternatives"]
    rejected = diagnostics["rejected"]

    # 1. Attention Focus Box
    print(f"{BOLD}{CYAN}┌──────────────────────── Attention Profile ────────────────────────┐{RESET}")
    print(f"│ Tactical Focus:  {draw_progress_bar(profile['tactical'], color=RED)} │ Strategic Focus: {draw_progress_bar(profile['strategic'], color=GREEN)} │")
    print(f"│ Defensive Focus: {draw_progress_bar(profile['defensive'], color=CYAN)} │ Endgame Focus:   {draw_progress_bar(profile['endgame'], color=MAGENTA)} │")
    print(f"{BOLD}{CYAN}└───────────────────────────────────────────────────────────────────┘{RESET}\n")

    # 2. Meta Consciousness Reflection Diary
    print(f"{BOLD}{YELLOW}┌───────────────────────── Meta Observer Reflection ─────────────────────────┐{RESET}")
    print(f"│ {BOLD}Active Goal:{RESET} {reflection['primary_goal'][:60]:<62} │")
    print(f"│ {BOLD}Main Concern:{RESET} {reflection['concern'][:59]:<62} │")
    print(f"│ {BOLD}Confidence Level:{RESET} {BOLD}{GREEN}{reflection['confidence']:<10}{RESET}                                                    │")
    print(f"├────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ {BOLD}{YELLOW}[Meta Narrative Diary]{RESET}                                                       │")
    
    # Wrap text cleanly
    text = reflection['narrative']
    words = text.split()
    lines = []
    curr_line = ""
    for w in words:
        if len(curr_line) + len(w) + 1 > 72:
            lines.append(curr_line)
            curr_line = w
        else:
            curr_line = (curr_line + " " + w).strip()
    if curr_line:
        lines.append(curr_line)
        
    for line in lines:
        print(f"│ {line:<74} │")
        
    print(f"├────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ {BOLD}Uncertainties / Core Questions:{RESET}                                            │")
    for unc in reflection['uncertainties'][:2]:
        print(f"│  • {GRAY}{unc:<71}{RESET} │")
    print(f"{BOLD}{YELLOW}└────────────────────────────────────────────────────────────────────────────┘{RESET}\n")

    # 3. Probability Decision Tree
    print(f"{BOLD}{GREEN}┌── Probability Decision Intention Taxonomy ──────────────────────────────────{RESET}")
    tree_str = tree.print_tree()
    for line in tree_str.splitlines():
        if line.strip():
            print(f"│ {GREEN}{line}{RESET}")
    print(f"{BOLD}{GREEN}└─────────────────────────────────────────────────────────────────────────────{RESET}\n")

    # 4. Simulated Multiverse Timelines
    print(f"{BOLD}{CYAN}┌── Simulated Multiverse Universes & Timelines ───────────────────────────────{RESET}")
    # Main
    main_seq = " ➔ ".join(str(m) for m in main_tl.move_sequence)
    print(f"│ {BOLD}{GREEN}[Main Universe]{RESET}  {main_seq:<30} | {main_tl.description}")
    # Alternatives
    for i, alt in enumerate(alternatives[:2]):
        alt_seq = " ➔ ".join(str(m) for m in alt.move_sequence)
        print(f"│ {CYAN}[Alt Universe {i+1}]{RESET} {alt_seq:<30} | {alt.description}")
    # Rejected
    for i, rej in enumerate(rejected[:2]):
        rej_seq = " ➔ ".join(str(m) for m in rej.move_sequence)
        print(f"│ {RED}[Rejected Risk]{RESET} {rej_seq:<30} | {rej.description}")
    print(f"{BOLD}{CYAN}└─────────────────────────────────────────────────────────────────────────────{RESET}\n")

    # 5. Semantic Knowledge Graph Sneak-peek
    print(f"{BOLD}{MAGENTA}┌── Active Master Knowledge Graph Concepts ───────────────────────────────────{RESET}")
    active_nodes = graph.query_active_concepts(threshold=0.35)[:6]
    nodes_str = ", ".join(f"{BOLD}{node}{RESET} ({GRAY}{act*100:.0f}%{RESET})" for node, act in active_nodes)
    print(f"│ {nodes_str}")
    print(f"{BOLD}{MAGENTA}└─────────────────────────────────────────────────────────────────────────────{RESET}\n")

    # 6. Subconscious Brain Stats
    sc = diagnostics.get("subconscious", {})
    hybrid = diagnostics.get("hybrid_scores", {})
    uncertainty = diagnostics.get("uncertainty", 1.0)
    depth_boost = diagnostics.get("depth_boost", 0)
    pv = sc.get("principal_variation", [])
    pv_str = " ➔ ".join(pv[:6]) if pv else "N/A"
    print(f"{BOLD}{YELLOW}┌── Subconscious Alpha-Beta Engine ───────────────────────────────────────────{RESET}")
    print(f"│ {BOLD}Depth Reached:{RESET}   {sc.get('depth_reached', 0):<3} (boost +{depth_boost})   "
          f"{BOLD}Nodes Evaluated:{RESET} {sc.get('nodes_evaluated', 0):>8,}")
    print(f"│ {BOLD}TT Hits:{RESET}         {sc.get('tt_hits', 0):<8,}   "
          f"{BOLD}TT Cache Size:{RESET}   {sc.get('tt_size', 0):>8,}")
    print(f"│ {BOLD}Positional Uncertainty:{RESET} {uncertainty*100:.1f}%   "
          f"{BOLD}Memory Bonus:{RESET} {diagnostics.get('memory_bonus', 0.0)*100:.1f}%")
    print(f"│ {BOLD}Principal Variation:{RESET} {CYAN}{pv_str}{RESET}")
    print(f"{BOLD}{YELLOW}└─────────────────────────────────────────────────────────────────────────────{RESET}\n")

    # 7. Hybrid Scoring Formula Breakdown
    if hybrid:
        top3 = sorted(hybrid.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"{BOLD}{GREEN}┌── Hybrid Score Formula  (0.75 tactical + 0.15 strategic + 0.05 memory + 0.05 confidence){RESET}")
        for mv_str, hs in top3:
            bar = draw_progress_bar(hs, 1.0, length=10, color=GREEN)
            print(f"│  {BOLD}{mv_str:<8}{RESET}  {bar}")
        print(f"{BOLD}{GREEN}└─────────────────────────────────────────────────────────────────────────────{RESET}\n")


def play_game():
    board = Board.initial()
    mind = ProbabilisticChessMind()

    while True:
        clear_screen()
        print_banner()
        print_board(board)

        # Check for game over
        color = select_color(board.white_to_move)
        legal = generate_legal_moves(board, color)
        
        if not legal:
            opp_color = "black" if color == "white" else "white"
            in_chk = is_in_check(board, color)
            if in_chk:
                print(f"{BOLD}{RED}GAME OVER! {opp_color.upper()} wins by Checkmate!{RESET}\n")
                # Engine plays Black; White winning = engine loss
                result = "loss" if board.white_to_move else "win"
            else:
                print(f"{BOLD}{CYAN}GAME OVER! Draw by Stalemate!{RESET}\n")
                result = "draw"
            mind.finalize_game(result)
            print(f"{BOLD}{MAGENTA}[CognitiveMemory] Game recorded as: {result.upper()}{RESET}\n")
            break

        if board.white_to_move:
            # Human move
            print(f"{BOLD}{YELLOW}Your Turn (White).{RESET}")
            user_move_text = input("Enter move in coordinate notation (e.g. e2e4) or 'quit': ").strip()
            
            if user_move_text.lower() == "quit":
                mind.finalize_game("draw")  # treat quit as draw for memory
                break
                
            # Quality-of-life translation for Castling notation
            if user_move_text.lower() in ["o-o", "0-0"]:
                user_move_text = "e1g1" if board.white_to_move else "e8g8"
            elif user_move_text.lower() in ["o-o-o", "0-0-0"]:
                user_move_text = "e1c1" if board.white_to_move else "e8c8"

            move = parse_move(user_move_text)

            if not move:
                print(f"{RED}Invalid format. Try e2e4, b1c3 etc.{RESET}")
                time.sleep(1.5)
                continue
                
            legal_strs = [str(m) for m in legal]
            if str(move) not in legal_strs:
                print(f"{RED}Illegal move in this position!{RESET}")
                time.sleep(1.5)
                continue
                
            # Execute move
            # Match move from legal list to preserve potential properties
            matching_move = [m for m in legal if str(m) == str(move)][0]
            board = board.apply_move(matching_move)
            
        else:
            # AI Move
            print(f"{BOLD}{CYAN}Cognitive Chess Mind is thinking in parallel dimensions...{RESET}")
            think_start = time.time()
            res = mind.think(board)
            think_dur = time.time() - think_start
            
            if not res:
                print(f"{RED}No moves simulated by the AI mind.{RESET}")
                break
                
            ai_move, diagnostics = res
            
            # Print beautiful cognitive processes
            clear_screen()
            print_banner()
            print(f"{BOLD}{CYAN}Cognitive analysis completed in {think_dur:.2f} seconds.{RESET}\n")
            display_diagnostics(diagnostics, "black")
            
            print(f"{BOLD}{CYAN}Chess Mind chose move:{RESET} {BOLD}{GREEN}{ai_move}{RESET}\n")
            input("Press Enter to continue board state and view board...")
            
            board = board.apply_move(ai_move)

    print(f"\n{BOLD}{CYAN}Thank you for playing against the Probabilistic Chess Mind!{RESET}\n")

if __name__ == "__main__":
    play_game()
