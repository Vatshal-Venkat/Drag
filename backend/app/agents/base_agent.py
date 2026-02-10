from typing import Any, Dict


class BaseAgent:
    """
    Minimal base class for all callable agents.
    """

    name: str = "base_agent"

    def run(self, **kwargs) -> Any:
        raise NotImplementedError
