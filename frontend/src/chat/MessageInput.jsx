import { useState, useCallback, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import FileIngest from "../components/FileIngest";

export default function MessageInput({ hasMessages }) {
  const [text, setText] = useState("");
  const fileRef = useRef(null);

  const sendUserMessage = useChatStore((s) => s.sendUserMessage);
  const loading = useChatStore((s) => s.loading);

  const { uploadFile, loading: uploading } = FileIngest({
    onIngest: () => {},
  });

  const handleSend = useCallback(async () => {
    if (!text.trim() || loading) return;
    const msg = text;
    setText("");
    await sendUserMessage(msg);
  }, [text, loading, sendUserMessage]);

  async function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    await uploadFile(file);
    e.target.value = "";
  }

  return (
    <div
      style={{
        ...styles.dock,
        position: hasMessages ? "fixed" : "relative",
        bottom: hasMessages ? 20 : "auto",
        transition: "all 0.35s ease",
      }}
    >
      <div style={styles.bar}>
        <div style={styles.inputShell}>
          <input
            ref={fileRef}
            type="file"
            accept=".pdf,.doc,.docx"
            style={{ display: "none" }}
            onChange={handleFileSelect}
          />

          <button
            style={styles.iconButton}
            onClick={() => fileRef.current.click()}
            disabled={uploading || loading}
          >
            +
          </button>

          <textarea
            rows={1}
            value={text}
            placeholder="Ask anything"
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            disabled={loading}
            style={styles.textarea}
          />

          <button
            onClick={handleSend}
            disabled={loading || !text.trim()}
            style={{
              ...styles.sendButton,
              opacity: loading || !text.trim() ? 0.4 : 1,
            }}
          >
            ↑
          </button>
        </div>
      </div>
    </div>
  );
}

const styles = {
  dock: {
  left: 0,
  right: 0,
  bottom: 20,
  zIndex: 40,
  display: "flex",
  justifyContent: "center",
  pointerEvents: "auto",
  background:
    "linear-gradient(180deg, rgba(20,20,24,0), rgba(20,20,24,0.85))",
  },

  bar: {
    width: "60%",
    minWidth: 520,
    maxWidth: 760,
  },
  inputShell: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "14px 16px",
    borderRadius: 20,
    border: "1.5px solid rgba(255,255,255,0.16)",
  },
  textarea: {
    flex: 1,
    background: "transparent",
    border: "none",
    outline: "none",
    color: "#e7ebef",
    fontSize: 15,
  },
  iconButton: {
    background: "transparent",
    border: "1px solid rgba(255,255,255,0.14)",
    borderRadius: 10,
    width: 34,
    height: 34,
    color: "#2dd4bf",
    cursor: "pointer",
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: "50%",
    background: "transparent",
    border: "1.5px solid #2dd4bf",
    color: "#2dd4bf",
    fontSize: 18,
    cursor: "pointer",
  },
};
