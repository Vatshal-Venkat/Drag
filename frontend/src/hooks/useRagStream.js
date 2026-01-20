import { useState, useRef } from "react";

export function useRagStream() {
  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const controllerRef = useRef(null);

  async function ask(question, topK = 5) {
    if (!question?.trim()) return;

    setIsStreaming(true);
    setSources([]);

    // 1️⃣ Push user + empty assistant shell
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", citations: [] },
    ]);

    controllerRef.current = new AbortController();

    try {
      const response = await fetch(
        "http://localhost:8000/query/stream",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            query: question,
            top_k: topK,
          }),
          signal: controllerRef.current.signal,
        }
      );

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");

      let assistantText = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const events = chunk.split("\n\n").filter(Boolean);

        for (const event of events) {
          if (!event.startsWith("data:")) continue;

          const payload = event.replace("data:", "").trim();

          // 🔚 END
          if (payload === "[DONE]") {
            setIsStreaming(false);
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
                citations: parsed.value || [],
              };
              return updated;
            });
          }

          // 🔹 SOURCES (with page + confidence)
          if (parsed.type === "sources") {
            setSources(parsed.value || []);
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("RAG stream error:", err);
      }
    } finally {
      setIsStreaming(false);
    }
  }

  function stop() {
    controllerRef.current?.abort();
    setIsStreaming(false);
  }

  return {
    messages,     // [{ role, content, citations }]
    sources,      // [{ id, source, page, confidence, text }]
    isStreaming,
    ask,
    stop,
  };
}
