import { useState, useRef, useMemo } from "react";
import { useChatStore } from "../store/chatStore";

/* =========================
   API BASE CONFIG
========================= */
import { API_BASE } from "../config/api";




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
    onSkip,
  }) {
    if (!question || !question.trim()) {
      console.warn("ask() called with empty question");
      onSkip?.("empty_question");
      onDone?.();
      return;
    }

    /* --------------------------------------------------
       ROUTING DECISION
       -------------------------------------------------- */
    const shouldUseChatEndpoint =
      !compareMode &&
      !documentId &&
      (!Array.isArray(documentIds) || documentIds.length === 0);

    const chatStore = useChatStore.getState();
    let sessionId = chatStore.currentSessionId;

    // Ensure session exists BEFORE /chat/stream
    if (shouldUseChatEndpoint && !sessionId) {
      try {
        sessionId = await chatStore.startNewSession();
      } catch (err) {
        console.error("Failed to create session:", err);
        onSkip?.("session_create_failed");
        onDone?.();
        return;
      }
    }

    /* --------------------------------------------------
       ENDPOINT SELECTION (FIXED)
       -------------------------------------------------- */
    const endpoint = shouldUseChatEndpoint
      ? `${API_BASE}/chat/stream`
      : `${API_BASE}/rag/query/stream`;

    const payload = shouldUseChatEndpoint
      ? {
          session_id: sessionId,
          user_text: question,
        }
      : {
          query: question,
          top_k: topK,
          document_id: compareMode ? null : documentId,
          document_ids: compareMode ? documentIds : null,
          compare_mode: compareMode,
          use_human_feedback: useHumanFeedback,
        };

    setIsStreaming(true);
    setLastActivity(Date.now());
    setSources([]);

    controllerRef.current = new AbortController();

    try {
      const response = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        signal: controllerRef.current.signal,
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errText = await response.text();
        console.error("STREAM HTTP ERROR:", response.status, errText);
        onSkip?.("http_error");
        onDone?.();
        return;
      }

      if (!response.body) {
        throw new Error("No response body for stream");
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

          const payloadText = event.replace("data:", "").trim();

          if (payloadText === "[DONE]") {
            setIsStreaming(false);
            onDone?.();
            return;
          }

          let parsed;
          try {
            parsed = JSON.parse(payloadText);
          } catch {
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
        console.error("Stream error:", err);
      }
      onSkip?.("stream_error");
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
