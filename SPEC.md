# REPEAT SPEC

## B4IU_LOCKED Registry Rule

### Purpose
The `B4IU_LOCKED` token is a locked execution framework marker used to enforce compliance checks before merging code changes. This token allows the CI system to track and verify critical markers in the codebase.

### Token Definition
- **Token**: `B4IU_LOCKED`
- **Registry Variable**: `N_locked` (count of token occurrences)
- **Scope**: Repository-wide

### Registry Rule
1. **Counting**: The verifier script (`tools/ci/count_b4iu_locked.mjs`) scans all tracked files in the repository.
2. **Reporting**: The script reports `N_locked`, the total count of `B4IU_LOCKED` tokens found.
3. **Enforcement**: The CI workflow runs the verifier and enforces compliance by failing on non-zero exit codes.

### File Extensions Scanned
The verifier searches the following file types:
- Python: `.py`
- JavaScript/Node: `.js`, `.mjs`, `.ts`
- Documentation: `.md`, `.txt`
- Configuration: `.yml`, `.yaml`, `.json`, `.toml`, `.cfg`, `.ini`
- Shell: `.sh`

### Ignored Paths
The following paths are excluded from scanning:
- `node_modules/`
- `.git/`
- `__pycache__/`
- `*.pyc`
- `.egg-info/`
- `dist/`
- `build/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.ruff_cache/`

### Usage

#### Manual Verification
```bash
make ci-count-b4iu
```

#### CI Integration
The GitHub Actions workflow automatically runs the verifier on each PR and push to main:
```yaml
- name: B4IU_LOCKED Compliance Check
  run: make ci-count-b4iu
```

### Exit Codes
- `0`: Compliance check passed
- `1`: Compliance check failed

### Example Output
```
B4IU_LOCKED Verifier - Token Compliance Check
=========================================

Scanning directory: /path/to/repo
Looking for token: B4IU_LOCKED

Found 28 files to scan

Results:
--------
Total B4IU_LOCKED tokens found: 4

Files containing B4IU_LOCKED:
  path/to/file.py: 2 occurrence(s)
  path/to/other.md: 2 occurrence(s)

N_locked = 4

✓ Compliance check passed
```

### Version
- **Version**: 1.0.0
- **Date**: 2026-02-17
- **Status**: Active
