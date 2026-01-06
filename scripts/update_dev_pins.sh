#!/usr/bin/env bash
# Update pinned versions of development dependencies in requirements-dev.txt
# This script installs the latest versions of dev tools and captures their pinned versions
# Note: This modifies your current Python environment. Consider running in a virtual environment.

set -euo pipefail

cd "$(dirname "$0")/.."

# Ensure Python is available before proceeding
if ! command -v python >/dev/null 2>&1; then
    echo "Error: Python is required but was not found in PATH." >&2
    exit 1
fi
# Define the list of dev packages to pin
DEV_PACKAGES="pytest ruff build twine"

echo "Installing latest versions of dev dependencies..."
for pkg in pip $DEV_PACKAGES; do
    echo "Installing/upgrading ${pkg}..."
    if ! pip install --upgrade "${pkg}"; then
        echo "Error: Failed to install or upgrade '${pkg}'." >&2
        echo "Aborting update_dev_pins.sh. Please fix the issue with '${pkg}' and retry." >&2
        exit 1
    fi
done

echo "Generating requirements-dev.txt with pinned versions (including transitive dependencies)..."
pip list --format=freeze | sort > requirements-dev.txt

echo "Successfully updated requirements-dev.txt with:"
cat requirements-dev.txt
