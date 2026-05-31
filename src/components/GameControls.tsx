import React from 'react';
import { RotateCcw, Loader2, Plus, Sparkles } from 'lucide-react';
import { GameMode } from '../App';

interface GameControlsProps {
  gameMode: GameMode;
  isAIThinking: boolean;
  onStartNew: () => void;
}

export const GameControls: React.FC<GameControlsProps> = ({
  gameMode,
  isAIThinking,
  onStartNew
}) => {
  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 p-4 backdrop-blur-xl shadow-xl">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          {isAIThinking && (
            <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-500/30">
              <Loader2 className="w-5 h-5 text-cyan-400 animate-spin" />
              <div>
                <div className="text-sm font-bold text-cyan-300">AI Thinking...</div>
                <div className="text-xs text-cyan-400/70">Analyzing position</div>
              </div>
            </div>
          )}
        </div>

        <button
          onClick={onStartNew}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-slate-700 to-slate-800 hover:from-slate-600 hover:to-slate-700 text-white font-bold text-sm transition-all shadow-lg border border-slate-600"
        >
          <Plus className="w-4 h-4" />
          New Game
        </button>
      </div>
    </div>
  );
};
