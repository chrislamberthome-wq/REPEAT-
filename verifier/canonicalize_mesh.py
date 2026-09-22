from __future__ import annotations

import json
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

PRECISION = Decimal("0.000000001")


def _quantize_number(value: float) -> float:
    d = Decimal(str(value)).quantize(PRECISION, rounding=ROUND_HALF_UP)
    return float(d)


def _canonicalize_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _canonicalize_value(value[k]) for k in sorted(value.keys())}
    if isinstance(value, list):
        return [_canonicalize_value(v) for v in value]
    if isinstance(value, float):
        return _quantize_number(value)
    return value


def canonicalize_mesh_state(mesh_state: dict[str, Any]) -> dict[str, Any]:
    normalized = _canonicalize_value(mesh_state)

    cells = normalized["cells"]
    normalized_cells = []
    for cell in cells:
        vertex_ids = sorted(cell["vertex_ids"])
        vertices = {vid: cell["vertices"][vid] for vid in vertex_ids}
        out = dict(cell)
        out["vertex_ids"] = vertex_ids
        out["vertices"] = vertices
        normalized_cells.append(out)

    normalized["cells"] = sorted(normalized_cells, key=lambda c: c["cell_id"])
    return normalized


def canonical_json_bytes(mesh_state: dict[str, Any]) -> bytes:
    canonical = canonicalize_mesh_state(mesh_state)
    return json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
