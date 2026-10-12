import React from 'react';
import { Target, Clock, ShieldCheck, Sparkles, TrendingUp } from 'lucide-react';
import { ActionCard } from '../store/chatStore';
import SuggestedStockCard from './SuggestedStockCard';

interface ActionCardViewProps {
  card: ActionCard;
}

/**
 * Generative-UI card emitted by agents:
 * - `goal_allocation_card`: Goal blueprint
 * - `stock_recommendation_card` or cards with `stocks`: Suggested stock cards with Buy CTA
 */
export const ActionCardView: React.FC<ActionCardViewProps> = ({ card }) => {
  // 1. Stock Recommendation / Suggested Products Card
  if (card.card_type === 'stock_recommendation_card' || (card.stocks && card.stocks.length > 0)) {
    const stocks = card.stocks || [];
    return (
      <div className="mt-4 w-full rounded-2xl border border-emerald-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-emerald-50 via-teal-50 to-blue-50 border-b border-emerald-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#00D09C] text-white flex items-center justify-center shadow-xs">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <span className="text-sm font-extrabold text-slate-900 block">
                {card.title || 'Suggested Investment Assets'}
              </span>
              <span className="text-[11px] text-slate-500 font-medium">
                Tap any stock card to simulate buy order
              </span>
            </div>
          </div>
          <span className="text-[10px] uppercase font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
            {stocks.length} Recommended
          </span>
        </div>

        {/* Responsive Stock Cards Grid */}
        <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-3.5 bg-slate-50/40">
          {stocks.map((stock) => (
            <SuggestedStockCard key={stock.symbol} stock={stock} />
          ))}
        </div>

        <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 text-[11px] text-slate-400">
          Educational simulation. No real money or bank balance will be charged.
        </div>
      </div>
    );
  }

  // 2. Goal Blueprint Card
  if (card.card_type === 'goal_allocation_card') {
    return (
      <div className="mt-3 w-full rounded-2xl border border-blue-100 bg-white shadow-sm overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100 flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-blue-600 text-white flex items-center justify-center">
            <Target className="w-4 h-4" />
          </div>
          <span className="text-sm font-bold text-slate-900">{card.title}</span>
        </div>

        <div className="px-4 py-3 space-y-2.5 text-xs md:text-sm">
          {card.strategy && (
            <div className="flex items-start gap-2.5">
              <Sparkles className="w-4 h-4 text-indigo-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-[11px] uppercase font-bold text-slate-400">Strategy</span>
                <span className="font-semibold text-slate-800">{card.strategy}</span>
              </div>
            </div>
          )}
          {card.liquidity_timeline && (
            <div className="flex items-start gap-2.5">
              <Clock className="w-4 h-4 text-emerald-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-[11px] uppercase font-bold text-slate-400">Taking money out</span>
                <span className="font-semibold text-slate-800">{card.liquidity_timeline}</span>
              </div>
            </div>
          )}
          {card.risk_profile && (
            <div className="flex items-start gap-2.5">
              <ShieldCheck className="w-4 h-4 text-amber-500 mt-0.5 shrink-0" />
              <div>
                <span className="block text-[11px] uppercase font-bold text-slate-400">Risk</span>
                <span className="font-semibold text-slate-800">{card.risk_profile}</span>
              </div>
            </div>
          )}
        </div>

        <div className="px-4 py-2 bg-slate-50 border-t border-slate-100 text-[11px] text-slate-400">
          Educational, not investment advice. Returns are not guaranteed and can be negative in the short term.
        </div>
      </div>
    );
  }

  return null;
};

export default ActionCardView;
