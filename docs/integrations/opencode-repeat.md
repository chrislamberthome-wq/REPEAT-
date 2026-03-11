# OpenCode Integration for REPEAT — REPEAT-Safe Constraints and Plugin Behavior

## Purpose

This document specifies the integration of [OpenCode](https://opencode.ai) as an
operator-side assistant for the REPEAT governance framework. It defines exactly
what OpenCode is and is not permitted to do within the REPEAT trust model.

---

## Authoritative Lane (Deterministic Verifiers)

The following components are the **sole authority** for all governance outcomes:

| Component | Role |
|---|---|
| `verifiers/repeat_verifier.py` | Validates action and receipt JSON deterministically |
| `verifiers/replay_ledger_engine.py` | Replays the ledger; reconstructs and verifies state chain |
| `schemas/*.schema.json` | Canonical schema definitions for actions, receipts, and state |
| `receipts/council_ledger.jsonl` | Append-only ledger of verifier-approved receipts |

**Rules:**
- Only verifiers may emit `PASS`, `FAIL`, or `ERROR`.
- Only verifiers may define state-transition validity.
- Ledger entries are appended **only on `PASS`** and only through deterministic code paths.
- No component outside this lane may mutate canonical ledger state.

---

## Advisory Lane (OpenCode)

OpenCode operates strictly in the advisory lane. It may:

- Help operators **draft** `council_action.json`, receipt candidates, or test fixtures.
- **Invoke** local verifier scripts (`repeat.verify_action`, `repeat.verify_receipt`, `repeat.replay_ledger`) and display their raw outputs.
- **Explain** verifier failures to the operator.
- **Generate** remediation notes or candidate patches for operator review.
- **Scaffold** test fixtures and governance action templates.

OpenCode **must not**:

- Emit, reinterpret, or override verifier `PASS`/`FAIL`/`ERROR` outcomes.
- Write to `receipts/council_ledger.jsonl` directly or indirectly.
- Perform policy inference or automatically correct invalid actions.
- Mutate canonical state outside verifier-approved processes.
- Apply governance changes based on model judgment rather than deterministic code.
- Introduce learning-based governance changes without explicit versioned code and tests.

### The REPEAT-Safe Rule

> **OpenCode may draft, inspect, explain, and scaffold.**
> **OpenCode may not certify, authorize, or alter replay truth.**

---

## Plugin Commands

The OpenCode plugin (`.opencode/plugins/repeat.ts`) registers the following commands:

### `repeat.verify_action <path>`

Validates a council governance action JSON file.

- Invokes `tools/repeat_verify_action.sh <path>` → `verifiers/repeat_verifier.py verify-action <path>`.
- Preserves **raw stdout, stderr, and exit status** from the verifier unchanged.
- Exit codes: `0` = PASS, `1` = FAIL, `2` = ERROR.

### `repeat.verify_receipt <path>`

Validates a seat-fill receipt JSON file.

- Invokes `tools/repeat_verify_receipt.sh <path>` → `verifiers/repeat_verifier.py verify-receipt <path>`.
- Preserves **raw stdout, stderr, and exit status** from the verifier unchanged.
- Exit codes: `0` = PASS, `1` = FAIL, `2` = ERROR.

### `repeat.replay_ledger [path]`

Replays the council ledger and emits the resulting state.

- Invokes `tools/repeat_replay_ledger.sh [path]` → `verifiers/replay_ledger_engine.py`.
- Defaults to `receipts/council_ledger.jsonl` if no path is provided.
- On `PASS`: emits final council state as JSON to stdout.
- Exit codes: `0` = PASS, `1` = FAIL, `2` = ERROR.

---

## Plugin Behavior Contract

The plugin **must**:

- Use CLI file path arguments, not shell-interpolated strings (enforced via `spawnSync` with explicit argument arrays).
- Preserve raw stdout, stderr, and exit statuses from verifier scripts.
- Treat infrastructure faults (spawn errors, non-zero exit) as `ERROR` without silent downgrade.
- Label any advisory note clearly as `[ADVISORY]` so operators can distinguish it from verifier output.

---

## Verification Workflow

The recommended operator workflow is:

```
IDENTITY → AUTHORIZATION → STATE TRANSITION → RECEIPT REPLAY
```

1. **Draft** the council action using OpenCode assistance or manually.
2. **Verify** the action: `repeat.verify_action path/to/action.json`
3. **If PASS**: append the resulting receipt to `receipts/council_ledger.jsonl` through the authoritative write path.
4. **If FAIL/ERROR**: review OpenCode's advisory note, correct the action, and re-verify.
5. **Replay** the ledger periodically: `repeat.replay_ledger` to confirm chain integrity.

---

## Schemas

| File | Description |
|---|---|
| `schemas/council_action.schema.json` | JSON Schema for governance action candidates |
| `schemas/seat_fill_receipt.schema.json` | JSON Schema for `seat_fill` receipts (c9-receipt-v1.0) |
| `schemas/council_state.schema.json` | JSON Schema for council state snapshots |

---

## Non-Goals

- No autonomous ledger writes.
- No policy inference or automatic correction of invalid actions.
- No mutation of canonical state outside verifier-approved processes.
- No learning-based governance changes without explicit versioned code and tests.
- No use of OpenCode as a trust anchor or final authority for any governance decision.

---

## Architecture Boundary

```
┌─────────────────────────────────────────────────────────────────────┐
│  ADVISORY LANE (OpenCode)                                           │
│  Draft → Explain → Scaffold → Remediate (operator-reviewed)        │
│                          │                                          │
│                          ▼ (calls via CLI arguments)                │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  AUTHORITATIVE LANE (Deterministic Verifiers)                │  │
│  │  repeat_verifier.py  ←→  replay_ledger_engine.py             │  │
│  │  JSON schemas        ←→  receipts/council_ledger.jsonl       │  │
│  │  PASS / FAIL / ERROR (final; cannot be overridden)           │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

The advisory lane may invoke but never override the authoritative lane.
State transitions flow exclusively through deterministic verifiers and
append-only ledger mechanics.
