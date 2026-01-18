"use client";

import { useState } from "react";
import Message from "./Message";
import SourceCitations from "./SourceCitations";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(false);

  async function sendMessage() {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    setMessages((m) => [...m, userMsg]);
    setLoading(true);

    const res = await fetch("http://127.0.0.1:8000/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: input }),
    });

    const data = await res.json();

    setMessages((m) => [
      ...m,
      { role: "assistant", content: data.answer },
    ]);
    setSources(data.sources || []);
    setInput("");
    setLoading(false);
  }

  return (
    <div>
      <div style={{ border: "1px solid #ccc", padding: 16, minHeight: 300 }}>
        {messages.map((m, i) => (
          <Message key={i} role={m.role} content={m.content} />
        ))}
        {loading && <p>Thinking…</p>}
      </div>

      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        rows={3}
        style={{ width: "100%", marginTop: 12 }}
      />

      <button onClick={sendMessage} style={{ marginTop: 8 }}>
        Ask
      </button>

      {sources.length > 0 && <SourceCitations sources={sources} />}
    </div>
  );
}
