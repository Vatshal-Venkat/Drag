import { create } from "zustand";
import {
  createSession,
  fetchSessions,
  fetchSession,
  sendMessage,
} from "../services/chatApi";

export const useChatStore = create((set, get) => ({
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,

  loadSessions: async () => {
    const sessions = await fetchSessions();
    set({ sessions });
  },

  startNewSession: async () => {
    const session = await createSession();
    set((state) => ({
      sessions: [session, ...state.sessions],
      currentSessionId: session.id,
      messages: [],
    }));
  },

  loadSession: async (sessionId) => {
    const session = await fetchSession(sessionId);
    set({
      currentSessionId: session.id,
      messages: session.messages || [],
    });
  },

  sendUserMessage: async (text) => {
    const { currentSessionId } = get();
    if (!currentSessionId || !text.trim()) return;

    const userMsg = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    // 1️⃣ Always show user message immediately
    set((state) => ({
      messages: [...state.messages, userMsg],
      loading: true,
    }));

    try {
      // 2️⃣ Call backend
      const res = await sendMessage(currentSessionId, text);

      // 3️⃣ Normalize agent response
      const agentMsg = {
        role: "assistant",
        content:
          typeof res === "string"
            ? res
            : res?.content || res?.answer || "No response",
        timestamp: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, agentMsg],
        loading: false,
      }));
    } catch (err) {
      // 4️⃣ Never fail silently
      set((state) => ({
        messages: [
          ...state.messages,
          {
            role: "assistant",
            content: "⚠️ Error contacting server.",
            timestamp: new Date().toISOString(),
          },
        ],
        loading: false,
      }));
    }
  },
}));