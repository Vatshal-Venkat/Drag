import { create } from "zustand";
import {
  createSession,
  fetchSessions,
  fetchDocuments,
} from "../services/chatApi";

export const useChatStore = create((set, get) => ({
  /* =================================================
     UI STATE
     ================================================= */
  sidebarOpen: true,
  hoveredSessionId: null,

  toggleSidebar: () =>
    set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  setHoveredSession: (id) =>
    set({ hoveredSessionId: id }),

  /* =================================================
     MODES
     ================================================= */
  compareMode: false,
  hitlMode: false,

  setCompareMode: (v) => set({ compareMode: v }),
  setHitlMode: (v) => set({ hitlMode: v }),

  /* =================================================
     DOCUMENT STATE
     ================================================= */
  documents: [],
  selectedDocuments: [],
  lastActiveDocument: null,

  setLastActiveDocument: (docId) =>
    set({ lastActiveDocument: docId }),

  registerDocument: (docId) =>
    set((state) => ({
      documents: state.documents.includes(docId)
        ? state.documents
        : [...state.documents, docId].sort(),
    })),

  toggleDocumentSelection: (docId) =>
    set((state) => ({
      selectedDocuments: state.selectedDocuments.includes(docId)
        ? state.selectedDocuments.filter((d) => d !== docId)
        : [...state.selectedDocuments, docId],
    })),

  clearSelectedDocuments: () =>
    set({ selectedDocuments: [] }),

  loadDocuments: async () => {
    const res = await fetchDocuments();
    set({ documents: res?.documents || [] });
  },

  /* =================================================
     CHAT / SESSION STATE
     ================================================= */
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  error: null,
  sessionSummaries: {},

  /* 🔥 Alias for frontend simplicity */
  get sessionId() {
    return get().currentSessionId;
  },

  setSessionSummary: (id, summary) =>
    set((state) => ({
      sessionSummaries: {
        ...state.sessionSummaries,
        [id]: summary,
      },
    })),

  /* =================================================
     SESSION MANAGEMENT
     ================================================= */
  loadSessions: async () => {
    const sessions = await fetchSessions();
    const docs = await fetchDocuments();

    set({
      sessions,
      documents: docs?.documents || [],
    });
  },

  startNewSession: async () => {
    const session = await createSession();

    set((state) => ({
      sessions: [session, ...state.sessions],
      currentSessionId: session.id,
      messages: [],
      loading: false,
      error: null,
    }));

    return session.id;
  },

  ensureSession: async () => {
    let { currentSessionId } = get();
    if (!currentSessionId) {
      currentSessionId = await get().startNewSession();
    }
    return currentSessionId;
  },

  loadSession: async (sessionId) => {
    set({
      currentSessionId: sessionId,
      messages: [],
      loading: false,
      error: null,
    });
  },

  /* =================================================
     MESSAGE FLOW
     ================================================= */
  sendUserMessage: async (input) => {
    const payload =
      typeof input === "string"
        ? { question: input }
        : input;

    if (!payload?.question?.trim()) return;

    let sessionId = await get().ensureSession();

    const timestamp = new Date().toISOString();

    const userMsg = {
      role: "user",
      content: payload.question,
      timestamp,
    };

    const assistantMsg = {
      role: "assistant",
      content: "…",
      citations: [],
      meta: payload,
      timestamp,
    };

    set((state) => ({
      messages: [...state.messages, userMsg, assistantMsg],
      loading: true,
      error: null,
    }));

    return sessionId;
  },

  updateLastAssistant: (updater) =>
    set((state) => {
      const msgs = [...state.messages];
      if (!msgs.length) return {};
      updater(msgs[msgs.length - 1]);
      return { messages: msgs };
    }),

  stopLoading: () => set({ loading: false }),

  setError: (err) =>
    set({ error: err, loading: false }),
}));