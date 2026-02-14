# REPEAT Mission and Design

## Mission Statement

**REPEAT exists to make claims verifiable: audited protocols that produce receiver-checkable receipts (PASS/FAIL), so medicine and science can be trusted without relying on authority.**

Trust in critical domains—medicine, diagnostics, research—should not depend on institutional authority or "expert opinions." Instead, trust should be built on **verifiable evidence** that anyone can check. REPEAT provides the infrastructure to make scientific and medical protocols transparent, reproducible, and independently verifiable.

## Core Definitions

### Protocol
A **protocol** is a defined procedure with:
- Explicit inputs and expected outputs
- Step-by-step instructions
- Acceptance criteria (what makes a run valid)
- Version information

Examples: AI-based classification test, diagnostic workflow, clinical trial procedure.

### Trace
A **trace** is a chronological log of protocol execution:
- Format: JSONL (JSON Lines) for streaming and line-by-line processing
- Records: Every step, input, output, decision, timestamp
- Immutability: Once written, never modified
- Purpose: Provides complete audit trail for reproduction and verification

### Receipt
A **receipt** is a tamper-evident summary of a protocol run:
- Contains cryptographic hashes of inputs, outputs, and trace
- Includes metadata: protocol ID, run ID, timestamp, verifier version
- Verdict: Explicit PASS or FAIL with reasons
- Deterministic: Same trace always produces same receipt

### Verifier
A **verifier** is an independent tool that:
- Re-computes hashes from traces
- Validates receipt signatures/CRCs
- Checks protocol requirements
- Emits clear PASS or FAIL verdict with reasons
- Must be deterministic and reproducible

### Audit Log
An **audit log** is the permanent record:
- Traces from all protocol runs
- Receipts with verification results
- Code/protocol versions used
- Stored in immutable archive (e.g., git, content-addressed storage)

## Threat Model

REPEAT is designed to detect and prevent:

### 1. Silent Wrong
**Threat**: Errors or manipulations that go undetected.

**Mitigation**:
- Explicit PASS/FAIL verdicts (no ambiguity)
- Verification requires independent re-computation
- All steps logged in trace

### 2. Tamper Evidence
**Threat**: Someone modifies results, traces, or receipts after the fact.

**Mitigation**:
- Cryptographic hashes (SHA-256) on all artifacts
- Receipts signed or CRC-checked
- Any modification invalidates the receipt
- Verification will fail with "hash mismatch"

### 3. Reproducibility
**Threat**: Results cannot be independently reproduced or checked.

**Mitigation**:
- Deterministic canonicalization (c14n rules)
- Explicit version pinning (protocol, tools, dependencies)
- Complete trace captures all state needed for reproduction
- Independent verifiers can run on any machine

### 4. Authority Bypass
**Threat**: Trust placed in institutions rather than evidence.

**Mitigation**:
- Anyone can run the verifier
- Verification does not require credentials or authority
- Open-source tools and schemas
- Receipts are "receiver-checkable" without contacting issuer

## Lifecycle

REPEAT follows a five-phase lifecycle:

### 1. Design
- Define the protocol (inputs, steps, outputs, acceptance criteria)
- Create schema for trace and receipt
- Write verifier rules

### 2. Run
- Execute the protocol
- Emit structured trace (JSONL)
- Capture all relevant state

### 3. Emit Receipt
- Canonicalize trace data (c14n)
- Compute hashes (inputs, outputs, trace)
- Generate receipt with metadata
- Sign or add CRC

### 4. Verify
- Independent verifier loads receipt and trace
- Re-computes hashes
- Checks signatures
- Validates protocol requirements
- Emits PASS or FAIL

### 5. Archive
- Store trace, receipt, and code
- Use immutable storage (git, IPFS, content-addressed)
- Ensure long-term reproducibility

## Folder Map

```
REPEAT-/
├── audit/                           # Audit trails
│   └── examples/                    # Example traces and receipts
│       ├── demo.trace.jsonl         # Example trace
│       └── demo.receipt.json        # Example receipt
├── docs/                            # Documentation
│   ├── REPEAT_MISSION.md            # This file
│   └── probes/                      # Additional documentation
├── schemas/                         # JSON schemas
│   └── receipt_schema_v1.json       # Receipt schema v1
├── tools/                           # Core REPEAT tools
│   ├── demo_protocol.py             # Example AI loopback protocol
│   ├── emit_receipt.py              # Receipt generation tool
│   └── verify_receipt.py            # Receipt verification tool
├── ai_loopback_visual_binary/       # AI loopback example
│   ├── audit/                       # Audit logs for this protocol
│   └── tools/                       # Protocol-specific tools
├── repeat_hd/                       # Huntington's Disease protocol
├── repeat_devops_gift_processing/   # DevOps gift processing
└── tests/                           # Unit and integration tests
```

## Invariants

REPEAT maintains these invariants:

### 1. Deterministic Canonicalization
- Same input data always produces same canonical form
- Follows c14n rules (see C14N_RULES.md)
- Required for hash stability

### 2. Stable IDs
- Protocol IDs are unique and versioned
- Run IDs are unique within a protocol
- Receipt IDs are globally unique

### 3. Explicit PASS/FAIL Gates
- Every verification produces PASS or FAIL (never "maybe")
- Failure reasons must be explicit and actionable
- No silent failures

### 4. Hash Integrity
- All hashes use SHA-256 (or stronger)
- Receipts include hashes of: inputs, outputs, trace
- Any mismatch fails verification

### 5. Reproducibility
- All dependencies and versions recorded
- Complete state captured in trace
- Verification can run offline

### 6. Tamper Evidence
- Modifications break hashes
- Receipts cannot be forged without detection
- Verification will fail if any data changed

## Receipt Schema v1

The standard receipt format includes:

```json
{
  "protocol_id": "unique-protocol-identifier",
  "run_id": "unique-run-identifier",
  "inputs_hash": "sha256-of-inputs",
  "outputs_hash": "sha256-of-outputs",
  "trace_hash": "sha256-of-trace-file",
  "timestamp": "ISO8601-timestamp",
  "verdict": "PASS|FAIL",
  "verifier_version": "version-string"
}
```

Additional optional fields:
- `metadata`: Protocol-specific metadata
- `signature`: Cryptographic signature
- `crc`: Checksum for quick integrity check

## Examples

See `audit/examples/` for:
- `demo.trace.jsonl`: Example trace from AI loopback protocol
- `demo.receipt.json`: Corresponding receipt

Run the quickstart commands in the main README to generate and verify your own receipts.

## Philosophy

REPEAT is built on three principles:

1. **Trust through Verification**: Don't trust, verify. Every claim must be checkable.
2. **No Silent Wrong**: Failures must be loud, explicit, and actionable.
3. **Reproducibility First**: If it can't be reproduced, it can't be trusted.

These principles guide every design decision in REPEAT.
