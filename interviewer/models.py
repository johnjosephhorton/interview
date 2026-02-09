from __future__ import annotations

import os
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

# Root of the project (one level above interviewer/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GAMES_DIR = _PROJECT_ROOT / "games"


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
    messages: list[dict[str, Any]] = Field(default_factory=list)
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


class GameConfig(BaseModel):
    name: str
    description: str = ""
    interviewer_system_prompt: str
    respondent_system_prompt: str
    opening_instruction: str
    last_question_response: str
    end_of_session_response: str
    opening_max_tokens: int = 150


def load_game(name: str) -> GameConfig:
    """Load a game definition from games/{name}/ folder.

    Reads config.toml, interviewer.md, and respondent.md.
    """
    game_dir = _GAMES_DIR / name
    if not game_dir.is_dir():
        raise ValueError(f"Game not found: '{name}'. Available: {[g['name'] for g in list_games()]}")

    config_path = game_dir / "config.toml"
    interviewer_path = game_dir / "interviewer.md"
    respondent_path = game_dir / "respondent.md"

    if not config_path.exists():
        raise ValueError(f"Missing config.toml in games/{name}/")
    if not interviewer_path.exists():
        raise ValueError(f"Missing interviewer.md in games/{name}/")
    if not respondent_path.exists():
        raise ValueError(f"Missing respondent.md in games/{name}/")

    with open(config_path, "rb") as f:
        cfg = tomllib.load(f)

    interviewer_prompt = interviewer_path.read_text().strip()
    respondent_prompt = respondent_path.read_text().strip()

    canned = cfg.get("canned", {})
    settings = cfg.get("settings", {})

    return GameConfig(
        name=cfg.get("name", name),
        description=cfg.get("description", ""),
        interviewer_system_prompt=interviewer_prompt,
        respondent_system_prompt=respondent_prompt,
        opening_instruction=canned.get("opening_instruction", ""),
        last_question_response=canned.get("last_question", ""),
        end_of_session_response=canned.get("end_of_session", ""),
        opening_max_tokens=settings.get("opening_max_tokens", 150),
    )


def list_games() -> list[dict[str, str]]:
    """Return available games as a list of {name, description} dicts."""
    games = []
    if not _GAMES_DIR.is_dir():
        return games
    for entry in sorted(_GAMES_DIR.iterdir()):
        if entry.is_dir() and (entry / "config.toml").exists():
            try:
                with open(entry / "config.toml", "rb") as f:
                    cfg = tomllib.load(f)
                games.append({
                    "name": entry.name,
                    "description": cfg.get("description", ""),
                })
            except Exception:
                games.append({"name": entry.name, "description": ""})
    return games
