import { useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import ChatHistoryItem from "./ChatHistoryItem";

export default function Sidebar() {
  const {
    sessions,
    currentSessionId,
    loadSessions,
    startNewSession,
    loadSession,
    sidebarOpen,
    toggleSidebar,

    compareMode,
    hitlMode,
    setCompareMode,
    setHitlMode,

    documents,
    selectedDocuments,
    toggleDocumentSelection,
  } = useChatStore();

  useEffect(() => {
    loadSessions();
  }, [loadSessions]);

  return (
    <div
      style={{
        ...styles.sidebar,
        transform: sidebarOpen
          ? "translateX(0)"
          : "translateX(-100%)",
      }}
    >
      {/* HEADER */}
      <div style={styles.header}>
        <span style={styles.brand}>ECHO</span>
        <button
          onClick={toggleSidebar}
          style={styles.collapseBtn}
        >
          {sidebarOpen ? "⟨" : "⟩"}
        </button>
      </div>

      {/* NEW CHAT */}
      <button
        style={styles.newChat}
        onClick={startNewSession}
      >
        + New Chat
      </button>

      {/* MODES */}
      <div style={styles.section}>
        <div style={styles.sectionTitle}>Modes</div>

        <Toggle
          label="Compare"
          value={compareMode}
          onChange={setCompareMode}
        />

        <Toggle
          label="HITL"
          value={hitlMode}
          onChange={setHitlMode}
        />
      </div>

      {/* COMPARE DOCUMENTS */}
      {compareMode && (
        <div style={styles.section}>
          <div style={styles.sectionTitle}>
            Documents
          </div>

          {documents.length === 0 && (
            <div style={styles.emptyDocs}>
              No documents uploaded
            </div>
          )}

          {documents.map((doc) => (
            <label key={doc} style={styles.docItem}>
              <input
                type="checkbox"
                checked={selectedDocuments.includes(doc)}
                onChange={() =>
                  toggleDocumentSelection(doc)
                }
              />
              <span>{doc}</span>
            </label>
          ))}
        </div>
      )}

      {/* CHAT HISTORY */}
      <div style={{ ...styles.section, flex: 1 }}>
        <div style={styles.sectionTitle}>
          Chat History
        </div>

        {sessions.map((s) => (
          <ChatHistoryItem
            key={s.id}
            id={s.id}
            title={
              s.title && s.title !== "New Chat"
                ? s.title
                : "Untitled Conversation"
            }
            active={s.id === currentSessionId}
            onClick={() => loadSession(s.id)}
          />
        ))}
      </div>
    </div>
  );
}

/* ---------------- TOGGLE ---------------- */
function Toggle({ label, value, onChange }) {
  return (
    <div style={styles.toggleRow}>
      <span>{label}</span>

      <div
        style={{
          ...styles.toggle,
          background: value
            ? "linear-gradient(135deg, #00e5ff, #2979ff)"
            : "#334155",
        }}
        onClick={() => onChange(!value)}
      >
        <div
          style={{
            ...styles.knob,
            transform: value
              ? "translateX(18px)"
              : "translateX(0)",
          }}
        />
      </div>
    </div>
  );
}

/* ---------------- STYLES ---------------- */
const styles = {
  sidebar: {
    position: "fixed",
    left: 0,
    top: 0,
    width: 260,
    height: "100vh",
    background: "#000",
    padding: 12,
    display: "flex",
    flexDirection: "column",
    zIndex: 20,
    transition: "transform 0.25s ease",
  },

  header: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: 12,
  },

  brand: {
    color: "#e5e7eb",
    fontWeight: 600,
    fontSize: 14,
  },

  collapseBtn: {
    background: "none",
    border: "none",
    color: "#94a3b8",
    cursor: "pointer",
  },

  newChat: {
    padding: 10,
    borderRadius: 8,
    background:
      "linear-gradient(135deg, #00e5ff, #2979ff)",
    border: "none",
    cursor: "pointer",
    marginBottom: 12,
    fontWeight: 500,
  },

  section: {
    marginBottom: 12,
  },

  sectionTitle: {
    fontSize: 11,
    color: "#64748b",
    marginBottom: 6,
    textTransform: "uppercase",
  },

  toggleRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
    color: "#e5e7eb",
    fontSize: 13,
  },

  toggle: {
    width: 36,
    height: 18,
    borderRadius: 999,
    padding: 2,
    cursor: "pointer",
    transition: "background 0.2s",
  },

  knob: {
    width: 14,
    height: 14,
    background: "#020617",
    borderRadius: "50%",
    transition: "transform 0.2s",
  },

  docItem: {
    display: "flex",
    gap: 8,
    alignItems: "center",
    fontSize: 12,
    color: "#e5e7eb",
    marginBottom: 6,
    marginLeft: 4,
  },

  emptyDocs: {
    fontSize: 12,
    opacity: 0.5,
    marginLeft: 4,
  },
};
