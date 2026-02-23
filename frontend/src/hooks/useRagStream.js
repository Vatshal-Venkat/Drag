import { useState, useRef, useMemo } from "react";
import { useChatStore } from "../store/chatStore";
import { API_BASE } from "../config/api";

export function useRagStream() {
  const [sources, setSources] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastActivity, setLastActivity] = useState(Date.now());

  const controllerRef = useRef(null);

  const isIdle = useMemo(
    () => Date.now() - lastActivity > 18000,
    [lastActivity]
  );

  async function ask({
    question,
    topK = 5,
    documentId = null,
    documentIds = [],
    compareMode = false,
    useHumanFeedback = true,
    onToken,
    onCitations,
    onSources,
    onDone,
    onSkip,
  }) {
    if (!question?.trim()) {
      onSkip?.("empty_question");
      onDone?.();
      return;
    }

    const chatStore = useChatStore.getState();
    let sessionId = chatStore.currentSessionId;

    // --------------------------------------------------
    // ALWAYS ENSURE SESSION EXISTS (UNIFIED ENGINE REQUIRES IT)
    // --------------------------------------------------

    if (!sessionId) {
      try {
        sessionId = await chatStore.startNewSession();
      } catch {
        onSkip?.("session_create_failed");
        onDone?.();
        return;
      }
    }

    const useChat =
      !compareMode &&
      !documentId &&
      (!documentIds || documentIds.length === 0);

    const endpoint = useChat
      ? `${API_BASE}/chat/stream`
      : `${API_BASE}/rag/query/stream`;

    // --------------------------------------------------
    // UNIFIED PAYLOAD (ALWAYS INCLUDE session_id)
    // --------------------------------------------------

    const payload = useChat
      ? {
          session_id: sessionId,
          user_text: question,
        }
      : {
          session_id: sessionId,   // 🔥 REQUIRED NOW
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
      const res = await fetch(endpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "text/event-stream",
        },
        body: JSON.stringify(payload),
        signal: controllerRef.current.signal,
      });

      if (!res.ok || !res.body) {
        onSkip?.("http_error");
        onDone?.();
        return;
      }

      const reader = res.body.getReader();
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
            onDone?.();
            setIsStreaming(false);
            return;
          }

          let parsed;
          try {
            parsed = JSON.parse(data);
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
        onSkip?.("stream_error");
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
    sources,
    isStreaming,
    lastActivity,
    isIdle,
    ask,
    stop,
  };
}