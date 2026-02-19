"""GAD_FLY verifier — B4IU (Bounded Forensic-Interaction Unit) v0.1.

Implements a receiver-verifiable transition for a visual-binary microtask
channel.  A single trial transmits a 1-bit stimulus (tx_bit ∈ {0, 1}) and
captures the user's 1-bit response (rx_bit ∈ {0, 1}).  The verifier evaluates
correctness and disqualifying interference to produce a deterministic verdict.

Certificate formula
-------------------
    delta = 1  if rx_bit == tx_bit  else 0
    P     = 1  if any disqualifying condition is met  else 0
    C     = delta - P
    verdict = "PASS" if C == 1 else "FAIL"

Disqualifying conditions (P = 1)
---------------------------------
1. Response time exceeds t_max_ms.
2. invalid_response is True (missing, multi-input, or tampered response).
3. panic == 1 (manual intervention flag).
"""

from __future__ import annotations

import json
from typing import Any

B4IU_ID = "human-substrate/gad-fly/v0.1"


def verify_trial(
    tx_bit: int,
    rx_bit: int,
    rt_ms: float,
    t_max_ms: float,
    panic: int = 0,
    invalid_response: bool = False,
) -> dict[str, Any]:
    """Verify a single B4IU v0.1 trial and return the result as a dict.

    Parameters
    ----------
    tx_bit:
        Transmitted bit (0 or 1).
    rx_bit:
        Received / user-reported bit (0 or 1).
    rt_ms:
        Observed response time in milliseconds.
    t_max_ms:
        Maximum allowable response time in milliseconds.
    panic:
        Manual intervention flag; 1 disqualifies the trial.
    invalid_response:
        True when the response is missing, multi-input, or otherwise tampered.

    Returns
    -------
    dict
        A JSON-serialisable dict matching the B4IU v0.1 single-trial schema.
    """
    delta = 1 if rx_bit == tx_bit else 0
    P = 1 if (rt_ms > t_max_ms) or panic == 1 or invalid_response else 0
    C = delta - P
    verdict = "PASS" if C == 1 else "FAIL"

    return {
        "b4iu_id": B4IU_ID,
        "tx_bit": tx_bit,
        "rx_bit": rx_bit,
        "rt_ms": rt_ms,
        "t_max_ms": t_max_ms,
        "panic": panic,
        "delta": delta,
        "P": P,
        "C": C,
        "verdict": verdict,
    }


def verify_trial_json(
    tx_bit: int,
    rx_bit: int,
    rt_ms: float,
    t_max_ms: float,
    panic: int = 0,
    invalid_response: bool = False,
) -> str:
    """Convenience wrapper that returns the trial result as a JSON string."""
    return json.dumps(verify_trial(tx_bit, rx_bit, rt_ms, t_max_ms, panic, invalid_response))
