"""Tests for core models and defaults."""

import os
import tempfile

from interviewer.defaults import (
    DEFAULT_INTERVIEWER_SYSTEM_PROMPT,
    DEFAULT_MAX_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_OPENING_MAX_TOKENS,
    DEFAULT_RESPONDENT_SYSTEM_PROMPT,
    DEFAULT_TEMPERATURE,
    END_OF_INTERVIEW_RESPONSE,
    LAST_QUESTION_RESPONSE,
    OPENING_INSTRUCTION,
)
from interviewer.models import (
    AgentConfig,
    AgentResponse,
    GameConfig,
    LLMCallInfo,
    Message,
    Transcript,
    list_games,
    load_game,
    load_prompt,
)


def test_defaults():
    assert DEFAULT_MODEL == "gpt-5"
    assert DEFAULT_TEMPERATURE == 1
    assert DEFAULT_MAX_TOKENS == 200
    assert DEFAULT_OPENING_MAX_TOKENS == 150
    assert "interviewer" in DEFAULT_INTERVIEWER_SYSTEM_PROMPT.lower()
    assert "participant" in DEFAULT_RESPONDENT_SYSTEM_PROMPT.lower()
    assert LAST_QUESTION_RESPONSE.startswith("Before we wrap up")
    assert END_OF_INTERVIEW_RESPONSE.startswith("Thank you")
    assert "greeting" in OPENING_INSTRUCTION.lower()


def test_message():
    msg = Message(role="interviewer", text="Hello, how are you?")
    assert msg.role == "interviewer"
    assert msg.text == "Hello, how are you?"

    msg2 = Message(role="respondent", text="I'm doing well.")
    assert msg2.role == "respondent"


def test_agent_config_defaults():
    config = AgentConfig(system_prompt="Test prompt")
    assert config.model == "gpt-5"
    assert config.temperature == 1
    assert config.max_tokens == 200


def test_agent_config_from_prompt_inline():
    config = AgentConfig.from_prompt("You are a test interviewer.")
    assert config.system_prompt == "You are a test interviewer."


def test_agent_config_from_prompt_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# My Prompt\n\nYou are a great interviewer.")
        f.flush()
        path = f.name

    try:
        config = AgentConfig.from_prompt(path)
        assert config.system_prompt == "# My Prompt\n\nYou are a great interviewer."
    finally:
        os.unlink(path)


def test_load_prompt_inline():
    assert load_prompt("Hello world") == "Hello world"


def test_load_prompt_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("  File content  ")
        f.flush()
        path = f.name

    try:
        assert load_prompt(path) == "File content"
    finally:
        os.unlink(path)


def test_load_prompt_nonexistent_md_path():
    # A .md string that doesn't exist as a file should be returned as-is
    result = load_prompt("some_nonexistent_file.md")
    assert result == "some_nonexistent_file.md"


def test_llm_call_info():
    info = LLMCallInfo(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "test"}],
        params={"temperature": 1},
        input_tokens=100,
        output_tokens=50,
    )
    assert info.input_tokens == 100
    assert info.output_tokens == 50


def test_agent_response():
    resp = AgentResponse(text="Hello!")
    assert resp.text == "Hello!"
    assert resp.llm_call_info is None

    resp_with_info = AgentResponse(
        text="Hello!",
        llm_call_info=LLMCallInfo(
            model="gpt-4o-mini",
            messages=[],
            params={},
            input_tokens=10,
            output_tokens=5,
        ),
    )
    assert resp_with_info.llm_call_info is not None


def test_transcript():
    t = Transcript()
    assert t.messages == []
    assert t.interviewer_config is None
    assert t.total_input_tokens == 0

    msg = Message(role="interviewer", text="Hi")
    t.messages.append(msg)
    assert len(t.messages) == 1


def test_load_game_bargainer():
    gc = load_game("bargainer")
    assert gc.name == "Bargainer"
    assert gc.description == "A multi-round price negotiation over a mug"
    assert "game manager" in gc.interviewer_system_prompt.lower()
    assert "buyer" in gc.respondent_system_prompt.lower()
    assert gc.opening_max_tokens == 500
    assert gc.last_question_response != ""
    assert gc.end_of_session_response != ""
    assert gc.opening_instruction != ""


def test_load_game_not_found():
    import pytest
    with pytest.raises(ValueError, match="Game not found"):
        load_game("nonexistent_game_xyz")


def test_list_games():
    games = list_games()
    assert isinstance(games, list)
    names = [g["name"] for g in games]
    assert "bargainer" in names


def test_game_config_model():
    gc = GameConfig(
        name="Test",
        interviewer_system_prompt="test prompt",
        respondent_system_prompt="test respondent",
        opening_instruction="begin",
        last_question_response="last?",
        end_of_session_response="done",
    )
    assert gc.name == "Test"
    assert gc.opening_max_tokens == 150  # default
