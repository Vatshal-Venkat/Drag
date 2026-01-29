import { create } from "zustand";
import {
  createSession,
  fetchSessions,
} from "../services/chatApi";
import { streamChatMessage } from "../services/chatApi";

export const useChatStore = create((set, get) => ({
  /* ----------------- STATE ----------------- */
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,

  /* ----------------- SESSIONS ----------------- */

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

  /* ----------------- MESSAGES ----------------- */

  sendUserMessage: async (text) => {
    if (!text.trim()) return;

    let { currentSessionId } = get();
    if (!currentSessionId) {
      currentSessionId = await get().startNewSession();
    }

    const userMsg = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    const assistantMsg = {
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg, assistantMsg],
      loading: true,
    }));

    let buffer = "";

    try {
      await streamChatMessage(
        currentSessionId,
        text,
        (token) => {
          buffer += token;
          set((state) => {
            const msgs = [...state.messages];
            msgs[msgs.length - 1].content = buffer;
            return { messages: msgs };
          });
        },
        () => {
          set({ loading: false });
        }
      );
    } catch {
      set((state) => ({
        messages: [
          ...state.messages.slice(0, -1),
          {
            role: "assistant",
            content: "⚠️ Error streaming response.",
            timestamp: new Date().toISOString(),
          },
        ],
        loading: false,
      }));
    }
  },
}));