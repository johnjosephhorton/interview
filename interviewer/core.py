from __future__ import annotations

import os
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

from openai import AsyncOpenAI

from .defaults import (
    DEFAULT_OPENING_MAX_TOKENS,
    END_OF_INTERVIEW_RESPONSE,
    LAST_QUESTION_RESPONSE,
    OPENING_INSTRUCTION,
)
from .models import AgentConfig, AgentResponse, LLMCallInfo, Message


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

    async def generate_response(
        self,
        messages: list[Message],
        config: AgentConfig,
        message_type: Literal[
            "opening_message", "next_message", "last_question", "end_of_interview"
        ] = "next_message",
    ) -> AgentResponse:
        """Generate next interviewer response."""
        # Hardcoded responses that don't need an LLM call
        if message_type == "last_question":
            return AgentResponse(text=LAST_QUESTION_RESPONSE)
        if message_type == "end_of_interview":
            return AgentResponse(text=END_OF_INTERVIEW_RESPONSE)

        client = self._get_client()

        if message_type == "opening_message":
            api_messages = [
                {"role": "system", "content": config.system_prompt},
                {"role": "user", "content": OPENING_INSTRUCTION},
            ]
            max_tokens = DEFAULT_OPENING_MAX_TOKENS
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
