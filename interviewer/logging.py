from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .models import Transcript, _PROJECT_ROOT


def save_transcript(
    transcript: Transcript,
    path: str | Path,
    format: str = "json",
) -> None:
    """Save a transcript to disk.

    Args:
        transcript: The transcript to save.
        path: Output file path.
        format: "json" for full structured data, "csv" for flat table.
    """
    path = Path(path)

    if format == "json":
        path.write_text(
            transcript.model_dump_json(indent=2, exclude={"llm_calls": {"__all__": {"messages"}}})
        )
    elif format == "csv":
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["turn", "role", "text"])
            for i, msg in enumerate(transcript.messages):
                writer.writerow([i + 1, msg.role, msg.text])
    else:
        raise ValueError(f"Unsupported format: {format!r}. Use 'json' or 'csv'.")


def auto_save_transcript(
    transcript: Transcript,
    game_name: str,
    suffix: str | None = None,
    timestamp: str | None = None,
) -> Path:
    """Auto-save a transcript to transcripts/<game_name>/<timestamp>[_suffix].json.

    Args:
        transcript: The transcript to save.
        game_name: Game folder name (e.g. "bargainer").
        suffix: Optional suffix (e.g. "sim1") appended before .json.
        timestamp: Optional pre-computed timestamp string. If None, uses current local time.

    Returns:
        Path to the saved file.
    """
    if timestamp is None:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    filename = f"{timestamp}_{suffix}.json" if suffix else f"{timestamp}.json"
    path = _PROJECT_ROOT / "transcripts" / game_name / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    save_transcript(transcript, path, format="json")
    return path
