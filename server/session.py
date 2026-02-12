from __future__ import annotations

import uuid
from random import Random
from typing import Any, Literal

from pydantic import BaseModel, Field

from interviewer import (
    DEFAULT_AGENT_MODEL,
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    AgentConfig,
    GameConfig,
    Message,
)
from interviewer.randomization import apply_conditions_to_game_config, draw_conditions


class Session(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    interviewer_config: AgentConfig = Field(
        default_factory=lambda: AgentConfig(system_prompt=DEFAULT_INTERVIEWER_SYSTEM_PROMPT)
    )
    respondent_config: AgentConfig = Field(
        default_factory=lambda: AgentConfig(system_prompt=DEFAULT_RESPONDENT_SYSTEM_PROMPT, model=DEFAULT_AGENT_MODEL)
    )
    messages: list[Message] = Field(default_factory=list)
    status: Literal["created", "active", "ended"] = "created"
    game_name: str | None = None
    game_config: GameConfig | None = None
    conditions: dict[str, Any] = Field(default_factory=dict)


# In-memory session store
_sessions: dict[str, Session] = {}


def create_session(
    interviewer_config: AgentConfig | None = None,
    respondent_config: AgentConfig | None = None,
    game_name: str | None = None,
    game_config: GameConfig | None = None,
    seed: int | None = None,
) -> Session:
    session = Session()
    if game_config:
        # Draw conditions if game has variables
        conditions: dict[str, Any] = {}
        effective_gc = game_config
        if game_config.variables:
            rng = Random(seed)
            conditions = draw_conditions(game_config.variables, 0, rng)
            effective_gc = apply_conditions_to_game_config(game_config, conditions)

        session.game_name = game_name
        session.game_config = effective_gc
        session.conditions = conditions
        session.interviewer_config = AgentConfig(
            system_prompt=effective_gc.interviewer_system_prompt,
            max_tokens=effective_gc.max_tokens,
        )
        session.respondent_config = AgentConfig(
            system_prompt=effective_gc.respondent_system_prompt,
            model=DEFAULT_AGENT_MODEL,
            max_tokens=effective_gc.max_tokens,
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
