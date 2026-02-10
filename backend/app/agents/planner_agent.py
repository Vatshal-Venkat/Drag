import json
from typing import Dict, Any

from app.core.llms import planner_llm
from app.core.session_manager import session_manager
from app.core.config import MCP_ENABLED


PLANNER_SYSTEM_PROMPT = """You are a Planner Agent.

Your job is to decide WHAT actions to take, not to answer the user.

Available local actions:
- chat
- retrieve
- rerank
- generate
- search

Available external actions (ONLY if enabled):
- mcp:<tool_name>   (external tools via MCP servers)

When to use MCP tools:
- The question requires fresh, real-time, or external information
- The answer cannot be found in uploaded documents
- The task requires capabilities beyond text retrieval (APIs, services, actions)

Rules:
1. Output ONLY valid JSON
2. Do NOT explain reasoning
3. Do NOT answer the user
4. Choose the MINIMUM actions needed
5. Prefer local tools before MCP tools
6. MCP tools MUST appear before "generate"
7. Always end with "generate" unless chat-only
"""


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

Notes:
- Use "mcp:<tool_name>" only if MCP is enabled
- Do NOT invent MCP tool names
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
        # Safe fallback (local-only)
        plan = {
            "actions": (
                [{"name": "chat", "params": {}}]
                if not active_docs
                else [
                    {"name": "retrieve", "params": {}},
                    {"name": "rerank", "params": {}},
                    {"name": "generate", "params": {}},
                ]
            )
        }

    return plan
