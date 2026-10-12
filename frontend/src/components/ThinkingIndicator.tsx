import React, { useEffect, useState } from 'react';
import { Search, Sparkles } from 'lucide-react';

// Shown until the backend tells us what it is actually doing (agent / tool events).
const FALLBACK_STEPS = [
  'Understanding your question…',
  'Thinking it through…',
  'Putting your answer together…',
];

interface ThinkingIndicatorProps {
  /** Live status from the backend (e.g. "Searching the web…"). Falls back to rotating generic steps. */
  status?: string;
  /** Small pill version, used when text is already streaming but a tool is running again. */
  compact?: boolean;
}

export const ThinkingIndicator: React.FC<ThinkingIndicatorProps> = ({ status, compact = false }) => {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (status) return;
    const timer = setInterval(() => {
      setStepIndex((i) => (i + 1) % FALLBACK_STEPS.length);
    }, 1800);
    return () => clearInterval(timer);
  }, [status]);

  const label = status || FALLBACK_STEPS[stepIndex];
  const isSearching = /search|fetch|checking|live/i.test(label);
  const Icon = isSearching ? Search : Sparkles;

  return (
    <div
      className={`flex items-center gap-2.5 ${compact ? 'mt-3 pt-2.5 border-t border-slate-200/70' : ''}`}
      role="status"
      aria-live="polite"
    >
      <span className="relative flex h-6 w-6 items-center justify-center shrink-0">
        <span className="absolute inline-flex h-full w-full rounded-full bg-blue-400/30 animate-ping" />
        <span className="relative flex h-6 w-6 items-center justify-center rounded-full bg-blue-100 text-blue-600">
          <Icon className="h-3.5 w-3.5" />
        </span>
      </span>

      <span
        key={label}
        className="text-sm font-medium bg-gradient-to-r from-slate-400 via-slate-800 to-slate-400 bg-[length:200%_100%] bg-clip-text text-transparent animate-shimmer"
      >
        {label}
      </span>

      <span className="flex items-center gap-1" aria-hidden="true">
        {[0, 150, 300].map((delay) => (
          <span
            key={delay}
            className="h-1.5 w-1.5 rounded-full bg-blue-500 animate-bounce"
            style={{ animationDelay: `${delay}ms` }}
          />
        ))}
      </span>
    </div>
  );
};

export default ThinkingIndicator;
