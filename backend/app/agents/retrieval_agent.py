from typing import List, Dict

from app.services.retriever import retrieve
from app.agents.base_agent import BaseAgent


class RetrievalAgent(BaseAgent):
    name = "retrieval_agent"

    def run(self, **kwargs) -> List[Dict]:
        return retrieve(**kwargs)
