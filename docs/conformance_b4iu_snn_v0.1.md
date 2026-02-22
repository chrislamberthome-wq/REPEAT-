# B4IU-SNN v0.1 Conformance Checklist

## B.1 Artifact completeness

- [ ] `manifest.json` present and schema-valid
- [ ] `policy.json` present and schema-valid
- [ ] `trace.jsonl` present, non-empty, no blank lines
- [ ] `receipt.json` present and schema-valid
- [ ] `verdict.json` present, schema-valid, `verdict == "PASS"`

## B.2 Manifest integrity

- [ ] `manifest.artifacts` contains exactly the top-level files in the run directory (no more, no less, no duplicates)
- [ ] `manifest.run_id` is a non-empty string

## B.3 Trace integrity

- [ ] `seq` values are strictly `0, 1, 2, … N-1`
- [ ] `prev_hash` of event 0 equals genesis hash (`sha256:` + 64 zeros)
- [ ] Each `hash` equals `sha256(c14n(event_without_hash))`
- [ ] `prev_hash[i] == hash[i-1]` for all `i > 0`
- [ ] `step` values are non-decreasing

## B.4 Step structure

- [ ] Every `STEP_START` has a matching `STEP_END` for the same `step` value
- [ ] No unclosed steps at end of trace

## B.5 Locality policy

- [ ] Every locality event carries `hop_count`
- [ ] `hop_count <= H_max` OR `unit_id` in `hop_exceptions`
- [ ] `exception_reason == null` when `hop_count <= H_max`

## B.6 IDA consistency

- [ ] No `unit_id` appears with conflicting IDA fields across events
- [ ] `receipt.ida_root` matches recomputed value

## B.7 Receipt determinism

- [ ] `receipt.run_id` matches `manifest.run_id`
- [ ] Recomputed receipt (canonical form) equals `receipt.json` byte-for-byte

---

## Run

Emit a synthetic passing run:

```
python -m tools.b4iu_snn_emit_synthetic_run examples/b4iu_snn_v0.1_synthetic_run
```

Verify it:

```
python -m verifier.b4iu_snn_verify examples/b4iu_snn_v0.1_synthetic_run
```

Or via Make:

```
make emit-b4iu-snn-synth
make verify
```
