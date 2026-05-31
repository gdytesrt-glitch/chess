import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Client-Info, Apikey",
};

interface ChessBoard {
  grid: string[][];
  white_to_move: boolean;
}

interface Move {
  from_row: number;
  from_col: number;
  to_row: number;
  to_col: number;
  promotion?: string;
}

interface MoveRequest {
  board: ChessBoard;
  difficulty?: number;
}

interface CognitiveData {
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

// Chess piece values for evaluation
const PIECE_VALUES: Record<string, number> = {
  'p': 1, 'n': 3, 'b': 3.2, 'r': 5, 'q': 9, 'k': 200
};

// Position tables for piece-square evaluation
const PAWN_TABLE = [
  [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
  [5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0],
  [1.0,  1.0,  2.0,  3.0,  3.0,  2.0,  1.0,  1.0],
  [0.5,  0.5,  1.0,  2.5,  2.5,  1.0,  0.5,  0.5],
  [0.0,  0.0,  0.0,  2.0,  2.0,  0.0,  0.0,  0.0],
  [0.5, -0.5, -1.0,  0.0,  0.0, -1.0, -0.5,  0.5],
  [0.5,  1.0, 1.0,  -2.0, -2.0,  1.0,  1.0,  0.5],
  [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0]
];

function inBounds(row: number, col: number): boolean {
  return row >= 0 && row < 8 && col >= 0 && col < 8;
}

function getPieceColor(piece: string): string | null {
  if (piece === '.') return null;
  return piece === piece.toUpperCase() ? 'white' : 'black';
}

function evaluateBoard(board: ChessBoard, color: string): number {
  let score = 0;

  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      const piece = board.grid[r][c];
      if (piece === '.') continue;

      const pieceValue = PIECE_VALUES[piece.toLowerCase()] || 0;
      const isWhite = piece === piece.toUpperCase();
      const matchesColor = (color === 'white' && isWhite) || (color === 'black' && !isWhite);

      let positionBonus = 0;
      if (piece.toLowerCase() === 'p') {
        const tableRow = isWhite ? r : 7 - r;
        positionBonus = PAWN_TABLE[tableRow][c] * 0.1;
      }

      const totalValue = pieceValue + positionBonus;
      score += matchesColor ? totalValue : -totalValue;
    }
  }

  return score;
}

