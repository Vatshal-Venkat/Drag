from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Optional


class SessionManager:
    def __init__(self):
        # session_id -> session object
        self.sessions: Dict[str, Dict] = {}

    def create_session(self) -> Dict:
        session_id = str(uuid4())
        now = datetime.utcnow()

        session = {
            "id": session_id,
            "title": "New Chat",
            "messages": [],  # list of {role, content, timestamp}
            "created_at": now,
            "updated_at": now,
        }

        self.sessions[session_id] = session
        return session

    def list_sessions(self) -> List[Dict]:
        return [
            {
                "id": session["id"],
                "title": session["title"],
                "updated_at": session["updated_at"],
            }
            for session in self.sessions.values()
        ]

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)

    def append_message(self, session_id: str, role: str, content: str) -> None:
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")

        if role not in {"user", "agent"}:
            raise ValueError(f"Invalid role: {role}")

        session = self.sessions[session_id]
        now = datetime.utcnow()

        session["messages"].append(
            {
                "role": role,
                "content": content,
                "timestamp": now,
            }
        )

        session["updated_at"] = now


# ✅ SINGLE GLOBAL INSTANCE (IMPORTANT)
# This ensures the same memory is shared across routes
session_manager = SessionManager()