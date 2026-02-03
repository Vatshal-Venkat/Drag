import { useState, useCallback, useRef, useEffect } from "react";
import { useChatStore } from "../store/chatStore";
import { useVoiceInput } from "../hooks/useVoiceInput";
import { useRagStream } from "../hooks/useRagStream";
import "./MessageInput.css";

const MAX_TEXTAREA_HEIGHT = 140;

export default function MessageInput({ hasMessages }) {
  const [text, setText] = useState("");
  const [fileState, setFileState] = useState(null);

  const [compareMode, setCompareMode] = useState(false);
  const [documentIds, setDocumentIds] = useState("");
  const [useHumanFeedback, setUseHumanFeedback] = useState(true);

  const textareaRef = useRef(null);
  const fileRef = useRef(null);

  const sendUserMessage = useChatStore((s) => s.sendUserMessage);
  const updateLastAssistant = useChatStore((s) => s.updateLastAssistant);
  const stopLoading = useChatStore((s) => s.stopLoading);

  const lastActiveDocument = useChatStore(
    (s) => s.lastActiveDocument
  );
  const setLastActiveDocument = useChatStore(
    (s) => s.setLastActiveDocument
  );

  const loading = useChatStore((s) => s.loading);
  const rag = useRagStream();

  const {
    supported: voiceSupported,
    listening,
    start: startVoice,
    stop: stopVoice,
  } = useVoiceInput({
    onResult: (spoken) =>
      setText((prev) => (prev ? prev + " " + spoken : spoken)),
  });

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height =
      Math.min(el.scrollHeight, MAX_TEXTAREA_HEIGHT) + "px";
  }, [text]);

  const handleSend = useCallback(async () => {
    if (loading || !text.trim()) return;

    const question = text.trim();
    setText("");

    await sendUserMessage({
      question,
      compareMode,
      documentIds: compareMode
        ? documentIds.split(",").map((d) => d.trim()).filter(Boolean)
        : null,
      useHumanFeedback,
    });

    await rag.ask({
      question,
      compareMode,
      documentIds: compareMode
        ? documentIds.split(",").map((d) => d.trim()).filter(Boolean)
        : null,
      documentId: !compareMode ? lastActiveDocument : null,
      useHumanFeedback,

      onToken: (content) =>
        updateLastAssistant((m) => {
          if (m) m.content = content;
        }),

      onSkip: () => {
        updateLastAssistant((m) => {
          if (m)
            m.content =
              "Please upload a document to continue.";
        });
        stopLoading();
      },

      onDone: stopLoading,
    });
  }, [
    text,
    loading,
    compareMode,
    documentIds,
    useHumanFeedback,
    lastActiveDocument,
  ]);

  const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(
      "http://127.0.0.1:8000/ingest/file",
      { method: "POST", body: formData }
    );

    const data = await res.json();
    if (data.document_id) {
      setLastActiveDocument(data.document_id);
    }

    setFileState({ name: file.name, status: "done" });
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

        {/* CONTROLS */}
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
            >
              +
            </button>

            <textarea
              ref={textareaRef}
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

            {voiceSupported && (
              <button
                className="altaric-voice-button"
                onClick={listening ? stopVoice : startVoice}
              >
                🎤
              </button>
            )}

            <button
              className="altaric-send-button"
              onClick={handleSend}
            >
              ↑
            </button>

          </div>
        </div>
      </div>
    </div>
  );
}
