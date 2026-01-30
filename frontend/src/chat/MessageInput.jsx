import { useState, useCallback, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import FileIngest from "../components/FileIngest";

export default function MessageInput() {
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
    <div style={styles.dock}>
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
            title="Add attachment"
          >
            +
          </button>

          <textarea
            rows={1}
            value={text}
            placeholder="Ask Altaric a business or technical question…"
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
            title="Send"
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
    position: "fixed",
    bottom: 0,
    left: 0,
    right: 0,
    padding: "18px 24px 22px",
    background:
      "linear-gradient(180deg, rgba(15,15,18,0.7), rgba(15,15,18,0.98))",
    backdropFilter: "blur(10px)",
    borderTop: "1px solid rgba(255,255,255,0.08)",
    zIndex: 40,
  },
  bar: {
    maxWidth: 1280,
    margin: "0 auto",
  },
  inputShell: {
    display: "flex",
    alignItems: "center",
    gap: 12,
    padding: "12px 14px",
    borderRadius: 14,
    background: "rgba(255,255,255,0.04)",
    border: "1px solid rgba(255,255,255,0.08)",
  },
  textarea: {
    flex: 1,
    resize: "none",
    background: "transparent",
    border: "none",
    outline: "none",
    color: "#fff",
    fontSize: 15,
    lineHeight: 1.5,
    maxHeight: 140,
  },
  iconButton: {
    background: "transparent",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: 8,
    fontSize: 18,
    width: 32,
    height: 32,
    color: "#67e8f9",
    cursor: "pointer",
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: "50%",
    background: "#5b7cff",
    border: "none",
    color: "#fff",
    fontSize: 18,
    fontWeight: 600,
    cursor: "pointer",
  },
};
