import { create } from "zustand";
import {
  createSession,
  fetchSessions,
  streamChatMessage,
} from "../services/chatApi";

export const useChatStore = create((set, get) => ({
  /* ----------------- UI STATE ----------------- */
  sidebarOpen: true,

  // 🔒 SOURCES PANEL IS PERMANENTLY DISABLED
  
  hoveredSessionId: null,

  toggleSidebar: () =>
    set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  // 🚫 noop – panel cannot be opened accidentally
  toggleSourcesPanel: () => {
    /* intentionally disabled */
  },

  setHoveredSession: (id) =>
    set({ hoveredSessionId: id }),

  /* ----------------- STATE ----------------- */
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  error: null,
  sessionSummaries: {},

  // 🔒 kept for compatibility but never used
  hasOpenedSourcesForSession: {},

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

  loadSession: async (sessionId) => {
    set({
      currentSessionId: sessionId,
      messages: [],
      
    });
  },

  /* ----------------- MESSAGES ----------------- */
  sendUserMessage: async (text) => {
    if (!text.trim()) return;

    let { currentSessionId, sessions } = get();

    if (!currentSessionId) {
      currentSessionId = await get().startNewSession();
    }

    const session = sessions.find((s) => s.id === currentSessionId);
    if (session && (!session.title || session.title === "New Chat")) {
      const title =
        text.length > 48 ? text.slice(0, 48) + "…" : text;

      set((state) => ({
        sessions: state.sessions.map((s) =>
          s.id === currentSessionId
            ? { ...s, title }
            : s
        ),
        sessionSummaries: {
          ...state.sessionSummaries,
          [currentSessionId]: title,
        },
      }));
    }

    const userMsg = {
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    };

    const assistantMsg = {
      role: "assistant",
      content: "",
      citations: [],
      responseMeta: {
        startedAt: Date.now(),
        completedAt: null,
        sourceCount: 0,
      },
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg, assistantMsg],
      loading: true,
      error: null,
      
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
            const last = msgs[msgs.length - 1];

            last.content = buffer;

            return {
              messages: msgs,
              
            };
          });
        },

        // 🔑 IMPORTANT: capture citations here
        (citations = []) => {
          set((state) => {
            const msgs = [...state.messages];
            const last = msgs[msgs.length - 1];

            last.citations = citations;
            last.responseMeta = {
              ...last.responseMeta,
              completedAt: Date.now(),
              sourceCount: citations.length,
            };

            return {
              messages: msgs,
              loading: false,
              
            };
          });
        }
      );
    } catch {
      set({
        loading: false,
        error: "stream_failed",
        
      });
    }
  },
}));
