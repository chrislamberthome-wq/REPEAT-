# CRC Vectors Freeze Automation

## Overview

This directory contains automation scripts for managing the CRC vectors freeze marker file.

## Files

### `update_crc_freeze.sh`

A bash script that updates `tests/vectors/CRC_VECTORS_FREEZE.md` with the latest commit SHA.

**Usage:**
```bash
./scripts/update_crc_freeze.sh
```

**What it does:**
- Retrieves the latest commit SHA from the current branch
- Updates `tests/vectors/CRC_VECTORS_FREEZE.md` with the format: `CRC vectors frozen as of: <commit_sha>`
- Exits with an error if git is unavailable or no commit history exists

## GitHub Actions Workflow

The repository includes a GitHub Actions workflow (`.github/workflows/update-crc-freeze.yml`) that automatically updates the freeze marker file when code is pushed to the main branch.

**How it works:**
1. Triggered on push to the `main` branch (or can be manually triggered via `workflow_dispatch`)
2. Checks out the code with full history
3. Runs the `update_crc_freeze.sh` script
4. If the freeze marker file has changed:
   - Commits the change with message: `Update CRC_VECTORS_FREEZE.md with commit SHA <sha> [skip ci]`
   - Pushes the commit back to the repository
5. The `[skip ci]` tag prevents infinite loop by skipping CI on the automated commit

**Important:** The freeze marker will reference the commit that triggered the workflow (the "real" commit with code changes), not the automated commit that updates the marker file itself.

## Purpose

The freeze marker serves as a boundary marker to document at which commit the CRC vectors were frozen. This provides:
- **Reproducibility**: Exact commit SHA for vector freeze point
- **Traceability**: Clear history of when vectors were last updated
- **Verification**: Ability to validate against a specific commit state

## Manual Usage

You can manually run the script at any time:

```bash
cd /path/to/REPEAT-
./scripts/update_crc_freeze.sh
```

This is useful for:
- Testing the script locally
- Manually updating the freeze marker if needed
- Verifying the script works correctly before merging changes
