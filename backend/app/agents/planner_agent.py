import json
from typing import Dict, List, Any

from app.core.llms import planner_llm
from app.core.session_manager import session_manager

# ==================================================
# REACT-STYLE PLANNER AGENT (PHASE 4C)
# ==================================================

PLANNER_SYSTEM_PROMPT = """You are an Agentic RAG Planner.

Your job is to decide WHAT actions to take, not to answer the user.

Available actions:
- chat
- retrieve
- rerank
- summarize
- compare
- read_memory
- write_memory
- generate

Tool actions (use ONLY if needed):
- tool:web_search      (search the web for fresh info)
- tool:calculator      (math / numeric reasoning)

Rules:
1. Output ONLY valid JSON
2. Do NOT explain reasoning
3. Do NOT answer the user
4. Choose the MINIMUM actions needed
5. Tool actions MUST come before generate
6. Always end with "generate" unless chat-only
"""

# --------------------------------------------------
# PUBLIC API
# --------------------------------------------------

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
    }

    user_prompt = f"""
Session State:
{json.dumps(context_snapshot, indent=2)}

User Query:
{user_query}

Return a JSON plan with this schema:

{{
  "actions": [
    {{
      "name": "<action_name>",
      "params": {{ }}
    }}
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
