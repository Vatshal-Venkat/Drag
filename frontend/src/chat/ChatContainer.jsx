import { useChatStore } from "../store/chatStore";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

export default function ChatContainer() {
  const messages = useChatStore((s) => s.messages);
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const hasMessages = messages.length > 0;

  return (
    <div style={styles.container}>
      <div
        style={{
          ...styles.inner,
          maxWidth: sidebarOpen ? "900px" : "1100px",
        }}
      >
        {!hasMessages && (
          <div style={styles.emptyState}>
            <h1 style={styles.title}>
              What can I help you figure out?
            </h1>
            <p style={styles.subtitle}>
              Ask anything — explanations, comparisons, or deep dives.
            </p>
            <MessageInput hasMessages={false} />
          </div>
        )}

        {hasMessages && (
          <>
            {/* MESSAGE LIST (SCROLLS) */}
            <div style={styles.messageArea}>
              <MessageList />
            </div>

            {/* INPUT DOCK (FIXED HEIGHT) */}
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
    margin: "0 auto",
    height: "100%",
    display: "flex",
    flexDirection: "column",
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
