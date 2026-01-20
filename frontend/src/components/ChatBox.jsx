"use client";

import { useState, useRef } from "react";
import Message from "./Message";
import SourceCitations from "./SourceCitations";
import FileIngest from "./FileIngest";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  const abortControllerRef = useRef(null);

  async function sendMessage() {
    if (!input.trim() || loading) return;

    const question = input;
    setInput("");
    setSources([]);
    setLoading(true);

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", citations: [] },
    ]);

    abortControllerRef.current = new AbortController();

    let response;
    try {
      response = await fetch("http://127.0.0.1:8000/query/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: question,
          top_k: 5,
        }),
        signal: abortControllerRef.current.signal,
      });
    } catch (err) {
      console.error("Network error:", err);
      setLoading(false);
      return;
    }

    if (!response.ok) {
      console.error("Backend error:", response.status);
      setLoading(false);
      return;
    }

    if (!response.body) {
      console.error("No response body (stream failed)");
      setLoading(false);
      return;
    }

    const reader = response.body.getReader();
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

          // 🔹 TOKEN STREAM
          if (parsed.type === "token") {
            assistantText += parsed.value;

            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: assistantText,
              };
              return updated;
            });
          }

          // 🔹 SENTENCE-LEVEL CITATIONS
          if (parsed.type === "citations") {
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                citations: parsed.value,
              };
              return updated;
            });
          }

          // 🔹 SOURCES
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
    <div>
      <FileIngest />

      <div style={{ border: "1px solid #ccc", padding: 16, minHeight: 300 }}>
        {messages.map((m, i) => (
          <Message
            key={i}
            role={m.role}
            content={m.content}
            citations={m.citations}
          />
        ))}
        {loading && <p>Thinking…</p>}
      </div>

      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        rows={3}
        style={{ width: "100%", marginTop: 12 }}
        placeholder="Ask something…"
        disabled={loading}
      />

      <button onClick={sendMessage} disabled={loading} style={{ marginTop: 8 }}>
        Ask
      </button>

      {sources.length > 0 && <SourceCitations sources={sources} />}
    </div>
  );
}
