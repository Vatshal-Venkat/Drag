import { useState, useCallback, useRef, useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import FileIngest from "../components/FileIngest";
import { useVoiceInput } from "../hooks/useVoiceInput";
import "./MessageInput.css";

const MAX_TEXTAREA_HEIGHT = 140;

export default function MessageInput({ hasMessages }) {
  const [text, setText] = useState("");
  const [fileState, setFileState] = useState(null);
  const textareaRef = useRef(null);
  const fileRef = useRef(null);

  const sendUserMessage = useChatStore((s) => s.sendUserMessage);
  const loading = useChatStore((s) => s.loading);
  const error = useChatStore((s) => s.error);

  const { uploadFile, loading: uploading } = FileIngest({
    onIngest: () =>
      setFileState((s) => s && { ...s, status: "done" }),
  });

  /* ---------------- Voice ---------------- */
  const {
    supported: voiceSupported,
    listening,
    start: startVoice,
    stop: stopVoice,
  } = useVoiceInput({
    onResult: (spoken) =>
      setText((prev) => (prev ? prev + " " + spoken : spoken)),
    onEnd: () => {},
  });

  /* ---------------- Auto-grow textarea ---------------- */
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;

    el.style.height = "auto";
    el.style.height =
      Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT) + "px";
  }, [text]);

  const handleSend = useCallback(async () => {
    if (!text.trim() || loading) return;
    stopVoice();
    const msg = text;
    setText("");
    await sendUserMessage(msg);
  }, [text, loading, sendUserMessage, stopVoice]);

  async function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    setFileState({ name: file.name, status: "uploading" });
    try {
      await uploadFile(file);
    } catch {
      setFileState({ name: file.name, status: "error" });
    }

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
        <div
          className={`altaric-gradient-border ${
            error ? "altaric-border-error" : ""
          }`}
        >
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
              ref={textareaRef}
              value={text}
              placeholder={
                listening ? "Listening…" : "Ask Altaric AI…"
              }
              onChange={(e) => setText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={loading}
            />

            {voiceSupported && (
              <button
                className={`altaric-voice-button ${
                  listening ? "listening" : ""
                }`}
                onClick={listening ? stopVoice : startVoice}
                disabled={loading}
                title="Voice input"
              >
                🎤
              </button>
            )}

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

        {fileState && (
          <div className={`altaric-file-pill ${fileState.status}`}>
            {fileState.name}
            {fileState.status === "uploading" && " · processing"}
            {fileState.status === "done" && " ✓"}
            {fileState.status === "error" && " ⚠"}
          </div>
        )}

        {!text && !loading && (
          <div className="altaric-hints">
            ↵ Send · ⇧↵ New line · 🎤 Voice · /docs Search files
          </div>
        )}
      </div>
    </div>
  );
}
