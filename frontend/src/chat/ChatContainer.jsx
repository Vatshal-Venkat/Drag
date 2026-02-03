import { useChatStore } from "../store/chatStore";
import MessageList from "./MessageList";
import MessageInput from "./MessageInput";

const SIDEBAR_WIDTH = 260;

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

          /*
            🔑 KEY FIX:
            When sidebar is open, shift the chat column
            by half the sidebar width so it stays visually centered
            in the remaining space.
          */
          marginLeft: sidebarOpen
            ? `calc(50% - ${SIDEBAR_WIDTH / 2}px)`
            : "50%",
          transform: "translateX(-50%)",
        }}
      >
        {!hasMessages && (
          <div style={styles.emptyState}>
            <h1 style={styles.title}>
              What can I help you figure out?
            </h1>
            <p style={styles.subtitle}>
              Ask anything — explanations, comparisons,
              or deep dives.
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

            {/* INPUT DOCK */}
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
