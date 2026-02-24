import { useState, useCallback, useRef, useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import { useVoiceInput } from "../hooks/useVoiceInput";
import { useRagStream } from "../hooks/useRagStream";
import "./MessageInput.css";

const MAX_TEXTAREA_HEIGHT = 140;

export default function MessageInput({ hasMessages }) {
  const [text, setText] = useState("");
  const [fileState, setFileState] = useState(null);

  const compareMode = useChatStore((s) => s.compareMode);
  const selectedDocuments = useChatStore((s) => s.selectedDocuments);

  const ensureSession = useChatStore((s) => s.ensureSession);
  const registerDocument = useChatStore((s) => s.registerDocument);
  const setLastActiveDocument = useChatStore((s) => s.setLastActiveDocument);

  const sendUserMessage = useChatStore((s) => s.sendUserMessage);
  const updateLastAssistant = useChatStore((s) => s.updateLastAssistant);
  const stopLoading = useChatStore((s) => s.stopLoading);
  const loading = useChatStore((s) => s.loading);

  const lastActiveDocument = useChatStore((s) => s.lastActiveDocument);

  const rag = useRagStream();

  const textareaRef = useRef(null);
  const fileRef = useRef(null);

  const {
    supported: voiceSupported,
    listening,
    start: startVoice,
    stop: stopVoice,
  } = useVoiceInput({
    onResult: (spoken) =>
      setText((prev) => (prev ? prev + " " + spoken : spoken)),
  });

  /* ---------------- Auto-grow textarea ---------------- */
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height =
      Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT) + "px";
  }, [text]);

  /* ---------------- Send ---------------- */
  const handleSend = useCallback(async () => {
    if (loading || !text.trim()) return;

    const question = text.trim();
    setText("");

    // 🔥 Ensure session always exists
    const sessionId = await ensureSession();

    await sendUserMessage({
      question,
      compareMode,
      documentIds: compareMode ? selectedDocuments : null,
    });

    await rag.ask({
      sessionId,
      question,
      compareMode,
      documentIds: compareMode ? selectedDocuments : null,
      documentId: !compareMode ? lastActiveDocument : null,

      onToken: (content) =>
        updateLastAssistant((m) => {
          if (m) m.content = content;
        }),

      onSkip: () => {
        updateLastAssistant((m) => {
          if (m && !m.content) {
            m.content =
              "I couldn’t find anything relevant for that question. You can upload a document if you want me to answer based on it.";
          }
        });
        stopLoading();
      },

      onDone: stopLoading,
    });
  }, [
    text,
    loading,
    compareMode,
    selectedDocuments,
    lastActiveDocument,
    ensureSession,
    sendUserMessage,
    rag,
    updateLastAssistant,
    stopLoading,
  ]);

  /* ---------------- File Upload ---------------- */
  const uploadFile = async (file) => {
    if (!file) return;

    // 🔥 Ensure session before upload
    const sessionId = await ensureSession();

    setFileState({ name: file.name, status: "uploading" });

    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("file", file);

    try {
      const res = await fetch(
        "http://127.0.0.1:8000/ingest/file",
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail);

      registerDocument(data.document_id);
      setLastActiveDocument(data.document_id);

      setFileState({ name: file.name, status: "done" });
    } catch (err) {
      console.error("Upload failed:", err);
      setFileState({ name: file.name, status: "error" });
    }
  };

  return (
    <div
      className="altaric-dock"
      style={{
        position: hasMessages ? "fixed" : "relative",
        bottom: hasMessages ? 20 : "auto",
      }}
    >
      <div className="altaric-bar">
        <div className="altaric-gradient-border">
          <div className="altaric-glass">
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.doc,.docx"
              hidden
              onChange={(e) =>
                uploadFile(e.target.files[0])
              }
            />

            <button
              className="altaric-icon-button"
              onClick={() => fileRef.current.click()}
              disabled={loading}
            >
              +
            </button>

            <textarea
              ref={textareaRef}
              value={text}
              placeholder="Ask ECHO AI"
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
                className="altaric-voice-button"
                onClick={listening ? stopVoice : startVoice}
                disabled={loading}
              >
                🎤
              </button>
            )}

            <button
              className="altaric-send-button"
              onClick={handleSend}
              disabled={loading}
            >
              ↑
            </button>
          </div>
        </div>

        {fileState && (
          <div className={`altaric-file-pill ${fileState.status}`}>
            {fileState.name}
            {fileState.status === "uploading" && " · uploading"}
            {fileState.status === "done" && " ✓"}
            {fileState.status === "error" && " ⚠"}
          </div>
        )}
      </div>
    </div>
  );
}