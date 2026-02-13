from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.agents.retrieval_agent import RetrievalAgent
from app.agents.search_agent import SearchAgent


class AggregatorAgent:
    """
    Runs multiple agents in parallel and merges results.
    """

    def __init__(self):
        self.retrieval_agent = RetrievalAgent()
        self.search_agent = SearchAgent()

    def run(
        self,
        query: str,
        document_id: str | None = None,
    ) -> Dict[str, List]:
        results = {
            "retrieve": [],
            "search": [],
        }

        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {
                executor.submit(
                    self.retrieval_agent.run,
                    query=query,
                    document_id=document_id,
                ): "retrieve",
                executor.submit(
                    self.search_agent.run,
                    query=query,
                ): "search",
            }

            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception:
                    results[key] = []

        return results