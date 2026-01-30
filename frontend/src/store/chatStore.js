import { create } from "zustand";
import {
  createSession,
  fetchSessions,
} from "../services/chatApi";
import { streamChatMessage } from "../services/chatApi";

export const useChatStore = create((set, get) => ({
  /* ----------------- UI STATE ----------------- */
  sidebarOpen: true,
  sourcesPanelOpen: false,
  hoveredSessionId: null,

  toggleSidebar: () =>
    set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  toggleSourcesPanel: () =>
    set((s) => ({ sourcesPanelOpen: !s.sourcesPanelOpen })),

  setHoveredSession: (id) =>
    set({ hoveredSessionId: id }),

  /* ----------------- STATE ----------------- */
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  error: null, // ✅ added (non-breaking)
  sessionSummaries: {},
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

          const {
            hasOpenedSourcesForSession,
          } = get();

          if (!hasOpenedSourcesForSession[currentSessionId]) {
            set((state) => ({
              sourcesPanelOpen: true,
              hasOpenedSourcesForSession: {
                ...state.hasOpenedSourcesForSession,
                [currentSessionId]: true,
              },
            }));
          }

          set((state) => {
            const msgs = [...state.messages];
            msgs[msgs.length - 1].content = buffer;
            return { messages: msgs };
          });
        },
        () => set({ loading: false })
      );
    } catch {
      set({
        loading: false,
        error: "stream_failed",
      });
    }
  },
}));
