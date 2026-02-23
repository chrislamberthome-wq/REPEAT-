# README

## Scope

This repository is an **exploratory research tool** for simulating somatic CAG expansion dynamics and overlaying probabilistic inference layers (HMM/HHMM) to study model behavior and interpretability.

It explicitly:
- **Does not provide medical advice** or clinical decision support.
- **Is not a biological truth engine** and does not certify disease mechanisms.
- **Is not a substitute for validation** against empirical datasets.
- **Prioritizes reproducibility, transparency, and safe interpretation**.

See [SCOPE.md](SCOPE.md) for full details, including non-goals, interpretation boundaries, and guardrails for new features.

---

## GAD_FLY — B4IU v0.1 Verifier

`verifier/gad_fly.py` implements the **GAD_FLY** receiver-verifiable transition
under the *Bounded Forensic-Interaction Unit* (B4IU) v0.1 framework.

### Channel

A visual-binary microtask channel where a 1-bit stimulus is displayed (Tx) and
the user returns a 1-bit response (Rx).

### Verifier logic

| Symbol | Meaning |
|--------|---------|
| `tx_bit` | Transmitted bit (0 or 1) |
| `rx_bit` | Received bit (0 or 1) |
| `rt_ms` | Response time in milliseconds |
| `t_max_ms` | Maximum allowable response time |
| `panic` | Manual intervention flag (1 = disqualified) |
| `delta` | 1 if `rx_bit == tx_bit`, else 0 |
| `P` | 1 if any disqualifying condition is met, else 0 |
| `C` | `delta - P` |
| `verdict` | `"PASS"` if `C == 1`, else `"FAIL"` |

**Disqualifying conditions** (`P = 1`):
1. `rt_ms > t_max_ms` — response deadline exceeded.
2. `invalid_response = True` — missing, multi-input, or tampered response.
3. `panic = 1` — manual intervention flag raised.

### Usage

```python
from verifier.gad_fly import verify_trial

result = verify_trial(
    tx_bit=1, rx_bit=1, rt_ms=412, t_max_ms=1500, panic=0
)
# result["verdict"] == "PASS"
```

The function returns a dict matching the B4IU v0.1 JSON schema
(`b4iu_id`, `tx_bit`, `rx_bit`, `rt_ms`, `t_max_ms`, `panic`,
`delta`, `P`, `C`, `verdict`).  A `verify_trial_json` convenience
wrapper returns the same data as a JSON string.
