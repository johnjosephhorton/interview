from __future__ import annotations

import os

from openai import AsyncOpenAI

from .models import AgentConfig, AgentResponse, LLMCallInfo, Message

DECISION_INSTRUCTION = (
    "\n\nBased on the current game state above, state your decision now. "
    "Follow the Output Format rules in your instructions exactly. "
    "If no decision is needed from you this turn, say NO_DECISION_NEEDED."
)


class GamePlayer:
    """Internal AI player that generates strategic decisions for game turns.

    Unlike Interviewer/SimulatedRespondent which participate in conversation,
    GamePlayer is an observer that reads the full game state and outputs a
    concise decision for the Manager to execute.
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
        self, messages: list[Message], config: AgentConfig
    ) -> list[dict]:
        """Build the OpenAI messages array from the player's observer perspective.

        All conversation messages are sent as labeled user messages since the
        player is an external observer of the game state, not a participant
        in the conversation.
        """
        api_messages: list[dict] = [
            {"role": "system", "content": config.system_prompt},
        ]
        if messages:
            conversation = "\n\n".join(
                f"[{'GAME MANAGER' if m.role == 'interviewer' else 'HUMAN PLAYER'}]: {m.text}"
                for m in messages
            )
            api_messages.append({"role": "user", "content": conversation + DECISION_INSTRUCTION})
        else:
            api_messages.append(
                {"role": "user", "content": "The game is starting." + DECISION_INSTRUCTION}
            )
        return api_messages

    async def generate_decision(
        self,
        messages: list[Message],
        config: AgentConfig,
    ) -> AgentResponse:
        """Generate a strategic decision based on the current game state."""
        client = self._get_client()
        api_messages = self._format_messages(messages, config)

        params = {
            "temperature": config.temperature,
            "max_completion_tokens": config.max_tokens,
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
