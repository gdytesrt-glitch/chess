import React, { useState, useEffect, useCallback } from 'react';
import { ChessBoard } from './components/ChessBoard';
import { MoveHistory } from './components/MoveHistory';
import { CognitivePanel } from './components/CognitivePanel';
import { GameControls } from './components/GameControls';
import { supabase } from './lib/supabase';
import { ChessEngine, Move, ChessBoardState, CognitiveData } from './lib/chessEngine';

export type GameMode = 'new' | 'playing' | 'gameover';

export default function App() {
  const [board, setBoard] = useState<ChessBoardState>(ChessEngine.getInitialBoard());
  const [gameMode, setGameMode] = useState<GameMode>('new');
  const [selectedSquare, setSelectedSquare] = useState<{ row: number; col: number } | null>(null);
  const [legalMoves, setLegalMoves] = useState<Move[]>([]);
  const [moveHistory, setMoveHistory] = useState<string[]>([]);
  const [playerColor, setPlayerColor] = useState<'white' | 'black'>('white');
  const [difficulty, setDifficulty] = useState(3);
  const [isAIThinking, setIsAIThinking] = useState(false);
  const [cognitiveData, setCognitiveData] = useState<CognitiveData | null>(null);
  const [gameId, setGameId] = useState<string | null>(null);
  const [moveIndex, setMoveIndex] = useState(-1);

  // Initialize new game
  const startNewGame = useCallback(async (color: 'white' | 'black', diff: number) => {
    const newBoard = ChessEngine.getInitialBoard();
    setBoard(newBoard);
    setPlayerColor(color);
    setDifficulty(diff);
    setMoveHistory([]);
    setGameMode('playing');
    setSelectedSquare(null);
    setLegalMoves([]);
    setCognitiveData(null);
    setMoveIndex(-1);

    // Save to database
    const { data, error } = await supabase
      .from('chess_games')
      .insert({
        board_state: newBoard,
        difficulty: diff,
        player_color: color,
        game_status: 'active'
      })
      .select()
      .single();

    if (!error && data) {
      setGameId(data.id);
    }
  }, []);

  // Make a move
  const makeMove = useCallback(async (from: { row: number; col: number }, to: { row: number; col: number }) => {
    const move: Move = {
      from_row: from.row,
      from_col: from.col,
      to_row: to.row,
      to_col: to.col
    };

    const newBoard = ChessEngine.applyMove(board, move);
    const newHistory = [...moveHistory, ChessEngine.moveToNotation(move)];
    setBoard(newBoard);
    setMoveHistory(newHistory);
    setMoveIndex(newHistory.length - 1);
    setSelectedSquare(null);
    setLegalMoves([]);

    // Update database
    if (gameId) {
      await supabase
        .from('chess_games')
        .update({
          board_state: newBoard,
          move_history: newHistory,
          updated_at: new Date().toISOString()
        })
        .eq('id', gameId);
    }

    // Check game status
    const status = ChessEngine.getGameStatus(newBoard);
    if (status !== 'active') {
      setGameMode('gameover');
      const result = status === 'checkmate'
        ? (newBoard.white_to_move ? 'black' : 'white') === playerColor ? 'win' : 'loss'
        : 'draw';

      if (gameId) {
        await supabase
          .from('chess_games')
          .update({
            game_status: status,
            result: result,
            updated_at: new Date().toISOString()
          })
          .eq('id', gameId);
      }
      return;
    }

    // AI move if it's AI's turn
    const isPlayerTurn = (newBoard.white_to_move && playerColor === 'white') ||
                        (!newBoard.white_to_move && playerColor === 'black');

    if (!isPlayerTurn) {
      await makeAIMove(newBoard, newHistory);
    }
  }, [board, moveHistory, gameId, playerColor]);

  // AI makes a move
  const makeAIMove = useCallback(async (currentBoard: ChessBoardState, currentHistory: string[]) => {
    setIsAIThinking(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_SUPABASE_URL}/functions/v1/chess-ai`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${import.meta.env.VITE_SUPABASE_ANON_KEY}`
        },
        body: JSON.stringify({
          board: currentBoard,
          difficulty: difficulty
        })
      });

      const data = await response.json();

      if (data.error) {
        console.error('AI error:', data.error);
        setIsAIThinking(false);
        return;
      }

      const aiMove: Move = {
        from_row: data.move.from.row,
        from_col: data.move.from.col,
        to_row: data.move.to.row,
        to_col: data.move.to.col,
        promotion: data.move.promotion
      };

      const newBoard = ChessEngine.applyMove(currentBoard, aiMove);
      const newHistory = [...currentHistory, data.move.notation];

      setBoard(newBoard);
      setMoveHistory(newHistory);
      setMoveIndex(newHistory.length - 1);
      setCognitiveData(data.cognitive);

      // Update database
      if (gameId) {
        await supabase
          .from('chess_games')
          .update({
            board_state: newBoard,
            move_history: newHistory,
            ai_cognitive_data: data.cognitive,
            updated_at: new Date().toISOString()
          })
          .eq('id', gameId);
      }

      // Check game status
      if (data.status !== 'active') {
        setGameMode('gameover');
        const result = data.status === 'checkmate'
          ? (newBoard.white_to_move ? 'black' : 'white') === playerColor ? 'win' : 'loss'
          : 'draw';

        if (gameId) {
          await supabase
            .from('chess_games')
            .update({
              game_status: data.status,
              result: result,
              updated_at: new Date().toISOString()
            })
            .eq('id', gameId);
        }
      }
    } catch (error) {
      console.error('AI move error:', error);
    } finally {
      setIsAIThinking(false);
    }
  }, [difficulty, gameId, playerColor]);

  // Handle square click
  const handleSquareClick = useCallback((row: number, col: number) => {
    if (gameMode !== 'playing' || isAIThinking) return;

    const isPlayerTurn = (board.white_to_move && playerColor === 'white') ||
                        (!board.white_to_move && playerColor === 'black');

    if (!isPlayerTurn) return;

    const piece = board.grid[row][col];
    const pieceColor = piece === '.' ? null : (piece === piece.toUpperCase() ? 'white' : 'black');
    const isPlayerPiece = pieceColor === playerColor;

    if (selectedSquare) {
      // Check if clicking on a legal move destination
      const isLegalMove = legalMoves.some(m =>
        m.to_row === row && m.to_col === col &&
        m.from_row === selectedSquare.row && m.from_col === selectedSquare.col
      );

      if (isLegalMove) {
        makeMove(selectedSquare, { row, col });
      } else if (isPlayerPiece) {
        // Select new piece
        setSelectedSquare({ row, col });
        const moves = ChessEngine.generateLegalMoves(board, { row, col });
        setLegalMoves(moves);
      } else {
        setSelectedSquare(null);
        setLegalMoves([]);
      }
    } else if (isPlayerPiece) {
      setSelectedSquare({ row, col });
      const moves = ChessEngine.generateLegalMoves(board, { row, col });
      setLegalMoves(moves);
    }
  }, [board, selectedSquare, legalMoves, gameMode, isAIThinking, playerColor, makeMove]);

  // Navigate through move history
  const goToMove = useCallback((index: number) => {
    let currentBoard = ChessEngine.getInitialBoard();
    for (let i = 0; i <= index && i < moveHistory.length; i++) {
      const move = ChessEngine.notationToMove(moveHistory[i], currentBoard);
      if (move) {
        currentBoard = ChessEngine.applyMove(currentBoard, move);
      }
    }
    setBoard(currentBoard);
    setMoveIndex(index);
    setSelectedSquare(null);
    setLegalMoves([]);
  }, [moveHistory]);

  const inCheck = ChessEngine.isInCheck(board, board.white_to_move ? 'white' : 'black');
  const gameStatus = ChessEngine.getGameStatus(board);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-slate-900 to-black">
      {/* Header */}
      <header className="bg-slate-900/95 backdrop-blur-md border-b border-slate-700/50 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-amber-400 to-amber-600 flex items-center justify-center shadow-lg shadow-amber-500/30">
                <span className="text-3xl text-white">♔</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-400 to-amber-200">
                  Cognitive Chess
                </h1>
                <p className="text-xs text-slate-400 mt-0.5">AI-Powered Chess Engine</p>
              </div>
            </div>

            {gameMode === 'playing' && (
              <div className="flex items-center gap-3">
                {inCheck && gameStatus === 'active' && (
                  <div className="px-3 py-1.5 bg-red-500/20 border-2 border-red-500 rounded-lg animate-pulse">
                    <span className="text-red-400 font-bold text-sm">⚔ CHECK!</span>
                  </div>
                )}
                <div className={`px-4 py-2 rounded-xl font-semibold text-sm shadow-lg ${
                  board.white_to_move
                    ? 'bg-white text-slate-900'
                    : 'bg-slate-800 text-white border-2 border-slate-600'
                }`}>
                  {board.white_to_move ? '♔ White' : '♚ Black'} to move
                </div>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {gameMode === 'new' ? (
          <div className="max-w-lg mx-auto mt-16">
            <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 overflow-hidden shadow-2xl backdrop-blur-xl">
              <div className="bg-gradient-to-r from-amber-500/20 via-amber-400/10 to-transparent border-b border-slate-700/50 px-6 py-5">
                <h2 className="text-xl font-bold text-white">New Game</h2>
                <p className="text-sm text-slate-400 mt-1">Challenge the AI cognitive engine</p>
              </div>

              <div className="p-6 space-y-6">
                {/* Color Selection */}
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-3">
                    Choose Your Color
                  </label>
                  <div className="grid grid-cols-2 gap-4">
                    <button
                      onClick={() => setPlayerColor('white')}
                      className={`group relative p-6 rounded-xl transition-all duration-300 ${
                        playerColor === 'white'
                          ? 'bg-gradient-to-br from-amber-500/20 to-amber-600/10 border-2 border-amber-500 shadow-lg shadow-amber-500/20'
                          : 'bg-slate-800/50 border-2 border-slate-700 hover:border-slate-500'
                      }`}
                    >
                      <div className="text-5xl mb-3 group-hover:scale-110 transition-transform">♔</div>
                      <div className="text-lg font-bold text-white">White</div>
                      <div className="text-sm text-slate-400 mt-1">Move first</div>
                      {playerColor === 'white' && (
                        <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-amber-500"></div>
                      )}
                    </button>

                    <button
                      onClick={() => setPlayerColor('black')}
                      className={`group relative p-6 rounded-xl transition-all duration-300 ${
                        playerColor === 'black'
                          ? 'bg-gradient-to-br from-amber-500/20 to-amber-600/10 border-2 border-amber-500 shadow-lg shadow-amber-500/20'
                          : 'bg-slate-800/50 border-2 border-slate-700 hover:border-slate-500'
                      }`}
                    >
                      <div className="text-5xl mb-3 group-hover:scale-110 transition-transform">♚</div>
                      <div className="text-lg font-bold text-white">Black</div>
                      <div className="text-sm text-slate-400 mt-1">AI moves first</div>
                      {playerColor === 'black' && (
                        <div className="absolute top-2 right-2 w-3 h-3 rounded-full bg-amber-500"></div>
                      )}
                    </button>
                  </div>
                </div>

                {/* Difficulty */}
                <div>
                  <label className="block text-sm font-semibold text-slate-200 mb-3">
                    AI Difficulty Level
                  </label>
                  <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-slate-400 text-sm">Level</span>
                      <span className="text-2xl font-bold text-amber-400">{difficulty}</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={difficulty}
                      onChange={(e) => setDifficulty(parseInt(e.target.value))}
                      className="w-full h-3 bg-slate-700 rounded-full appearance-none cursor-pointer accent-amber-500"
                    />
                    <div className="flex justify-between text-xs text-slate-500 mt-2">
                      <span>Beginner</span>
                      <span>Intermediate</span>
                      <span>Expert</span>
                    </div>
                  </div>
                </div>

                {/* Start Button */}
                <button
                  onClick={() => startNewGame(playerColor, difficulty)}
                  className="w-full py-4 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-white font-bold text-lg hover:from-amber-600 hover:to-amber-700 transition-all shadow-xl shadow-amber-500/30 hover:scale-[1.02] active:scale-[0.98]"
                >
                  Start Game
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Board Section */}
            <div className="xl:col-span-2 space-y-4">
              <div className="bg-gradient-to-br from-slate-800/60 to-slate-900/60 rounded-2xl border border-slate-700/50 p-5 backdrop-blur-xl shadow-xl">
                <ChessBoard
                  board={board}
                  selectedSquare={selectedSquare}
                  legalMoves={legalMoves}
                  lastMove={moveHistory.length > 0 && moveIndex >= 0 ?
                    ChessEngine.notationToMove(moveHistory[moveIndex], board) : null}
                  playerColor={playerColor}
                  onSquareClick={handleSquareClick}
                  flipped={playerColor === 'black'}
                />
              </div>

              <GameControls
                gameMode={gameMode}
                isAIThinking={isAIThinking}
                onStartNew={() => setGameMode('new')}
              />
            </div>

            {/* Side Panel */}
            <div className="space-y-4">
              <MoveHistory
                history={moveHistory}
                currentIndex={moveIndex}
                onMoveSelect={goToMove}
              />

              {cognitiveData && <CognitivePanel data={cognitiveData} />}

              {gameMode === 'gameover' && (
                <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 p-6 text-center backdrop-blur-xl shadow-xl">
                  <div className="text-6xl mb-4">
                    {gameStatus === 'checkmate' ? '👑' : '🤝'}
                  </div>
                  <h3 className="text-2xl font-bold text-white mb-2">
                    {gameStatus === 'checkmate' ? 'Checkmate!' : 'Draw!'}
                  </h3>
                  <p className="text-slate-400 mb-6">
                    {gameStatus === 'checkmate'
                      ? `${board.white_to_move ? 'Black' : 'White'} wins`
                      : 'Game ended in a draw'}
                  </p>
                  <button
                    onClick={() => setGameMode('new')}
                    className="px-8 py-3 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 text-white font-bold hover:from-amber-600 hover:to-amber-700 transition-all shadow-lg"
                  >
                    Play Again
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-slate-900/80 backdrop-blur-md border-t border-slate-700/50 py-3 mt-auto">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-slate-500">
          Cognitive Chess Engine - AI-Powered Strategic Analysis
        </div>
      </footer>
    </div>
  );
}
