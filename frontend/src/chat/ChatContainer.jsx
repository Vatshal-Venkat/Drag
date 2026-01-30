import { useChatStore } from "../store/chatStore";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

export default function ChatContainer() {
  const messages = useChatStore((s) => s.messages);
  const hasMessages = messages.length > 0;

  return (
    <div style={styles.container}>
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
  );
}

const styles = {
  container: {
    position: "relative",
    height: "100vh",
    display: "flex",
    flexDirection: "column",
    background: "#141418",
    overflow: "hidden", // 🔥 critical
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
