from uuid import uuid4
from datetime import datetime
from typing import Dict, List, Optional, Literal, Any

from app.memory.session_memory import SessionMemory
from app.memory.summary_memory import (
    load_summary,
    update_summary,
    should_update_summary,
)

Role = Literal["system", "user", "assistant"]


class SessionManager:
    """
    Agent-aware Session Manager.
    """

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.allowed_roles = {"system", "user", "assistant"}

    # ==================================================
    # SESSION LIFECYCLE
    # ==================================================

    def create_session(self) -> Dict:
        session_id = str(uuid4())
        now = datetime.utcnow()

        session = {
            "id": session_id,
            "title": "New Chat",
            "created_at": now,
            "updated_at": now,
            "memory": SessionMemory(),
        }

        self.sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict]:
        """
        Return lightweight session metadata for UI listing.
        """
        return [
            {
                "id": s["id"],
                "title": s["title"],
                "created_at": s["created_at"],
                "updated_at": s["updated_at"],
            }
            for s in self.sessions.values()
        ]

    # ==================================================
    # MESSAGE HANDLING
    # ==================================================

    def append_message(self, session_id: str, role: Role, content: str) -> None:
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")

        if role not in self.allowed_roles:
            raise ValueError(f"Invalid role: {role}")

        if not content or not content.strip():
            return

        session = self.sessions[session_id]
        memory: SessionMemory = session["memory"]

        memory.add_message(role, content)
        session["updated_at"] = datetime.utcnow()

    def get_recent_messages(self, session_id: str, limit: int = 10):
        session = self.get_session(session_id)
        if not session:
            return []
        return session["memory"].get_recent_messages(limit)

    # ==================================================
    # DOCUMENT REFERENCES
    # ==================================================

    def add_active_document(self, session_id: str, document_id: str):
        session = self.get_session(session_id)
        if not session:
            return
        session["memory"].add_document(document_id)
        session["updated_at"] = datetime.utcnow()

    def get_active_documents(self, session_id: str) -> List[str]:
        session = self.get_session(session_id)
        if not session:
            return []
        return session["memory"].get_active_documents()

    # ==================================================
    # MEMORY AGENT HOOK
    # ==================================================

    def maybe_update_summary(
        self,
        session_id: str,
        user_query: str,
        assistant_answer: str,
    ):
        if not should_update_summary(user_query, assistant_answer):
            return

        prev = load_summary()
        update_summary(prev, user_query, assistant_answer)

    # ==================================================
    # OBSERVATIONS
    # ==================================================

    def add_observation(self, session_id: str, step: str, value: Any):
        session = self.get_session(session_id)
        if not session:
            return
        session["memory"].add_observation(step, value)
        session["updated_at"] = datetime.utcnow()

    def get_observations(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            return []
        return session["memory"].get_observations()

    # ==================================================
    # RESET
    # ==================================================

    def clear_session(self, session_id: str):
        session = self.get_session(session_id)
        if not session:
            return
        session["memory"].clear()
        session["updated_at"] = datetime.utcnow()


# ==================================================
# SINGLE GLOBAL INSTANCE
# ==================================================

session_manager = SessionManager()
