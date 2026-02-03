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
  const [hovered, setHovered] = useState(null);

  function handleCopy() {
    navigator.clipboard.writeText(content || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1200);
  }

  function handleLike() {
    console.log("Feedback: like");
    // 🔜 wire to backend later
  }

  function handleDislike() {
    console.log("Feedback: dislike");
    // 🔜 wire to backend later
  }

  const iconBaseStyle = {
    width: 28,
    height: 28,
    borderRadius: 8,
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    color: "#94a3b8",
    transition: "all 0.18s ease",
  };

  const iconHoverStyle = {
    background:
      "linear-gradient(135deg, rgba(0,229,255,0.18), rgba(41,121,255,0.18))",
    color: "#67e8f9",
  };

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
          <Message
            role={role}
            content={content}
            citations={citations}
          />
        )}

        {/* ACTION BAR (AI ONLY) */}
        {!isUser && content && (
          <div
            style={{
              display: "flex",
              gap: "8px",
              marginTop: "8px",
              opacity: 0.85,
            }}
          >
            {/* COPY */}
            <div
              style={{
                ...iconBaseStyle,
                ...(hovered === "copy" ? iconHoverStyle : {}),
              }}
              onMouseEnter={() => setHovered("copy")}
              onMouseLeave={() => setHovered(null)}
              onClick={handleCopy}
              title={copied ? "Copied" : "Copy"}
            >
              ⧉
            </div>

            {/* LIKE */}
            <div
              style={{
                ...iconBaseStyle,
                ...(hovered === "like" ? iconHoverStyle : {}),
              }}
              onMouseEnter={() => setHovered("like")}
              onMouseLeave={() => setHovered(null)}
              onClick={handleLike}
              title="Like"
            >
              👍
            </div>

            {/* DISLIKE */}
            <div
              style={{
                ...iconBaseStyle,
                ...(hovered === "dislike" ? iconHoverStyle : {}),
              }}
              onMouseEnter={() => setHovered("dislike")}
              onMouseLeave={() => setHovered(null)}
              onClick={handleDislike}
              title="Dislike"
            >
              👎
            </div>
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
