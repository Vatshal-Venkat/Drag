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

  /* ---------------- Sessions ---------------- */

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
    return session.id;
  },

  loadSession: async (sessionId) => {
    const session = await fetchSession(sessionId);
    set({
      currentSessionId: session.id,
      messages: session.messages || [],
    });
  },

  /* ---------------- Messaging ---------------- */

  sendUserMessage: async (text) => {
    if (!text.trim()) return;

    let { currentSessionId } = get();

    // ✅ AUTO-CREATE SESSION IF NONE EXISTS
    if (!currentSessionId) {
      currentSessionId = await get().startNewSession();
    }

    const userMsg = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    // ✅ Show user message immediately
    set((state) => ({
      messages: [...state.messages, userMsg],
      loading: true,
    }));

    try {
      const res = await sendMessage(currentSessionId, text);

      const agentMsg = {
        role: "assistant",
        content:
          res?.content ||
          res?.answer ||
          res?.response ||
          "No response from model.",
        timestamp: new Date().toISOString(),
      };

      set((state) => ({
        messages: [...state.messages, agentMsg],
        loading: false,
      }));
    } catch (err) {
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