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
   Chat Streaming API (SSE)
========================= */
export async function fetchDocuments() {
  const res = await fetch("http://localhost:8000/documents");
  if (!res.ok) {
    throw new Error("Failed to fetch documents");
  }
  return res.json();
}


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

        /* -------- TOKEN -------- */
        if (parsed.type === "token" && typeof parsed.value === "string") {
          onToken(parsed.value);
        }

        if (typeof parsed.token === "string") {
          onToken(parsed.token);
        }

        /* -------- CITATIONS -------- */
        if (parsed.type === "citations" && Array.isArray(parsed.value)) {
          collectedCitations = parsed.value;
        }

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
