# REPEAT External-System Boundary — Experiment Specification v0.1

**Status:** Research/prototype specification; non-invasive only  
**Scope:** External-system boundary experiment  
**Compatibility:** Does not modify `REPEAT_CORE_v1`

## 1. Purpose

This experiment tests whether an externally observable event can be transformed into an encoded representation, transmitted over an external channel, recovered as a received signal, and reported by a human listener. It is designed to separate machine-observable transmission fidelity from human perception.

The experiment does **not** claim that successful transmission establishes that the listener perceived the encoded event correctly.

## 2. Safety and non-invasive boundary

The first experiment is **non-invasive research / prototype only**.

It MUST NOT:

- modify, connect to, reprogram, interrogate, or otherwise alter a cochlear implant;
- modify clinical programming, maps, stimulation parameters, firmware, or clinical equipment;
- inject signals into an implant or bypass its approved external interfaces;
- be used as a treatment, diagnostic procedure, or substitute for clinical care.

The experiment MAY use ordinary external playback, recording, and transmission equipment only when operated within its manufacturer-approved use and under appropriate research and institutional oversight. Participation, consent, stop criteria, and privacy handling MUST be defined before any human-perception session.

## 3. System boundary

`REPEAT` owns the experiment record and the machine-observable verification steps. The human listener and their perception report are recorded as a separate outcome; the report is not treated as a machine-verifiable signal.

```text
Observation → Transformation → Transmission → Received signal → Perception report
      |             |               |                 |                 |
   recorded      recorded        verified          recorded           separately
   input         mapping          externally        output             reported
```

`REPEAT_CORE_v1` remains unchanged. Boundary adapters, fixtures, and experiment records MUST be additive and MUST NOT redefine core semantics.

## 4. Acceptance chain

### 4.1 Observation

Record the source event and its provenance before transformation. The observation record MUST include:

- experiment and trial identifiers;
- timestamp and source identifier;
- source representation and units, where applicable;
- calibration or provenance metadata;
- integrity hash of the captured observation.

**Acceptance condition:** the observation is present, unambiguous, reproducible from its recorded artifact, and integrity-checked.

### 4.2 Transformation

Apply the predeclared encoding or mapping to the observation. The transformation MUST be deterministic for the same input and configuration, or MUST record all permitted sources of variability.

Record:

- transformation algorithm and version;
- configuration and calibration parameters;
- input and output hashes;
- expected encoded event or frame;
- warnings, clipping, loss, or rejected inputs.

**Acceptance condition:** the expected encoded representation is derived from the recorded observation using the declared transformation, without silent changes.

### 4.3 Transmission

Transmit the encoded representation through the external system under test. The transmission record MUST identify:

- channel and protocol;
- sender and receiver equipment identifiers;
- relevant configuration and software/firmware versions;
- start/end times and trial identifier;
- transport status, sequence data, errors, retries, and loss indicators.

**Acceptance condition:** the external channel reports completion or failure, and the complete machine-readable transmission trace is retained.

### 4.4 Received signal

Capture the output available at the receiving boundary without assuming that it was perceived correctly. The received-signal record MUST include:

- raw or losslessly retained capture where feasible;
- capture configuration and clock information;
- received-signal hash;
- decoder/extractor version;
- decoded representation;
- comparison with the expected encoded representation;
- corruption, truncation, latency, and confidence metrics.

**Acceptance condition:** REPEAT can independently compare the received signal with the expected representation and classify the result as `exact`, `degraded`, `ambiguous`, or `failed`.

### 4.5 Perception report

After the received-signal capture is finalized, collect the listener's report using a predeclared protocol. The report MUST be stored separately from machine-observable acceptance and MUST include:

- anonymized participant/trial identifier;
- prompt and response options shown;
- response, confidence, and response time where collected;
- whether the trial was heard, unclear, missed, or stopped;
- accessibility, fatigue, or other protocol-relevant notes;
- consent and withdrawal status.

The protocol MUST avoid coaching the listener toward the expected answer. A perception report is an observation of the participant's response, not proof of the transmitted content.

**Acceptance condition:** the report is complete and associated with the trial, but it MUST NOT upgrade a machine-level failure to a successful transmission.

## 5. Acceptance matrix

| Stage | Owner | Evidence | Pass criterion |
|---|---|---|---|
| Observation | REPEAT boundary adapter | Observation artifact + hash | Source event is captured and reproducible |
| Transformation | REPEAT boundary adapter | Config, input/output hashes, encoded frame | Declared mapping produces expected frame |
| Transmission | External channel adapter | Transport trace | Channel outcome is recorded without silent loss |
| Received signal | REPEAT verifier | Capture, decoder result, comparison metrics | Received representation is classified against expectation |
| Perception report | Human-study protocol | Separate participant report | Response is recorded without conflating it with fidelity |

A trial MUST report at least two independent outcomes:

1. **Transmission fidelity:** machine-observable result for transformation, transmission, and received signal.
2. **Human perception:** participant response and associated protocol metadata.

Possible combined interpretations include:

- high fidelity / correct perception;
- high fidelity / incorrect or uncertain perception;
- degraded or failed fidelity / reported perception;
- insufficient evidence at either layer.

No combined result may collapse these dimensions into a single claim of success.

## 6. Falsifiability and failure handling

The experiment is falsifiable if a declared expected representation can be compared with a captured received representation and if perception results can disagree with that machine comparison.

REPEAT MUST fail closed for missing, malformed, unverifiable, or contradictory machine evidence. It MUST preserve the distinction between:

- transmission failure;
- received-signal mismatch;
- missing/invalid evidence;
- human non-perception or uncertain perception;
- human report inconsistent with the expected event.

No retry, filtering, or post hoc relabeling may remove an unsuccessful trial from the audit record. Any exclusion MUST include a reason, author/process identifier, and timestamp.

## 7. Out of scope for v0.1

- implant-side integration or clinical-programming changes;
- therapeutic or diagnostic claims;
- inference that a received signal was perceived;
- modification of `REPEAT_CORE_v1`;
- autonomous adaptation of clinical or human-facing parameters;
- generalization beyond the tested equipment, protocol, and participant population.

## 8. Minimum audit record

Each trial MUST be exportable as an append-only record containing:

- protocol/specification version;
- trial and experiment identifiers;
- observation, transformation, transmission, and received-signal evidence references;
- hashes for retained artifacts;
- machine-level verdict and rationale;
- separately stored perception report reference;
- safety, consent, stop, and deviation events;
- timestamps and software/equipment versions.

The audit record MUST make it possible for an independent reviewer to determine whether the machine-observable chain passed, whether the listener reported the encoded event, and where the evidence is insufficient.
