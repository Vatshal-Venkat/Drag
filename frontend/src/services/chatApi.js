const API_BASE = "http://localhost:8000";

/* -------------------------------------------------------
   Session APIs
------------------------------------------------------- */

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
 * Fetch all chat sessions
 */
export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/sessions`);

  if (!res.ok) {
    throw new Error("Failed to fetch sessions");
  }

  return await res.json();
}

/**
 * Fetch a single session with messages
 */
export async function fetchSession(sessionId) {
  if (!sessionId) {
    throw new Error("Session ID is required");
  }

  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch session");
  }

  return await res.json();
}

/* -------------------------------------------------------
   Messaging API
------------------------------------------------------- */

/**
 * Send a user message and receive ONE agent response
 * ✅ Pure async
 * ✅ No side effects
 * ✅ No UI coupling
 * ✅ Always normalized output
 */
export async function sendMessage(sessionId, userText) {
  if (!sessionId || !userText?.trim()) {
    throw new Error("Invalid message payload");
  }

  const res = await fetch(`${API_BASE}/chat/message`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      session_id: sessionId,
      user_text: userText,
    }),
  });

  if (!res.ok) {
    throw new Error("Failed to send message");
  }

  const data = await res.json();

  // 🔒 HARD NORMALIZATION (never breaks UI)
  return {
    role: "assistant",
    content:
      typeof data === "string"
        ? data
        : data?.content ||
          data?.answer ||
          data?.response ||
          "No response from model.",
    timestamp: new Date().toISOString(),
    sources: Array.isArray(data?.sources) ? data.sources : [],
  };
}