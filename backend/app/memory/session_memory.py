from typing import Dict, List, Any
from datetime import datetime

# ==================================================
# SESSION-SCOPED MEMORY (EPHEMERAL)
# ==================================================

class SessionMemory:
    """
    Short-term working memory for a single session.
    Lives ONLY for the session lifetime.
    """

    def __init__(self):
        self.messages: List[Dict[str, str]] = []
        self.active_documents: List[str] = []
        self.observations: List[Dict[str, Any]] = []
        self.created_at = datetime.utcnow().isoformat()

    # --------------------------------------------------
    # MESSAGE MEMORY
    # --------------------------------------------------

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
        })

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, str]]:
        return self.messages[-limit:]

    # --------------------------------------------------
    # DOCUMENT REFERENCES
    # --------------------------------------------------

    def add_document(self, document_id: str):
        if document_id not in self.active_documents:
            self.active_documents.append(document_id)

    def get_active_documents(self) -> List[str]:
        return self.active_documents

    # --------------------------------------------------
    # AGENT OBSERVATIONS
    # --------------------------------------------------

    def add_observation(self, step: str, value: Any):
        self.observations.append({
            "step": step,
            "value": value,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_observations(self) -> List[Dict[str, Any]]:
        return self.observations

    # --------------------------------------------------
    # RESET
    # --------------------------------------------------

    def clear(self):
        self.messages.clear()
        self.active_documents.clear()
        self.observations.clear()
