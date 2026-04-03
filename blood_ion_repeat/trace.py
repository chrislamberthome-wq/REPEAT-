"""JSONL trace writer for ionic channel experiments."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class TraceWriter:
    """Append-only JSONL trace writer."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self._path.open("w", encoding="utf-8")

    def write(self, event: dict[str, Any]) -> None:
        """Append *event* as a single JSON line."""
        self._fh.write(json.dumps(event, separators=(",", ":")) + "\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "TraceWriter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def load_trace(path: Path | str) -> list[dict[str, Any]]:
    """Read all events from a JSONL trace file."""
    events: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return events
