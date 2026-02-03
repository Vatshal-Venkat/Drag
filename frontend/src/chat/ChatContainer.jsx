import { useChatStore } from "../store/chatStore";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

export default function ChatContainer() {
  const messages = useChatStore((s) => s.messages);
  const sidebarOpen = useChatStore((s) => s.sidebarOpen);
  const hasMessages = messages.length > 0;

  return (
    <div
      style={{
        ...styles.container,
        paddingLeft: 0,
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: sidebarOpen ? "900px" : "1100px",
          margin: "0 auto",
          transition: "max-width 0.35s ease",
          display: "flex",
          flexDirection: "column",
          height: "100%",
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
            <MessageList hasMessages />
            <MessageInput hasMessages />
          </>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    position: "relative",
    height: "100vh",
    background: "#141418",
    overflow: "hidden",
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
