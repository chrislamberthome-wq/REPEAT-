# IDA CONTROL LOOP Specification

## Overview
The IDA (Instigate / Diagnose / Adjust) control loop is embedded in the operational controller of the fail-closed stack:

- **IDA**: The active control loop probing, detecting deviation, and applying corrections.
- **REPEAT**: Certifies the verifiability of operations and ensures they count as existence in the system.
- **B4IU**: Establishes the contract fields, rigor, and fail-closed behavior so that the loop cannot silently drift.
- **Platoputer**: Acts as the substrate, translating binary requests into geometric states and back into certified binary states.

In this schema:
- IDA is the operational hand on the controls.
- REPEAT acts as the judge of correctness.
- B4IU is the law enforcing invariants.
- Platoputer operates the machine subtending IDA’s control.

## IDA Role in the Stack

1. **Instigate**: Perturb the system or initiate an operational action to probe behavior.
2. **Diagnose**: Observe the resulting system state, infer deviation, and extract failure surfaces.
3. **Adjust**: Apply corrections via precise control feedback to restore the system toward invariants.

### Practical Operation of the Fail-Closed Stack:

- **IDA**: Asks what should be perturbed, observed, or corrected.
- **REPEAT**: Asks whether that result passes verification/auditability testing.
- **B4IU**: Ensures IDA actions are couched in rigor, contract rules, and fail-safe behavior.
- **Platoputer**: Seals the operational substrate state for binary interpretation into geometric flows and vice-versa.

### IDA States, Transitions, and Invariants

| State      | Transition Event       | Description                                 |
|------------|------------------------|---------------------------------------------|
| Init       | Observe Input          | Begins with a perturbation or system-probing action. |
| Diagnose   | Infer Deviations       | Observes resulting state and diagnostics from B4IU layer. |
| Adjust     | Issue Control Feedback | Applies corrective adjustments constrained by B4IU contract. |
| Verify     | Pass REPEAT Certification | Finalizes operations with REPEAT-certified entities. |

### Critical Invariants:

- **Invariant IDA-01**: IDA always runs downstream of B4IU. No direct external state is altered without binding to B4IU contracts and enabled transitions.
- **Invariant IDA-02**: Adjustments must include metadata traceable to diagnostics and perturbed inputs.
- **Invariant IDA-03**: Control traceability ensures every output perturbation's cause is captureable in logs.
- **Invariant IDA-04**: Diagnostics cannot reinterpret REPEAT outputs. The pass/fail communication boundary upholds separable judgment rules.

## Example Trace Schema (JSONL)
- IDA traces the progress of its control actions in JSONL format for investigable backward audits.

```json
{
  "event": "instigate",
  "action": "probe",
  "metadata": {
    "trigger_sha": "32f9c248...",
    "b4iu_contract": "v1.2.3"
  }
}
{
  "event": "diagnose",
  "detections": [
    { "deviation": "latency-drift", "impact": 2.4, "example_field": "x" }
  ]
}
{
  "event": "adjust",
  "corrective_feedback": { "target_field": "valueToOffset", "delta": -0.42 },
  "linked_to": "diagnostics-event-abc123"
}
```

## Closing
IDA serves as the operational feedback loop ensuring the entire fail-closed stack operates as a mechanistic, auditable system. With explicit definitions, transitions, and invariants, its function ensures control rigor blends seamlessly with certification envelopes (REPEAT), operational substrates (Platoputer), and strict legal restraints (B4IU).