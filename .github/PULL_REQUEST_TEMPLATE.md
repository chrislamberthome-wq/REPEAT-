# Pull Request: Convergence + Platoputer v0.1 (Thin Slice)

## Summary
Describe what this PR does in 1–3 sentences.

## Scope
Select one:
- [ ] Phase 0: Convergence Gate (CI + CRC freeze → stabilize `main`)
- [ ] Phase 1: Platoputer v0.1 Thin Slice (module + SPEC + vectors + verifier + tests)
- [ ] Both (only if Phase 0 gates are satisfied first)

## Changes
- [ ] CI workflows / guardrails
- [ ] CRC-16/CCITT-FALSE implementation
- [ ] CRC golden vectors + tests
- [ ] Platoputer module scaffold (`platoputer/`)
- [ ] Platoputer `SPEC.md`
- [ ] Platoputer golden vectors
- [ ] Platoputer verifier
- [ ] Platoputer tests wired into CI
- [ ] README narrative split (REPEAT vs Platoputer)

---

# Phase 0 — Convergence Gate Checklist (Precondition)

## 0. Merge set locked
- [ ] Minimum merge set identified (CI + CRC only)
- [ ] Non-essential PRs excluded from this merge set
- [ ] Merge order planned (see below)

## 1. CI integrity gate (per PR in merge set)
For each PR included:
- [ ] All required checks are **GREEN**
- [ ] No failing required checks
- [ ] Re-run is deterministic (no flake observed / rerun matches)

## 2. CRC vector freeze gate
- [ ] CRC vector files present and versioned
- [ ] CRC parameters explicit (poly/init/xorout/refin/refout)
- [ ] Encoding rules explicit where applicable (UTF-8, no BOM)
- [ ] Tests assert fixed inputs → fixed outputs
- [ ] Freeze boundary recorded (“vectors frozen as of <SHA>”)

## 3. Merge order (recommended)
- [ ] 1) CI workflows / guardrails
- [ ] 2) Core CRC implementation
- [ ] 3) CRC vectors + tests
- [ ] 4) Minimal glue only (strictly bounded)

**Stop condition**
- [ ] If “minimal glue” expands beyond test enablement, STOP and re-scope.

## 4. Post-merge validation (on `main`)
- [ ] Fresh clone → full test suite PASS
- [ ] Targeted CRC tests PASS
- [ ] CI on `main` is GREEN

## 5. Optional baseline tag
- [ ] Tag created: `repeat-infra-v1`
- [ ] Tag note includes: CI baseline + CRC vectors frozen + deterministic PASS/FAIL

### Phase 0 Definition of Done (DOD)
- CI on `main` is GREEN
- CRC vectors are frozen and enforced by tests
- Fresh clone verification succeeds end-to-end

---

# Phase 1 — Platoputer v0.1 Thin Slice

## Commit plan (atomic sequence)
- [ ] Commit 1: `Add platoputer module scaffold (dirs + orientation README)`
- [ ] Commit 2: `Add platoputer SPEC v0.1 (Mode 2 five-solids frame)`
- [ ] Commit 3: `Add platoputer golden vectors for Mode 2 decode rules`
- [ ] Commit 4: `Add platoputer verifier for golden vectors (PASS/FAIL, deterministic)`
- [ ] Commit 5: `Add CI tests enforcing platoputer vectors (no silent wrong)`
- [ ] Commit 6: `Document Platoputer as geometric codebook layer alongside REPEAT substrate`

## Content checks
- [ ] `platoputer/SPEC.md` is authoritative for v0.1 semantics
- [ ] Vectors are stored under `platoputer/vectors/`
- [ ] Verifier produces deterministic PASS/FAIL + explicit FAIL reasons
- [ ] Tests enforce vectors exactly (no silent wrong)

## Immutability rule (release discipline)
- [ ] Vectors are treated as immutable after tag
- [ ] Any changes require new vector file/version (no edits-in-place)

## Optional guardrail (only if needed)
- [ ] Commit: `Add immutability guard for platoputer vectors (versioned-only changes)`

## Release/tag
- [ ] Tag created: `platoputer-v0.1`
- [ ] Tag note: Mode 2 + decode rules + golden vectors + verifier

### Phase 1 Definition of Done (DOD)
- Fresh clone → run tests → PASS
- Running verifier on golden vectors yields deterministic PASS/FAIL
- Platoputer exists as a declared deliverable (`platoputer/` + SPEC + vectors + verifier + tests)
- README links to `platoputer/SPEC.md`

---

## Test Evidence
Paste command(s) run and output snippets:
- [ ] `...`
- [ ] `...`

## Risk / Rollback
- Rollback plan:
  - [ ] Remove `platoputer/` changes (Phase 1)
  - [ ] Revert merge commits (Phase 0) if CI regression detected
- Blast radius assessment:
  - [ ] Confined to new module + tests (Phase 1) / CI+CRC baseline (Phase 0)

## Notes
Anything reviewers should be aware of:
- [ ] None