# B4IU Locked Counter and Spec Rule

## Overview

The B4IU (Before-In-Use) locked counter is a safety mechanism that tracks verification operations and enforces compliance with a "spec rule" before data can be considered safe for use.

## Purpose

The counter ensures that:
1. Verification operations are properly tracked
2. Data undergoes sufficient validation before being marked as "safe"
3. Once verification is complete, the counter state becomes immutable
4. Compliance with minimum verification requirements (spec rule) is enforced

## How It Works

### Counter States

- **Unlocked**: Counter can be incremented to track verification operations
- **Locked**: Counter becomes immutable, indicating verification is complete

### Spec Rule

The spec rule ensures that a minimum number of verification operations have been performed before the counter is locked:

- **Non-strict mode**: Requires at least 1 verification operation (basic CRC/parse check)
- **Strict mode**: Requires at least 2 verification operations (CRC/parse + invariant checks)

### Integration with CLI

The counter is automatically used in the `verify` command:

```bash
# Non-strict verification (1 operation tracked)
python -m repeat_hd.cli verify --infile data.enc

# Strict verification (2 operations tracked)  
python -m repeat_hd.cli verify --strict --infile data.enc
```

## API Usage

```python
from repeat_hd.cli import B4IULockedCounter

# Create a counter
counter = B4IULockedCounter()

# Track operations
counter.increment()  # Returns True
counter.increment()  # Returns True

# Lock the counter
counter.lock()

# Further increments are rejected
counter.increment()  # Returns False, violation recorded

# Check spec rule compliance
is_valid, error = counter.check_spec_rule(min_required=2)
if not is_valid:
    print(f"Spec rule violation: {error}")

# Get counter state
count = counter.get_count()
is_locked = counter.is_locked()
violations = counter.get_violations()
```

## Testing

The feature includes comprehensive test coverage:

- Unit tests for counter operations (test_b4iu_counter.py)
- Spec rule validation tests
- Integration tests with CLI
- All tests: `make test`
- Diagnostics: `make diag-strict`

## CI/CD Integration

The b4iu counter is integrated into the CI pipeline via the `make diag-strict` target, which:

1. Runs all tests with short traceback mode
2. Validates b4iu locked counter functionality
3. Reports diagnostics completion status

This ensures that all verification operations in the CI pipeline are properly tracked and comply with the spec rule.