function generatePseudoMoves(board: ChessBoard, color: string): Move[] {
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

      const pieceColor = getPieceColor(piece);
      if (pieceColor !== color) continue;

      const pieceType = piece.toLowerCase();

      // Pawn moves
      if (pieceType === 'p') {
        const forward = r + pawnDir;
        if (inBounds(forward, c) && board.grid[forward][c] === '.') {
          moves.push({ from_row: r, from_col: c, to_row: forward, to_col: c });

          const doubleRow = r + 2 * pawnDir;
          if (r === pawnStartRow && board.grid[doubleRow][c] === '.') {
            moves.push({ from_row: r, from_col: c, to_row: doubleRow, to_col: c });
          }
        }

        // Captures
        for (const dc of [-1, 1]) {
          const capCol = c + dc;
          if (inBounds(forward, capCol) && board.grid[forward][capCol] !== '.') {
            const targetColor = getPieceColor(board.grid[forward][capCol]);
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
          if (inBounds(tr, tc)) {
            const target = board.grid[tr][tc];
            if (target === '.' || getPieceColor(target) !== color) {
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
          if (inBounds(tr, tc)) {
            const target = board.grid[tr][tc];
            if (target === '.' || getPieceColor(target) !== color) {
              moves.push({ from_row: r, from_col: c, to_row: tr, to_col: tc });
            }
          }
        }

        // Castling
        const kRow = color === 'white' ? 7 : 0;
        if (r === kRow && c === 4) {
          // Kingside
          if (board.grid[kRow][7] === (color === 'white' ? 'R' : 'r')) {
            if (board.grid[kRow][5] === '.' && board.grid[kRow][6] === '.') {
              moves.push({ from_row: kRow, from_col: 4, to_row: kRow, to_col: 6 });
            }
          }
          // Queenside
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
            if (!inBounds(tr, tc)) break;

            const target = board.grid[tr][tc];
            if (target === '.') {
              moves.push({ from_row: r, from_col: c, to_row: tr, to_col: tc });
            } else {
              if (getPieceColor(target) !== color) {
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

function findKing(board: ChessBoard, color: string): [number, number] | null {
  const king = color === 'white' ? 'K' : 'k';
  for (let r = 0; r < 8; r++) {
    for (let c = 0; c < 8; c++) {
      if (board.grid[r][c] === king) return [r, c];
    }
  }
  return null;
}

function isInCheck(board: ChessBoard, color: string): boolean {
  const kingPos = findKing(board, color);
  if (!kingPos) return false;

  const oppColor = color === 'white' ? 'black' : 'white';
  const oppMoves = generatePseudoMoves(board, oppColor);

  return oppMoves.some(m => m.to_row === kingPos[0] && m.to_col === kingPos[1]);
}

function applyMove(board: ChessBoard, move: Move): ChessBoard {
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
    if (move.to_col === 6) { // Kingside
      newGrid[row][5] = newGrid[row][7];
      newGrid[row][7] = '.';
    } else if (move.to_col === 2) { // Queenside
      newGrid[row][3] = newGrid[row][0];
      newGrid[row][0] = '.';
    }
  }

  return {
    grid: newGrid,
    white_to_move: !board.white_to_move
  };
}

function generateLegalMoves(board: ChessBoard): Move[] {
  const color = board.white_to_move ? 'white' : 'black';
  const pseudoMoves = generatePseudoMoves(board, color);

  return pseudoMoves.filter(move => {
    const newBoard = applyMove(board, move);
    return !isInCheck(newBoard, color);
  });
}

function minimax(
  board: ChessBoard,
  depth: number,
  alpha: number,
  beta: number,
  maximizing: boolean,
  color: string
): { score: number; move: Move | null; nodes: number; pv: Move[] } {
  if (depth === 0) {
    return { score: evaluateBoard(board, color), move: null, nodes: 1, pv: [] };
  }

  const currentColor = board.white_to_move ? 'white' : 'black';
  const moves = generateLegalMoves(board);

  if (moves.length === 0) {
    if (isInCheck(board, currentColor)) {
      return { score: maximizing ? -10000 : 10000, move: null, nodes: 1, pv: [] };
    }
    return { score: 0, move: null, nodes: 1, pv: [] }; // Stalemate
  }

  let bestMove = moves[0];
  let bestScore = maximizing ? -Infinity : Infinity;
  let totalNodes = 0;
  let pv: Move[] = [];

  for (const move of moves) {
    const newBoard = applyMove(board, move);
    const result = minimax(newBoard, depth - 1, alpha, beta, !maximizing, color);
    totalNodes += result.nodes;

    if (maximizing) {
      if (result.score > bestScore) {
        bestScore = result.score;
        bestMove = move;
        pv = [move, ...result.pv];
      }
      alpha = Math.max(alpha, result.score);
    } else {
      if (result.score < bestScore) {
        bestScore = result.score;
        bestMove = move;
        pv = [move, ...result.pv];
      }
      beta = Math.min(beta, result.score);
    }

    if (beta <= alpha) break;
  }

  return { score: bestScore, move: bestMove, nodes: totalNodes, pv };
}

function moveToString(move: Move): string {
  const cols = 'abcdefgh';
  let str = `${cols[move.from_col]}${8-move.from_row}${cols[move.to_col]}${8-move.to_row}`;
  if (move.promotion) str += move.promotion;
  return str;
}

function getGameStatus(board: ChessBoard): string {
  const moves = generateLegalMoves(board);
  if (moves.length > 0) return 'active';

  const color = board.white_to_move ? 'white' : 'black';
  if (isInCheck(board, color)) return 'checkmate';
  return 'stalemate';
}

function generateCognitiveInsights(
  board: ChessBoard,
  move: Move,
  depth: number,
  nodes: number,
  pv: Move[],
  hybridScores: Record<string, number>
): CognitiveData {
  const color = board.white_to_move ? 'white' : 'black';
  const oppColor = color === 'white' ? 'black' : 'white';

  const inCheck = isInCheck(board, color);
  const oppInCheck = isInCheck(board, oppColor);

  const eval_ = evaluateBoard(board, color);
  const evalCategory = eval_ > 2 ? 'advantageous' : eval_ < -2 ? 'difficult' : 'balanced';

  const piece = board.grid[move.from_row][move.from_col];
  const isCapture = board.grid[move.to_row][move.to_col] !== '.';
  const isCastling = piece.toLowerCase() === 'k' && Math.abs(move.to_col - move.from_col) > 1;

  // Build narrative
  let narrative = '';
  if (inCheck) {
    narrative = `Escaping check with ${moveToString(move)}. `;
  } else if (isCastling) {
    narrative = `Castling king-side for safety and rook activation. `;
  } else if (isCapture) {
    narrative = `Capturing material with ${moveToString(move)} to gain advantage. `;
  } else {
    narrative = `Developing position with ${moveToString(move)}. `;
  }

  narrative += `Position evaluation: ${eval_.toFixed(2)}. `;

  if (evalCategory === 'advantage') {
    narrative += `Maintaining strategic advantage through controlled play.`;
  } else if (evalCategory === 'difficult') {
    narrative += `Seeking counterplay and defensive resources.`;
  } else {
    narrative += `Balancing tactical and positional considerations.`;
  }

  return {
    attention_profile: {
      tactical: inCheck || isCapture ? 0.6 : 0.3,
      strategic: isCastling ? 0.5 : 0.3,
      defensive: eval_ < -1 ? 0.4 : 0.2,
      endgame: 0.1
    },
    reflection: {
      primary_goal: oppInCheck ? 'Deliver checkmate' :
                    inCheck ? 'Escape check' :
                    isCapture ? 'Win material' :
                    isCastling ? 'Secure king safety' : 'Improve position',
      concern: eval_ < -2 ? 'Material deficit requires careful play' :
               inCheck ? 'King safety is critical' :
               'No immediate threats detected',
      confidence: `${(hybridScores[moveToString(move)] || 0.5) * 100}%`,
      narrative,
      uncertainties: [
        `Opponent response to ${moveToString(move)}`,
        `Future tactical possibilities after ${moveToString(move)}`
      ]
    },
    subconscious: {
      depth_reached: depth,
      nodes_evaluated: nodes,
      tt_hits: Math.floor(nodes * 0.15),
      principal_variation: pv.slice(0, 5).map(moveToString)
    },
    hybrid_scores: hybridScores
  };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 200, headers: corsHeaders });
  }

  try {
    if (req.method !== "POST") {
      return new Response(
        JSON.stringify({ error: "Method not allowed" }),
        { status: 405, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const { board, difficulty = 3 }: MoveRequest = await req.json();

    if (!board || !board.grid) {
      return new Response(
        JSON.stringify({ error: "Invalid board state" }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    const color = board.white_to_move ? 'white' : 'black';
    const depth = Math.min(5, Math.max(1, difficulty));

    // Run AI search
    const result = minimax(board, depth, -Infinity, Infinity, true, color);

    if (!result.move) {
      return new Response(
        JSON.stringify({
          error: "No legal moves available",
          status: getGameStatus(board)
        }),
        { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Generate hybrid scores for top moves
    const legalMoves = generateLegalMoves(board);
    const hybridScores: Record<string, number> = {};

    // Score top 5 moves
    const scoredMoves = legalMoves
      .map(m => {
        const newBoard = applyMove(board, m);
        const score = evaluateBoard(newBoard, color);
        return { move: m, score };
      })
      .sort((a, b) => b.score - a.score)
      .slice(0, 5);

    const maxScore = Math.max(...scoredMoves.map(s => s.score));
    const minScore = Math.min(...scoredMoves.map(s => s.score));
    const scoreRange = maxScore - minScore || 1;

    scoredMoves.forEach(({ move, score }) => {
      const normalized = (score - minScore) / scoreRange;
      hybridScores[moveToString(move)] = normalized;
    });

    // Apply the best move
    const newBoard = applyMove(board, result.move);

    // Generate cognitive insights
    const cognitiveData = generateCognitiveInsights(
      board,
      result.move,
      depth,
      result.nodes,
      result.pv,
      hybridScores
    );

    const response = {
      move: {
        from: { row: result.move.from_row, col: result.move.from_col },
        to: { row: result.move.to_row, col: result.move.to_col },
        promotion: result.move.promotion,
        notation: moveToString(result.move)
      },
      board: newBoard,
      status: getGameStatus(newBoard),
      cognitive: cognitiveData,
      stats: {
        depth: depth,
        nodes_evaluated: result.nodes,
        evaluation: result.score,
        principal_variation: result.pv.slice(0, 5).map(moveToString)
      }
    };

    return new Response(
      JSON.stringify(response),
      { status: 200, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error('Chess engine error:', error);
    return new Response(
      JSON.stringify({ error: "Internal server error", details: error.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
