# README

## Scope

This repository is an **exploratory research tool** for simulating somatic CAG expansion dynamics and overlaying probabilistic inference layers (HMM/HHMM) to study model behavior and interpretability.

It explicitly:
- **Does not provide medical advice** or clinical decision support.
- **Is not a biological truth engine** and does not certify disease mechanisms.
- **Is not a substitute for validation** against empirical datasets.
- **Prioritizes reproducibility, transparency, and safe interpretation**.

See [SCOPE.md](SCOPE.md) for full details, including non-goals, interpretation boundaries, and guardrails for new features.

## Autotonomy (bounded autonomy)

**Autotonomy (REPEAT-bounded):** The system may select plans and execute steps without human micro-approval **only within predeclared constraints** and **only if each step produces an auditable trace and a verifier can NACK/fail-closed** (non-zero exit / invalid receipt).  
This does **not** claim self-governing goal sovereignty, moral agency, or rights—only autonomy of execution under mandatory verification.

See:
- `docs/autotonomy/AUTOTONOMY.md`
- `docs/autotonomy/IMPLEMENTATION_MAP.md`
- `docs/autotonomy/FAIL_CLOSED_AUDIT.md`
