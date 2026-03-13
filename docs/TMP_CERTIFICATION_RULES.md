# TMP Certification Rules

## Certification Gate
TMP v1 is certified only if the following conditions hold simultaneously:
- Canonicalization equivalence test passes
- Golden vector digest is stable
- Replay verification passes
- Tamper detection produces `FAIL`
- Malformed input produces `ERROR`
- CI matrix produces identical canonical hash and byte length
- Version-binding across code/docs/metadata is consistent

## Frozen Protocol Rule
After certification:
- **Verifier semantics MUST NOT change**
- **Canonicalization rules MUST NOT change**
- **Golden vector artifacts MUST NOT change**

Only determinism defects may justify modification.

## Allowed Post-Certification Work
- PlatoBench benchmark corpus
- Benchmark vector metadata
- Analysis tools that do not affect verifier semantics

## Prohibited Changes
- Modifying canonicalization logic
- Altering invariant rules
- Regenerating golden vector artifacts
- Changing receipt schema fields

## Transition Marker
When the following marker appears in the repository, the protocol layer is considered stable:

```
TMP_VERSION: tmp_v1
TMP_STATUS: CERTIFIED
```

Post-certification development should focus on benchmark construction with the following geometric benchmarks:
- Tetrahedron
- Cube
- Octahedron
