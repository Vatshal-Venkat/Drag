"use client";

import { useState, useRef, useEffect } from "react";
import Message from "./Message";
import SourceCitations from "./SourceCitations";
import FileIngest from "./FileIngest";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const [documents, setDocuments] = useState([]);
  const [activeDocumentId, setActiveDocumentId] = useState("");

  const endRef = useRef(null);
  const abortControllerRef = useRef(null);

  /* ============================
     Auto-scroll (session continuity)
     ============================ */
  useEffect(() => {
    endRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  /* ============================
     Document ingest handler
     ============================ */
  function handleIngest(docId) {
    setDocuments((prev) => (prev.includes(docId) ? prev : [...prev, docId]));
    setActiveDocumentId(docId);
  }

  /* ============================
     Message send
     ============================ */
  async function sendMessage() {
    if (!input.trim() || loading || !activeDocumentId) return;

    const question = input;
    setInput("");
    setSources([]);
    setLoading(true);

    /* Push user message + assistant shell */
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", citations: [] },
    ]);

    abortControllerRef.current = new AbortController();

    const res = await fetch("http://127.0.0.1:8000/query/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: question,
        top_k: 5,
        document_id: activeDocumentId,
      }),
      signal: abortControllerRef.current.signal,
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let assistantText = "";

    try {
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const events = chunk.split("\n\n").filter(Boolean);

        for (const event of events) {
          if (!event.startsWith("data:")) continue;

          const payload = event.replace("data:", "").trim();

          if (payload === "[DONE]") {
            setLoading(false);
            return;
          }

          const parsed = JSON.parse(payload);

          /* Token stream */
          if (parsed.type === "token") {
            assistantText += parsed.value;

            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1].content = assistantText;
              return updated;
            });
          }

          /* Sentence-level citations */
          if (parsed.type === "citations") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1].citations = parsed.value || [];
              return updated;
            });
          }

          /* Source metadata */
          if (parsed.type === "sources") {
            setSources(parsed.value || []);
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Streaming error:", err);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      {/* ============================
          Header
         ============================ */}
      <header className="app-header">
        <h1>RAG Accelerator</h1>
        <p>Enterprise Knowledge Assistant</p>
      </header>

      {/* ============================
          Top utility panel
         ============================ */}
      <div className="top-panel">
        <FileIngest onIngest={handleIngest} />

        {documents.length > 0 && (
          <select
            className="doc-selector"
            value={activeDocumentId}
            onChange={(e) => setActiveDocumentId(e.target.value)}
          >
            <option value="" disabled>
              Select active document
            </option>
            {documents.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* ============================
          Chat area (conversation history)
         ============================ */}
      <div className="chat-area">
        {messages.map((m, i) => (
          <Message
            key={i}
            role={m.role}
            content={m.content}
            citations={m.citations}
          />
        ))}

        {loading && (
          <div className="thinking">
            Analyzing…
          </div>
        )}

        <div ref={endRef} />
      </div>

      {/* ============================
          Input
         ============================ */}
      <div className="input-bar">
        <textarea
          rows={2}
          placeholder="Ask a business or technical question…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          Analyze
        </button>
      </div>

      {/* ============================
          Sources
         ============================ */}
      {sources.length > 0 && <SourceCitations sources={sources} />}
    </div>
  );
}
