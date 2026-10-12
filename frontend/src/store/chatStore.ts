import { create } from 'zustand';

export interface SuggestedStock {
  symbol: string;
  company_name: string;
  price: number;
  change?: string;
  currency?: string;
  exchange?: string;
  tag?: string;
}

export interface ActionCard {
  card_type: string;
  title: string;
  principal?: number;
  strategy?: string;
  liquidity_timeline?: string;
  risk_profile?: string;
  stocks?: SuggestedStock[];
}

export interface ChatMessage {
  id: string;
  sender: 'user' | 'ai';
  text: string;
  timestamp: string;
  isStreaming?: boolean;
  /** Live "what the agent is doing" label (e.g. "Searching the web…"), shown until text starts streaming. */
  status?: string;
  actionCard?: ActionCard | null;
  quickReplies?: string[];
}

interface ChatState {
  activeTab: 'home' | 'dashboard' | 'chat';
  messages: ChatMessage[];
  inputPrompt: string;
  isStreaming: boolean;
  userId: string;
  chatId: string;

  // Actions
  setActiveTab: (tab: 'home' | 'dashboard' | 'chat') => void;
  setInputPrompt: (text: string) => void;
  setStreaming: (status: boolean) => void;
  setUserId: (id: string) => void;
  setChatId: (id: string) => void;
  addUserMessage: (text: string) => string;
  addAIMessagePlaceholder: () => string;
  appendStreamChunk: (messageId: string, chunk: string) => void;
  setMessageStatus: (messageId: string, status?: string) => void;
  setMessageCard: (messageId: string, card: ActionCard) => void;
  setMessageQuickReplies: (messageId: string, replies: string[]) => void;
  finalizeAIMessage: (messageId: string, fullText: string) => void;
  setMessages: (messages: ChatMessage[]) => void;
  resetChat: () => void;
  startNewChat: () => string;
}

const generateUniqueChatId = () => `chat_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;

// Each browser gets its own stable guest id, so evaluators opening the deployed app
// don't share goals or chat history with each other (the backend creates the user on first message).
const getOrCreateUserId = (): string => {
  const KEY = 'growwise_user_id';
  try {
    const existing = localStorage.getItem(KEY);
    if (existing) return existing;
    const fresh = `guest_${crypto.randomUUID()}`;
    localStorage.setItem(KEY, fresh);
    return fresh;
  } catch {
    return `guest_${Date.now()}`;
  }
};

export const useChatStore = create<ChatState>((set) => ({
  activeTab: 'home',
  userId: getOrCreateUserId(),
  chatId: generateUniqueChatId(),
  inputPrompt: '',
  isStreaming: false,
  messages: [],

  setActiveTab: (tab) => set({ activeTab: tab }),

  setInputPrompt: (text) => set({ inputPrompt: text }),

  setStreaming: (status) => set({ isStreaming: status }),

  setUserId: (id) => set({ userId: id }),

  setChatId: (id) => set({ chatId: id }),

  addUserMessage: (text: string) => {
    const id = `user-${Date.now()}`;
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const newMessage: ChatMessage = {
      id,
      sender: 'user',
      text,
      timestamp: timeString,
    };

    set((state) => ({
      messages: [...state.messages, newMessage],
      inputPrompt: '',
    }));

    return id;
  },

  addAIMessagePlaceholder: () => {
    const id = `ai-${Date.now()}`;
    const now = new Date();
    const timeString = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const placeholder: ChatMessage = {
      id,
      sender: 'ai',
      text: '',
      timestamp: timeString,
      isStreaming: true,
    };

    set((state) => ({
      messages: [...state.messages, placeholder],
      isStreaming: true,
    }));

    return id;
  },

  appendStreamChunk: (messageId: string, chunk: string) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, text: msg.text + chunk, status: undefined } : msg
      ),
    }));
  },

  setMessageStatus: (messageId: string, status?: string) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, status } : msg
      ),
    }));
  },

  setMessageCard: (messageId: string, card: ActionCard) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, actionCard: card } : msg
      ),
    }));
  },

  setMessageQuickReplies: (messageId: string, replies: string[]) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId ? { ...msg, quickReplies: replies } : msg
      ),
    }));
  },

  finalizeAIMessage: (messageId: string, fullText: string) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === messageId
          ? {
              ...msg,
              text: fullText || msg.text,
              isStreaming: false,
              status: undefined,
            }
          : msg
      ),
      isStreaming: false,
    }));
  },

  setMessages: (messages) => set({ messages }),

  resetChat: () =>
    set({
      messages: [],
      isStreaming: false,
    }),

  startNewChat: () => {
    const freshChatId = generateUniqueChatId();
    set({
      chatId: freshChatId,
      messages: [],
      inputPrompt: '',
      isStreaming: false,
    });
    return freshChatId;
  },
}));
