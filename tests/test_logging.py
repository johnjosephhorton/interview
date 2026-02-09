"""Tests for transcript saving."""

import csv
import json
import tempfile
from pathlib import Path

from interviewer.logging import save_transcript
from interviewer.models import AgentConfig, Message, Transcript


def _make_transcript() -> Transcript:
    return Transcript(
        messages=[
            Message(role="interviewer", text="Hello!"),
            Message(role="respondent", text="Hi there."),
            Message(role="interviewer", text="Tell me about your experience."),
        ],
        interviewer_config=AgentConfig(system_prompt="Test interviewer prompt"),
        respondent_config=AgentConfig(system_prompt="Test respondent prompt"),
        total_input_tokens=150,
        total_output_tokens=60,
    )


def test_save_json():
    t = _make_transcript()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name

    save_transcript(t, path, format="json")
    data = json.loads(Path(path).read_text())
    assert len(data["messages"]) == 3
    assert data["messages"][0]["role"] == "interviewer"
    assert data["total_input_tokens"] == 150
    Path(path).unlink()


def test_save_csv():
    t = _make_transcript()
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        path = f.name

    save_transcript(t, path, format="csv")
    with open(path) as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert rows[0] == ["turn", "role", "text"]
    assert len(rows) == 4  # header + 3 messages
    assert rows[1] == ["1", "interviewer", "Hello!"]
    assert rows[2] == ["2", "respondent", "Hi there."]
    Path(path).unlink()
