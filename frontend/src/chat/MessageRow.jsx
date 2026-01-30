import { useChatStore } from "../store/chatStore";

export default function MessageRow({ role, content, timestamp }) {
  const isUser = role === "user";
  const toggleSources = useChatStore(
    (s) => s.toggleSourcesPanel
  );

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: isUser ? "18px" : "26px",
      }}
    >
      <div
        style={{
          maxWidth: "72%",
          padding: isUser ? "12px 14px" : "0px",
          background: isUser ? "#1e1e1e" : "transparent",
          color: "#e5e7eb",
          borderRadius: isUser ? "10px" : "0px",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          lineHeight: 1.65,
        }}
      >
        <div>{content}</div>

        {/* Assistant controls */}
        {!isUser && (
          <div
            style={{
              marginTop: 10,
              fontSize: 12,
              color: "#67e8f9",
              cursor: "pointer",
              width: "fit-content",
              opacity: 0.85,
            }}
            onClick={toggleSources}
          >
            View sources →
          </div>
        )}

        {timestamp && isUser && (
          <div
            style={{
              fontSize: "11px",
              opacity: 0.5,
              marginTop: "6px",
              textAlign: "right",
            }}
          >
            {timestamp}
          </div>
        )}
      </div>
    </div>
  );
}
