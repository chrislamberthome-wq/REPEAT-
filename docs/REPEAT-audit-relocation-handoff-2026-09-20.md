# Handoff: REPEAT- audit relocation cleanup

**Repository:** `chrislamberthome-wq/REPEAT-`
**Date:** 2026-09-20
**Prepared for:** whoever has delete/revert-capable git access — this handoff was prepared using tools limited to file create/update only.

## Background

The 2026-09-20 repository boundary audit was originally committed to
`main` at `docs/repository-boundary-audit-2026-09-20.md` (commit
`b2c4617`, blob `4c2bc56caa4312a6367c014f66e1b75bc2711789`). It was
later decided to relocate the audit to `audits/` for separation from
the normative/external documents it evaluates. That relocation
encountered several tooling-limited errors along the way (wording drift
on one attempt, a stray direct commit to `main`, missing delete capability). This
 document is the consolidated, corrected state of that effort.

## Current state

| Ref | Path | Blob SHA | Status |
|---|---|---|---|
| `main` | `docs/repository-boundary-audit-2026-09-20.md` | `4c2bc56c...` | Correct content, wrong path — leave as-is until step 2 below |
| `main` | `audits/2026-09-20_repeat-core-boundary-audit.md` | `4e0756bf...` | Correct content, but landed on `main` by accident (commit `a3641ae`) — remove |
| `docs/relocate-boundary-audit-2026-09-20` | `docs/repository-boundary-audit-2026-09-20.md` | `4c2bc56c...` | Stale duplicate — remove |
| `docs/relocate-boundary-audit-2026-09-20` | `audits/2026-09-20_repeat-core-boundary-audit.md` | `b0ec614c...` | Reworded/incorrect — overwrite |

## Commands

```bash
# 1. Revert the accidental direct commit on main
git checkout main
git revert a3641aeff4f648e5640e449a7f97db6690ebc1d4
git push origin main

# 2. Fix the feature branch
git checkout docs/relocate-boundary-audit-2026-09-20
git pull origin docs/relocate-boundary-audit-2026-09-20
git show b2c461795f1a4c6bc52f4a6e1f8bc855aab2470b:docs/repository-boundary-audit-2026-09-20.md > audits/2026-09-20_repeat-core-boundary-audit.md
git add audits/2026-09-20_repeat-core-boundary-audit.md
git rm docs/repository-boundary-audit-2026-09-20.md
git commit -m "Correct relocation: restore byte-identical content, remove docs/ duplicate

Restores audits/2026-09-20_repeat-core-boundary-audit.md to be
byte-identical to blob 4c2bc56c (the audit as committed to main
in b2c4617), replacing a prior reworded version. Removes the
stale docs/repository-boundary-audit-2026-09-20.md duplicate.

No audit findings or the modification decision are changed —
only the relocation is now clean."
git push origin docs/relocate-boundary-audit-2026-09-20

# 3. Verify before opening PR
git show docs/relocate-boundary-audit-2026-09-20:audits/2026-09-20_repeat-core-boundary-audit.md | git hash-object --stdin
# should output 4c2bc56caa4312a6367c014f66e1b75bc2711789
git ls-tree docs/relocate-boundary-audit-2026-09-20 -- docs/repository-boundary-audit-2026-09-20.md
# should return nothing
```

## PR description

Open from `docs/relocate-boundary-audit-2026-09-20` into `main`, after step 3 above verifies clean:

```markdown
## Summary

Relocates the 2026-09-20 repository boundary audit from `docs/` to
`audits/`. Supersedes an accidental direct commit to `main`
(a3641ae, reverted) and corrects an earlier in-branch commit
(440c632) that introduced unintended wording drift.

## Final state

- `audits/2026-09-20_repeat-core-boundary-audit.md` — byte-identical
  to the audit as committed to `main` at b2c4617 (blob `4c2bc56c`)
- `docs/repository-boundary-audit-2026-09-20.md` — removed

## Why

The audit evaluates separation between normative REPEAT artifacts
and external/commercial documents. Filing the audit itself under
`docs/` placed it alongside material it audits; `audits/` restores
that separation.

## Verification

`git hash-object` on the `audits/` file content should return
`4c2bc56caa4312a6367c014f66e1b75bc2711789`.
```

## Note on this handoff file itself

This file can be deleted once the cleanup above is complete and merged — it documents a transient tooling situation, not a permanent process.
