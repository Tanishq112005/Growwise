import React, { useMemo } from 'react';
import { Bot, CheckCheck } from 'lucide-react';
import { ChatMessage, SuggestedStock } from '../store/chatStore';
import ActionCardView from './ActionCardView';
import SuggestedStockCard from './SuggestedStockCard';
import MarkdownMessage from './MarkdownMessage';
import ThinkingIndicator from './ThinkingIndicator';

const POPULAR_STOCKS: Record<string, SuggestedStock> = {
  RELIANCE: { symbol: 'RELIANCE', company_name: 'Reliance Industries Ltd', price: 2987.50, change: '+1.2%', exchange: 'NSE' },
  TCS: { symbol: 'TCS', company_name: 'Tata Consultancy Services', price: 3452.00, change: '+0.8%', exchange: 'NSE' },
  INFY: { symbol: 'INFY', company_name: 'Infosys Limited', price: 1785.40, change: '+1.5%', exchange: 'NSE' },
  HDFCBANK: { symbol: 'HDFCBANK', company_name: 'HDFC Bank Ltd', price: 1678.30, change: '-0.4%', exchange: 'NSE' },
  ICICIBANK: { symbol: 'ICICIBANK', company_name: 'ICICI Bank Ltd', price: 1145.20, change: '+0.9%', exchange: 'NSE' },
  SBIN: { symbol: 'SBIN', company_name: 'State Bank of India', price: 792.10, change: '+0.5%', exchange: 'NSE' },
  ZOMATO: { symbol: 'ZOMATO', company_name: 'Zomato Ltd', price: 268.40, change: '+2.1%', exchange: 'NSE' },
  TATAMOTORS: { symbol: 'TATAMOTORS', company_name: 'Tata Motors Ltd', price: 924.50, change: '+1.1%', exchange: 'NSE' },
  AAPL: { symbol: 'AAPL', company_name: 'Apple Inc.', price: 236.40, change: '+0.7%', exchange: 'NASDAQ', currency: 'USD' },
  MSFT: { symbol: 'MSFT', company_name: 'Microsoft Corporation', price: 442.20, change: '+1.3%', exchange: 'NASDAQ', currency: 'USD' },
  NVDA: { symbol: 'NVDA', company_name: 'NVIDIA Corporation', price: 138.80, change: '+2.4%', exchange: 'NASDAQ', currency: 'USD' },
};

interface ChatMessageBubbleProps {
  message: ChatMessage;
  /** Called when a quick-reply chip is tapped. Chips only render when this is provided. */
  onQuickReply?: (text: string) => void;
}

export const ChatMessageBubble: React.FC<ChatMessageBubbleProps> = ({ message, onQuickReply }) => {
  const isUser = message.sender === 'user';

  // Detect stocks mentioned in message text if no action card was emitted
  const detectedMentionedStocks = useMemo(() => {
    if (message.actionCard || message.isStreaming || isUser) return [];
    const textUpper = message.text.toUpperCase();
    const matches: SuggestedStock[] = [];
    Object.keys(POPULAR_STOCKS).forEach((sym) => {
      const regex = new RegExp(`\\b${sym}\\b`, 'i');
      if (regex.test(textUpper)) {
        matches.push(POPULAR_STOCKS[sym]);
      }
    });
    return matches.slice(0, 4);
  }, [message.text, message.actionCard, message.isStreaming, isUser]);

  if (isUser) {
    // -----------------------------------------------------------------
    // Human Chat Card: Right-aligned blue bubble with avatar and status
    // -----------------------------------------------------------------
    return (
      <div className="flex justify-end items-end gap-2.5 mb-6 group">
        <div className="flex flex-col items-end max-w-[85%] md:max-w-lg">
          <div className="bg-[#2563EB] text-white px-5 py-3.5 rounded-2xl rounded-tr-xs shadow-sm text-sm md:text-[15px] leading-relaxed">
            <p className="whitespace-pre-wrap">{message.text}</p>
          </div>
          <div className="flex items-center gap-1 mt-1.5 text-[11px] text-slate-400 font-medium pr-1">
            <span>{message.timestamp}</span>
            <CheckCheck className="w-3.5 h-3.5 text-blue-500" />
          </div>
        </div>

        {/* User Avatar */}
        <div className="w-8 h-8 rounded-full bg-slate-300 border border-slate-200 overflow-hidden shrink-0 shadow-xs mb-5">
          <img
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=120"
            alt="User avatar"
            className="w-full h-full object-cover"
          />
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------------
  const cleanText = useMemo(() => {
    return (message.text || '')
      .replace(/^\s*\{\s*"complete":[\s\S]*?\}\s*/, '')
      .replace(/!function_call:\s*\{[\s\S]*?\}/g, '')
      .replace(/<tool_call>[\s\S]*?<\/tool_call>/g, '')
      .trim();
  }, [message.text]);

  // AI Response Card: Left-aligned soft card with bot avatar
  // -------------------------------------------------------------------
  return (
    <div className="flex justify-start items-start gap-2.5 mb-6 group animate-fade-in-up">
      {/* Bot Avatar */}
      <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shrink-0 shadow-xs mt-1">
        <Bot className="w-4 h-4" />
      </div>

      <div className="flex flex-col items-start max-w-[92%] md:max-w-2xl">
        <div className="bg-[#F1F5F9] text-slate-800 px-5 py-4 rounded-2xl rounded-tl-xs border border-slate-200/60 shadow-xs text-sm md:text-[15px] leading-relaxed">
          {message.isStreaming && !cleanText ? (
            // Nothing streamed yet: show the "searching / thinking" animation
            <ThinkingIndicator status={message.status} />
          ) : (
            <MarkdownMessage text={cleanText} />
          )}

          {message.isStreaming && cleanText && (
            message.status ? (
              // A tool is running again mid-answer
              <ThinkingIndicator status={message.status} compact />
            ) : (
              <span className="inline-block w-1.5 h-4 mt-1 bg-blue-600 animate-pulse rounded-full align-middle"></span>
            )
          )}
        </div>

        {message.actionCard && <ActionCardView card={message.actionCard} />}

        {/* Fallback stock cards if AI mentioned stocks without an explicit action card */}
        {detectedMentionedStocks.length > 0 && (
          <div className="mt-3.5 w-full">
            <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-2">
              Featured Asset Cards
            </span>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full">
              {detectedMentionedStocks.map((stock) => (
                <SuggestedStockCard key={stock.symbol} stock={stock} />
              ))}
            </div>
          </div>
        )}

        {onQuickReply && !message.isStreaming && message.quickReplies && message.quickReplies.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-3">
            {message.quickReplies.map((reply) => (
              <button
                key={reply}
                type="button"
                onClick={() => onQuickReply(reply)}
                className="px-3.5 py-1.5 rounded-full bg-white border border-blue-200 text-blue-700 text-xs md:text-sm font-semibold hover:bg-blue-50 transition-colors active:scale-95"
              >
                {reply}
              </button>
            ))}
          </div>
        )}

        <span className="text-[11px] text-slate-400 font-medium pl-1 mt-1.5">
          {message.timestamp}
        </span>
      </div>
    </div>
  );
};

export default ChatMessageBubble;
