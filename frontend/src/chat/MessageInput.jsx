import { useState } from "react";
import { useChatStore } from "../store/chatStore";

export default function MessageInput() {
  const [text, setText] = useState("");
  const sendUserMessage = useChatStore((s) => s.sendUserMessage);

  const handleSend = async () => {
    if (!text.trim()) return;
    await sendUserMessage(text);
    setText("");
  };

  return (
    <div style={styles.wrapper}>
      <input
        style={styles.input}
        value={text}
        placeholder="Ask a business or technical question..."
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSend();
        }}
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
  },
};