# QUANTUM LINEAGE SUBSTRATE

...existing content...

## 11. Implementation Index (Reference Modules)

This section maps specification components to the corresponding reference implementation modules in the repository. These mappings are informational and do not supersede the normative rules defined in this document.

### Canonical QUBO

Specification sections
- Section 2.1 — Canonical QUBO
- Section 3 — Canonicalization Rules

Reference module

`repeat_quantum/canonicalize_qubo.py`

Responsibilities
- index normalization
- diagonal folding
- duplicate merging
- zero pruning
- deterministic serialization
- `problem_digest` generation

### Deterministic QUBO → Ising Mapping

Specification sections
- Section 2.2 — Deterministic Ising Mapping
- Section 4 — Mapping Rules

Reference module

`repeat_quantum/qubo_to_ising.py`

Responsibilities
- QUBO → Ising coefficient transformation
- constant offset computation
- deterministic coefficient ordering
- `mapping_digest` generation

### Generator Specification

Specification sections
- Section 2.3 — Generator Specification
- Section 5 — Generator Rules

Reference module

`repeat_quantum/generator_spec.py`

Responsibilities
- validation of generator parameters
- enforcement of QAOA conventions
- deterministic canonical serialization
- `generator_digest` generation

### Trace Logger

Specification sections
- Section 2.4 — Trace
- Section 6 — Trace Format and Chain-Hash Rules

Reference module

`repeat_quantum/log_trace.py`

Responsibilities
- trace entry construction
- deterministic timestamp integration
- incremental chain hashing
- trace file emission

### Verifier

Specification sections
- Section 7 — Verifier Semantics

Reference module

`repeat_quantum/verifier.py`

Responsibilities
- schema validation
- lineage homogeneity checks
- bitstring validation
- energy validation
- chain hash verification
- PASS / FAIL receipt generation

### Receipt Construction

Specification sections
- Section 2.5 — Receipt
- Section 7 — Verifier Semantics

Reference module

`repeat_quantum/receipt.py`

Responsibilities
- PASS receipt creation
- FAIL receipt creation
- deterministic receipt serialization
- `receipt_digest` generation

### Golden Vectors and Test Corpus

Specification sections
- Section 8 — Golden Vectors

Test directories

`tests/vectors/trace_valid.jsonl`  
`tests/vectors/trace_empty.jsonl`  
`tests/vectors/trace_mixed_problem.jsonl`  
`tests/vectors/trace_invalid_bitstring.jsonl`  
`tests/vectors/trace_bad_chain_hash.jsonl`

Purpose
- deterministic PASS verification
- deterministic FAIL verification
- regression protection for verifier behavior

### CLI Utilities (Optional)

If the reference CLI is implemented, commands map as follows:

`repeat-quantum canonicalize problem.json`  
`repeat-quantum map problem.json`  
`repeat-quantum generate mapping.json`  
`repeat-quantum log shots.json`  
`repeat-quantum verify trace.jsonl`

Reference module

`repeat_quantum/cli.py`

### Implementation Independence

Implementations in other languages must conform to the rules defined in this specification rather than the reference modules listed above.

Conformance is demonstrated if an independent implementation can:
- reproduce canonical artifacts
- regenerate identical digests
- verify trace integrity
- emit byte-identical PASS or FAIL receipts.