import React from 'react';
import { ChessBoardState, Move, ChessEngine } from '../lib/chessEngine';

interface ChessBoardProps {
  board: ChessBoardState;
  selectedSquare: { row: number; col: number } | null;
  legalMoves: Move[];
  lastMove: Move | null;
  playerColor: 'white' | 'black';
  onSquareClick: (row: number, col: number) => void;
  flipped: boolean;
}

export const ChessBoard: React.FC<ChessBoardProps> = ({
  board,
  selectedSquare,
  legalMoves,
  lastMove,
  playerColor,
  onSquareClick,
  flipped
}) => {
  const cols = 'abcdefgh';

  const getSquareColor = (row: number, col: number) => {
    const isLight = (row + col) % 2 === 0;
    return isLight ? 'bg-amber-100' : 'bg-amber-800';
  };

  const renderSquare = (row: number, col: number) => {
    const piece = board.grid[row][col];
    const isSelected = selectedSquare?.row === row && selectedSquare?.col === col;
    const isLegalMove = legalMoves.some(m => m.to_row === row && m.to_col === col);
    const isLastMoveFrom = lastMove && lastMove.from_row === row && lastMove.from_col === col;
    const isLastMoveTo = lastMove && lastMove.to_row === row && lastMove.to_col === col;

    const squareClasses = `
      w-full h-full relative cursor-pointer
      transition-all duration-200 ease-out
      ${getSquareColor(row, col)}
      ${isSelected ? 'ring-4 ring-yellow-400 ring-inset z-10' : ''}
      ${(isLastMoveFrom || isLastMoveTo) ? 'bg-yellow-300' : ''}
      hover:brightness-125
    `;

    return (
      <div
        key={`${row}-${col}`}
        onClick={() => onSquareClick(row, col)}
        className={squareClasses}
      >
        {/* Legal move dot */}
        {isLegalMove && piece === '.' && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-[30%] h-[30%] rounded-full bg-slate-900/20 backdrop-blur-sm" />
          </div>
        )}

        {/* Capture ring */}
        {isLegalMove && piece !== '.' && (
          <div className="absolute inset-0 pointer-events-none">
            <div className="w-full h-full rounded-full ring-4 ring-red-500/60 ring-inset" />
          </div>
        )}

        {/* Chess piece */}
        {piece !== '.' && (
          <div className="absolute inset-0 flex items-center justify-center select-none pointer-events-none">
            <span
              className="text-4xl sm:text-5xl md:text-6xl"
              style={{
                color: piece === piece.toUpperCase() ? '#FFFFFF' : '#1A1A1A',
                textShadow: piece === piece.toUpperCase()
                  ? '2px 2px 4px rgba(0,0,0,0.9), 0 0 8px rgba(0,0,0,0.8)'
                  : '2px 2px 4px rgba(0,0,0,0.5)',
                lineHeight: 1,
                fontWeight: 'bold'
              }}
            >
              {ChessEngine.getPieceSymbol(piece)}
            </span>
          </div>
        )}
      </div>
    );
  };

  const displayRows = flipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];
  const displayCols = flipped ? [7, 6, 5, 4, 3, 2, 1, 0] : [0, 1, 2, 3, 4, 5, 6, 7];

  return (
    <div className="flex flex-col items-center w-full max-w-2xl mx-auto">
      {/* Top file labels */}
      <div className="w-full flex mb-2 px-8 sm:px-12">
        {displayCols.map(col => (
          <div key={col} className="flex-1 text-center text-sm font-bold text-slate-300">
            {cols[col].toUpperCase()}
          </div>
        ))}
      </div>

      <div className="flex w-full items-stretch">
        {/* Left rank labels */}
        <div className="flex flex-col justify-around py-2 pr-2 sm:pr-3">
          {displayRows.map(row => (
            <div
              key={row}
              className="flex items-center justify-center text-sm font-bold text-slate-300"
              style={{ minHeight: '3rem' }}
            >
              {8 - row}
            </div>
          ))}
        </div>

        {/* Chess board */}
        <div className="flex-1 rounded-lg overflow-hidden shadow-2xl ring-2 ring-amber-900/40">
          <div className="grid grid-cols-8">
            {displayRows.map(row =>
              displayCols.map(col => renderSquare(row, col))
            )}
          </div>
        </div>

        {/* Right rank labels */}
        <div className="flex flex-col justify-around py-2 pl-2 sm:pl-3">
          {displayRows.map(row => (
            <div
              key={row}
              className="flex items-center justify-center text-sm font-bold text-slate-300"
              style={{ minHeight: '3rem' }}
            >
              {8 - row}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom file labels */}
      <div className="w-full flex mt-2 px-8 sm:px-12">
        {displayCols.map(col => (
          <div key={col} className="flex-1 text-center text-sm font-bold text-slate-300">
            {cols[col].toUpperCase()}
          </div>
        ))}
      </div>
    </div>
  );
};
