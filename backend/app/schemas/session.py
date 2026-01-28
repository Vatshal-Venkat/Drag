from pydantic import BaseModel
from datetime import datetime
from typing import List, Literal


# -------------------------
# Session schemas
# -------------------------

class SessionCreateResponse(BaseModel):
    id: str
    title: str
    created_at: datetime


class SessionSummary(BaseModel):
    id: str
    title: str
    updated_at: datetime


# -------------------------
# Chat message schemas
# -------------------------

class ChatRequest(BaseModel):
    session_id: str
    user_text: str


class ChatResponse(BaseModel):
    role: Literal["agent"] = "agent"
    content: str
    timestamp: datetime


# -------------------------
# (Optional) Internal message model
# -------------------------

class Message(BaseModel):
    role: Literal["user", "agent"]
    content: str
    timestamp: datetime