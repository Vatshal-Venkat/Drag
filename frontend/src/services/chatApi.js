const API_BASE = "http://localhost:8000";

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

  return res.json();
}

/**
 * Fetch all chat sessions
 */
export async function fetchSessions() {
  const res = await fetch(`${API_BASE}/sessions`);

  if (!res.ok) {
    throw new Error("Failed to fetch sessions");
  }

  return res.json();
}

/**
 * Fetch a single session with messages
 */
export async function fetchSession(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);

  if (!res.ok) {
    throw new Error("Failed to fetch session");
  }

  return res.json();
}

/**
 * Send a user message and receive ONE agent response
 * 🔥 ALWAYS returns a normalized assistant message
 */
export async function sendMessage(sessionId, userText) {
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

  // 🔥 NORMALIZATION LAYER (THIS WAS MISSING)
  return {
    role: "assistant",
    content:
      data?.content ||
      data?.answer ||
      data?.response ||
      "No response from model.",
    timestamp: new Date().toISOString(),
    sources: data?.sources || [],
  };
}