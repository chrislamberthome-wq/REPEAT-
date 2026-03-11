#!/usr/bin/env bash
# tools/repeat_replay_ledger.sh
#
# Wrapper for the REPEAT ledger replay engine.
# Invokes verifiers/replay_ledger_engine.py to deterministically replay the
# council ledger and emit the resulting council state as JSON to stdout.
#
# Usage:
#   tools/repeat_replay_ledger.sh [path-to-ledger.jsonl]
#
# If no path is provided, defaults to receipts/council_ledger.jsonl.
#
# Exit codes (propagated unchanged from replay_ledger_engine.py):
#   0 = PASS — replay succeeded; final state on stdout
#   1 = FAIL — hash chain broken or governance rule violated
#   2 = ERROR — infrastructure fault
#
# OpenCode plugin contract: this script preserves raw stdout, stderr, and
# exit status from the engine. It must never suppress or reinterpret them.
set -euo pipefail

LEDGER_PATH="${1:-receipts/council_ledger.jsonl}"

exec python3 verifiers/replay_ledger_engine.py "$LEDGER_PATH"
