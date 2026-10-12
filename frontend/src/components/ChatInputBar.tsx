import React, { useState, FormEvent, KeyboardEvent } from 'react';
import { SendHorizontal } from 'lucide-react';

interface ChatInputBarProps {
  onSendMessage: (text: string) => void;
  disabled?: boolean;
}

export const ChatInputBar: React.FC<ChatInputBarProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e?: FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || disabled) return;

    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full bg-white border border-slate-200/90 rounded-full shadow-sm pl-5 pr-2 py-1.5 flex items-center gap-3 transition-all focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100"
    >
      <input
        type="text"
        value={input}
        disabled={disabled}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything about investing..."
        className="flex-1 bg-transparent border-none outline-none text-slate-800 placeholder-slate-400 text-sm md:text-[15px] font-normal py-1.5"
      />

      <button
        type="submit"
        disabled={!input.trim() || disabled}
        aria-label="Send message"
        className="w-10 h-10 rounded-full bg-[#2563EB] hover:bg-blue-700 text-white flex items-center justify-center shrink-0 shadow-sm transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-[#2563EB]"
      >
        <SendHorizontal className="w-4 h-4 ml-0.5" />
      </button>
    </form>
  );
};

export default ChatInputBar;
