from __future__ import annotations

import os
import re
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI

from .game_defaults import DEFAULT_GAME_OPENING_INSTRUCTION, DEFAULT_GAME_OPENING_MAX_TOKENS
from .game_models import GameMessage
from .models import AgentConfig, AgentResponse, LLMCallInfo

# Regex for parsing protocol tags from manager output
PLAYER_TURN_PATTERN = re.compile(
    r"\[PLAYER_TURN\](.*?)\[/PLAYER_TURN\]",
    re.DOTALL,
)


class GameManager:
    """Generates game manager responses using an LLM.

    The manager controls game flow, validates inputs, tracks state, and
    formats display output. It communicates with the framework via
    [PLAYER_TURN] blocks and {PLAYER_DECISION} placeholders.
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Pass api_key or set OPENAI_API_KEY env var."
            )

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=self._api_key)

    def _format_messages(
        self, messages: list[GameMessage], config: AgentConfig
    ) -> list[dict]:
        """Build OpenAI messages array from game history.

        From the manager's perspective:
        - manager messages -> "assistant"
        - human and player messages -> "user"
        """
        api_messages: list[dict] = [
            {"role": "system", "content": config.system_prompt},
        ]
        for msg in messages:
            if msg.role == "manager":
                role = "assistant"
            else:
                role = "user"
            api_messages.append({"role": role, "content": msg.text})
        return api_messages

    async def generate_response(
        self,
        messages: list[GameMessage],
        config: AgentConfig,
        message_type: Literal["opening_message", "next_message"] = "next_message",
    ) -> AgentResponse:
        """Generate next manager response."""
        client = self._get_client()

        if message_type == "opening_message":
            api_messages = [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": DEFAULT_GAME_OPENING_INSTRUCTION},
            ]
            max_tokens = DEFAULT_GAME_OPENING_MAX_TOKENS
        else:
            api_messages = self._format_messages(messages, config)
            max_tokens = config.max_tokens

        params = {
            "temperature": config.temperature,
            "max_completion_tokens": max_tokens,
        }

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

        return AgentResponse(text=text, llm_call_info=llm_call_info)


class PlayerAgent:
    """Generates AI player strategic decisions using an LLM.

    The player has an ISOLATED context — it only sees what the manager
    explicitly passes via [PLAYER_TURN] blocks, preventing information leakage.
    The player accumulates its own conversation history across turns so it
    can remember past decisions.
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "OpenAI API key required. Pass api_key or set OPENAI_API_KEY env var."
            )

    def _get_client(self) -> AsyncOpenAI:
        return AsyncOpenAI(api_key=self._api_key)

    async def generate_response(
        self,
        player_messages: list[dict],
        new_context: str,
        config: AgentConfig,
    ) -> AgentResponse:
        """Generate a player decision given context from the manager.

        Args:
            player_messages: Accumulated player conversation history
                (system prompt + past PLAYER_TURN/response pairs).
                This list is mutated — new messages are appended.
            new_context: The text extracted from [PLAYER_TURN]...[/PLAYER_TURN].
            config: Player agent configuration.

        Returns:
            AgentResponse with the player's decision text and LLM call info.
        """
        client = self._get_client()

        # Append the new context as a user message
        player_messages.append({"role": "user", "content": new_context})

        params = {
            "temperature": config.temperature,
            "max_completion_tokens": config.max_tokens,
        }

        response = await client.chat.completions.create(
            model=config.model,
            messages=player_messages,
            **params,
        )

        text = response.choices[0].message.content or ""
        usage = response.usage

        # Append the player's response to its own history
        player_messages.append({"role": "assistant", "content": text})

        llm_call_info = LLMCallInfo(
            model=config.model,
            messages=list(player_messages),  # snapshot
            params=params,
            input_tokens=usage.prompt_tokens if usage else 0,
            output_tokens=usage.completion_tokens if usage else 0,
        )

        return AgentResponse(text=text, llm_call_info=llm_call_info)


