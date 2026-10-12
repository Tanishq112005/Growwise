import React from 'react';
import { TrendingUp, TrendingDown, ShoppingBag, Sparkles } from 'lucide-react';
import { SuggestedStock } from '../store/chatStore';
import { useStockModalStore } from '../store/stockModalStore';

interface SuggestedStockCardProps {
  stock: SuggestedStock;
}

export const SuggestedStockCard: React.FC<SuggestedStockCardProps> = ({ stock }) => {
  const { openBuyModal } = useStockModalStore();

  const handleOpenBuy = (e: React.MouseEvent) => {
    e.stopPropagation();
    openBuyModal({
      symbol: stock.symbol,
      companyName: stock.company_name || stock.symbol,
      price: stock.price,
      change: stock.change,
      currency: stock.currency || 'INR',
      exchange: stock.exchange || 'NSE',
    });
  };

  const isPositive = !stock.change || !stock.change.startsWith('-');
  const currencySymbol = stock.currency === 'USD' ? '$' : '₹';

  const formatPrice = (val: number) => {
    return `${currencySymbol}${val.toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  };

  // Deterministic accent color based on symbol letter
  const getAvatarGradient = (sym: string) => {
    const code = (sym.charCodeAt(0) || 65) % 4;
    switch (code) {
      case 0:
        return 'from-emerald-500 to-teal-600 text-white';
      case 1:
        return 'from-blue-600 to-indigo-600 text-white';
      case 2:
        return 'from-purple-600 to-pink-600 text-white';
      default:
        return 'from-amber-500 to-orange-600 text-white';
    }
  };

  return (
    <div
      onClick={handleOpenBuy}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleOpenBuy(e as any);
        }
      }}
      className="group relative bg-white hover:bg-gradient-to-b hover:from-white hover:to-emerald-50/20 border border-slate-200/80 hover:border-emerald-400/90 rounded-2xl p-4 shadow-xs hover:shadow-md transition-all duration-200 cursor-pointer flex flex-col justify-between gap-3 text-left w-full"
    >
      {/* 1. Header: Symbol, Avatar & Change */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2.5">
          <div
            className={`w-9 h-9 rounded-xl bg-gradient-to-br ${getAvatarGradient(
              stock.symbol
            )} flex items-center justify-center font-bold text-xs shadow-xs shrink-0`}
          >
            {stock.symbol.slice(0, 2).toUpperCase()}
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-sm md:text-base text-slate-900 group-hover:text-emerald-700 transition-colors">
                {stock.symbol}
              </span>
              <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded-md bg-slate-100 text-slate-500">
                {stock.exchange || 'NSE'}
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium truncate max-w-[150px] md:max-w-[180px]">
              {stock.company_name || stock.symbol}
            </p>
          </div>
        </div>

        {/* Change Badge */}
        {stock.change && (
          <div
            className={`flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-bold shrink-0 ${
              isPositive
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/60'
                : 'bg-rose-50 text-rose-700 border border-rose-200/60'
            }`}
          >
            {isPositive ? (
              <TrendingUp className="w-3 h-3 text-emerald-600" />
            ) : (
              <TrendingDown className="w-3 h-3 text-rose-600" />
            )}
            <span>{stock.change}</span>
          </div>
        )}
      </div>

      {/* 2. Tag / Category if provided */}
      {stock.tag && (
        <div className="flex items-center gap-1 text-[11px] font-semibold text-indigo-600 bg-indigo-50/80 px-2 py-0.5 rounded-md self-start">
          <Sparkles className="w-3 h-3" />
          <span>{stock.tag}</span>
        </div>
      )}

      {/* 3. Footer: Live Price & Buy Action */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100">
        <div>
          <span className="block text-[10px] uppercase font-bold text-slate-400">
            Current Price
          </span>
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="text-base md:text-lg font-black text-slate-900 tracking-tight">
              {formatPrice(stock.price)}
            </span>
          </div>
        </div>

        {/* Primary Buy Button */}
        <button
          type="button"
          onClick={handleOpenBuy}
          className="px-3.5 py-1.5 rounded-xl bg-[#00D09C] hover:bg-[#00B887] text-white text-xs font-bold transition-all shadow-xs active:scale-95 flex items-center gap-1.5 group-hover:shadow-emerald-200"
        >
          <ShoppingBag className="w-3.5 h-3.5" />
          <span>Buy</span>
        </button>
      </div>
    </div>
  );
};

export default SuggestedStockCard;
