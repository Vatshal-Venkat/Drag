const API_BASE = "http://localhost:8000";

/* =========================
   Session APIs (JSON)
========================= */

/**
 * Create a new chat session
 */
export async function createSession() {
  const res = await fetch(`${API_BASE}/sessions/new`, {
    method: "POST",
  });

  if (!res.ok) {
    throw new Error("Failed to create session");
  }

  return await res.json();
}

/**
 * Fetch all sessions
 */
export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/sessions`);

  if (!res.ok) {
    throw new Error("Failed to fetch sessions");
  }

  return await res.json();
}

/**
 * Fetch one session
 */
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

/**
 * Stream chat response from backend (/chat/stream)
 */
export async function streamChatMessage(
  sessionId,
  userText,
  onToken,
  onDone
) {
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
  });

  if (!res.ok || !res.body) {
    throw new Error("Failed to stream chat response");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value, { stream: true });
    const events = chunk.split("\n\n").filter(Boolean);

    for (const event of events) {
      if (!event.startsWith("data:")) continue;

      const payload = event.replace("data:", "").trim();

      if (payload === "[DONE]") {
        onDone?.();
        return;
      }

      const parsed = JSON.parse(payload);
      if (parsed.type === "token") {
        onToken(parsed.value);
      }
    }
  }
}