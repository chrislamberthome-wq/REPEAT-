#!/usr/bin/env bash
# Update pinned versions of development dependencies in requirements-dev.txt
# This script installs the latest versions of dev tools and captures their pinned versions

set -euo pipefail

cd "$(dirname "$0")/.."

echo "Installing latest versions of dev dependencies..."
pip install --upgrade pip pytest ruff build twine

echo "Generating requirements-dev.txt with pinned versions..."
pip freeze | grep -E "^(pytest|ruff|build|twine)==" | sort > requirements-dev.txt

echo "Successfully updated requirements-dev.txt with:"
cat requirements-dev.txt