class GameOrchestrator:
    """Orchestrates the Manager-Player-Human game loop.

    Uses a 2-call protocol (manager + player) instead of 3 calls:
    1. Manager generates output with [PLAYER_TURN] block(s) and {PLAYER_DECISION}
       placeholder(s) in the visible text
    2. Framework calls Player for each [PLAYER_TURN] block
    3. Framework substitutes each {PLAYER_DECISION} with the player's response
    """

    def __init__(self, api_key: str | None = None):
        self._api_key = api_key
        self._manager = GameManager(api_key=api_key)
        self._player = PlayerAgent(api_key=api_key)
        self._player_messages: list[dict] = []  # accumulated player conversation

    def _init_player_messages(self, player_config: AgentConfig) -> None:
        """Initialize player message history with system prompt if empty."""
        if not self._player_messages:
            self._player_messages = [
                {"role": "system", "content": player_config.system_prompt}
            ]

    @staticmethod
    def _strip_protocol_tags(text: str) -> str:
        """Remove [PLAYER_TURN]...[/PLAYER_TURN] blocks from text shown to human."""
        return PLAYER_TURN_PATTERN.sub("", text).strip()

    async def _resolve_player_turns(
        self,
        manager_text: str,
        player_config: AgentConfig,
    ) -> tuple[str, list[LLMCallInfo], bool]:
        """Resolve all [PLAYER_TURN] blocks and {PLAYER_DECISION} placeholders.

        Iterates over paired [PLAYER_TURN] blocks and {PLAYER_DECISION} placeholders
        in the manager's output. For each pair, calls the player agent and substitutes
        the result. Handles the "bundling" case where a single manager message contains
        multiple player turns (e.g., ultimatum even-round resolution + next odd-round).

        Args:
            manager_text: Raw manager output potentially containing protocol tags.
            player_config: Player agent configuration.

        Returns:
            (visible_text, llm_calls, had_player_turn):
                visible_text: Final text for the human with all substitutions done.
                llm_calls: LLM call info for each player call made.
                had_player_turn: True if at least one [PLAYER_TURN] was processed.
        """
        llm_calls: list[LLMCallInfo] = []
        had_player_turn = False
        text = manager_text

        while True:
            match = PLAYER_TURN_PATTERN.search(text)
            if not match:
                break

            had_player_turn = True
            player_context = match.group(1).strip()

            # Call the player
            self._init_player_messages(player_config)
            player_resp = await self._player.generate_response(
                self._player_messages, player_context, player_config
            )
            if player_resp.llm_call_info:
                llm_calls.append(player_resp.llm_call_info)

            # Remove the [PLAYER_TURN] block
            text = text[:match.start()] + text[match.end():]

            # Substitute the first {PLAYER_DECISION} placeholder with player's response
            text = text.replace("{PLAYER_DECISION}", player_resp.text, 1)

        # Clean up any remaining whitespace from tag removal
        visible_text = text.strip()
        # Collapse runs of 3+ newlines to 2
        visible_text = re.sub(r"\n{3,}", "\n\n", visible_text)

        return visible_text, llm_calls, had_player_turn

    async def process_opening(
        self,
        manager_config: AgentConfig,
        player_config: AgentConfig,
    ) -> tuple[list[GameMessage], list[LLMCallInfo]]:
        """Generate the opening message, handling any player turn needed.

        Returns:
            (new_messages, llm_calls) to be appended to the session.
        """
        messages: list[GameMessage] = []
        llm_calls: list[LLMCallInfo] = []

        # Step 1: Manager generates opening
        manager_resp = await self._manager.generate_response(
            messages, manager_config, message_type="opening_message"
        )
        if manager_resp.llm_call_info:
            llm_calls.append(manager_resp.llm_call_info)

        # Step 2: Resolve any player turns via string substitution
        visible_text, player_llm_calls, _ = await self._resolve_player_turns(
            manager_resp.text, player_config
        )
        llm_calls.extend(player_llm_calls)

        final_msg = GameMessage(role="manager", text=visible_text, visible=True)
        messages.append(final_msg)

        return messages, llm_calls

    async def process_human_input(
        self,
        human_text: str,
        existing_messages: list[GameMessage],
        manager_config: AgentConfig,
        player_config: AgentConfig,
    ) -> tuple[list[GameMessage], list[LLMCallInfo]]:
        """Process a human input through the manager-player pipeline.

        Args:
            human_text: What the human typed.
            existing_messages: Full conversation history so far.
            manager_config: Manager agent configuration.
            player_config: Player agent configuration.

        Returns:
            (new_messages, llm_calls) to be appended to the session.
        """
        new_messages: list[GameMessage] = []
        llm_calls: list[LLMCallInfo] = []

        # Add human message
        human_msg = GameMessage(role="human", text=human_text)
        new_messages.append(human_msg)

        # Build full message list for manager context
        all_messages = existing_messages + new_messages

        # Step 1: Manager processes human input
        manager_resp = await self._manager.generate_response(all_messages, manager_config)
        if manager_resp.llm_call_info:
            llm_calls.append(manager_resp.llm_call_info)

        # Step 2: Resolve any player turns via string substitution
        visible_text, player_llm_calls, _ = await self._resolve_player_turns(
            manager_resp.text, player_config
        )
        llm_calls.extend(player_llm_calls)

        final_msg = GameMessage(role="manager", text=visible_text, visible=True)
        new_messages.append(final_msg)

        return new_messages, llm_calls
