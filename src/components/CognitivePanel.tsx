import React from 'react';
import { Brain, Target, Shield, Zap, BarChart3, Sparkles } from 'lucide-react';
import { CognitiveData } from '../lib/chessEngine';

interface CognitivePanelProps {
  data: CognitiveData;
}

export const CognitivePanel: React.FC<CognitivePanelProps> = ({ data }) => {
  const attentionItems = [
    { key: 'tactical', label: 'Tactical', icon: Zap, color: 'from-red-500 to-red-600' },
    { key: 'strategic', label: 'Strategic', icon: Target, color: 'from-emerald-500 to-emerald-600' },
    { key: 'defensive', label: 'Defensive', icon: Shield, color: 'from-cyan-500 to-cyan-600' },
    { key: 'endgame', label: 'Endgame', icon: BarChart3, color: 'from-purple-500 to-purple-600' }
  ];

  const topMoves = Object.entries(data.hybrid_scores)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  return (
    <div className="bg-gradient-to-br from-slate-800/80 to-slate-900/80 rounded-2xl border border-slate-700/50 overflow-hidden backdrop-blur-xl shadow-xl">
      <div className="bg-gradient-to-r from-amber-500/20 via-amber-400/10 to-transparent border-b border-slate-700/50 px-5 py-4 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
          <Brain className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-base font-bold text-white">AI Cognitive Analysis</h3>
          <p className="text-xs text-slate-400">Real-time thinking process</p>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Attention Profile */}
        <div>
          <h4 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">
            Attention Focus
          </h4>
          <div className="space-y-2">
            {attentionItems.map(({ key, label, icon: Icon, color }) => {
              const value = data.attention_profile[key] || 0;
              return (
                <div key={key} className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${color} flex items-center justify-center`}>
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-slate-200">{label}</span>
                      <span className="text-sm font-bold text-white">{(value * 100).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full bg-gradient-to-r ${color} transition-all duration-500`}
                        style={{ width: `${value * 100}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Strategic Reflection */}
        <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/30">
          <h4 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">
            Strategic Thoughts
          </h4>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <Target className="w-5 h-5 text-amber-400 mt-0.5 shrink-0" />
              <div>
                <div className="text-xs text-slate-500 uppercase mb-1">Primary Goal</div>
                <div className="text-sm font-medium text-white">{data.reflection.primary_goal}</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <Shield className="w-5 h-5 text-red-400 mt-0.5 shrink-0" />
              <div>
                <div className="text-xs text-slate-500 uppercase mb-1">Concern</div>
                <div className="text-sm text-slate-200">{data.reflection.concern}</div>
              </div>
            </div>
            <div className="flex items-center gap-3 pt-2 border-t border-slate-700/50">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              <div>
                <div className="text-xs text-slate-500 uppercase mb-1">Confidence</div>
                <div className="text-lg font-bold text-emerald-400">{data.reflection.confidence}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Narrative */}
        <div>
          <h4 className="text-xs font-bold text-slate-300 mb-2 uppercase tracking-wider">
            Thinking Process
          </h4>
          <div className="bg-slate-900/50 rounded-xl p-4 border border-slate-700/30">
            <p className="text-sm text-slate-200 leading-relaxed">
              {data.reflection.narrative}
            </p>
          </div>
        </div>

        {/* Move Rankings */}
        {topMoves.length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">
              Top Move Candidates
            </h4>
            <div className="space-y-2">
              {topMoves.map(([move, score], idx) => (
                <div key={move} className="flex items-center gap-2">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center font-bold text-sm ${
                    idx === 0
                      ? 'bg-gradient-to-br from-amber-400 to-amber-600 text-white'
                      : 'bg-slate-700/50 text-slate-300'
                  }`}>
                    {idx + 1}
                  </div>
                  <span className="font-mono text-sm font-bold text-white">{move}</span>
                  <div className="flex-1 h-2.5 bg-slate-700/50 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        idx === 0
                          ? 'bg-gradient-to-r from-amber-400 to-amber-500'
                          : 'bg-slate-500/50'
                      }`}
                      style={{ width: `${score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-slate-400 w-12 text-right font-semibold">
                    {(score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Engine Stats */}
        <div>
          <h4 className="text-xs font-bold text-slate-300 mb-3 uppercase tracking-wider">
            Engine Statistics
          </h4>
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/30 text-center">
              <div className="text-2xl font-bold text-white mb-1">
                {data.subconscious.depth_reached}
              </div>
              <div className="text-xs text-slate-400 font-medium">Depth</div>
            </div>
            <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/30 text-center">
              <div className="text-2xl font-bold text-white mb-1">
                {(data.subconscious.nodes_evaluated / 1000).toFixed(1)}k
              </div>
              <div className="text-xs text-slate-400 font-medium">Nodes</div>
            </div>
            <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/30 text-center">
              <div className="text-base font-bold text-white mb-1 font-mono">
                {data.subconscious.principal_variation?.[0] || '-'}
              </div>
              <div className="text-xs text-slate-400 font-medium">Best Move</div>
            </div>
          </div>
        </div>

        {/* Principal Variation */}
        {data.subconscious.principal_variation.length > 1 && (
          <div>
            <h4 className="text-xs font-bold text-slate-300 mb-2 uppercase tracking-wider">
              Principal Variation
            </h4>
            <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-700/30 flex items-center gap-2 overflow-x-auto">
              {data.subconscious.principal_variation.slice(0, 5).map((move, idx) => (
                <React.Fragment key={idx}>
                  <span className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-600 text-sm font-mono font-bold text-white">
                    {move}
                  </span>
                  {idx < Math.min(data.subconscious.principal_variation.length - 1, 4) && (
                    <span className="text-slate-500 text-lg">→</span>
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
