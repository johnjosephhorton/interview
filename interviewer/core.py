from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI

from .defaults import (
    DEFAULT_AGENT_MODEL,
    DEFAULT_OPENING_MAX_TOKENS,
    END_OF_INTERVIEW_RESPONSE,
    LAST_QUESTION_RESPONSE,
    OPENING_INSTRUCTION,
)
from .models import AgentConfig, AgentResponse, GameConfig, LLMCallInfo, Message
from .player import GamePlayer


class Interviewer:
    """Generates interviewer responses using an LLM."""

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Pass api_key or set OPENAI_API_KEY env var."
            )

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=self._api_key)

    def _format_messages(
        self, messages: list[Message], config: AgentConfig
    ) -> list[dict]:
        """Build the OpenAI messages array from conversation history."""
        api_messages: list[dict] = [
            {"role": "system", "content": config.system_prompt},
        ]
        for msg in messages:
            role = "assistant" if msg.role == "interviewer" else "user"
            api_messages.append({"role": role, "content": msg.text})
        return api_messages

    async def _get_player_decision(
        self,
        messages: list[Message],
        game_config: GameConfig,
        config: AgentConfig,
    ) -> AgentResponse | None:
        """Call the player LLM to get a strategic decision, if two-agent mode is active."""
        if not game_config or not game_config.player_system_prompt:
            return None

        player = GamePlayer(api_key=self._api_key)
        player_config = AgentConfig(
            system_prompt=game_config.player_system_prompt,
            model=DEFAULT_AGENT_MODEL,
            temperature=config.temperature,
            max_tokens=1024,
        )
        return await player.generate_decision(messages, player_config)

    @staticmethod
    def _inject_decision(text: str) -> str:
        """Format the player decision for injection into manager context."""
        return (
            "\n\n---\n"
            "AI PLAYER DECISION (internal — do NOT reveal reasoning to the human):\n"
            f"{text}\n"
            "Execute the AI player's decision. Format the response per your Message Flow rules.\n"
            "---"
        )

    async def generate_response(
        self,
        messages: list[Message],
        config: AgentConfig,
        message_type: Literal[
            "opening_message", "next_message", "last_question", "end_of_interview"
        ] = "next_message",
        game_config: GameConfig | None = None,
    ) -> AgentResponse:
        """Generate next interviewer response."""
        # Hardcoded responses that don't need an LLM call
        if message_type == "last_question":
            text = game_config.last_question_response if game_config else LAST_QUESTION_RESPONSE
            return AgentResponse(text=text)
        if message_type == "end_of_interview":
            text = game_config.end_of_session_response if game_config else END_OF_INTERVIEW_RESPONSE
            return AgentResponse(text=text)

        # Two-agent flow: get player decision first (if applicable)
        player_response = await self._get_player_decision(messages, game_config, config)
        player_llm_call_info = None
        decision_injection = ""
        if player_response and "NO_DECISION_NEEDED" not in player_response.text.upper():
            player_llm_call_info = player_response.llm_call_info
            decision_injection = self._inject_decision(player_response.text)
        elif player_response:
            # Still track the call even if no decision was needed
            player_llm_call_info = player_response.llm_call_info

        client = self._get_client()

        if message_type == "opening_message":
            instruction = game_config.opening_instruction if game_config else OPENING_INSTRUCTION
            max_tok = game_config.opening_max_tokens if game_config else DEFAULT_OPENING_MAX_TOKENS
            api_messages = [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": instruction + decision_injection},
            ]
            max_tokens = max_tok
        else:
            system_prompt = config.system_prompt + decision_injection
            effective_config = AgentConfig(
                system_prompt=system_prompt,
                model=config.model,
                temperature=config.temperature,
                max_tokens=config.max_tokens,
            )
            api_messages = self._format_messages(messages, effective_config)
            max_tokens = config.max_tokens

        params = {
            "temperature": config.temperature,
            "max_completion_tokens": max_tokens,
        }
        if config.seed is not None:
            params["seed"] = config.seed

        response = await client.chat.completions.create(
            model=config.model,
            messages=api_messages,
            **params,
        )

        text = response.choices[0].message.content or ""
        usage = response.usage
        llm_call_info = LLMCallInfo(
            model=config.model,
            messages=api_messages,
            params=params,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

        return AgentResponse(
            text=text,
            llm_call_info=llm_call_info,
            player_llm_call_info=player_llm_call_info,
        )
