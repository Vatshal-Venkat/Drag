import { useChatStore } from "../store/chatStore";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

const SIDEBAR_WIDTH = 260;

export default function ChatContainer() {
  const messages = useChatStore((s) => s.messages);
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const compareMode = useChatStore((s) => s.compareMode);
  const selectedDocuments = useChatStore(
    (s) => s.selectedDocuments
  );

  const hasMessages = messages.length > 0;
  const showCompareBanner =
    compareMode && selectedDocuments.length >= 2;

  return (
    <div style={styles.container}>
      <div
        style={{
          ...styles.inner,
          maxWidth: sidebarOpen ? "900px" : "1100px",
          marginLeft: sidebarOpen
            ? `calc(50% - ${SIDEBAR_WIDTH / 2}px)`
            : "50%",
          transform: "translateX(-50%)",
        }}
      >
        {/* 🔍 COMPARISON MODE BANNER */}
        {showCompareBanner && (
          <div style={styles.compareBanner}>
            <div style={styles.compareTitle}>
              🔍 Comparison Mode Active
            </div>
            <div style={styles.compareDocs}>
              Comparing:
              {selectedDocuments.map((doc) => (
                <span key={doc} style={styles.docBadge}>
                  {doc}
                </span>
              ))}
            </div>
          </div>
        )}

        {!hasMessages && (
          <div style={styles.emptyState}>
            <h1 style={styles.title}>
              What can I help you figure out?
            </h1>
            <p style={styles.subtitle}>
              Ask anything — explanations,
              comparisons, or deep dives.
            </p>
            <MessageInput hasMessages={false} />
          </div>
        )}

        {hasMessages && (
          <>
            <div style={styles.messageArea}>
              <MessageList />
            </div>

            <div style={styles.inputDock}>
              <MessageInput hasMessages />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    height: "100vh",
    background: "#141418",
    overflow: "hidden",
    position: "relative",
  },

  inner: {
    height: "100%",
    display: "flex",
    flexDirection: "column",
    transition:
      "max-width 0.35s ease, margin-left 0.35s ease",
  },

  compareBanner: {
    background: "#0f172a",
    border: "1px solid #1e293b",
    borderRadius: 12,
    padding: 12,
    marginBottom: 12,
  },

  compareTitle: {
    fontSize: 13,
    fontWeight: 600,
    marginBottom: 6,
    color: "#67e8f9",
  },

  compareDocs: {
    display: "flex",
    flexWrap: "wrap",
    gap: 8,
    fontSize: 12,
    color: "#e5e7eb",
  },

  docBadge: {
    background: "#1e293b",
    padding: "4px 8px",
    borderRadius: 8,
  },

  messageArea: {
    flex: 1,
    overflowY: "auto",
    paddingBottom: 12,
  },

  inputDock: {
    flexShrink: 0,
  },

  emptyState: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    gap: 18,
    textAlign: "center",
  },

  title: {
    fontSize: 28,
    fontWeight: 500,
    color: "#e7ebef",
  },

  subtitle: {
    fontSize: 14,
    color: "#9ca3af",
    maxWidth: 420,
    lineHeight: 1.6,
  },
};
