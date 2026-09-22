# Evidence Node V0.1

> **Status:** Non-normative product evidence artifact.
>
> **Scope boundary:** This document describes a physical evidence-node prototype and its potential product use. It is intentionally outside `REPEAT_CORE`. It does not amend, interpret, override, or create requirements for any REPEAT_CORE specification, schema, authority decision, or implementation.
>
> **REPEAT_CORE_CHANGE: NO**
>
> The prototype may produce records, receipts, and demonstrations for evaluation. Any future integration with REPEAT_CORE would require a separately authorized decision and explicit change process. This document alone grants no authority to do so.

## 1. Claim-status vocabulary

The following labels are used throughout this document:

- **Prototype claim:** A proposed design characteristic or target that has not necessarily been built or measured.
- **Demonstrated behavior:** Behavior observed in a particular prototype build or controlled demonstration. It is not a guarantee of production performance.
- **Unresolved hypothesis:** A market, operational, technical, safety, or economic proposition requiring evidence.

Unless explicitly labeled otherwise, statements below are design targets or hypotheses, not commitments or conformance claims.

## 2. Physical product purpose and boundary

The Evidence Node is a small, physically sealed or tamper-evident device intended to collect selected observations from a bounded physical process and produce a time-ordered, reviewable evidence record. The initial purpose is to make a simple event, measurement, or operator action easier to inspect later without relying solely on a retrospective narrative.

The V0.1 boundary is deliberately narrow:

- **Inside the boundary:** device identity, configured sensors and inputs, local timestamping, event capture, integrity metadata, local storage, export, and a human-readable receipt/replay view.
- **Outside the boundary:** deciding organizational policy, certifying compliance, proving intent, determining legal truth, replacing an authoritative business system, making safety-critical control decisions, or changing REPEAT_CORE behavior.
- The node is observational in V0.1. It must not actuate machinery or silently alter a controlled process.
- A record can show what this device observed and when according to its clock; it cannot by itself prove that an observation is complete, truthful, or representative of everything that happened.

## 3. Target users and initial markets

### Target users

- A technician or operator who installs, starts, pauses, or services the node.
- A supervisor, quality lead, or process owner who reviews a receipt.
- A buyer or evaluator who needs a short, repeatable demonstration rather than a platform deployment.
- A developer or test engineer who exports records and replays them independently.

### Initial market hypotheses

1. Small manufacturers and specialty fabricators may pay for a low-friction way to document repeatable process steps, inspection observations, or equipment state.
2. Field-service organizations may value an offline-first evidence trail for visits, handoffs, and verification steps.
3. Larger enterprises may use a bounded pilot in quality, maintenance, logistics, or supplier-assurance workflows where existing systems are expensive to adapt.
4. Initial sales should target a single workflow with a measurable review or dispute-reduction benefit, not a general-purpose “trust layer.”

These are unresolved hypotheses until supported by buyer interviews, paid pilots, retention, and measured workflow outcomes.

## 4. V0.1 functional requirements

The prototype should:

1. Have a stable device identifier and a visible or electronically retrievable configuration identity.
2. Accept at least one sensor input and one explicit operator input.
3. Record input observations with a local timestamp, sequence number, input identifier, value/status, and quality/error indicator.
4. Persist records across ordinary power interruption, subject to stated storage limits.
5. Detect and visibly report invalid configuration, missing required input, clock uncertainty, storage exhaustion, and integrity failures.
6. Provide an export that can be copied without requiring a live network connection.
7. Provide a receipt/replay interface that makes the record sequence, gaps, failures, and configuration apparent.
8. Make no silent edits to committed records; corrections or annotations must be separate and attributable.
9. Support a repeatable demonstration procedure and a reset/reprovisioning procedure for evaluation units.
10. Fail closed for evidence claims when required conditions are not met: mark the affected interval invalid or indeterminate rather than presenting it as verified.

Non-requirements for V0.1 include cloud dependence, production security certification, legal or regulatory certification, high-rate industrial control, autonomous actuation, and integration into REPEAT_CORE.

## 5. Hardware architecture

**Prototype claim:** A practical V0.1 can use a single-board computer or microcontroller-class compute module, a real-time clock, removable or soldered flash storage, a small power subsystem, a sensor interface board, status indicators, and a protective enclosure.

A representative block architecture is:

```text
[Sensor/input interfaces] -> [Acquisition/validation] -> [Local event store]
                                      |                         |
[Operator controls/status] ----------+                         v
                               [Clock + identity] -> [Receipt/export]
                                      ^                         |
                               [Power/watchdog] <---------------+
```

The enclosure should expose only the required connectors, status indicators, and operator control. A tamper-evident label or fastener is useful for demonstrations, but it is not a claim of tamper proofing. A watchdog and brownout-aware shutdown path are preferred; neither makes data loss impossible.

