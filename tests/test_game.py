"""Tests for game framework (protocol parsing, message formatting, models)."""

from __future__ import annotations

import os

import pytest

from interviewer.game import GameManager, GameOrchestrator, PlayerAgent, PLAYER_TURN_PATTERN
from interviewer.game_models import GameMessage, GameTranscript
from interviewer.models import AgentConfig


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
        GameMessage(role="manager", text="Welcome!"),
        GameMessage(role="human", text="I offer $50"),
        GameMessage(
            role="player",
            text="[PLAYER_DECISION]OFFER $60[/PLAYER_DECISION]",
            visible=False,
        ),
        GameMessage(role="manager", text="AI offers $60"),
    ]
    api_messages = manager._format_messages(messages, manager_config)

    assert api_messages[0]["role"] == "system"
    assert api_messages[0]["content"] == manager_config.system_prompt
    assert api_messages[1]["role"] == "assistant"  # manager -> assistant
    assert api_messages[2]["role"] == "user"  # human -> user
    assert api_messages[3]["role"] == "user"  # player -> user
    assert api_messages[4]["role"] == "assistant"  # manager -> assistant


def test_manager_format_messages_empty(manager, manager_config):
    api_messages = manager._format_messages([], manager_config)
    assert len(api_messages) == 1
    assert api_messages[0]["role"] == "system"


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
