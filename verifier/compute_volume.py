from __future__ import annotations

from typing import Sequence


Vector = Sequence[float]


def _sub(a: Vector, b: Vector) -> tuple:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _det3(a: Vector, b: Vector, c: Vector) -> float:
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    )


def compute_signed_volume(v1: Vector, v2: Vector, v3: Vector, v4: Vector) -> float:
    a = _sub(v2, v1)
    b = _sub(v3, v1)
    c = _sub(v4, v1)
    return _det3(a, b, c) / 6.0
