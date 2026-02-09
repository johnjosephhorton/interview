"""Tests for game framework (protocol parsing, message formatting, models)."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, patch

import pytest

from interviewer.game import GameManager, GameOrchestrator, PlayerAgent, PLAYER_TURN_PATTERN
from interviewer.game_models import GameMessage, GameTranscript
from interviewer.models import AgentConfig, AgentResponse, LLMCallInfo


# --- Fixtures ---


@pytest.fixture
def manager():
    return GameManager(api_key="sk-test-dummy")


@pytest.fixture
def player():
    return PlayerAgent(api_key="sk-test-dummy")


@pytest.fixture
def orchestrator():
    return GameOrchestrator(api_key="sk-test-dummy")


@pytest.fixture
def manager_config():
    return AgentConfig(system_prompt="You are a test game manager.", max_tokens=500)


@pytest.fixture
def player_config():
    return AgentConfig(system_prompt="You are a test player.", max_tokens=100)


# --- Model tests ---


def test_game_message():
    msg = GameMessage(role="manager", text="Welcome to the game!")
    assert msg.role == "manager"
    assert msg.text == "Welcome to the game!"
    assert msg.visible is True


def test_game_message_hidden():
    msg = GameMessage(role="player", text="OFFER $50", visible=False)
    assert msg.role == "player"
    assert msg.visible is False


def test_game_message_roles():
    for role in ("manager", "human", "player"):
        msg = GameMessage(role=role, text="test")
        assert msg.role == role


def test_game_transcript():
    t = GameTranscript()
    assert t.messages == []
    assert t.manager_config is None
    assert t.player_config is None
    assert t.total_input_tokens == 0
    assert t.total_output_tokens == 0
    assert t.llm_calls == []
    assert t.ended_at is None
    assert t.started_at is not None


def test_game_transcript_with_messages():
    msg = GameMessage(role="manager", text="Game started")
    config = AgentConfig(system_prompt="test", max_tokens=500)
    t = GameTranscript(messages=[msg], manager_config=config)
    assert len(t.messages) == 1
    assert t.manager_config.system_prompt == "test"


# --- Protocol parsing tests ---


def test_player_turn_pattern_match():
    text = "Some preamble [PLAYER_TURN]Make your offer[/PLAYER_TURN] some suffix"
    match = PLAYER_TURN_PATTERN.search(text)
    assert match is not None
    assert match.group(1).strip() == "Make your offer"


def test_player_turn_pattern_no_match():
    text = "No player turn here, just regular manager output."
    match = PLAYER_TURN_PATTERN.search(text)
    assert match is None


def test_player_turn_pattern_multiline():
    text = """Here is the game state:
[PLAYER_TURN]
Round: 3/6
Surplus: $72.90
Make your offer.
[/PLAYER_TURN]"""
    match = PLAYER_TURN_PATTERN.search(text)
    assert match is not None
    assert "Round: 3/6" in match.group(1)
    assert "Make your offer." in match.group(1)


def test_player_turn_pattern_empty_content():
    text = "[PLAYER_TURN][/PLAYER_TURN]"
    match = PLAYER_TURN_PATTERN.search(text)
    assert match is not None
    assert match.group(1).strip() == ""


def test_strip_protocol_tags(orchestrator):
    text = "Preamble [PLAYER_TURN]hidden context[/PLAYER_TURN] visible text"
    result = orchestrator._strip_protocol_tags(text)
    assert "[PLAYER_TURN]" not in result
    assert "[/PLAYER_TURN]" not in result
    assert "visible text" in result
    assert "Preamble" in result


def test_strip_protocol_tags_no_tags(orchestrator):
    text = "No tags here, just plain text."
    result = orchestrator._strip_protocol_tags(text)
    assert result == text


def test_strip_protocol_tags_multiline(orchestrator):
    text = """Game state:
