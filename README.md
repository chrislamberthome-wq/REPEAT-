# REPEAT: Reproducible Evidence Protocol with Executable Audit Traces

## Mission

**REPEAT exists to make claims verifiable: audited protocols that produce receiver-checkable receipts (PASS/FAIL), so medicine and science can be trusted without relying on authority.**

In domains where correctness matters—clinical trials, diagnostics, research—trust should come from verifiable evidence, not institutional authority. REPEAT provides a framework for creating protocols that emit tamper-evident, reproducible audit trails and receipts that anyone can verify.

## How It Works

REPEAT follows a simple pipeline:

1. **Protocol → Run**: Execute a defined protocol (e.g., an AI classification test, a diagnostic workflow)
2. **Trace → Log**: Record all steps, inputs, outputs, and decisions in a structured JSONL trace
3. **Receipt → Compute**: Generate a deterministic receipt from the trace:
   - Canonicalize (c14n) the trace data
   - Compute cryptographic hashes
   - Add signatures or CRCs for tamper evidence
4. **Verifier → PASS/FAIL**: Independently verify the receipt by:
   - Re-computing hashes from the trace
   - Checking signatures
   - Validating against protocol requirements
   - Emitting a clear PASS or FAIL verdict with reasons
5. **Artifacts → Reproducible**: All artifacts (traces, receipts, code) are archived so anyone can reproduce and verify the results

## Quickstart

### Prerequisites

```bash
# Clone the repository
git clone https://github.com/chrislamberthome-wq/REPEAT-.git
cd REPEAT-

# Install dependencies (optional for running Python tools)
pip install -r requirements-dev.txt
```

### Run a Demo Protocol

Execute the AI Loopback Visual Binary demo protocol:

```bash
python tools/demo_protocol.py --output audit/examples/demo.trace.jsonl
```

This runs a minimal AI-based binary classification test and generates a trace file.

### Emit a Receipt

Generate a receipt from the trace:

```bash
python tools/emit_receipt.py audit/examples/demo.trace.jsonl --output audit/examples/demo.receipt.json
```

### Verify a Receipt

Verify the receipt to ensure integrity:

```bash
python tools/verify_receipt.py audit/examples/demo.receipt.json
```

Expected output:
```
VERDICT: PASS
All integrity checks passed.
```

### Inspect Audit Log

Traces are stored as JSONL (JSON Lines). View them with:

```bash
cat audit/examples/demo.trace.jsonl | jq
```

## Project Structure

```
REPEAT-/
├── docs/                      # Core documentation
│   └── REPEAT_MISSION.md      # Mission, threat model, lifecycle
├── tools/                     # Core REPEAT tools
│   ├── demo_protocol.py       # Example protocol implementation
│   ├── emit_receipt.py        # Receipt generation tool
│   └── verify_receipt.py      # Receipt verification tool
├── audit/                     # Audit trails and examples
│   └── examples/              # Example traces and receipts
├── schemas/                   # Receipt and trace schemas
└── README.md                  # This file
```

## Core Concepts

- **Protocol**: A defined procedure with explicit steps and acceptance criteria
- **Trace**: A chronological log of protocol execution (JSONL format)
- **Receipt**: A tamper-evident summary with hashes and verdict
- **Verifier**: Independent tool that validates receipts (PASS/FAIL)
- **Audit Log**: Permanent, reproducible record of all executions

For detailed documentation, see [docs/REPEAT_MISSION.md](docs/REPEAT_MISSION.md).

## Development

Run tests:
```bash
pytest tests/
```

Lint code:
```bash
ruff check .
```

## License

See [LICENSE](LICENSE) for details.