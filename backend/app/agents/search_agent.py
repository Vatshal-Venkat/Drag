from typing import List, Dict

from app.agents.base_agent import BaseAgent


class SearchAgent(BaseAgent):
    name = "search_agent"

    def run(self, query: str, **kwargs) -> List[Dict]:
        """
        Phase-4 stub. Replace with real search later.
        """
        return []
