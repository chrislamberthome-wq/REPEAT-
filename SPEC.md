## Registry rule: B4IU locked (N_locked)

**Definition:** `N_locked` is the total number of occurrences of the literal token `B4IU_LOCKED` across the repository (text files only), excluding common build/vendor/binary paths.

**Verifier:** `tools/ci/count_b4iu_locked.mjs`

**Pass/Fail:**
- FAIL if `N_locked = 0`.
- If `EXPECT` is provided, FAIL unless `N_locked = EXPECT`.

**CI entrypoint:** `make ci-count-b4iu`