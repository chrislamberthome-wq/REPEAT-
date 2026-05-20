"""Canonical JSON serialisation for deterministic hashing."""
from __future__ import annotations

import json


def canonical_json(obj: object) -> bytes:
    """Return a deterministic UTF-8 JSON encoding of *obj* (sorted keys, no extra whitespace)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