[PLAYER_TURN]
Round 1
Offer: $50
[/PLAYER_TURN]
Your turn!"""
    result = orchestrator._strip_protocol_tags(text)
    assert "[PLAYER_TURN]" not in result
    assert "Game state:" in result
    assert "Your turn!" in result


# --- Message formatting tests ---


def test_manager_format_messages(manager, manager_config):
    messages = [
        GameMessage(role="manager", text="Welcome! The AI offers you $40."),
        GameMessage(role="human", text="I accept"),
        GameMessage(role="manager", text="You accepted. Round 2: Your turn to propose."),
    ]
    api_messages = manager._format_messages(messages, manager_config)

    assert api_messages[0]["role"] == "system"
    assert api_messages[0]["content"] == manager_config.system_prompt
    assert api_messages[1]["role"] == "assistant"  # manager -> assistant
    assert api_messages[2]["role"] == "user"  # human -> user
    assert api_messages[3]["role"] == "assistant"  # manager -> assistant


def test_manager_format_messages_empty(manager, manager_config):
    api_messages = manager._format_messages([], manager_config)
    assert len(api_messages) == 1
    assert api_messages[0]["role"] == "system"


# --- {PLAYER_DECISION} substitution tests ---


async def test_resolve_player_turns_no_tags(orchestrator, player_config):
    """Text with no [PLAYER_TURN] blocks passes through unchanged."""
    text = "No player turn here, just plain text."
    result, llm_calls, had_turn = await orchestrator._resolve_player_turns(text, player_config)
    assert result == text
    assert llm_calls == []
    assert had_turn is False


async def test_resolve_player_turns_single_substitution(orchestrator, player_config):
    """Single [PLAYER_TURN] + {PLAYER_DECISION} gets resolved."""
    manager_text = (
        "Round 1: The AI Player is the Proposer.\n\n"
        "[PLAYER_TURN]\nPROPOSER_TURN\nOFFER <number>\n[/PLAYER_TURN]\n\n"
        "The AI Player offers you ${PLAYER_DECISION} out of $100. Do you accept or reject?"
    )

    mock_llm_info = LLMCallInfo(
        model="test", messages=[], params={}, input_tokens=10, output_tokens=5
    )
    mock_resp = AgentResponse(text="OFFER 40", llm_call_info=mock_llm_info)

    with patch.object(orchestrator._player, "generate_response", new_callable=AsyncMock) as mock:
        mock.return_value = mock_resp
        result, llm_calls, had_turn = await orchestrator._resolve_player_turns(
            manager_text, player_config
        )

    assert had_turn is True
    assert len(llm_calls) == 1
    assert "[PLAYER_TURN]" not in result
    assert "{PLAYER_DECISION}" not in result
    assert "OFFER 40" in result
    assert "The AI Player offers you $OFFER 40 out of $100" in result


async def test_resolve_player_turns_bundled_two_turns(orchestrator, player_config):
    """Bundled message with two [PLAYER_TURN] blocks and two {PLAYER_DECISION} placeholders."""
    manager_text = (
        "You offered $30.\n\n"
        "[PLAYER_TURN]\nRESPONDER_TURN\nACCEPT or REJECT\n[/PLAYER_TURN]\n\n"
        "The AI Player {PLAYER_DECISION}.\n\n"
        "Score: Human $30 | AI $70\n\n"
        "Round 3:\n\n"
        "[PLAYER_TURN]\nPROPOSER_TURN\nOFFER <number>\n[/PLAYER_TURN]\n\n"
        "The AI Player offers you ${PLAYER_DECISION} out of $100. Do you accept?"
    )

    mock_llm_info = LLMCallInfo(
        model="test", messages=[], params={}, input_tokens=10, output_tokens=5
    )
    call_count = 0

    async def fake_generate(messages, context, config):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return AgentResponse(text="ACCEPT", llm_call_info=mock_llm_info)
        else:
            return AgentResponse(text="OFFER 45", llm_call_info=mock_llm_info)

    with patch.object(orchestrator._player, "generate_response", side_effect=fake_generate):
        result, llm_calls, had_turn = await orchestrator._resolve_player_turns(
            manager_text, player_config
        )

    assert had_turn is True
    assert call_count == 2
    assert len(llm_calls) == 2
    assert "[PLAYER_TURN]" not in result
    assert "{PLAYER_DECISION}" not in result
    assert "The AI Player ACCEPT." in result
    assert "OFFER 45" in result


# --- API key tests ---


def test_manager_api_key_from_param():
    m = GameManager(api_key="sk-test-123")
    assert m._api_key == "sk-test-123"


def test_player_api_key_from_param():
    p = PlayerAgent(api_key="sk-test-123")
    assert p._api_key == "sk-test-123"


def test_orchestrator_api_key():
    o = GameOrchestrator(api_key="sk-test-456")
    assert o._manager._api_key == "sk-test-456"
    assert o._player._api_key == "sk-test-456"


def test_manager_api_key_missing_raises():
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="API key required"):
            GameManager(api_key=None)
    finally:
        if old:
            os.environ["OPENAI_API_KEY"] = old


def test_player_api_key_missing_raises():
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="API key required"):
            PlayerAgent(api_key=None)
    finally:
        if old:
            os.environ["OPENAI_API_KEY"] = old


def test_orchestrator_api_key_missing_raises():
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(ValueError, match="API key required"):
            GameOrchestrator(api_key=None)
    finally:
        if old:
            os.environ["OPENAI_API_KEY"] = old


# --- Player message accumulation tests ---


def test_player_messages_init(orchestrator, player_config):
    orchestrator._init_player_messages(player_config)
    assert len(orchestrator._player_messages) == 1
    assert orchestrator._player_messages[0]["role"] == "system"
    assert orchestrator._player_messages[0]["content"] == player_config.system_prompt


def test_player_messages_init_idempotent(orchestrator, player_config):
    orchestrator._init_player_messages(player_config)
    orchestrator._player_messages.append({"role": "user", "content": "test"})
    orchestrator._init_player_messages(player_config)
    # Should not re-initialize since list is not empty
    assert len(orchestrator._player_messages) == 2
