import React, { useState, useEffect, useCallback } from 'react';
import {
  TrendingUp,
  Target,
  Eye,
  Briefcase,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
  ChevronRight,
  BookOpen,
  Plus,
  RefreshCw,
  ShoppingBag,
} from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useUserStore } from '../store/userStore';
import { useStockModalStore } from '../store/stockModalStore';

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

interface StockHoldingValuation {
  symbol: string;
  company_name: string;
  quantity: number;
  buy_price: number;
  current_price: number;
  invested_value: number;
  current_value: number;
  pnl: number;
  pnl_percent: number;
  pnl_display: string;
  currency?: string;
}

interface PortfolioValuation {
  total_portfolio_value: number;
  total_invested: number;
  total_pnl: number;
  total_pnl_percent: number;
  total_profit: number;
  total_loss: number;
  holdings_count: number;
  holdings: StockHoldingValuation[];
}

interface UserGoal {
  goal_id: string;
  task: string;
  percentage_of_completion: number;
}

interface RecentlyViewedStock {
  symbol: string;
  company_name: string;
  price?: number;
  change?: string;
}

export const DashboardView: React.FC = () => {
  const { setActiveTab, userId, setInputPrompt } = useChatStore();
  const { user } = useUserStore();
  const { openBuyModal, lastPurchasedStock } = useStockModalStore();

  const [valuation, setValuation] = useState<PortfolioValuation>({
    total_portfolio_value: 0,
    total_invested: 0,
    total_pnl: 0,
    total_pnl_percent: 0,
    total_profit: 0,
    total_loss: 0,
    holdings_count: 0,
    holdings: [],
  });

  const [goals, setGoals] = useState<UserGoal[]>([]);
  const [recentlyViewed, setRecentlyViewed] = useState<RecentlyViewedStock[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [lastUpdated, setLastUpdated] = useState<string>('Just now');

  const displayName = user?.name ? user.name.split(' ')[0] : 'Investor';
  const effectiveUserId = user?.user_id || userId;

  const fetchDashboardData = useCallback(async () => {
    if (!effectiveUserId) return;
    setIsLoading(true);
    try {
      // 1. Fetch live portfolio valuation calculated via Twelve Data & buy prices
      const valPromise = fetch(`${API_BASE}/api/stocks/${effectiveUserId}/valuation`)
        .then((res) => (res.ok ? res.json() : null))
        .catch(() => null);

      // 2. Fetch user financial goals
      const goalsPromise = fetch(`${API_BASE}/api/goals/${effectiveUserId}`)
        .then((res) => (res.ok ? res.json() : { goals: [] }))
        .catch(() => ({ goals: [] }));

      // 3. Fetch recently viewed stocks
      const recentPromise = fetch(`${API_BASE}/api/stocks/${effectiveUserId}/recently-viewed`)
        .then((res) => (res.ok ? res.json() : { recently_viewed: [] }))
        .catch(() => ({ recently_viewed: [] }));

      const [valData, goalsData, recentData] = await Promise.all([
        valPromise,
        goalsPromise,
        recentPromise,
      ]);

      if (valData && valData.status === 'success') {
        setValuation(valData);
      }
      setGoals(goalsData.goals || []);
      setRecentlyViewed(recentData.recently_viewed || []);

      const now = new Date();
      setLastUpdated(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    } catch (e) {
      console.warn('[DashboardView] Failed to fetch dashboard data:', e);
    } finally {
      setIsLoading(false);
    }
  }, [effectiveUserId]);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // Automatically refresh live valuation when a user finishes a purchase
  useEffect(() => {
    if (lastPurchasedStock) {
      fetchDashboardData();
    }
  }, [lastPurchasedStock, fetchDashboardData]);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2,
    }).format(val);
  };

  const handleActionClick = (promptText: string) => {
    setInputPrompt(promptText);
    setActiveTab('chat');
  };

  const primaryGoal = goals.length > 0 ? goals[0] : null;

  return (
    <div className="w-full max-w-6xl mx-auto px-4 md:px-8 py-6 md:py-8 pb-28">
      {/* 1. Greeting Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
            Good morning, {displayName} <span className="inline-block animate-wiggle">👋</span>
          </h1>
          <p className="text-sm md:text-base text-slate-500 font-medium mt-0.5">
            Your money, made easier.
          </p>
        </div>

        <button
          type="button"
          onClick={fetchDashboardData}
          disabled={isLoading}
          title="Refresh live Twelve Data quotes and recalculate P&L"
          className="inline-flex items-center gap-2 px-3.5 py-2 rounded-2xl bg-white border border-slate-200 hover:border-blue-300 text-slate-700 hover:text-blue-600 transition-all shadow-2xs active:scale-95 disabled:opacity-50 text-xs font-semibold"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin text-blue-600' : ''}`} />
          <span>{isLoading ? 'Updating...' : 'Refresh Quotes'}</span>
        </button>
      </div>

      {/* 2. Main Portfolio Hero Card */}
      <div className="bg-white rounded-3xl border border-slate-100 p-6 md:p-8 shadow-sm mb-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-10 h-10 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-2xs">
                <TrendingUp className="w-5 h-5" />
              </div>
              <span className="text-xs md:text-sm font-semibold text-slate-500">
                Portfolio value (Live Twelve Data)
              </span>
            </div>

            <div className="flex items-baseline gap-3 mb-1">
              <span className="text-3xl md:text-4xl font-extrabold text-slate-900 tracking-tight">
                {valuation.holdings_count > 0 ? formatCurrency(valuation.total_portfolio_value) : '₹0.00'}
              </span>
            </div>

            {valuation.holdings_count > 0 ? (
              <div
                className={`flex items-center gap-1.5 text-xs md:text-sm font-semibold mb-1 ${
                  valuation.total_pnl >= 0 ? 'text-emerald-600' : 'text-rose-600'
                }`}
              >
                {valuation.total_pnl >= 0 ? (
                  <ArrowUpRight className="w-4 h-4" />
                ) : (
                  <ArrowDownRight className="w-4 h-4" />
                )}
                <span>
                  {valuation.total_pnl >= 0 ? '+' : ''}
                  {formatCurrency(valuation.total_pnl)} ({valuation.total_pnl >= 0 ? '+' : ''}
                  {valuation.total_pnl_percent.toFixed(1)}%)
                </span>
              </div>
            ) : (
              <p className="text-xs text-slate-400 font-normal mb-1">
                No active holdings yet • Start investing from ₹100
              </p>
            )}

            <p className="text-xs text-slate-400 font-normal">
              {valuation.holdings_count} {valuation.holdings_count === 1 ? 'position' : 'positions'} tracked in MongoDB
            </p>
          </div>

          {/* Right Summary Chips */}
          <div className="flex flex-row md:flex-col gap-3">
            <div className="flex-1 md:flex-none flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-emerald-50 border border-emerald-100 text-emerald-700">
              <TrendingUp className="w-4 h-4 text-emerald-600 shrink-0" />
              <div>
                <span className="text-[10px] uppercase font-bold text-emerald-600 block leading-tight">
                  Invested (Buy Value)
                </span>
                <span className="text-sm font-bold text-emerald-700">
                  {formatCurrency(valuation.total_invested)}
                </span>
              </div>
            </div>

            <div className="flex-1 md:flex-none flex items-center gap-2.5 px-4 py-2.5 rounded-2xl bg-blue-50 border border-blue-100 text-blue-700">
              <Target className="w-4 h-4 text-blue-600 shrink-0" />
              <div>
                <span className="text-[10px] uppercase font-bold text-blue-600 block leading-tight">
                  Total Profit
                </span>
                <span className="text-sm font-bold text-blue-700">
                  +{formatCurrency(valuation.total_profit)}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Decorative SVG curve */}
        <div className="absolute right-0 bottom-0 w-1/2 h-20 opacity-30 pointer-events-none hidden md:block">
          <svg viewBox="0 0 400 100" className="w-full h-full stroke-blue-500 fill-none" strokeWidth="3">
            <path d="M0,80 Q100,60 200,40 T400,10" />
          </svg>
        </div>

        <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
          <span>Real-time Pricing • Powered by Twelve Data & MongoDB</span>
          <span>Last recalculated: {lastUpdated}</span>
        </div>
      </div>

      {/* 3. Grid Row: Current Goal & Recently Viewed */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Your Current Goal */}
        <div className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-emerald-50 border border-emerald-100 flex items-center justify-center text-emerald-600">
                  <Target className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-slate-700">Your current goal</span>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400" />
            </div>

            {primaryGoal ? (
              <>
                <h2 className="text-lg font-bold text-slate-900 mb-2 truncate">
                  {primaryGoal.task}
                </h2>

                <div className="inline-block px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-600 font-semibold text-xs mb-4">
                  Goal in progress
                </div>

                {/* Progress Bar */}
                <div className="mb-4">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-500 mb-1.5">
                    <span>Progress</span>
                    <span className="text-blue-600">
                      {Math.round(primaryGoal.percentage_of_completion || 0)}%
                    </span>
                  </div>
                  <div className="w-full h-2.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-600 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, Math.max(5, primaryGoal.percentage_of_completion || 0))}%`,
                      }}
                    ></div>
                  </div>
                </div>

                <div className="pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-slate-400">Manage with AI Copilot</span>
                  <button
                    type="button"
                    onClick={() => handleActionClick(`Tell me how to reach my goal: "${primaryGoal.task}"`)}
                    className="font-semibold text-blue-600 hover:underline"
                  >
                    View strategy →
                  </button>
                </div>
              </>
            ) : (
              <div className="py-4 text-center">
                <p className="text-sm font-bold text-slate-800 mb-1">No active goals yet</p>
                <p className="text-xs text-slate-400 mb-4">
                  Set a savings habit or investment target with AI guidance.
                </p>
                <button
                  type="button"
                  onClick={() => handleActionClick('I want to set a goal to invest ₹500 every month')}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs transition-colors shadow-xs"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Create Goal with AI</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Recently Viewed */}
        <div className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                <Eye className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-slate-700">
                {recentlyViewed.length > 0 ? 'Recently viewed' : 'Market Leaders'}
              </span>
            </div>
            <button
              type="button"
              onClick={() => handleActionClick('Show me live quotes for top Indian benchmark stocks')}
              className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
            >
              Explore all <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3.5">
            {(recentlyViewed.length > 0
              ? recentlyViewed.slice(0, 3)
              : [
                  { symbol: 'RELIANCE', company_name: 'Reliance Industries', price: 2987.5, change: '+1.2%' },
                  { symbol: 'TCS', company_name: 'Tata Consultancy Services', price: 3452.0, change: '+0.8%' },
                  { symbol: 'HDFCBANK', company_name: 'HDFC Bank', price: 1678.3, change: '-0.4%' },
                ]
            ).map((item, idx) => (
              <div
                key={idx}
                onClick={() => handleActionClick(`What is the live quote and outlook for ${item.symbol}?`)}
                className="flex items-center justify-between py-1.5 hover:bg-slate-50/80 px-2 rounded-xl cursor-pointer transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-slate-900 text-white flex items-center justify-center font-bold text-xs shrink-0">
                    {item.symbol.charAt(0)}
                  </div>
                  <div>
                    <span className="text-xs md:text-sm font-bold text-slate-900 block truncate max-w-[150px]">
                      {item.company_name}
                    </span>
                    <span className="text-[11px] text-slate-400 font-medium">
                      {item.price ? formatCurrency(item.price) : item.symbol}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      (item.change || '').startsWith('-')
                        ? 'text-rose-600 bg-rose-50'
                        : 'text-emerald-600 bg-emerald-50'
                    }`}
                  >
                    {item.change || '+0.0%'}
                  </span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      openBuyModal({
                        symbol: item.symbol,
                        companyName: item.company_name,
                        price: item.price || 1000,
                        change: item.change,
                      });
                    }}
                    className="px-2.5 py-1 rounded-lg bg-[#00D09C]/10 hover:bg-[#00D09C] text-[#00A87E] hover:text-white text-xs font-bold transition-all flex items-center gap-1 active:scale-95"
                  >
                    <ShoppingBag className="w-3 h-3" />
                    <span>Buy</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. Grid Row: Your Portfolio & Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Your Portfolio List */}
        <div className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-xl bg-purple-50 border border-purple-100 flex items-center justify-center text-purple-600">
                <Briefcase className="w-4 h-4" />
              </div>
              <span className="text-xs font-bold text-slate-700">Your portfolio holdings</span>
            </div>
            {valuation.holdings_count > 0 && (
              <button
                type="button"
                onClick={() => handleActionClick('Review my portfolio and suggest rebalancing')}
                className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
              >
                Analyze <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {valuation.holdings_count > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="text-slate-400 border-b border-slate-100">
                    <th className="pb-2 font-normal">Stock</th>
                    <th className="pb-2 font-normal">Qty</th>
                    <th className="pb-2 font-normal">Buy price</th>
                    <th className="pb-2 font-normal">Live price</th>
                    <th className="pb-2 font-normal text-right">P&L</th>
                    <th className="pb-2 font-normal text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {valuation.holdings.map((stock, i) => (
                    <tr
                      key={i}
                      className="hover:bg-slate-50/60"
                    >
                      <td
                        onClick={() => handleActionClick(`Tell me about my position in ${stock.symbol}`)}
                        className="py-3 font-bold text-slate-800 cursor-pointer hover:text-blue-600"
                      >
                        {stock.company_name || stock.symbol}
                      </td>
                      <td className="py-3 text-slate-500">{stock.quantity || 1}</td>
                      <td className="py-3 font-semibold text-slate-700">
                        {formatCurrency(stock.buy_price)}
                      </td>
                      <td className="py-3 font-semibold text-slate-900">
                        {formatCurrency(stock.current_price)}
                      </td>
                      <td
                        className={`py-3 text-right font-bold ${
                          stock.pnl >= 0 ? 'text-emerald-600' : 'text-rose-600'
                        }`}
                      >
                        {stock.pnl_display}
                      </td>
                      <td className="py-3 text-right">
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            openBuyModal({
                              symbol: stock.symbol,
                              companyName: stock.company_name,
                              price: stock.current_price,
                            });
                          }}
                          className="px-2 py-0.5 rounded-md bg-emerald-50 hover:bg-emerald-100 text-[#00A87E] text-[11px] font-bold transition-colors"
                        >
                          + Buy
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center">
              <p className="text-xs font-bold text-slate-700 mb-1">No stock positions held yet</p>
              <p className="text-xs text-slate-400 mb-4">
                Ask AI Copilot to help you pick your first index fund or stock.
              </p>
              <button
                type="button"
                onClick={() => handleActionClick('I have ₹500 to invest. Which stocks or index funds should I start with?')}
                className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold text-xs transition-colors"
              >
                <span>Find beginner stocks →</span>
              </button>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <div className="w-8 h-8 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center text-amber-600">
              <Zap className="w-4 h-4" />
            </div>
            <span className="text-xs font-bold text-slate-700">Quick actions</span>
          </div>

          <div className="space-y-3">
            <div
              onClick={() => handleActionClick('Help me create a savings goal with a realistic timeframe')}
              className="p-3.5 rounded-2xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/40 transition-colors flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
                  <Target className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-xs md:text-sm font-bold text-slate-800 block">Create a goal</span>
                  <span className="text-[11px] text-slate-400">Plan micro-SIPs and targets with AI</span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
            </div>

            <div
              onClick={() => handleActionClick('What are the top 3 Nifty 50 stocks for long-term growth?')}
              className="p-3.5 rounded-2xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/40 transition-colors flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
                  <Eye className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-xs md:text-sm font-bold text-slate-800 block">Explore stocks</span>
                  <span className="text-[11px] text-slate-400">Zero-jargon breakdowns and live data</span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
            </div>

            <div
              onClick={() => handleActionClick('Explain what an Index Fund is using everyday brands like Zudio and Jio')}
              className="p-3.5 rounded-2xl border border-slate-100 hover:border-blue-200 hover:bg-blue-50/40 transition-colors flex items-center justify-between cursor-pointer group"
            >
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
                  <BookOpen className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-xs md:text-sm font-bold text-slate-800 block">Learn investing</span>
                  <span className="text-[11px] text-slate-400">Simple, relatable everyday analogies</span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 transition-colors" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardView;
