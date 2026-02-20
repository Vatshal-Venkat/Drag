from typing import Any, Dict, Optional, TypedDict


class AgentStep(TypedDict, total=False):
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: Any
    final: str


class AgentResult(TypedDict, total=False):
    steps: list[AgentStep]
    final_answer: Optional[str]


class BaseAgent:
    """
    Base class for all agents.
    Supports ReACT step-based execution.
    """

    name: str = "base_agent"

    def run(self, **kwargs) -> Any:
        raise NotImplementedError

    def run_step(self, **kwargs) -> AgentStep:
        """
        Single ReACT step execution.
        Must return:
        {
            thought,
            action,
            action_input
        }
        """
        raise NotImplementedError