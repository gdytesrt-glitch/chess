export interface Move {
  from_row: number;
  from_col: number;
  to_row: number;
  to_col: number;
  promotion?: string;
}

export interface ChessBoardState {
  grid: string[][];
  white_to_move: boolean;
}

export interface CognitiveData {
  attention_profile: Record<string, number>;
  reflection: {
    primary_goal: string;
    concern: string;
    confidence: string;
    narrative: string;
    uncertainties: string[];
  };
  subconscious: {
    depth_reached: number;
    nodes_evaluated: number;
    tt_hits: number;
    principal_variation: string[];
  };
  hybrid_scores: Record<string, number>;
}

export class ChessEngine {
  private static PIECE_VALUES: Record<string, number> = {
    'p': 1, 'n': 3, 'b': 3.2, 'r': 5, 'q': 9, 'k': 200
  };

  static getInitialBoard(): ChessBoardState {
    return {
      grid: [
        ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
        ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.'],
        ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
        ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
      ],
      white_to_move: true
    };
  }

  static getPieceColor(piece: string): string | null {
    if (piece === '.') return null;
    return piece === piece.toUpperCase() ? 'white' : 'black';
  }

  static moveToNotation(move: Move): string {
    const cols = 'abcdefgh';
    let notation = `${cols[move.from_col]}${8 - move.from_row}${cols[move.to_col]}${8 - move.to_row}`;
    if (move.promotion) {
      notation += move.promotion.toLowerCase();
    }
    return notation;
  }

  static notationToMove(notation: string, board: ChessBoardState): Move | null {
    if (notation.length < 4) return null;

    const cols = 'abcdefgh';
    const from_col = cols.indexOf(notation[0]);
    const from_row = 8 - parseInt(notation[1]);
    const to_col = cols.indexOf(notation[2]);
    const to_row = 8 - parseInt(notation[3]);
    const promotion = notation.length > 4 ? notation[4] : undefined;

    if (from_col < 0 || to_col < 0 || isNaN(from_row) || isNaN(to_row)) return null;

    return { from_row, from_col, to_row, to_col, promotion };
  }

  private static inBounds(row: number, col: number): boolean {
    return row >= 0 && row < 8 && col >= 0 && col < 8;
  }