## 6. Sensor and input interfaces

Candidate V0.1 interfaces are:

- Digital GPIO for a switch, contact, beam-break, or machine-state signal.
- I2C or SPI for a temperature, pressure, vibration, or other low-rate sensor.
- USB or serial for a deliberately selected external instrument.
- A physical start/mark/acknowledge button for operator events.
- Optional status input such as a door or enclosure switch, clearly labeled as an observation rather than a security guarantee.

Every input should have a declared unit, expected range, sampling or event policy, debounce/filter policy, calibration metadata where relevant, and error behavior. Unsupported, out-of-range, disconnected, or stale input must be represented as a fault or indeterminate observation—not coerced into a normal value. Sensor calibration traceability is an unresolved V0.1 hypothesis unless independently demonstrated.

## 7. Compute, storage, clock, and identity

- **Compute:** A low-power MCU is preferred for deterministic acquisition; a small Linux SBC is acceptable when a richer replay interface is needed. The choice is a prototype tradeoff, not a production architecture decision.
- **Storage:** Use nonvolatile storage sized for the pilot duration, with a reserved margin and an explicit full-storage threshold. Writes should be append-oriented. Export should include a manifest and integrity information.
- **Clock:** Include a battery-backed RTC or equivalent. Network time may improve accuracy when available, but loss of synchronization must be visible. Each record should distinguish device time from any synchronization status or uncertainty estimate.
- **Identity:** Provision a unique device identifier and a configuration/version identifier. A cryptographic key may be included for signing exports, but a key's presence does not by itself establish trustworthy provenance. Key custody, rotation, recovery, and manufacturing provisioning remain unresolved for a commercial product.
- **Power:** Prototype operation may use USB-C or a battery pack. The power source, expected runtime, brownout behavior, and restart behavior must be recorded in the demonstration notes.

## 8. Evidence-record structure

The following is an illustrative, non-normative record shape for V0.1. It is not a REPEAT_CORE schema and must not be treated as one:

```json
{
  "record_id": "device-0001:00000042",
  "device_id": "device-0001",
  "config_id": "config-2026-01",
  "sequence": 42,
  "observed_at": "2026-01-01T12:00:00.123Z",
  "clock_status": "rtc-unsynchronized",
  "input": {"id": "door_switch", "kind": "digital", "value": true},
  "quality": "valid",
  "operator_event": null,
  "previous_digest": "...",
  "record_digest": "..."
}
```

A complete export should also identify firmware/build information, sensor configuration, units, acquisition policy, export time, detected gaps, and failure intervals. Large payloads, raw waveforms, and personal data should be excluded unless specifically justified. Privacy and retention requirements must be assessed per pilot.

## 9. Receipt and replay interface

The receipt is an export and presentation of what the node recorded; it is not a certificate of external truth. V0.1 should provide:

- A chronological event list with timestamps, sequence numbers, input values/status, and quality.
- A clear display of boot, shutdown, clock synchronization, configuration, storage, and fault events.
- Visible gaps, resets, duplicate/invalid records, and intervals marked indeterminate.
- Device and configuration identity, export metadata, and a digest or signature status where implemented.
- A compact human-readable summary plus machine-readable JSON or CSV export.
- A replay mode that reproduces the recorded sequence without contacting the device or changing the record.
- A verification result that distinguishes “integrity check passed” from “event is true” or “process complied.”

A buyer should be able to inspect a receipt on an ordinary laptop and understand both what is present and what is missing.

## 10. Failure modes and fail-closed behavior

| Failure mode | Required V0.1 response |
|---|---|
| Sensor disconnected or out of range | Record fault/indeterminate status; do not substitute a normal reading. |
| Input debounce or acquisition overload | Apply declared policy; record dropped/aggregated events and the reason. |
| RTC missing, invalid, or unsynchronized | Continue only with explicit clock status; do not represent time as authoritative. |
| Power loss or brownout | Recover safely; mark the affected boundary and any possible write loss. |
| Storage nearly full/full | Warn early; stop claiming complete capture when full; preserve prior records. |
| Corrupt record or failed integrity check | Quarantine or mark it invalid; never silently repair in place. |
| Configuration mismatch | Refuse acquisition or mark the run invalid until acknowledged and corrected. |
| Device reset/watchdog | Record reboot if possible; expose the interval as a potential gap. |
| Export interruption | Produce no “complete” receipt until export integrity is verified. |
| Suspected enclosure tamper | Mark status for review; do not claim physical tamper detection unless demonstrated. |

“Fail closed” means the device and receipt withhold a positive evidence claim when a required precondition is missing. It does not necessarily mean that the electronics power off.

## 11. Prototype BOM and approximate cost targets

Illustrative single-unit targets in USD, excluding labor, tooling, tax, and shipping:

