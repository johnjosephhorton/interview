from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from .models import AgentConfig, LLMCallInfo


class GameMessage(BaseModel):
    """A single message in a game conversation."""

    role: Literal["manager", "human", "player"]
    text: str
    visible: bool = True


class GameTranscript(BaseModel):
    """Full record of a game session."""

    messages: list[GameMessage] = Field(default_factory=list)
    manager_config: AgentConfig | None = None
    player_config: AgentConfig | None = None
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: str | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    llm_calls: list[LLMCallInfo] = Field(default_factory=list)
