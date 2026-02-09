from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

from interviewer import AgentConfig
from interviewer.game_defaults import (
    DEFAULT_GAME_MANAGER_SYSTEM_PROMPT,
    DEFAULT_GAME_MAX_TOKENS,
    DEFAULT_GAME_PLAYER_MAX_TOKENS,
    DEFAULT_GAME_PLAYER_SYSTEM_PROMPT,
)
from interviewer.game import GameOrchestrator
from interviewer.game_models import GameMessage


class GameSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    manager_config: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            system_prompt=DEFAULT_GAME_MANAGER_SYSTEM_PROMPT,
            max_tokens=DEFAULT_GAME_MAX_TOKENS,
        )
    )
    player_config: AgentConfig = Field(
        default_factory=lambda: AgentConfig(
            system_prompt=DEFAULT_GAME_PLAYER_SYSTEM_PROMPT,
            max_tokens=DEFAULT_GAME_PLAYER_MAX_TOKENS,
        )
    )
    messages: list[GameMessage] = Field(default_factory=list)
    status: Literal["created", "active", "ended"] = "created"
    realized_params: dict[str, Any] = Field(default_factory=dict)
    game_name: str | None = None


# In-memory stores
_game_sessions: dict[str, GameSession] = {}
_game_orchestrators: dict[str, GameOrchestrator] = {}


def create_game_session(
    manager_config: AgentConfig | None = None,
    player_config: AgentConfig | None = None,
    realized_params: dict[str, Any] | None = None,
    game_name: str | None = None,
) -> GameSession:
    session = GameSession()
    if manager_config:
        session.manager_config = manager_config
    if player_config:
        session.player_config = player_config
    if realized_params:
        session.realized_params = realized_params
    if game_name:
        session.game_name = game_name
    _game_sessions[session.id] = session
    _game_orchestrators[session.id] = GameOrchestrator()
    return session


def get_game_session(session_id: str) -> GameSession | None:
    return _game_sessions.get(session_id)


def get_game_orchestrator(session_id: str) -> GameOrchestrator | None:
    return _game_orchestrators.get(session_id)


def delete_game_session(session_id: str) -> bool:
    _game_orchestrators.pop(session_id, None)
    return _game_sessions.pop(session_id, None) is not None
