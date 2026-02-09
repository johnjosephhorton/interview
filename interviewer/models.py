from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def load_prompt(value: str) -> str:
    """If value is a path to an existing .md file, read and return its contents; otherwise return as-is."""
    if value.endswith(".md") and os.path.isfile(value):
        with open(value) as f:
            return f.read().strip()
    return value


class Message(BaseModel):
    role: Literal["interviewer", "respondent"]
    text: str


class AgentConfig(BaseModel):
    system_prompt: str
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: int = 200

    @classmethod
    def from_prompt(cls, prompt: str, **kwargs: Any) -> AgentConfig:
        """Create config, resolving prompt from file path if needed."""
        return cls(system_prompt=load_prompt(prompt), **kwargs)


class LLMCallInfo(BaseModel):
    model: str
    messages: list[dict[str, Any]]
    params: dict[str, Any]
    input_tokens: int = Field(description="Number of input tokens used")
    output_tokens: int = Field(description="Number of output tokens used")


class AgentResponse(BaseModel):
    text: str
    llm_call_info: LLMCallInfo | None = None


class Transcript(BaseModel):
    messages: list[Message] = Field(default_factory=list)
    interviewer_config: AgentConfig | None = None
    respondent_config: AgentConfig | None = None
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    ended_at: str | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    llm_calls: list[LLMCallInfo] = Field(default_factory=list)
