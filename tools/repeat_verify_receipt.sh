#!/usr/bin/env bash
# tools/repeat_verify_receipt.sh
#
# Wrapper for the REPEAT receipt verifier.
# Invokes verifiers/repeat_verifier.py to validate a seat_fill receipt file.
#
# Usage:
#   tools/repeat_verify_receipt.sh <path-to-receipt.json>
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
    echo "ERROR: usage: $0 <path-to-receipt.json>" >&2
    exit 2
fi

RECEIPT_PATH="$1"

exec python3 verifiers/repeat_verifier.py verify-receipt "$RECEIPT_PATH"
