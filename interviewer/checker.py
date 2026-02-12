from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI

from .models import CheckResult, CriterionResult, Message, _GAMES_DIR, load_game
from .randomization import substitute_template

_CHECKER_PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "checker.md"


class TranscriptChecker:
    """Evaluates game transcripts against quality criteria using an LLM."""

    def __init__(self, api_key: str | None = None, model: str = "gpt-4o"):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Pass api_key or set OPENAI_API_KEY env var."
            )
        self.model = model

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=self._api_key)

    @staticmethod
    def _load_game_prompts(game_name: str) -> tuple[str, str, str]:
        """Load manager.md, player.md, and opening_instruction for a game.

        Returns (manager_prompt, player_prompt, opening_instruction).
        """
        game_dir = _GAMES_DIR / game_name
        if not game_dir.is_dir():
            raise ValueError(f"Game not found: '{game_name}'")

        manager_path = game_dir / "manager.md"
        player_path = game_dir / "player.md"

        if not manager_path.exists():
            raise ValueError(f"Missing manager.md in games/{game_name}/")
        if not player_path.exists():
            raise ValueError(f"Missing player.md in games/{game_name}/")

        game_config = load_game(game_name)
        return (
            manager_path.read_text().strip(),
            player_path.read_text().strip(),
            game_config.opening_instruction,
        )

    @staticmethod
    def _format_transcript(messages: list[Message]) -> str:
        """Convert messages to readable text with turn labels."""
        lines = []
        turn = 0
        for msg in messages:
            if msg.role == "interviewer":
                turn += 1
                lines.append(f"[Turn {turn}] MANAGER: {msg.text}")
            else:
                lines.append(f"[Turn {turn}] HUMAN: {msg.text}")
        return "\n\n".join(lines)

    def _build_prompt(
        self,
        game_name: str,
        messages: list[Message],
        conditions: dict[str, Any] | None = None,
    ) -> str:
        """Fill the checker template with game rules and transcript.

        If conditions are provided, substitute {{var}} placeholders in prompts
        and include a Session Parameters section so the checker has ground truth.
        """
        manager_prompt, player_prompt, opening_instruction = self._load_game_prompts(game_name)
        transcript_text = self._format_transcript(messages)

        # Substitute template variables so the checker sees concrete values
        if conditions:
            manager_prompt = substitute_template(manager_prompt, conditions)
            player_prompt = substitute_template(player_prompt, conditions)
            opening_instruction = substitute_template(opening_instruction, conditions)

        # Build session parameters section
        if conditions:
            param_lines = [f"- {k} = {v}" for k, v in conditions.items()]
            session_parameters = "## Session Parameters\n\n" + "\n".join(param_lines)
        else:
            session_parameters = ""

        template = _CHECKER_PROMPT_PATH.read_text()
        return template.format(
            manager_prompt=manager_prompt,
            player_prompt=player_prompt,
            opening_instruction=opening_instruction,
            transcript_text=transcript_text,
            session_parameters=session_parameters,
        )

    async def check(
        self,
        game_name: str,
        messages: list[Message],
        conditions: dict[str, Any] | None = None,
    ) -> CheckResult:
        """Evaluate a transcript against all criteria. Returns a CheckResult."""
        prompt = self._build_prompt(game_name, messages, conditions=conditions)
        client = self._get_client()

        response = await client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)

        usage = response.usage
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        criteria = [
            CriterionResult(
                criterion=c["criterion"],
                passed=c["passed"],
                explanation=c["explanation"],
            )
            for c in data.get("criteria", [])
        ]

        overall_passed = all(c.passed for c in criteria)

        return CheckResult(
            game_name=game_name,
            transcript_summary=data.get("transcript_summary", ""),
            criteria=criteria,
            overall_passed=overall_passed,
            checker_model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
