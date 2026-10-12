import { useChatStore, ActionCard } from '../store/chatStore';

// In dev, Vite proxies /api to http://localhost:8000. For a deployed frontend, set VITE_API_BASE_URL.
const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

// Friendly status shown in the chat bubble while the agent works (before any text arrives).
const AGENT_STATUS: Record<string, string> = {
  goal: 'Building your goal plan…',
  answer: 'Writing your answer…',
  coverage: 'Making sure nothing is missed…',
  general: 'Saying hello…',
};

const toolStatus = (tool: string): string => {
  const t = tool.toLowerCase();
  if (t.includes('fetch') || t.includes('gathering') || t.includes('data')) return 'Gathering data…';
  if (t.includes('completeness') || t.includes('checking')) return 'Checking completeness…';
  if (t.includes('search') || t.includes('web')) return 'Searching the web…';
  if (t.includes('quote') || t.includes('price') || t.includes('market') || t.includes('stock')) {
    return 'Fetching live prices…';
  }
  if (t.includes('profile') || t.includes('goal') || t.includes('user') || t.includes('db')) return 'Reading your profile…';
  return 'Working on it…';
};

interface StreamEvent {
  token?: string;
  content?: string;
  agent?: string;
  tool?: string;
  args?: any;
  action_card?: ActionCard;
  quick_replies?: string[];
}

/**
 * Streams a chat turn from the backend agent API over Server-Sent Events (SSE).
 * Backend event contract (agent_controller.stream_chat):
 *   data: {"agent": "..."}           -> agent routed event (logs to console)
 *   data: {"tool": "...", "args": {}}-> tool call event (logs to console)
 *   data: {"token": "..."}           -> append text token
 *   data: {"action_card": {...}}     -> render a generative-UI card
 *   data: {"quick_replies": [...]}   -> render tappable follow-up chips
 *   data: [DONE]                     -> end of turn
 */
export async function streamChatResponse(
  prompt: string,
  userId: string,
  chatId?: string
): Promise<void> {
  const store = useChatStore.getState();
  const activeChatId = chatId || store.chatId;

  store.addUserMessage(prompt);
  const aiMessageId = store.addAIMessagePlaceholder();

  let fullText = '';

  const handleLine = (line: string): boolean => {
    const trimmed = line.trim();
    if (!trimmed.startsWith('data:')) return false;

    const dataStr = trimmed.slice(5).trim();
    if (dataStr === '[DONE]') return true;
    if (!dataStr) return false;

    try {
      const parsed: StreamEvent = JSON.parse(dataStr);

      // Console log for active agent
      if (parsed.agent) {
        store.setMessageStatus(aiMessageId, AGENT_STATUS[parsed.agent] || 'Thinking…');
        console.log(
          `%c[AI Agent] Routed to: ${parsed.agent}`,
          'color: #2563eb; font-weight: bold; font-size: 12px; background: #eff6ff; padding: 2px 6px; border-radius: 4px;'
        );
      }

      // Console log for tool call
      if (parsed.tool) {
        store.setMessageStatus(aiMessageId, toolStatus(parsed.tool));
        console.log(
          `%c[Tool Call] Executing: ${parsed.tool}`,
          'color: #059669; font-weight: bold; font-size: 12px; background: #ecfdf5; padding: 2px 6px; border-radius: 4px;',
          parsed.args || {}
        );
      }

      // If backend signals to clear scratchpad before synthesizing post-tool answer
      if ((parsed as any).clear) {
        fullText = '';
        store.finalizeAIMessage(aiMessageId, '');
        return false;
      }

      const token = parsed.token ?? parsed.content ?? '';
      if (token) {
        // Suppress any raw tool call syntax emitted by OpenRouter models
        if (!token.includes('!function_call:') && !token.includes('<tool_call>')) {
          fullText += token;
          store.appendStreamChunk(aiMessageId, token);
        }
      }
      if (parsed.action_card) {
        store.setMessageCard(aiMessageId, parsed.action_card);
      }
      if (Array.isArray(parsed.quick_replies) && parsed.quick_replies.length > 0) {
        store.setMessageQuickReplies(aiMessageId, parsed.quick_replies);
      }
    } catch {
      // Ignore malformed frames instead of printing raw JSON into the chat bubble.
      console.warn('[streamChatResponse] Skipped malformed SSE frame:', dataStr);
    }
    return false;
  };

  try {
    const response = await fetch(`${API_BASE}/api/agent/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        query: prompt,
        chat_id: activeChatId,
      }),
    });

    if (response.status === 401) {
      store.finalizeAIMessage(
        aiMessageId,
        '🔒 Please **sign in** to chat with the Growwise AI copilot. Your goals, portfolio and personalised answers are waiting for you!'
      );
      return;
    }

    if (!response.ok || !response.body) {
      store.finalizeAIMessage(
        aiMessageId,
        'The server returned an error. Please make sure the backend is running and try again.'
      );
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let streamBuffer = '';
    let finished = false;

    while (!finished) {
      const { done, value } = await reader.read();
      if (done) break;

      streamBuffer += decoder.decode(value, { stream: true });
      const lines = streamBuffer.split('\n');
      streamBuffer = lines.pop() || '';

      for (const line of lines) {
        if (handleLine(line)) {
          finished = true;
          break;
        }
      }
    }

    // Flush any final frame that arrived without a trailing newline.
    if (!finished && streamBuffer) handleLine(streamBuffer);

    store.finalizeAIMessage(aiMessageId, fullText);
  } catch (error) {
    console.error('[streamChatResponse] Network error connecting to backend:', error);
    store.finalizeAIMessage(
      aiMessageId,
      'Could not connect to the AI agent. Please check that the backend is running and try again.'
    );
  }
}