  private static generatePseudoMoves(board: ChessBoardState, color: string): Move[] {
    const moves: Move[] = [];
    const pawnDir = color === 'white' ? -1 : 1;
    const pawnStartRow = color === 'white' ? 6 : 1;

    const knightMoves = [
      [-2, -1], [-2, 1], [-1, -2], [-1, 2],
      [1, -2], [1, 2], [2, -1], [2, 1]
    ];

    const kingMoves = [
      [-1, -1], [-1, 0], [-1, 1], [0, -1],
      [0, 1], [1, -1], [1, 0], [1, 1]
    ];

    const bishopDirs = [[-1, -1], [-1, 1], [1, -1], [1, 1]];
    const rookDirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    const queenDirs = [...bishopDirs, ...rookDirs];

    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        const piece = board.grid[r][c];
        if (piece === '.') continue;

        const pieceColor = this.getPieceColor(piece);
        if (pieceColor !== color) continue;

        const pieceType = piece.toLowerCase();

        // Pawn moves
        if (pieceType === 'p') {
          const forward = r + pawnDir;
          if (this.inBounds(forward, c) && board.grid[forward][c] === '.') {
            moves.push({ from_row: r, from_col: c, to_row: forward, to_col: c });

            const doubleRow = r + 2 * pawnDir;
            if (r === pawnStartRow && board.grid[doubleRow][c] === '.') {
              moves.push({ from_row: r, from_col: c, to_row: doubleRow, to_col: c });
            }
          }

          for (const dc of [-1, 1]) {
            const capCol = c + dc;
            if (this.inBounds(forward, capCol) && board.grid[forward][capCol] !== '.') {
              const targetColor = this.getPieceColor(board.grid[forward][capCol]);
              if (targetColor !== color && targetColor !== null) {
                moves.push({ from_row: r, from_col: c, to_row: forward, to_col: capCol });
              }
            }
          }
        }

        // Knight moves
        else if (pieceType === 'n') {
          for (const [dr, dc] of knightMoves) {
            const tr = r + dr;
            const tc = c + dc;
            if (this.inBounds(tr, tc)) {
              const target = board.grid[tr][tc];
              if (target === '.' || this.getPieceColor(target) !== color) {
                moves.push({ from_row: r, from_col: c, to_row: tr, to_col: tc });
              }
            }
          }
        }

        // King moves
        else if (pieceType === 'k') {
          for (const [dr, dc] of kingMoves) {
            const tr = r + dr;
            const tc = c + dc;
            if (this.inBounds(tr, tc)) {
              const target = board.grid[tr][tc];
              if (target === '.' || this.getPieceColor(target) !== color) {
                moves.push({ from_row: r, from_col: c, to_row: tr, to_col: tc });
              }
            }
          }

          // Castling
          const kRow = color === 'white' ? 7 : 0;
          if (r === kRow && c === 4) {
            if (board.grid[kRow][7] === (color === 'white' ? 'R' : 'r')) {
              if (board.grid[kRow][5] === '.' && board.grid[kRow][6] === '.') {
                moves.push({ from_row: kRow, from_col: 4, to_row: kRow, to_col: 6 });
              }
            }
            if (board.grid[kRow][0] === (color === 'white' ? 'R' : 'r')) {
              if (board.grid[kRow][1] === '.' && board.grid[kRow][2] === '.' && board.grid[kRow][3] === '.') {
                moves.push({ from_row: kRow, from_col: 4, to_row: kRow, to_col: 2 });
              }
            }
          }
        }

        // Sliding pieces
        else if (pieceType === 'b' || pieceType === 'r' || pieceType === 'q') {
          const dirs = pieceType === 'b' ? bishopDirs :
                       pieceType === 'r' ? rookDirs : queenDirs;

          for (const [dr, dc] of dirs) {
            let dist = 1;
            while (true) {
              const tr = r + dr * dist;
              const tc = c + dc * dist;
              if (!this.inBounds(tr, tc)) break;

              const target = board.grid[tr][tc];
              if (target === '.') {
                moves.push({ from_row: r, from_col: c, to_row: tr, to_col: tc });
              } else {
                if (this.getPieceColor(target) !== color) {
                  moves.push({ from_row: r, from_col: c, to_row: tr, to_col: tc });
                }
                break;
              }
              dist++;
            }
          }
        }
      }
    }

    return moves;
  }

  private static findKing(board: ChessBoardState, color: string): [number, number] | null {
    const king = color === 'white' ? 'K' : 'k';
    for (let r = 0; r < 8; r++) {
      for (let c = 0; c < 8; c++) {
        if (board.grid[r][c] === king) return [r, c];
      }
    }
    return null;
  }

  static isInCheck(board: ChessBoardState, color: string): boolean {
    const kingPos = this.findKing(board, color);
    if (!kingPos) return false;

    const oppColor = color === 'white' ? 'black' : 'white';
    const oppMoves = this.generatePseudoMoves(board, oppColor);

    return oppMoves.some(m => m.to_row === kingPos[0] && m.to_col === kingPos[1]);
  }

  static generateLegalMoves(board: ChessBoardState, from?: { row: number; col: number }): Move[] {
    const color = board.white_to_move ? 'white' : 'black';
    let pseudoMoves = this.generatePseudoMoves(board, color);

    if (from) {
      pseudoMoves = pseudoMoves.filter(m =>
        m.from_row === from.row && m.from_col === from.col
      );
    }

    return pseudoMoves.filter(move => {
      const newBoard = this.applyMove(board, move);
      return !this.isInCheck(newBoard, color);
    });
  }

  static applyMove(board: ChessBoardState, move: Move): ChessBoardState {
    const newGrid = board.grid.map(row => [...row]);
    const piece = newGrid[move.from_row][move.from_col];

    newGrid[move.from_row][move.from_col] = '.';

    let finalPiece = move.promotion || piece;
    if (piece.toLowerCase() === 'p') {
      if ((piece === 'P' && move.to_row === 0) || (piece === 'p' && move.to_row === 7)) {
        finalPiece = piece === 'P' ? 'Q' : 'q';
      }
    }

    newGrid[move.to_row][move.to_col] = finalPiece;

    // Handle castling rook move
    if (piece.toLowerCase() === 'k' && Math.abs(move.to_col - move.from_col) > 1) {
      const row = move.from_row;
      if (move.to_col === 6) {
        newGrid[row][5] = newGrid[row][7];
        newGrid[row][7] = '.';
      } else if (move.to_col === 2) {
        newGrid[row][3] = newGrid[row][0];
        newGrid[row][0] = '.';
      }
    }

    return {
      grid: newGrid,
      white_to_move: !board.white_to_move
    };
  }

  static getGameStatus(board: ChessBoardState): string {
    const moves = this.generateLegalMoves(board);
    if (moves.length > 0) return 'active';

    const color = board.white_to_move ? 'white' : 'black';
    if (this.isInCheck(board, color)) return 'checkmate';
    return 'stalemate';
  }

  static getPieceSymbol(piece: string): string {
    const symbols: Record<string, string> = {
      'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
      'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
      '.': ''
    };
    const symbol = symbols[piece];
    // If Unicode symbol not available, use ASCII fallback
    return symbol !== undefined ? symbol : (piece !== '.' ? piece.toUpperCase() : '');
  }
}
