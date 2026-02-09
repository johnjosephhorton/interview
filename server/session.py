from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from interviewer import (
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    AgentConfig,
    Message,
)


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    interviewer_config: AgentConfig = Field(
        default_factory=lambda: AgentConfig(system_prompt=DEFAULT_INTERVIEWER_SYSTEM_PROMPT)
    )
    respondent_config: AgentConfig = Field(
        default_factory=lambda: AgentConfig(system_prompt=DEFAULT_RESPONDENT_SYSTEM_PROMPT)
    )
    messages: list[Message] = Field(default_factory=list)
    status: Literal["created", "active", "ended"] = "created"


# In-memory session store
_sessions: dict[str, Session] = {}


def create_session(
    interviewer_config: AgentConfig | None = None,
    respondent_config: AgentConfig | None = None,
) -> Session:
    session = Session()
    if interviewer_config:
        session.interviewer_config = interviewer_config
    if respondent_config:
        session.respondent_config = respondent_config
    _sessions[session.id] = session
    return session


def get_session(session_id: str) -> Session | None:
    return _sessions.get(session_id)


def delete_session(session_id: str) -> bool:
    return _sessions.pop(session_id, None) is not None


def list_sessions() -> list[Session]:
    return list(_sessions.values())
