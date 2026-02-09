from __future__ import annotations

import os

from openai import AsyncOpenAI

from .models import AgentConfig, AgentResponse, LLMCallInfo, Message


class SimulatedRespondent:
    """Generates simulated respondent responses using an LLM."""

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
        """Build the OpenAI messages array from the respondent's perspective."""
        api_messages: list[dict] = [
            {"role": "system", "content": config.system_prompt},
        ]
        for msg in messages:
            # From respondent's perspective: respondent is "assistant", interviewer is "user"
            role = "assistant" if msg.role == "respondent" else "user"
            api_messages.append({"role": role, "content": msg.text})
        return api_messages

    async def generate_response(
        self,
        messages: list[Message],
        config: AgentConfig,
    ) -> AgentResponse:
        """Generate a simulated respondent reply."""
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
