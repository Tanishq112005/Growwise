import React, { FormEvent, useState } from 'react';
import {
  Sparkles,
  MessageCircle,
  BookOpen,
  Target,
  ArrowRight,
  SendHorizontal,
  ShieldCheck,
  Coffee,
} from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useUserStore } from '../store/userStore';
import { streamChatResponse } from '../ai/getData';

const STARTER_ASKS = [
  { label: 'I have ₹200. Where do I start?', prompt: 'I have ₹200, where do I start?' },
  { label: 'What is a SIP, in plain English?', prompt: 'What is a SIP? Explain simply' },
  { label: 'My income is irregular. Can I still invest?', prompt: 'My income is irregular. Can I still invest?' },
  { label: 'What even is an index fund?', prompt: 'Explain what an Index Fund is using everyday brands like Zudio and Jio' },
];

const JARGON_CARDS = [
  {
    term: 'SIP',
    plain: 'A tiny auto-save. You put in a little money every month, like a standing UPI to your future self.',
    icon: Coffee,
    tint: 'bg-amber-50 border-amber-100 text-amber-600',
  },
  {
    term: 'Index fund',
    plain: 'Instead of picking one brand, you buy a mix of many — like a playlist, not a single song.',
    icon: BookOpen,
    tint: 'bg-blue-50 border-blue-100 text-blue-600',
  },
  {
    term: 'Portfolio',
    plain: 'Everything you own in one place. Your stocks, funds, and goals — not a fancy spreadsheet.',
    icon: Target,
    tint: 'bg-emerald-50 border-emerald-100 text-emerald-600',
  },
  {
    term: 'P&L',
    plain: 'Just “up or down vs what you paid.” Green is extra. Red is you paid more than it’s worth right now.',
    icon: Sparkles,
    tint: 'bg-indigo-50 border-indigo-100 text-indigo-600',
  },
];

