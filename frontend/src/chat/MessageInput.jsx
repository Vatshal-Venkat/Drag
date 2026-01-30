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
    <div className="input-bar" style={{ padding: "22px 32px" }}>
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
  );
}
