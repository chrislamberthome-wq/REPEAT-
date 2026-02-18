#!/bin/bash
# Script to update CRC_VECTORS_FREEZE.md with the latest commit SHA
# This records the commit at which the CRC vectors are frozen

set -e

# Get the latest commit SHA from the current branch
COMMIT_SHA=$(git log -1 --format="%H" 2>/dev/null)

if [ -z "$COMMIT_SHA" ]; then
  echo "Error: Unable to get commit SHA from git" >&2
  exit 1
fi

# Path to the freeze file
FREEZE_FILE="tests/vectors/CRC_VECTORS_FREEZE.md"

# Update the file with the commit SHA
echo "CRC vectors frozen as of: ${COMMIT_SHA}" > "${FREEZE_FILE}"

echo "Updated ${FREEZE_FILE} with commit SHA: ${COMMIT_SHA}"
