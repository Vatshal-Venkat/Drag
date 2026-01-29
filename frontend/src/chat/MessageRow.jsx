export default function MessageRow({ role, content, timestamp }) {
  const isUser = role === "user";

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: "14px",
      }}
    >
      <div
        style={{
          backgroundColor: isUser ? "#1e293b" : "#0f172a",
          color: "#e5e7eb",
          padding: "12px 14px",
          borderRadius: "12px",
          maxWidth: "70%",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          boxShadow: "0 0 0 1px rgba(255,255,255,0.05)",
        }}
      >
        <div>{content}</div>
        {timestamp && (
          <div
            style={{
              fontSize: "11px",
              opacity: 0.6,
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