| Item | Target |
|---|---:|
| MCU or SBC compute module | $25–$80 |
| RTC and backup cell | $3–$12 |
| Flash storage and/or removable media | $8–$25 |
| Sensor/interface board and one or two sensors | $20–$100 |
| Input button, indicators, connectors, wiring | $15–$40 |
| Power supply, protection, and optional battery | $20–$70 |
| Enclosure, mounting, and tamper-evident materials | $20–$80 |
| Assembly, contingency, and replacement allowance | $40–$120 |
| **Approximate prototype total** | **$150–$525** |

These are planning targets, not quotations. A paid pilot should separately price installation, calibration, support, data handling, and replacement risk.

## 12. Prototype build sequence

1. Define one bounded workflow, one success measure, permitted inputs, retention period, and explicit out-of-scope claims.
2. Assemble compute, clock, storage, power, enclosure, and a minimal sensor set on a bench.
3. Implement append-only event capture, boot/shutdown markers, fault states, and configuration display.
4. Exercise disconnects, bad values, clock loss, resets, brownouts, full storage, and interrupted export.
5. Implement receipt generation and offline replay before adding additional sensors.
6. Run a scripted demonstration with known inputs and independently compare expected versus recorded events.
7. Repeat the demonstration after transport, restart, and operator handoff; document variation and gaps.
8. Conduct a small supervised field trial with no safety-critical or compliance-critical reliance.
9. Record observed behavior, limitations, costs, and buyer feedback separately from design targets.
10. Decide whether a paid pilot is justified; do not expand scope by modifying REPEAT_CORE.

## 13. Buyer demonstration protocol

A 15–20 minute demonstration should:

1. State the workflow boundary and the claims the node does not make.
2. Show device identity, configuration, clock status, sensor wiring, and storage state.
3. Perform a known sequence: start, two or three input changes, one operator mark, and a normal stop.
4. Intentionally disconnect or invalidate an input and show the fail-closed receipt status.
5. Interrupt power or restart the device, then show the boot marker and any indeterminate interval.
6. Export the receipt to a laptop, replay it offline, and show integrity status and visible gaps.
7. Ask the buyer to identify what they can conclude, what they cannot conclude, and what workflow cost would be reduced.
8. Capture questions, acceptance criteria, privacy concerns, installation time, and a proposed paid-pilot metric.

The demonstration is successful only if the buyer can distinguish observed device behavior from broader process claims.

## 14. Commercial test and paid-pilot hypothesis

**Hypothesis:** A buyer will pay for a bounded pilot if the node reduces the time or ambiguity involved in reviewing a recurring physical process, while imposing less installation and workflow burden than modifying an existing system.

A pilot should test:

- Review time per event or job before and after deployment.
- Percentage of receipts that are complete and understandable without vendor intervention.
- Number and cost of disputed or unreconstructable events.
- Installation, training, maintenance, and replacement time.
- Willingness to pay for hardware, support, and a defined evidence workflow.

A useful pilot is paid or has a written purchase commitment, a named workflow owner, a fixed duration, agreed data handling, and a predeclared success threshold. Free demonstrations, positive anecdotes, or a successful bench test do not validate the commercial hypothesis.

## 15. Application hypotheses

### Fortune 500 / large enterprise

- Quality or supplier-assurance teams may use a bounded node to document a small number of high-cost inspection or handoff steps across sites.
- Maintenance organizations may test whether an offline receipt reduces time spent reconstructing equipment-state transitions.
- Logistics or cold-chain teams may investigate whether independently reviewable sensor intervals improve exception triage.
- Enterprise blockers may include security review, procurement, device fleet management, privacy, union/workforce concerns, integration ownership, and evidentiary policy. These are unresolved until a named buyer validates them.

### Smaller companies

- A small manufacturer may use one node for a repeatable setup, inspection, or packaging step where spreadsheets and memory currently dominate.
- A field-service company may use a portable node to document a visit or handoff where connectivity is unreliable.
- A specialty operator may value a simple receipt more than a broad dashboard if setup takes minutes and the device works offline.
- Smaller-company risks include support burden, calibration responsibility, replacement cost, and insufficient volume to justify custom integration.

## 16. Explicit status and change control

- **Demonstrated behavior:** Only the behaviors documented in a dated, reproducible prototype test log should be called demonstrated.
- **Prototype claims:** Hardware targets, record fields, cost ranges, and interface choices in this document are provisional design targets.
- **Unresolved hypotheses:** Market demand, evidentiary sufficiency, security posture, calibration traceability, reliability, regulatory fit, and willingness to pay remain unresolved unless separately evidenced.
- **REPEAT_CORE_CHANGE: NO.** This artifact is documentation for a separate physical-product exploration. It must not be used to alter existing REPEAT_CORE specifications, schemas, authority decisions, or implementation merely to accommodate the Evidence Node.
