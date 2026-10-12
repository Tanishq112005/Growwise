import React from 'react';
import { Bot, Plus } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { useUserStore } from '../store/userStore';

export const ChatWelcomeHeader: React.FC = () => {
  const { startNewChat, isStreaming } = useChatStore();
  const { user } = useUserStore();

  const greetingName = user?.name ? `Hey, ${user.name.split(' ')[0]}!` : 'Hey!';

  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3.5">
        <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 shadow-sm shrink-0">
          <Bot className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl md:text-2xl font-bold text-slate-900 flex items-center gap-1.5">
            {greetingName} <span className="inline-block animate-wiggle">👋</span>
          </h1>
          <p className="text-xs md:text-sm text-slate-500 font-medium">
            What would you like to understand today?
          </p>
        </div>
      </div>

      {/* New Chat Action Button */}
      <button
        type="button"
        disabled={isStreaming}
        onClick={() => startNewChat()}
        title="Start a new chat session and reset history"
        className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border border-slate-200 hover:border-blue-300 hover:bg-blue-50/60 text-slate-700 hover:text-blue-600 font-semibold text-xs md:text-sm shadow-xs transition-all duration-150 active:scale-95 disabled:opacity-40 disabled:cursor-not-allowed group"
      >
        <Plus className="w-4 h-4 text-slate-500 group-hover:text-blue-600 transition-colors" />
        <span>New Chat</span>
      </button>
    </div>
  );
};

export default ChatWelcomeHeader;
