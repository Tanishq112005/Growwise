import React, { useEffect, useRef } from 'react';
import { useChatStore } from '../store/chatStore';
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages update or stream tokens arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = (text: string) => {
    if (!text.trim() || isStreaming) return;
    streamChatResponse(text, userId, chatId);
  };

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
