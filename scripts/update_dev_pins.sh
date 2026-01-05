#!/usr/bin/env bash
# Update pinned versions of development dependencies in requirements-dev.txt
# This script installs the latest versions of dev tools and captures their pinned versions
# Note: This modifies your current Python environment. Consider running in a virtual environment.

set -euo pipefail

cd "$(dirname "$0")/.."

# Define the list of dev packages to pin
DEV_PACKAGES="pytest ruff build twine"

echo "Installing latest versions of dev dependencies..."
pip install --upgrade pip $DEV_PACKAGES

echo "Generating requirements-dev.txt with pinned versions..."
# Build grep pattern from package list
PATTERN=$(echo "$DEV_PACKAGES" | tr ' ' '|')
pip freeze | grep -E "^($PATTERN)==" | sort > requirements-dev.txt

echo "Successfully updated requirements-dev.txt with:"
cat requirements-dev.txt
