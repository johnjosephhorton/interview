from __future__ import annotations

import csv
from pathlib import Path

from .game_models import GameTranscript


def save_game_transcript(
    transcript: GameTranscript,
    path: str | Path,
    format: str = "json",
) -> None:
    """Save a game transcript to disk.

    Args:
        transcript: The game transcript to save.
        path: Output file path.
        format: "json" for full structured data, "csv" for flat table.
    """
    path = Path(path)

    if format == "json":
        path.write_text(
            transcript.model_dump_json(
                indent=2, exclude={"llm_calls": {"__all__": {"messages"}}}
            )
        )
    elif format == "csv":
        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["turn", "role", "text", "visible"])
            for i, msg in enumerate(transcript.messages):
                writer.writerow([i + 1, msg.role, msg.text, msg.visible])
    else:
        raise ValueError(f"Unsupported format: {format!r}. Use 'json' or 'csv'.")
