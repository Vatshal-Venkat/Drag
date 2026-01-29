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
    <div style={styles.wrapper}>
      <textarea
        style={styles.input}
        rows={2}
        value={text}
        placeholder="Ask a business or technical question..."
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
        disabled={loading}
      />
    </div>
  );
}

const styles = {
  wrapper: {
    padding: "16px",
    borderTop: "1px solid #1f2937",
  },
  input: {
    width: "100%",
    padding: "12px",
    borderRadius: "8px",
    background: "#020617",
    color: "#e5e7eb",
    border: "1px solid #1f2937",
    resize: "none",
    outline: "none",
    fontSize: "14px",
  },
};