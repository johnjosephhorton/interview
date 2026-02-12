"""Standalone AI Interviewer — symmetric LLM agents for qualitative research."""

from .checker import TranscriptChecker
from .core import Interviewer
from .player import GamePlayer
from .defaults import (
    DEFAULT_AGENT_MODEL,
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
)
from .logging import auto_save_transcript, save_transcript
from .models import (
    AgentConfig,
    AgentResponse,
    CheckResult,
    CriterionResult,
    GameConfig,
    LLMCallInfo,
    Message,
    Transcript,
    VariableDefinition,
    list_games,
    load_game,
    load_prompt,
)
from .randomization import (
    apply_conditions_to_game_config,
    draw_conditions,
    generate_factorial_design,
    substitute_template,
)
from .respondent import SimulatedRespondent
from .simulation import Simulation

__all__ = [
    "AgentConfig",
    "AgentResponse",
    "CheckResult",
    "CriterionResult",
    "DEFAULT_AGENT_MODEL",
    "DEFAULT_INTERVIEWER_SYSTEM_PROMPT",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_MODEL",
    "DEFAULT_RESPONDENT_SYSTEM_PROMPT",
    "DEFAULT_TEMPERATURE",
    "GameConfig",
    "GamePlayer",
    "Interviewer",
    "LLMCallInfo",
    "Message",
    "SimulatedRespondent",
    "Simulation",
    "Transcript",
    "TranscriptChecker",
    "VariableDefinition",
    "apply_conditions_to_game_config",
    "auto_save_transcript",
    "draw_conditions",
    "generate_factorial_design",
    "list_games",
    "load_game",
    "load_prompt",
    "save_transcript",
    "substitute_template",
]
