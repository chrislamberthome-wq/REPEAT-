# Compliance Matrix

## Overview
This matrix maps each invariant in the IDA/REPEAT framework (INV-STACK) to its implementation points across different layers of the architecture, ensuring consistency and verifiability. The status column tracks whether each invariant is specified, enforced, tested, or formalized.

| Invariant ID  | Authoritative Layer      | Enforcement Point                | Runtime Assertion Identifier | Test Coverage | On-Chain Constraint | Replay/Immutability Condition | Failure Code/Violation ID | Status                |
|---------------|--------------------------|----------------------------------|-----------------------------|----------------|----------------------|-------------------------------|----------------------------|-----------------------|
| INV-STACK-01  | REPEAT                  | Control path verification        | assert_control_downstream   | test_control   | Commit binding        | REPEAT-certified immutability| INV-CTRL-001               | SPECIFIED/ENFORCED   |
| INV-STACK-02  | IDA                     | Adjustment metadata traceability | assert_causal_trace         | test_adjust    |                      | Replay metadata correctness  | INV-CTRL-002               | SPECIFIED/TESTED     |
| INV-STACK-03  | REPEAT/IDA              | Mutual authority separation      | assert_no_diag_influence    | test_diag_sep  | State binding         | Immutable diagnostics         | INV-CTRL-003               | SPECIFIED/FORMALIZED |
| INV-STACK-04  | B4IU                    | Fail-closed expression policies  | assert_fail_closed_trans    | test_b4iu      | Solidity constraints  | Non-repeatable mutation       | INV-CTRL-004               | SPECIFIED/ENFORCED   |

## Status Definitions
- **SPECIFIED**: Invariant described at the spec level.
- **ENFORCED**: Mechanically enforced via runtime assertions.
- **TESTED**: Verified through test coverage.
- **FORMALIZED**: Modeled formally in TLA+/other tools.

---
