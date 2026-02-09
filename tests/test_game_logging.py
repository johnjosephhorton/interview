"""Tests for game transcript saving."""

from __future__ import annotations

import csv
import json
import tempfile
from pathlib import Path

from interviewer.game_logging import save_game_transcript
from interviewer.game_models import GameMessage, GameTranscript
from interviewer.models import AgentConfig


def _make_game_transcript() -> GameTranscript:
    return GameTranscript(
        messages=[
            GameMessage(role="manager", text="Welcome! Round 1."),
            GameMessage(role="human", text="I offer $50"),
            GameMessage(
                role="player",
                text="[PLAYER_DECISION]OFFER $60[/PLAYER_DECISION]",
                visible=False,
            ),
            GameMessage(role="manager", text="AI counters with $60."),
        ],
        manager_config=AgentConfig(system_prompt="Test manager prompt", max_tokens=500),
        player_config=AgentConfig(system_prompt="Test player prompt", max_tokens=100),
        total_input_tokens=300,
        total_output_tokens=120,
    )


def test_save_game_json():
    t = _make_game_transcript()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name

    save_game_transcript(t, path, format="json")
    data = json.loads(Path(path).read_text())
    assert len(data["messages"]) == 4
    assert data["messages"][0]["role"] == "manager"
    assert data["messages"][2]["visible"] is False
    assert data["total_input_tokens"] == 300
    assert data["total_output_tokens"] == 120
    Path(path).unlink()


def test_save_game_csv():
    t = _make_game_transcript()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name

    save_game_transcript(t, path, format="csv")
    with open(path) as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ["turn", "role", "text", "visible"]
    assert len(rows) == 5  # header + 4 messages
    assert rows[1][1] == "manager"
    assert rows[3][3] == "False"  # player message not visible
    Path(path).unlink()


def test_save_game_unsupported_format():
    t = _make_game_transcript()
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        path = f.name

    try:
        import pytest

        with pytest.raises(ValueError, match="Unsupported format"):
            save_game_transcript(t, path, format="xml")
    finally:
        Path(path).unlink()
