import { create } from "zustand";
import { createSession, fetchSessions } from "../services/chatApi";

import { fetchDocuments } from "../services/chatApi";


export const useChatStore = create((set, get) => ({
  /* ----------------- UI STATE ----------------- */
  sidebarOpen: true,
  hoveredSessionId: null,

  toggleSidebar: () =>
    set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  setHoveredSession: (id) =>
    set({ hoveredSessionId: id }),

  /* ----------------- MODES ----------------- */
  compareMode: false,
  hitlMode: false,

  setCompareMode: (v) => set({ compareMode: v }),
  setHitlMode: (v) => set({ hitlMode: v }),

  /* ----------------- DOCUMENTS ----------------- */
  documents: [],
  selectedDocuments: [],

  lastActiveDocument: null, // ✅ exists, untouched

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

  /* ----------------- CHAT STATE ----------------- */
  sessions: [],
  currentSessionId: null,
  messages: [],
  loading: false,
  error: null,

  sessionSummaries: {}, // ✅ FIX: prevents ChatHistoryItem crash

  setSessionSummary: (id, summary) =>
    set((state) => ({
      sessionSummaries: {
        ...state.sessionSummaries,
        [id]: summary,
      },
    })),

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
  sendUserMessage: async (input) => {
    const payload =
      typeof input === "string"
        ? { question: input }
        : input;

    if (!payload?.question?.trim()) return;

    let { currentSessionId } = get();

    if (!currentSessionId) {
      currentSessionId = await get().startNewSession();
    }

    const userMsg = {
      role: "user",
      content: payload.question,
      timestamp: new Date().toISOString(),
    };

    const assistantMsg = {
      role: "assistant",
      content: "…",
      citations: [],
      meta: payload,
      timestamp: new Date().toISOString(),
    };

    set((state) => ({
      messages: [...state.messages, userMsg, assistantMsg],
      loading: true,
      error: null,
    }));
  },

  updateLastAssistant: (updater) =>
    set((state) => {
      const msgs = [...state.messages];
      if (!msgs.length) return {};
      updater(msgs[msgs.length - 1]);
      return { messages: msgs };
    }),

  stopLoading: () => set({ loading: false }),

  /* ----------------- DOCUMENTS ----------------- */
  documents: [],
  selectedDocuments: [],

  loadDocuments: async () => {
    const res = await fetchDocuments();
    set({ documents: res.documents || [] });
  },

  /* ----------------- SESSIONS ----------------- */
  
  loadSessions: async () => {
    const sessions = await fetchSessions();
    set({ sessions });
  
    
    const docs = await fetchDocuments();
    set({ documents: docs.documents || [] });
  },


}));
