from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from interviewer import (
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    AgentConfig,
    GameConfig,
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
    game_name: str | None = None
    game_config: GameConfig | None = None


# In-memory session store
_sessions: dict[str, Session] = {}


def create_session(
    interviewer_config: AgentConfig | None = None,
    respondent_config: AgentConfig | None = None,
    game_name: str | None = None,
    game_config: GameConfig | None = None,
) -> Session:
    session = Session()
    if game_config:
        session.game_name = game_name
        session.game_config = game_config
        session.interviewer_config = AgentConfig(
            system_prompt=game_config.interviewer_system_prompt,
            max_tokens=game_config.max_tokens,
        )
        session.respondent_config = AgentConfig(
            system_prompt=game_config.respondent_system_prompt,
            max_tokens=game_config.max_tokens,
        )
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
