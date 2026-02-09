"""Tests for Interviewer and SimulatedRespondent (hardcoded responses + message formatting)."""

import pytest

from interviewer.core import Interviewer
from interviewer.defaults import END_OF_INTERVIEW_RESPONSE, LAST_QUESTION_RESPONSE
from interviewer.models import AgentConfig, Message


@pytest.fixture
def interviewer():
    # Use a dummy key — we only test non-LLM paths
    return Interviewer(api_key="sk-test-dummy")


@pytest.fixture
def config():
    return AgentConfig(system_prompt="You are a test interviewer.")


@pytest.mark.asyncio
async def test_last_question_response(interviewer, config):
    resp = await interviewer.generate_response([], config, message_type="last_question")
    assert resp.text == LAST_QUESTION_RESPONSE
    assert resp.llm_call_info is None


@pytest.mark.asyncio
async def test_end_of_interview_response(interviewer, config):
    resp = await interviewer.generate_response([], config, message_type="end_of_interview")
    assert resp.text == END_OF_INTERVIEW_RESPONSE
    assert resp.llm_call_info is None


def test_format_messages(interviewer, config):
    messages = [
        Message(role="interviewer", text="Hello!"),
        Message(role="respondent", text="Hi there."),
        Message(role="interviewer", text="Tell me more."),
    ]
    api_messages = interviewer._format_messages(messages, config)

    assert api_messages[0]["role"] == "system"
    assert api_messages[0]["content"] == config.system_prompt
    assert api_messages[1]["role"] == "assistant"  # interviewer -> assistant
    assert api_messages[1]["content"] == "Hello!"
    assert api_messages[2]["role"] == "user"  # respondent -> user
    assert api_messages[2]["content"] == "Hi there."
    assert api_messages[3]["role"] == "assistant"
    assert api_messages[3]["content"] == "Tell me more."


def test_api_key_from_param():
    i = Interviewer(api_key="sk-test-123")
    assert i._api_key == "sk-test-123"


def test_api_key_missing_raises():
    import os
    # Temporarily remove env var if set
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="API key required"):
            Interviewer(api_key=None)
    finally:
        if old:
            os.environ["OPENAI_API_KEY"] = old
