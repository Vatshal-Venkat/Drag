import { useState, useRef } from "react";

export function useRagStream() {
  const [messages, setMessages] = useState([]);
  const [sources, setSources] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);

  const controllerRef = useRef(null);

  async function ask(question) {
    setIsStreaming(true);
    setSources([]);

    // add user message
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "" },
    ]);

    controllerRef.current = new AbortController();

    const response = await fetch(
      "http://localhost:8000/query/stream",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question }),
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

        const data = event.replace("data:", "").trim();
        if (data === "[DONE]") {
          setIsStreaming(false);
          return;
        }

        const parsed = JSON.parse(data);

        if (parsed.type === "token") {
          assistantText += parsed.value;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: assistantText,
            };
            return updated;
          });
        }

        if (parsed.type === "sources") {
          setSources(parsed.value);
        }
      }
    }
  }

  function stop() {
    controllerRef.current?.abort();
    setIsStreaming(false);
  }

  return {
    messages,
    sources,
    isStreaming,
    ask,
    stop,
  };
}
