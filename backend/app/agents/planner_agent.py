import json
from typing import Dict, Any

from app.core.llms import planner_llm
from app.core.session_manager import session_manager
from app.core.config import MCP_ENABLED


COMPARISON_KEYWORDS = [
    "compare",
    "comparison",
    "difference",
    "different",
    "vs",
    "versus",
    "contrast",
]


PLANNER_SYSTEM_PROMPT = """You are a Planner Agent.

Your job is to decide WHAT actions to take, not to answer the user.

Available actions:
- chat
- retrieve
- rerank
- generate
- search

External tools (if enabled):
- mcp:<tool_name>

Rules:
1. Output ONLY valid JSON
2. Do NOT explain reasoning
3. Do NOT answer the user
4. Choose the MINIMUM actions needed
5. Prefer local tools before MCP tools
6. MCP tools MUST come before generate
7. Always end with "generate" unless chat-only
"""


def _is_comparison_query(query: str) -> bool:
    q = query.lower()
    return any(k in q for k in COMPARISON_KEYWORDS)


def plan_next_steps(
    *,
    session_id: str,
    user_query: str,
) -> Dict[str, Any]:

    recent_messages = session_manager.get_recent_messages(
        session_id,
        limit=5,
    )

    active_docs = session_manager.get_active_documents(session_id)

    # --------------------------------------------------
    # 🔹 AUTO-COMPARISON MODE
    # --------------------------------------------------
    if _is_comparison_query(user_query) and len(active_docs) >= 2:
        return {
            "actions": [
                {"name": "retrieve", "params": {}},
                {"name": "generate", "params": {"compare_mode": True}},
            ]
        }

    context_snapshot = {
        "recent_messages": [
            {"role": m["role"], "content": m["content"][:200]}
            for m in recent_messages
        ],
        "active_documents": active_docs,
        "mcp_enabled": MCP_ENABLED,
    }

    user_prompt = f"""
Session State:
{json.dumps(context_snapshot, indent=2)}

User Query:
{user_query}

Return a JSON plan with this schema:

{{
  "actions": [
    {{ "name": "<action_name>", "params": {{ }} }}
  ]
}}
""".strip()

    messages = [
        {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    raw_output = planner_llm(messages, stream=False)

    try:
        plan = json.loads(raw_output)
        assert "actions" in plan
    except Exception:
        plan = {
            "actions": [
                {"name": "retrieve", "params": {}},
                {"name": "rerank", "params": {}},
                {"name": "generate", "params": {}},
            ]
        }

    return plan
