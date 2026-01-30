import { useState, useCallback, useRef } from "react";
import { useChatStore } from "../store/chatStore";
import FileIngest from "../components/FileIngest";
import "./MessageInput.css";

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
      className="altaric-dock"
      style={{
        position: hasMessages ? "fixed" : "relative",
        bottom: hasMessages ? 20 : "auto",
        transition: "all 0.35s ease",
      }}
    >
      <div className="altaric-bar">
        <div className="altaric-gradient-border">
          <div className="altaric-glass">
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.doc,.docx"
              style={{ display: "none" }}
              onChange={handleFileSelect}
            />

            <button
              className="altaric-icon-button"
              onClick={() => fileRef.current.click()}
              disabled={uploading || loading}
            >
              +
            </button>

            <textarea
              rows={1}
              value={text}
              placeholder="Ask Altaric AI…"
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
              className="altaric-send-button"
              style={{
                opacity: loading || !text.trim() ? 0.4 : 1,
              }}
            >
              ↑
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
