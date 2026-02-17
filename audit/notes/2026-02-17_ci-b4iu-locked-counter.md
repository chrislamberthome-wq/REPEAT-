# CI B4IU_LOCKED Counter Implementation

**Date**: 2026-02-17  
**Type**: Infrastructure Enhancement  
**Status**: Implemented

## Summary
This update introduces the locked execution framework with the `B4IU_LOCKED` token compliance system. The framework provides a mechanism to track and verify critical markers in the codebase before code changes are merged.

## Components Added

### 1. Verifier Script
- **File**: `tools/ci/count_b4iu_locked.mjs`
- **Purpose**: Scans the repository for `B4IU_LOCKED` tokens and reports compliance status
- **Language**: JavaScript (Node.js)
- **Key Features**:
  - Recursive directory scanning with ignore patterns
  - Multi-file-type support (.py, .js, .mjs, .ts, .md, .yml, .yaml, .json, .sh, .toml, .cfg, .ini, .txt)
  - Clear reporting of token count (`N_locked`)
  - Proper exit codes for CI integration

### 2. Makefile Integration
- **Target**: `ci-count-b4iu`
- **Command**: `make ci-count-b4iu`
- **Purpose**: Provides a consistent entrypoint for running the verifier
- **Location**: Root Makefile

### 3. GitHub Actions Integration
- **Workflow**: `.github/workflows/ci.yml`
- **Job Name**: `b4iu-locked-check`
- **Execution**: Runs on every push and pull request to main branch
- **Environment**: Ubuntu latest with Node.js 20
- **Enforcement**: Fails the workflow if the verifier exits with non-zero code

### 4. Specification Document
- **File**: `SPEC.md`
- **Purpose**: Documents the B4IU_LOCKED registry rule
- **Contents**:
  - Token definition and purpose
  - Registry rules and counting methodology
  - File extensions scanned
  - Ignored paths
  - Usage instructions
  - Exit codes
  - Example output

### 5. Audit Documentation
- **File**: `audit/notes/2026-02-17_ci-b4iu-locked-counter.md` (this file)
- **Purpose**: Records the implementation details and rationale

## Technical Details

### Token Definition
- **Token**: `B4IU_LOCKED`
- **Meaning**: "Before You (merge) - LOCKED" - indicates locked execution checkpoints
- **Registry Variable**: `N_locked` (total count across repository)

### Verifier Behavior
1. Scans all files with supported extensions
2. Ignores build artifacts, dependencies, and cache directories
3. Counts occurrences of `B4IU_LOCKED` token
4. Reports files containing the token
5. Outputs `N_locked` value
6. Exits with code 0 (success) or 1 (failure)

### CI Integration Flow
1. GitHub Actions triggers on push/PR to main
2. Checkout code
3. Setup Node.js environment
4. Execute `make ci-count-b4iu`
5. Verifier runs and reports results
6. CI fails if verifier exits non-zero

## Rationale

### Why Node.js?
- Native async file I/O performance
- Built-in regex and string handling
- Zero external dependencies required
- Cross-platform compatibility
- Already available in GitHub Actions

### Why Make Target?
- Consistent interface across different CI systems
- Easy local testing by developers
- Abstraction layer for implementation changes
- Standard practice in the repository

### Why Separate Job in CI?
- Clear separation of concerns
- Independent failure reporting
- Parallel execution with tests
- Easy to locate in CI logs

## Usage Examples

### Local Verification
```bash
# Run the verifier
make ci-count-b4iu

# Run the script directly
node tools/ci/count_b4iu_locked.mjs
```

### Expected Output
```
B4IU_LOCKED Verifier - Token Compliance Check
=========================================

Scanning directory: /home/runner/work/REPEAT-/REPEAT-
Looking for token: B4IU_LOCKED

Found 28 files to scan

Results:
--------
Total B4IU_LOCKED tokens found: 4

Files containing B4IU_LOCKED:
  tools/ci/count_b4iu_locked.mjs: 4 occurrence(s)

N_locked = 4

✓ Compliance check passed
```

## Testing

### Manual Testing Performed
- ✓ Script execution with no tokens (baseline)
- ✓ Script execution with tokens in verifier itself
- ✓ Make target invocation
- ✓ File scanning with ignore patterns
- ✓ Multi-file-type support

### CI Testing
- ✓ Workflow syntax validation
- ✓ Job definition correctness
- ✓ Node.js setup configuration

## Future Enhancements

### Potential Additions
1. **Threshold Enforcement**: Add maximum `N_locked` limits
2. **Historical Tracking**: Track `N_locked` changes over time
3. **Violation Rules**: Enforce specific placement rules for tokens
4. **Report Generation**: Output JSON/HTML reports
5. **Integration Points**: Link to issue tracker or documentation

### Extensibility Points
- Configuration file for custom patterns
- Multiple token types support
- Custom ignore patterns per directory
- Hook system for custom validators

## Maintenance Notes

### Dependencies
- Node.js >= 14 (ES modules support)
- No external npm packages required
- Uses only Node.js built-in modules

### File Paths
- Verifier: `tools/ci/count_b4iu_locked.mjs`
- Spec: `SPEC.md`
- Workflow: `.github/workflows/ci.yml`
- Makefile: `./Makefile`

### Known Limitations
1. Binary files are not scanned
2. Symlinks are not followed
3. Very large files (>100MB) may cause memory issues
4. Token must be exact match (case-sensitive)

## Rollback Plan
If issues arise:
1. Remove the `b4iu-locked-check` job from `.github/workflows/ci.yml`
2. Remove or comment out `ci-count-b4iu` target in Makefile
3. Remove `tools/ci/count_b4iu_locked.mjs`
4. Remove `SPEC.md` or revert B4IU_LOCKED section
5. Git revert the commit(s)

## References
- GitHub Actions Documentation: https://docs.github.com/en/actions
- Node.js File System API: https://nodejs.org/api/fs.html
- Make Documentation: https://www.gnu.org/software/make/manual/

## Change Log
- 2026-02-17: Initial implementation
  - Added verifier script
  - Added Makefile target
  - Added CI workflow job
  - Added SPEC.md documentation
  - Added audit notes

---

**Implemented by**: GitHub Copilot Agent  
**Reviewed by**: Pending  
**Approved by**: Pending
