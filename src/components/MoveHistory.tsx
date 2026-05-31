import React from 'react';
import { ChevronLeft, ChevronRight, RotateCcw } from 'lucide-react';

interface MoveHistoryProps {
  history: string[];
  currentIndex: number;
  onMoveSelect: (index: number) => void;
}

export const MoveHistory: React.FC<MoveHistoryProps> = ({ history, currentIndex, onMoveSelect }) => {
  const formattedMoves: { moveNum: number; white?: string; black?: string }[] = [];

  for (let i = 0; i < history.length; i += 2) {
    formattedMoves.push({
      moveNum: Math.floor(i / 2) + 1,
      white: history[i],
      black: history[i + 1]
    });
  }

  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 overflow-hidden backdrop-blur-xl shadow-xl">
      <div className="bg-gradient-to-r from-amber-500/15 via-amber-400/10 to-transparent border-b border-slate-700/50 px-5 py-4">
        <h3 className="text-base font-bold text-white">Move History</h3>
        <p className="text-xs text-slate-400 mt-1">Click to replay positions</p>
      </div>

      {history.length === 0 ? (
        <div className="px-5 py-12 text-center">
          <div className="text-slate-600 text-sm">No moves yet</div>
        </div>
      ) : (
        <>
          <div className="max-h-64 overflow-y-auto p-3 space-y-1.5">
            {formattedMoves.map(({ moveNum, white, black }) => (
              <div key={moveNum} className="flex items-center gap-2">
                <span className="w-8 text-slate-500 text-right font-mono text-sm">
                  {moveNum}.
                </span>
                <button
                  onClick={() => onMoveSelect((moveNum - 1) * 2)}
                  className={`flex-1 px-3 py-2 rounded-lg text-left font-mono text-sm font-semibold transition-all ${
                    currentIndex === (moveNum - 1) * 2
                      ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg'
                      : 'bg-slate-800/50 hover:bg-slate-700/50 text-slate-200 border border-slate-700/50'
                  }`}
                >
                  {white}
                </button>
                {black && (
                  <button
                    onClick={() => onMoveSelect((moveNum - 1) * 2 + 1)}
                    className={`flex-1 px-3 py-2 rounded-lg text-left font-mono text-sm font-semibold transition-all ${
                      currentIndex === (moveNum - 1) * 2 + 1
                        ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-white shadow-lg'
                        : 'bg-slate-800/50 hover:bg-slate-700/50 text-slate-200 border border-slate-700/50'
                    }`}
                  >
                    {black}
                  </button>
                )}
              </div>
            ))}
          </div>

          <div className="bg-slate-900/50 border-t border-slate-700/50 px-4 py-3 flex items-center justify-between">
            <button
              onClick={() => onMoveSelect(Math.max(currentIndex - 1, -1))}
              disabled={currentIndex < 0}
              className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronLeft className="w-5 h-5 text-slate-300" />
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={() => onMoveSelect(-1)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 text-xs text-slate-300 font-medium transition-all"
              >
                <RotateCcw className="w-3.5 h-3.5" />
                Start
              </button>

              <div className="px-4 py-1.5 rounded-lg bg-slate-800 border border-slate-700 text-xs text-slate-400 font-mono font-semibold">
                {currentIndex < 0 ? 'Start' : `${currentIndex + 1} / ${history.length}`}
              </div>

              <button
                onClick={() => onMoveSelect(history.length - 1)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 text-xs text-slate-300 font-medium transition-all"
              >
                End
                <RotateCcw className="w-3.5 h-3.5 rotate-180" />
              </button>
            </div>

            <button
              onClick={() => onMoveSelect(Math.min(currentIndex + 1, history.length - 1))}
              disabled={currentIndex >= history.length - 1}
              className="p-2 rounded-lg bg-slate-800/50 hover:bg-slate-700/50 border border-slate-700/50 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              <ChevronRight className="w-5 h-5 text-slate-300" />
            </button>
          </div>
        </>
      )}
    </div>
  );
};
