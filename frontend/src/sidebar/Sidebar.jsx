import { useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import ChatHistoryItem from "./ChatHistoryItem";
import FileIngest from "../components/FileIngest";

export default function Sidebar() {
  const sessions = useChatStore((s) => s.sessions);
  const currentSessionId = useChatStore((s) => s.currentSessionId);
  const loadSessions = useChatStore((s) => s.loadSessions);
  const startNewSession = useChatStore((s) => s.startNewSession);
  const loadSession = useChatStore((s) => s.loadSession); // may be undefined

  useEffect(() => {
    if (loadSessions) {
      loadSessions();
    }
  }, [loadSessions]);

  return (
    <div style={styles.sidebar}>
      {/* New Chat */}
      <button
        style={styles.newChat}
        onClick={() => startNewSession && startNewSession()}
      >
        + New Chat
      </button>

      {/* Upload Button */}
      <div style={styles.upload}>
        <FileIngest />
      </div>

      {/* Chat History */}
      <div style={styles.history}>
        {!sessions || sessions.length === 0 ? (
          <p style={{ opacity: 0.5 }}>No chats yet</p>
        ) : (
          sessions.map((s) => (
            <ChatHistoryItem
              key={s.id}
              title={s.title || "New Chat"}
              active={s.id === currentSessionId}
              onClick={() => {
                if (loadSession) {
                  loadSession(s.id);
                }
              }}
            />
          ))
        )}
      </div>
    </div>
  );
}

const styles = {
  sidebar: {
    borderRight: "1px solid #1f2937",
    padding: "12px",
    display: "flex",
    flexDirection: "column",
    width: "260px",
    background: "#020617",
  },
  newChat: {
    padding: "10px",
    borderRadius: "8px",
    background: "#111827",
    color: "#e5e7eb",
    border: "1px solid #1f2937",
    cursor: "pointer",
    marginBottom: "8px",
  },
  upload: {
    marginBottom: "12px",
  },
  history: {
    marginTop: "8px",
    overflowY: "auto",
    flex: 1,
  },
};