export const HomeView: React.FC = () => {
  const { setActiveTab, userId, chatId, isStreaming } = useChatStore();
  const { user, isAuthenticated, openAuthModal } = useUserStore();
  const [ask, setAsk] = useState('');

  const firstName = user?.name ? user.name.split(' ')[0] : null;

  const openChatWith = (text: string) => {
    const prompt = text.trim();
    if (!prompt || isStreaming) return;
    setActiveTab('chat');
    streamChatResponse(prompt, userId, chatId);
  };

  const handleAskSubmit = (e: FormEvent) => {
    e.preventDefault();
    openChatWith(ask);
    setAsk('');
  };

  return (
    <div className="w-full max-w-6xl mx-auto px-4 md:px-8 py-8 md:py-12 pb-24">
      {/* Hero */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center mb-14">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold mb-4">
            <Sparkles className="w-3.5 h-3.5" />
            Built for first-timers, not finance bros
          </div>

          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight text-slate-900 leading-[1.15] mb-4">
            {firstName ? `${firstName}, money doesn’t have to sound like homework.` : 'Money talk, minus the jargon.'}
          </h1>

          <p className="text-base md:text-lg text-slate-500 font-medium max-w-xl mb-7 leading-relaxed">
            Growwise is your investing copilot. Ask in your words. We explain like a friend — with everyday
            examples, live prices, and goals you can actually stick to.
          </p>

          <form onSubmit={handleAskSubmit} className="w-full bg-white border border-slate-200/90 rounded-full shadow-sm pl-5 pr-2 py-1.5 flex items-center gap-3 mb-4 focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100">
            <input
              type="text"
              value={ask}
              disabled={isStreaming}
              onChange={(e) => setAsk(e.target.value)}
              placeholder="Ask anything. Example: what is a SIP?"
              className="flex-1 bg-transparent border-none outline-none text-slate-800 placeholder-slate-400 text-sm md:text-[15px] py-2"
            />
            <button
              type="submit"
              disabled={isStreaming || !ask.trim()}
              className="w-10 h-10 rounded-full bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center disabled:opacity-40 transition-colors shrink-0"
              aria-label="Ask"
            >
              <SendHorizontal className="w-4 h-4" />
            </button>
          </form>

          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setActiveTab('chat')}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-xs transition-all active:scale-95"
            >
              <MessageCircle className="w-4 h-4" />
              Talk to AI
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('dashboard')}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 hover:border-blue-300 text-slate-700 text-sm font-semibold transition-colors"
            >
              Open dashboard
              <ArrowRight className="w-4 h-4" />
            </button>
            {!isAuthenticated && (
              <button
                type="button"
                onClick={() => openAuthModal('signup')}
                className="text-sm font-semibold text-blue-600 hover:underline px-2"
              >
                Create a free account
              </button>
            )}
          </div>
        </div>

        {/* Chat preview card */}
        <div className="bg-white rounded-3xl border border-slate-100 shadow-sm p-5 md:p-6 relative overflow-hidden">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-9 h-9 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <MessageCircle className="w-4 h-4" />
            </div>
            <div>
              <p className="text-sm font-bold text-slate-900">How a real answer feels</p>
              <p className="text-[11px] text-slate-400 font-medium">Zero lecture. Just the point.</p>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex justify-end">
              <div className="max-w-[85%] rounded-2xl rounded-br-md bg-blue-600 text-white px-4 py-2.5 text-sm font-medium">
                Bro what even is a SIP
              </div>
            </div>
            <div className="flex justify-start">
              <div className="max-w-[90%] rounded-2xl rounded-bl-md bg-slate-50 border border-slate-100 px-4 py-3 text-sm text-slate-700 leading-relaxed">
                Think of it as a standing UPI to yourself. You pick an amount — even ₹100 — and it goes in
                every month on autopilot. You don’t need a “perfect” market day. You just show up.
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <span className="px-3 py-1 rounded-full bg-white border border-slate-200 text-[11px] font-semibold text-slate-500">
                Start with ₹100?
              </span>
              <span className="px-3 py-1 rounded-full bg-white border border-slate-200 text-[11px] font-semibold text-slate-500">
                Is this risky?
              </span>
            </div>
          </div>

          <div className="absolute right-0 bottom-0 w-1/2 h-16 opacity-20 pointer-events-none hidden md:block">
            <svg viewBox="0 0 400 100" className="w-full h-full stroke-blue-500 fill-none" strokeWidth="3">
              <path d="M0,80 Q100,60 200,40 T400,10" />
            </svg>
          </div>
        </div>
      </section>

      {/* Ask chips */}
      <section className="mb-12">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-wide mb-3">Try asking</p>
        <div className="flex flex-wrap gap-2">
          {STARTER_ASKS.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => openChatWith(item.prompt)}
              className="px-4 py-2 rounded-full bg-white border border-slate-200 text-slate-700 text-xs md:text-sm font-medium hover:border-blue-300 hover:bg-blue-50/60 transition-colors"
            >
              {item.label}
            </button>
          ))}
        </div>
      </section>

      {/* Jargon decoder */}
      <section className="mb-12">
        <div className="flex items-end justify-between gap-4 mb-5">
          <div>
            <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
              The words people throw around
            </h2>
            <p className="text-sm text-slate-500 font-medium mt-1">
              Here’s the translation. Tap a card if you want the longer, still-simple version.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {JARGON_CARDS.map((card) => {
            const Icon = card.icon;
            return (
              <button
                key={card.term}
                type="button"
                onClick={() => openChatWith(`Explain ${card.term} in the simplest way possible, with an everyday example`)}
                className="text-left bg-white rounded-3xl border border-slate-100 p-5 shadow-sm hover:border-blue-200 hover:bg-blue-50/30 transition-colors"
              >
                <div className={`w-9 h-9 rounded-xl border flex items-center justify-center mb-3 ${card.tint}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <p className="text-sm font-bold text-slate-900 mb-1">{card.term}</p>
                <p className="text-sm text-slate-500 leading-relaxed">{card.plain}</p>
              </button>
            );
          })}
        </div>
      </section>

      {/* How it works */}
      <section className="mb-12">
        <h2 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight mb-5">How this works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            {
              step: '01',
              title: 'Ask like a human',
              body: 'Type how you actually talk. “I have ₹500 and I’m scared” is a perfect first message.',
            },
            {
              step: '02',
              title: 'Get the simple version',
              body: 'We skip the textbook. Analogies, live prices, and next steps you can actually do.',
            },
            {
              step: '03',
              title: 'Track what matters',
              body: 'Save a goal. See your holdings. Come back when you have another “wait, what?” moment.',
            },
          ].map((item) => (
            <div key={item.step} className="bg-white rounded-3xl border border-slate-100 p-6 shadow-sm">
              <span className="text-xs font-bold text-blue-600">{item.step}</span>
              <h3 className="text-base font-bold text-slate-900 mt-2 mb-1.5">{item.title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="bg-white rounded-3xl border border-slate-100 shadow-sm p-6 md:p-8 flex flex-col md:flex-row md:items-center justify-between gap-5">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900">Not a lecture. Not a sales pitch.</h2>
            <p className="text-sm text-slate-500 mt-1 max-w-xl">
              This is education — so you understand before you act. Markets can go down. Nothing here is a
              guaranteed return or personal advice.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setActiveTab('chat')}
          className="inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold shadow-xs transition-all active:scale-95 shrink-0"
        >
          Start a chat
          <ArrowRight className="w-4 h-4" />
        </button>
      </section>
    </div>
  );
};

export default HomeView;
