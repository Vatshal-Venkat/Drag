import { useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import ChatHistoryItem from "./ChatHistoryItem";

export default function Sidebar() {
  const sessions = useChatStore((s) => s.sessions);
  const currentSessionId = useChatStore((s) => s.currentSessionId);
  const loadSessions = useChatStore((s) => s.loadSessions);
  const startNewSession = useChatStore((s) => s.startNewSession);
  const loadSession = useChatStore((s) => s.loadSession);
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const toggleSidebar = useChatStore((s) => s.toggleSidebar);

  useEffect(() => {
    if (loadSessions) loadSessions();
  }, [loadSessions]);

  return (
    <div
      style={{
        ...styles.sidebar,
        transform: sidebarOpen ? "translateX(0)" : "translateX(-100%)",
      }}
    >
      {/* Header */}
      <div style={styles.header}>
        <span style={styles.brand}>AI-DOC</span>
        <button style={styles.collapseBtn} onClick={toggleSidebar}>
          {sidebarOpen ? "⟨" : "⟩"}
        </button>
      </div>

      {/* New Chat */}
      <button
        style={styles.newChat}
        onClick={() => startNewSession && startNewSession()}
      >
        + New Chat
      </button>

      {/* History */}
      <div style={styles.history}>
        {!sessions || sessions.length === 0 ? (
          <p style={{ opacity: 0.4, fontSize: 13 }}>No conversations</p>
        ) : (
          sessions.map((s) => (
            <ChatHistoryItem
              key={s.id}
              title={
                s.title && s.title !== "New Chat"
                  ? s.title
                  : "Untitled Conversation"
              }
              active={s.id === currentSessionId}
              onClick={() => loadSession && loadSession(s.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}

const styles = {
  sidebar: {
    position: "fixed",
    left: 0,
    top: 0,
    height: "100vh",
    width: 260,
    background: "#000000",
    borderRight: "1px solid #0f172a",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    transition: "transform 0.25s ease",
    zIndex: 20,
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 12,
  },
  brand: {
    fontWeight: 600,
    fontSize: 14,
    letterSpacing: 0.5,
    color: "#e5e7eb",
  },
  collapseBtn: {
    background: "transparent",
    border: "none",
    color: "#64748b",
    cursor: "pointer",
    fontSize: 14,
  },
  newChat: {
    padding: "10px",
    borderRadius: "8px",
    background: "linear-gradient(135deg, #00e5ff, #00bcd4, #2979ff)",
    color: "#020617",
    border: "none",
    fontWeight: 500,
    cursor: "pointer",
    marginBottom: "10px",
  },
  history: {
    marginTop: "6px",
    overflowY: "auto",
    flex: 1,
  },
};
