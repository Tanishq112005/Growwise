import React, { useEffect, useRef } from 'react';
import { LogIn, Sparkles, Target, TrendingUp } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useUserStore } from '../store/userStore';
import { streamChatResponse } from './getData';
import ChatWelcomeHeader from '../components/ChatWelcomeHeader';
import ChatMessageBubble from '../components/ChatMessageBubble';
import ChatInputBar from '../components/ChatInputBar';

const STARTER_PROMPTS = [
  'Suggest top stocks to start investing',
  'What is the RELIANCE share price right now?',
  'I have ₹200, where do I start?',
  'What is a SIP? Explain simply',
];

export const AIChatView: React.FC = () => {
  const { messages, isStreaming, userId, chatId } = useChatStore();
  const { isAuthenticated, openAuthModal } = useUserStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update or stream tokens arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (text: string) => {
    if (!text.trim() || isStreaming) return;
    streamChatResponse(text, userId, chatId);
  };

  // ── Sign-in gate ──────────────────────────────────────────────────
  if (!isAuthenticated) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4 md:px-8 flex flex-col items-center justify-center min-h-[calc(100vh-6rem)] gap-8">
        {/* Icon cluster */}
        <div className="flex -space-x-3">
          {[
            { Icon: TrendingUp, bg: 'bg-blue-50 border-blue-100 text-blue-600' },
            { Icon: Target,     bg: 'bg-emerald-50 border-emerald-100 text-emerald-600' },
            { Icon: Sparkles,   bg: 'bg-amber-50 border-amber-100 text-amber-600' },
          ].map(({ Icon, bg }, i) => (
            <div key={i} className={`w-12 h-12 rounded-2xl border-2 border-white flex items-center justify-center shadow-sm ${bg}`}>
              <Icon className="w-5 h-5" />
            </div>
          ))}
        </div>

        {/* Heading */}
        <div className="text-center max-w-sm">
          <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight mb-2">
            Sign in to chat with your AI copilot
          </h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            Get live market quotes, personalised investing advice and goal tracking
            — all in one place on <span className="font-semibold text-blue-600">Growwise</span>.
          </p>
        </div>

        {/* Perks */}
        <div className="w-full max-w-xs space-y-2.5">
          {[
            { emoji: '📊', text: 'Live share prices & real-time P&L' },
            { emoji: '🎯', text: 'Goal tracker that updates as you invest' },
            { emoji: '🧠', text: 'AI answers grounded in real data, not guesses' },
          ].map(({ emoji, text }) => (
            <div key={text} className="flex items-center gap-3 bg-white rounded-2xl border border-slate-100 px-4 py-3 shadow-sm">
              <span className="text-lg">{emoji}</span>
              <span className="text-sm font-medium text-slate-700">{text}</span>
            </div>
          ))}
        </div>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row gap-3 w-full max-w-xs">
          <button
            type="button"
            onClick={() => openAuthModal('login')}
            className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-bold shadow transition-all active:scale-95"
          >
            <LogIn className="w-4 h-4" />
            Sign in
          </button>
          <button
            type="button"
            onClick={() => openAuthModal('signup')}
            className="flex-1 inline-flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-white border border-slate-200 hover:border-blue-300 text-slate-700 text-sm font-bold transition-all active:scale-95"
          >
            Create account
          </button>
        </div>
      </div>
    );
  }

  // ── Authenticated chat view ────────────────────────────────────────
  return (
    <div className="w-full max-w-4xl mx-auto px-4 md:px-8 py-6 md:py-8 flex flex-col min-h-[calc(100vh-4rem)] pb-8">
      {/* 1. Header & Welcome Area */}
      <ChatWelcomeHeader />

      {/* 2. Message Stream List */}
      <div className="flex-1 flex flex-col space-y-1 mb-6">
        {messages.length === 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {STARTER_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => handleSendMessage(prompt)}
                className="px-4 py-2 rounded-full bg-white border border-slate-200 text-slate-700 text-xs md:text-sm font-medium hover:border-blue-300 hover:bg-blue-50/60 transition-colors"
              >
                {prompt}
              </button>
            ))}
          </div>
        )}
        {messages.map((message, index) => (
          <ChatMessageBubble
            key={message.id}
            message={message}
            onQuickReply={
              index === messages.length - 1 && !isStreaming ? handleSendMessage : undefined
            }
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* 3. Question Input Bar */}
      <div className="sticky bottom-4 z-20 w-full pt-2">
        <ChatInputBar
          disabled={isStreaming}
          onSendMessage={handleSendMessage}
        />
      </div>
    </div>
  );
};

export default AIChatView;
