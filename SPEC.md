# SPEC

## Canonicalization
All hashing uses the repo-pinned canonicalization rules in `C14N_RULES.md`.

## v0.1: REPEAT + PLATOPUTER + IDA + B4IU
- Tile spec: `spec/b4iu_tile_v0.1.md`
- Link protocol: `spec/link_protocol_v0.1.md`
- Docs:
  - `docs/B4IU.md`
  - `docs/IDA.md`
  - `docs/PLATOPUTER_CODEBOOK.md`
  - `docs/REPEAT_PIPELINE.md`

## Verifier (fail-closed)
Entry: `python -m verifier.verify` (or `make verify`)

Definition of Done (v0.1):
1. Manifest enumerates required artifacts and matches filesystem set exactly.
2. Trace validates against schema and hash-chain verifies end-to-end.
3. Receipt recomputes deterministically and matches on disk.
4. All link packets in trace validate CRC16-CCITT-FALSE.
5. IDA fields exist and their hashes match declared values.