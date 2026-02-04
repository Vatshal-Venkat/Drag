const API_BASE = "http://localhost:8000";

/* =========================
   Session APIs (JSON)
========================= */

export async function createSession() {
  const res = await fetch(`${API_BASE}/sessions/new`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error("Failed to create session");
  }

  return await res.json();
}

export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/sessions`);

  if (!res.ok) {
    throw new Error("Failed to fetch sessions");
  }

  return await res.json();
}

export async function fetchSession(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch session");
  }

  return await res.json();
}

/* =========================
   Documents API
========================= */

export async function fetchDocuments() {
  const res = await fetch(`${API_BASE}/documents`);

  if (!res.ok) {
    throw new Error("Failed to fetch documents");
  }

  return await res.json();
}

/* =========================
   Chat Streaming API (SSE)
   /chat/stream
========================= */

export async function streamChatMessage(
  sessionId,
  userText,
  onToken,
  onDone
) {
  const controller = new AbortController();

  const res = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      session_id: sessionId,
      user_text: userText,
    }),
    signal: controller.signal,
  });

  if (!res.ok || !res.body) {
    throw new Error("Failed to stream chat response");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");

  let buffer = "";
  let collectedCitations = [];
  let doneCalled = false;

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        if (!rawEvent.startsWith("data:")) continue;

        const payload = rawEvent.replace("data:", "").trim();

        /* -------- END -------- */
        if (payload === "[DONE]") {
          doneCalled = true;
          onDone?.(collectedCitations);
          controller.abort();
          return;
        }

        let parsed;
        try {
          parsed = JSON.parse(payload);
        } catch {
          continue;
        }

        /* -------- TOKEN (PRIMARY) -------- */
        if (parsed.type === "token" && typeof parsed.value === "string") {
          onToken(parsed.value);
        }

        /* -------- TOKEN (BACKWARD COMPAT) -------- */
        if (typeof parsed.token === "string") {
          onToken(parsed.token);
        }

        /* -------- CITATIONS (PRIMARY) -------- */
        if (parsed.type === "citations" && Array.isArray(parsed.value)) {
          collectedCitations = parsed.value;
        }

        /* -------- CITATIONS (BACKWARD COMPAT) -------- */
        if (Array.isArray(parsed.citations)) {
          collectedCitations = parsed.citations;
        }
      }
    }
  } catch (err) {
    if (err.name !== "AbortError") {
      console.error("SSE stream error:", err);
    }
  } finally {
    if (!doneCalled) {
      onDone?.(collectedCitations);
    }
    reader.releaseLock();
  }
}

/* =========================
   RAG Streaming API (SSE)
   /rag/query/stream
   (Optional direct usage)
========================= */

export async function streamRagQuery(
  payload,
  {
    onToken,
    onCitations,
    onSources,
    onDone,
    onError,
  } = {}
) {
  const controller = new AbortController();

  try {
    const res = await fetch(`${API_BASE}/rag/query/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });

    if (!res.ok || !res.body) {
      const errText = await res.text();
      throw new Error(errText || "Failed to start RAG stream");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      let boundary;
      while ((boundary = buffer.indexOf("\n\n")) !== -1) {
        const rawEvent = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);

        if (!rawEvent.startsWith("data:")) continue;

        const payloadText = rawEvent.replace("data:", "").trim();

        if (payloadText === "[DONE]") {
          onDone?.();
          controller.abort();
          return;
        }

        let parsed;
        try {
          parsed = JSON.parse(payloadText);
        } catch {
          continue;
        }

        if (parsed.type === "token") {
          onToken?.(parsed.value || "");
        }

        if (parsed.type === "citations") {
          onCitations?.(parsed.value || []);
        }

        if (parsed.type === "sources") {
          onSources?.(parsed.value || []);
        }
      }
    }
  } catch (err) {
    if (err.name !== "AbortError") {
      console.error("RAG SSE error:", err);
      onError?.(err);
    }
  }
}
