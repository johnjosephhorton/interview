from __future__ import annotations

import csv
import json
from pathlib import Path

from .models import Transcript


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
