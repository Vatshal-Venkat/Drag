import { useState, useRef, useMemo } from "react";

export function useRagStream() {
  const [sources, setSources] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastActivity, setLastActivity] = useState(Date.now());

  const controllerRef = useRef(null);

  /* -------------------------------
     Derived idle signal
     ------------------------------- */
  const isIdle = useMemo(() => {
    return Date.now() - lastActivity > 18000;
  }, [lastActivity]);

  async function ask({
    question,
    topK = 5,
    documentId = null,
    documentIds = null,
    compareMode = false,
    useHumanFeedback = true,

    onToken,
    onCitations,
    onSources,
    onDone,
    onSkip, // 🆕 NEW (OPTIONAL)
  }) {
    if (!question || !question.trim()) {
      console.warn("ask() called with empty question");
      onSkip?.("empty_question");
      onDone?.();
      return;
    }

    // 🚨 HARD CONTRACT ENFORCEMENT (BACKEND SAFE)
    if (!compareMode && !documentId) {
      console.error(
        "RAG BLOCKED: document_id is required for non-comparison queries"
      );
      onSkip?.("missing_document_id"); // 🆕 notify caller
      onDone?.();                      // 🆕 ensure UI unlocks
      return;
    }

    if (compareMode && (!Array.isArray(documentIds) || documentIds.length === 0)) {
      console.error(
        "RAG BLOCKED: document_ids[] required for comparison queries"
      );
      onSkip?.("missing_document_ids"); // 🆕 notify caller
      onDone?.();                       // 🆕 ensure UI unlocks
      return;
    }

    setIsStreaming(true);
    setLastActivity(Date.now());
    setSources([]);

    controllerRef.current = new AbortController();

    try {
      const response = await fetch(
        "http://localhost:8000/rag/query/stream",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          signal: controllerRef.current.signal,
          body: JSON.stringify({
            query: question,
            top_k: topK,
            document_id: compareMode ? null : documentId,
            document_ids: compareMode ? documentIds : null,
            compare_mode: compareMode,
            use_human_feedback: useHumanFeedback,
          }),
        }
      );

      if (!response.ok) {
        const errText = await response.text();
        console.error("RAG HTTP ERROR:", response.status, errText);
        throw new Error("Failed to start RAG stream");
      }

      if (!response.body) {
        throw new Error("No response body for RAG stream");
      }

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

          if (payload === "[DONE]") {
            setIsStreaming(false);
            onDone?.();
            return;
          }

          let parsed;
          try {
            parsed = JSON.parse(payload);
          } catch {
            console.warn("Non-JSON SSE payload:", payload);
            continue;
          }

          if (parsed.type === "token") {
            assistantText += parsed.value || "";
            setLastActivity(Date.now());
            onToken?.(assistantText);
          }

          if (parsed.type === "citations") {
            onCitations?.(parsed.value || []);
          }

          if (parsed.type === "sources") {
            setSources(parsed.value || []);
            onSources?.(parsed.value || []);
          }
        }
      }
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("RAG stream error:", err);
      }
      onSkip?.("stream_error"); // 🆕 optional visibility
    } finally {
      setIsStreaming(false);
    }
  }

  function stop() {
    controllerRef.current?.abort();
    setIsStreaming(false);
  }

  return {
    sources,
    isStreaming,
    lastActivity,
    isIdle,
    ask,
    stop,
  };
}
