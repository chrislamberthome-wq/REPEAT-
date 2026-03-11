#!/usr/bin/env bash
# tools/repeat_verify_action.sh
#
# Wrapper for the REPEAT council action verifier.
# Invokes verifiers/repeat_verifier.py with the provided action file path.
#
# Usage:
#   tools/repeat_verify_action.sh <path-to-action.json>
#
# Exit codes (propagated unchanged from repeat_verifier.py):
#   0 = PASS
#   1 = FAIL
#   2 = ERROR
#
# OpenCode plugin contract: this script preserves raw stdout, stderr, and
# exit status from the verifier. It must never suppress or reinterpret them.
set -euo pipefail

if [ $# -ne 1 ]; then
    echo "ERROR: usage: $0 <path-to-action.json>" >&2
    exit 2
fi

ACTION_PATH="$1"

exec python3 verifiers/repeat_verifier.py verify-action "$ACTION_PATH"
