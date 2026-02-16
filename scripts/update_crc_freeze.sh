#!/bin/bash
# Script to update CRC_VECTORS_FREEZE.md with the latest commit SHA

set -e

# Get the latest commit SHA from the main branch (or current branch if main doesn't exist)
COMMIT_SHA=$(git log -1 --format="%H" 2>/dev/null || echo "unknown")

# Path to the freeze file
FREEZE_FILE="tests/vectors/CRC_VECTORS_FREEZE.md"

# Update the file with the commit SHA
echo "CRC vectors frozen as of: ${COMMIT_SHA}" > "${FREEZE_FILE}"

echo "Updated ${FREEZE_FILE} with commit SHA: ${COMMIT_SHA}"
