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
        paddingLeft: 0, // 🔥 layout already handles sidebar offset
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: sidebarOpen ? "900px" : "1200px",
          margin: "0 auto",
          transition: "max-width 0.35s ease",
          display: "flex",
          flexDirection: "column",
          height: "100%",
        }}
      >
        {!hasMessages && (
          <div style={styles.emptyState}>
            <h1 style={styles.title}>What can I help with?</h1>
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
    gap: 28,
  },
  title: {
    fontSize: 28,
    fontWeight: 500,
    color: "#e7ebef",
    textAlign: "center",
  },
};
