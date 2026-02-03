import { useState } from "react";
import Message from "../components/Message";
import SourceCitations from "../components/SourceCitations";

export default function MessageRow({
  role,
  content,
  citations = [],
  timestamp,
}) {
  const isUser = role === "user";
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  function handleApprove() {
    console.log("HITL: approved answer");
    // 🔜 wired later to backend
  }

  function handleCorrect() {
    console.log("HITL: correction requested");
    // 🔜 open correction UI later
  }

  return (
    <div
      style={{
        display: "flex",
        justifyContent: isUser ? "flex-end" : "flex-start",
        marginBottom: isUser ? "16px" : "26px",
      }}
    >
      <div
        style={{
          maxWidth: isUser ? "70%" : "62%",
          padding: isUser ? "12px 14px" : "0px",
          background: isUser ? "#1f2933" : "transparent",
          color: "#e5e7eb",
          borderRadius: isUser ? "12px" : "0px",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          lineHeight: 1.65,
          position: "relative",
        }}
      >
        {/* MESSAGE CONTENT */}
        {isUser ? (
          <div>{content}</div>
        ) : (
          <Message role={role} content={content} citations={citations} />
        )}

        {/* ACTION BAR (AI ONLY) */}
        {!isUser && content && (
          <div
            style={{
              display: "flex",
              gap: "12px",
              marginTop: "10px",
              fontSize: "12px",
              color: "#9ca3af",
            }}
          >
            <span
              style={{ cursor: "pointer" }}
              onClick={handleCopy}
            >
              {copied ? "Copied" : "Copy"}
            </span>

            <span
              style={{ cursor: "pointer" }}
              onClick={handleApprove}
            >
              👍 Helpful
            </span>

            <span
              style={{ cursor: "pointer" }}
              onClick={handleCorrect}
            >
              ✏️ Correct
            </span>
          </div>
        )}

        {/* SOURCES SECTION */}
        {!isUser && citations.length > 0 && (
          <div style={{ marginTop: "12px" }}>
            <div
              style={{
                fontSize: 11,
                fontWeight: 600,
                color: "#9ca3af",
                marginBottom: 4,
                letterSpacing: "0.04em",
                textTransform: "uppercase",
              }}
            >
              Sources used
            </div>

            <SourceCitations sources={citations} />
          </div>
        )}

        {/* TIMESTAMP */}
        {timestamp && isUser && (
          <div
            style={{
              fontSize: "11px",
              opacity: 0.45,
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
