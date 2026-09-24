# REPEAT

REPEAT is an experimental, verifier-bounded execution and data-encoding project.

The repository combines:

- a normative REPEAT/B4IU/IDA specification;
- deterministic data encoding and verification tools;
- geometric binary codecs;
- audit-oriented simulation and verification workflows;
- supporting schemas, governance documents, and test fixtures.

This project does not claim self-governing agency, moral agency, rights, or
unrestricted autonomy. Its autonomy model is limited to executing predeclared
plans under mandatory verification and auditable traces.

## Current status

**Not independently verified.** The repository contains two conflicting internal
claims about system state:

- `DEPLOYMENT_BLOCKER.md` asserts `SYSTEM: PASS` and describes the system as
  "VERIFIED," "operational," and "deterministic."
- `audits/2026-09-20_repeat-core-boundary-audit.md` concludes `FAIL-CLOSED`,
  finding that the frozen `REPEAT_CORE_v1` schema/verifier authority cannot
  currently be certified from available evidence.

Per this repository's own verification standard, an unreproduced self-assertion
does not override a documented audit finding. Until the two are reconciled with
independent evidence, **the boundary audit's `FAIL-CLOSED` conclusion is treated
as current status**, and the `PASS`/`VERIFIED` language in `DEPLOYMENT_BLOCKER.md`
should be read as a self-assertion pending confirmation, not a settled result.

Deployment is separately blocked per `DEPLOYMENT_BLOCKER.md`, which also documents
a deploy command (`uvicorn server.main:app ...`) referencing a `server.main`
module that does not exist anywhere in this repository. No FastAPI or Starlette
application was found in the codebase. This instruction is stale or orphaned
documentation, not a runnable deployment step, and should not be treated as
corrected merely by fixing its typographic hyphens.

`status-log.txt` is a legacy note ("Day 1 reset. Still here. System not
finished.") and is not authoritative. See `audits/`, `ledger/`, and
`docs/autotonomy/` for current state and known limitations.

### Known limitations

- Verification authority is contested: see the `PASS`/`FAIL-CLOSED` conflict
  above.
- The repository does not unambiguously identify a frozen `REPEAT_CORE_v1`
  schema/verifier authority.
- Multiple receipt/schema surfaces coexist without a documented resolution
  order.
- `node_zero_v1/verify.py` is currently a stub (`def verify(): pass`).
- Cross-receipt hash-chain validation is documented as absent.
- `DEPLOYMENT_BLOCKER.md` documents a deploy command referencing a `server.main`
  module that is not present in the repository; no ASGI application implementation
  exists yet.
- More broadly: several documents in this repository describe capabilities or
  components (a verified system, a deployable server) that the current codebase
  does not yet implement. Treat status claims as unverified until checked against
  actual source.

## REPEAT-HD

`repeat_hd` is the current Python implementation package.

It provides:

- CRC32-protected data framing;
- length validation;
- UTF-8 decoding;
- strict invariant checks;
- 2D binary geometric encoding;
- 3D seashell encoding;
- 3D five-solids encoding;
- majority-vote and cosine-sum decoding rules.

### Install

Create an environment and install the project dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For development tools:

```bash
python -m pip install -e '.[dev]'
```

### Command-line usage

Encode a string:

```bash
python -m repeat_hd encode "hello" > encoded.bin
```

Verify the encoded data:

```bash
python -m repeat_hd verify --infile encoded.bin
```

Run strict verification:

```bash
python -m repeat_hd verify --strict --infile encoded.bin
```

The verifier returns a non-zero exit status when parsing, length, CRC, UTF-8, or
strict invariant checks fail.

### Python usage

```python
from repeat_hd import (
    encode_2d,
    decode_2d,
    encode_3d_seashell,
    decode_3d_seashell,
    encode_3d_solids,
    decode_3d_solids_rule_a,
    decode_3d_solids_rule_b,
)

point = encode_2d(1)
assert decode_2d(point) == 1

seashell_point = encode_3d_seashell(0)
assert decode_3d_seashell(seashell_point) == 0

angles = encode_3d_solids(1)
assert decode_3d_solids_rule_a(angles) == 1
assert decode_3d_solids_rule_b(angles) == 1
```

The codec formulas and decoding rules are documented in [`formulas.md`](formulas.md).

## Verification and diagnostics

Run the test suite:

```bash
make test
```

Run the strict diagnostic workflow:

```bash
make diag-strict
```

Run the preservation checks:

```bash
make preservation-test
```

## Repository layout

| Path | Purpose |
|---|---|
| `repeat_hd/` | REPEAT-HD Python package and CLI |
| `verifier/` | Verification entry points and receipt validation (CLI, not a server) |
| `scripts/` | Repository validation and maintenance scripts |
| `tests/` | Automated tests |
| `schema/`, `schemas/` | Data and audit schemas |
| `SPEC.md` | Normative REPEAT/B4IU/IDA overview |
| `formulas.md` | Geometric codec formulas |
| `docs/`, `spec/` | Supporting technical specifications |
| `docs/autotonomy/` | Autonomy-model documentation, including the fail-closed boundary audit |
| `governance/`, `repeat-governance/` | Governance and policy artifacts |
| `audits/`, `ledger/` | Audit and trace-related artifacts |
| `simulations/` | Simulation resources |
| `archive/` | Historical material |

Experimental prototypes not part of the core REPEAT-HD package (`ai_loopback_visual_binary/`,
`node_zero_v1/`, `species_id/`, `prototype/`) are kept separate from production-facing
code and should not be assumed functional. `repeat_devops_gift_processing/` is
unrelated to the codec and is a candidate for removal from this repository.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Changes to normative specifications,
schemas, verifier behavior, and audit formats should include corresponding tests
or validation evidence.

## License

See [`LICENSE`](LICENSE).
