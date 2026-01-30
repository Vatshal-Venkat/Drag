import { useState, useCallback } from "react";
import { useChatStore } from "../store/chatStore";

export default function MessageInput() {
  const [text, setText] = useState("");
  const sendUserMessage = useChatStore((s) => s.sendUserMessage);
  const loading = useChatStore((s) => s.loading);

  const handleSend = useCallback(async () => {
    if (!text.trim() || loading) return;
    const msg = text;
    setText("");
    await sendUserMessage(msg);
  }, [text, loading, sendUserMessage]);

  return (
    <div style={styles.dock}>
      <div className="input-bar" style={styles.bar}>
        <textarea
          rows={2}
          value={text}
          placeholder="Ask a business or technical question…"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={loading}
        />

        <button
          onClick={handleSend}
          disabled={loading || !text.trim()}
        >
          {loading ? "Thinking…" : "Analyze"}
        </button>
      </div>
    </div>
  );
}

const styles = {
  dock: {
    position: "fixed",
    bottom: 0,
    left: 0,
    right: 0,
    padding: "18px 24px 22px",
    background:
      "linear-gradient(180deg, rgba(20,20,20,0.65), rgba(20,20,20,0.95))",
    backdropFilter: "blur(8px)",
    borderTop: "1px solid rgba(255,255,255,0.06)",
    zIndex: 40,
  },
  bar: {
    maxWidth: 1280,
    margin: "0 auto",
  },
};
