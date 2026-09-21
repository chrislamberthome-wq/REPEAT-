# HD-REPEAT Observation Array v0.1

**Status:** Research/design specification  
**Project:** `chrislamberthome-wq/REPEAT-`  
**Scope:** External HD research and measurement layer  
**Constraint:** This document does not modify, extend, or redefine `REPEAT_CORE_v1`.

## 1. Purpose

The HD-REPEAT Observation Array is a separate research and measurement layer for capturing longitudinal Huntington’s disease (HD) observations at substantially higher resolution than periodic clinical examination.

The system is intended to:

- Preserve raw observations so future analyses are not constrained by today’s hypotheses.
- Support repeated, synchronized observations across movement, force, electromyography, gait, speech, video, physiology, sleep, activity, and clinical assessment domains.
- Maintain replayable links between an original observation and every subsequent transformation, feature, model output, or interpretation.
- Produce evidence packages that can be presented to REPEAT for integrity and provenance verification.
- Support individual trajectories and population-level research without treating a derived score as the source of truth.

The primary research asset is the recoverable longitudinal observation record, not a single HD score.

## 2. Non-goals and boundaries

The HD-REPEAT Observation Array is explicitly:

- **Not a diagnostic device.**
- **Not a therapeutic intervention or therapeutic claim.**
- **Not a replacement for clinical assessment.**
- **Not a clinical decision-making authority.**
- **Not a modification or alteration of `REPEAT_CORE_v1`.**
- **Not a certification that a model interpretation represents biological truth.**

The system may organize, preserve, and verify evidence about observations and transformations. It must not imply that data integrity establishes clinical validity, causality, diagnosis, prognosis, or treatment efficacy.

## 3. Architectural overview

```text
HD PATIENT
   │
   ▼
HD-REPEAT OBSERVATION ARRAY
   │
   ├── Motion
   ├── Force/pressure
   ├── EMG
   ├── Gait/balance
   ├── Audio
   ├── Video/eye movement
   ├── Physiology
   ├── Sleep/activity
   └── Clinical assessments
   │
   ▼
RAW OBSERVATION VAULT
   │
   ├── immutable observation
   ├── timestamp
   ├── sensor/device identity
   ├── calibration
   ├── sampling parameters
   ├── environmental/context metadata
   └── provenance
   │
   ▼
REPEAT VERIFICATION BOUNDARY
   │
   ├── observation integrity
   ├── transformation provenance
   ├── derivation reproducibility
   └── claimed state transitions
   │
   ▼
DERIVED DATA / MODELS
   │
   ├── motor phenotype
   ├── gait
   ├── speech
   ├── cognition
   ├── sleep/activity
   └── longitudinal trajectories
```

### 3.1 Separation of authority

The HD system is an external research application. It produces evidence packages for REPEAT rather than becoming part of REPEAT’s authority itself.

No change to `REPEAT_CORE_v1` is required. The interface between the systems must be treated as a boundary: HD-REPEAT records and packages observations and derivations; REPEAT verifies the integrity and provenance claims supplied at that boundary.

## 4. Sensor architecture

The initial architecture should support heterogeneous sensors while keeping acquisition, storage, and verification independent of any one vendor or analysis method.

### 4.1 Observation domains

| Domain | Example inputs | Example research uses |
|---|---|---|
| Motion | Accelerometer, gyroscope, magnetometer, inertial measurement units (IMUs) | Tremor, bradykinesia-related movement characteristics, timing, coordination |
| Force/pressure | Grip force, pressure mats, instrumented surfaces, load cells | Force production, release timing, asymmetry, task execution |
| EMG | Surface electromyography channels | Muscle activation timing and coordination |
| Gait/balance | Plantar pressure, force plates, IMUs, balance platforms | Stride characteristics, postural sway, stability |
| Audio | Microphone recordings and acoustic metadata | Speech timing, articulation, prosody, vocal characteristics |
| Video/eye movement | RGB/depth video, eye tracking, scene metadata | Movement review, oculomotor observations, task context |
| Physiology | Heart rate, respiratory rate, skin temperature, electrodermal activity, other approved sensors | Contextual physiological measurements and state characterization |
| Sleep/activity | Phone, watch, actigraphy, environmental signals | Activity patterns, sleep/wake estimates, daily context |
| Clinical assessments | Assessment instruments, scores, rater metadata, visit context | Comparison and validation against clinical measures |

The presence of a sensor in this architecture does not establish that its output is clinically meaningful. Each sensor and protocol requires its own validation plan.

### 4.2 Sensor registry

Every acquisition device or sensor channel must have a registry entry containing, at minimum:

- `sensor_id`
- `device_id`
- manufacturer and model, where available
- hardware and firmware version
- channel and modality definitions
- units and coordinate conventions
- nominal accuracy and operating range
- sampling and synchronization capabilities
- calibration procedure and calibration status
- software/driver version
- ownership or custody information
- decommissioning or replacement history

Device replacement must create a new identity or an explicitly versioned registry record; it must not silently merge incompatible devices.

## 5. Observation model

An observation is the immutable record of an acquisition event or an explicitly bounded portion of an acquisition event. A derived feature, model output, or interpretation is never the source observation.

```text
Observation
├── observation_id
├── subject_id
├── timestamp
├── sensor_id
├── device_id
├── acquisition_parameters
├── calibration_state
├── raw_payload_reference
├── quality_metadata
├── environmental_context
└── provenance
```

### 5.1 Required fields

| Field | Requirement |
|---|---|
| `observation_id` | Globally unique, immutable identifier |
| `subject_id` | Pseudonymous subject reference; direct identifiers remain outside the observation vault where practicable |
| `timestamp` | Timestamp with timezone/offset and declared clock source; precision must be recorded |
| `sensor_id` | Registered sensor/channel identity |
| `device_id` | Registered physical or logical device identity |
| `acquisition_parameters` | Sampling rate, resolution, channel map, units, duration, protocol/task, and relevant settings |
| `calibration_state` | Calibration record, validity interval, method, result, and exceptions |
| `raw_payload_reference` | Content-addressed or otherwise integrity-protected reference to the original payload |
| `quality_metadata` | Completeness, dropout, clipping, saturation, noise, synchronization, and operator/system flags |
| `environmental_context` | Location class, posture/task context, ambient conditions, and relevant concurrent signals |
| `provenance` | Collector, software, protocol version, custody events, transformations, and verification references |

### 5.2 Identity and time

Observation identity and event time are separate concepts. A re-upload, re-indexing operation, or replication event must not change the observation’s original acquisition timestamp or identity.

The system should record:

- device clock and reference clock values where available;
- synchronization method and estimated clock error;
- start and end timestamps;
- timestamp uncertainty or missingness;
- ordering information for samples and packets;
- daylight-saving/timezone handling where relevant.

### 5.3 Subject and consent boundaries

Subject references must be pseudonymous within the research data layer. Identity linkage, consent, withdrawal, access controls, and retention rules must be managed through a separate governance process appropriate to the deployment and jurisdiction.

An observation must carry enough consent/governance metadata to determine whether it may be used for a particular research purpose, while avoiding unnecessary inclusion of direct identifiers in the raw vault.

## 6. The three-tap protocol

The historical:

```text
PALM → KNUCKLE → FIST
```

is the first standardized longitudinal protocol.

The protocol should preserve the recognizable historical maneuver while capturing substantially richer data from the same basic task. Each session should define, where applicable:

- protocol and version;
- instruction presentation and language;
- hand/side and starting posture;
- number of repetitions;
- expected transition sequence;
- rest intervals;
- sensor placement and device identities;
- synchronized video/audio context;
- force, motion, EMG, and timing channels;
- operator, environment, and deviations;
- quality checks and reasons for invalid or incomplete trials.

The protocol must record what actually occurred, including hesitation, extra transitions, missed taps, premature closure, failed capture, or protocol deviation. A cleaned or idealized sequence must not replace the original recording.

The protocol is a standardized observation procedure, not a diagnostic test. Its biological associations remain unresolved until independently validated.

## 7. Raw-data preservation rule

**No irreversible transformation may replace the underlying observation.**

Derived features must reference their source observations rather than becoming the source of truth. At minimum:

- raw payloads are retained or referenced through an immutable, integrity-protected store;
- transformations create new versioned artifacts;
- every artifact records its parent observation(s) or artifact(s);
- lossy compression, filtering, resampling, anonymization, and redaction are explicitly declared;
- deletion, quarantine, or access restriction is recorded as a governed event rather than silently removing provenance;
- reproducibility metadata includes code, configuration, dependencies, and execution environment where feasible.

If retention or privacy policy requires destruction or alteration of raw data, the event must be explicit, authorized, and represented in the provenance record. A derived artifact must never be presented as equivalent to a destroyed source.

## 8. REPEAT verification boundary

The boundary is a chain of claims:

```text
RAW OBSERVATION
      ↓
PROCESSING
      ↓
FEATURE
      ↓
MODEL
      ↓
INTERPRETATION
```

HD-REPEAT should submit evidence packages that allow REPEAT to verify, as applicable:

- observation and artifact integrity;
- identity and ordering of inputs;
- transformation provenance;
- derivation reproducibility;
- claimed state transitions in the evidence chain.

REPEAT verifies integrity and provenance claims. It does **not** certify that the interpretation represents biological truth, that an association is causal, or that a model is clinically valid.

Each package should distinguish clearly between:

1. **Observed:** what was directly acquired or recorded.
2. **Derived:** what was computed from one or more observations.
3. **Modeled:** what was generated by a statistical or machine-learning method.
4. **Interpreted:** what a person or system claims those results mean.
5. **Validated:** what has been independently evaluated against a declared reference or outcome.

## 9. Provenance and derivation requirements

Every processing step should declare:

- input artifact identifiers;
- output artifact identifier;
- operation name and version;
- code or container reference;
- configuration and parameter values;
- execution time and environment;
- operator or automated service identity;
- quality checks and warnings;
- failure, retry, and exception information;
- whether the operation is reversible or lossy.

A model artifact should additionally identify its training, validation, and test data boundaries, model version, feature set, evaluation protocol, and known limitations. A longitudinal trajectory should identify the observations and derivations contributing to each point.

## 10. Research status and epistemic labeling

Every biological association remains:

> **UNRESOLVED**

until independently validated.

The system should use explicit status labels such as:

- `OBSERVED`
- `DERIVED`
- `MODELED`
- `HYPOTHESIS`
- `UNRESOLVED`
- `INDEPENDENTLY_VALIDATED`
- `REJECTED_OR_NOT_REPLICATED`

A model score must not be labeled as a clinical endpoint merely because it is repeatable or cryptographically verifiable. Verification of a chain establishes evidence integrity, not biological significance.

## 11. Quality, safety, and governance considerations

The design should support, but not prescribe, the following controls:

- role-based access and least-privilege access to sensitive observations;
- encryption in transit and at rest;
- audit logging for access, export, transformation, and governance events;
- documented retention, withdrawal, and destruction policies;
- separation of research outputs from clinical records unless formally governed;
- monitoring for missingness, sensor drift, device replacement, and protocol drift;
- human review for anomalous or safety-relevant acquisition events;
- clear communication that research outputs are not diagnoses or treatment recommendations.

Privacy-preserving transformations must be represented as derived artifacts with explicit limitations. For example, an anonymized video derivative does not replace the original video observation for provenance purposes.

## 12. Phased implementation sequence

### Phase 1 — Specification

- Observation ontology
- Sensor registry
- Provenance model
- Three-tap protocol
- Consent, governance, and retention requirements
- Evidence-package interface at the REPEAT boundary

### Phase 2 — Capture

- Hardware and software prototype
- Synchronized timestamps
- Raw-data storage
- Sensor and protocol metadata capture
- Initial quality and calibration checks

### Phase 3 — Verification

- REPEAT receipts around acquisition and processing
- Integrity checks for raw and derived artifacts
- Reproducible derivation chains
- Evidence-package export and boundary validation

### Phase 4 — Longitudinal research

- Repeated measurements
- Individual trajectories
- Population comparison
- Comparison with clinical measures
- Independent validation and replication

Progression between phases must not be interpreted as clinical validation. Each phase should retain the option to revise protocols without invalidating the raw observation history.

## 13. Acceptance criteria for v0.1

This design is ready for implementation planning when the project can answer, in a versioned specification:

1. What constitutes an observation and what constitutes a derived artifact?
2. How are device identity, calibration, units, and clock synchronization recorded?
3. How is the complete three-tap session preserved, including deviations and failures?
4. How can a future researcher locate and replay the inputs to a reported feature or model?
5. Which claims are verified at the REPEAT boundary, and which claims remain outside its authority?
6. How are consent, access, retention, withdrawal, and privacy events represented?
7. How are unresolved biological associations distinguished from independently validated findings?

## 14. Explicit architectural constraint

All work described in this document is external to `REPEAT_CORE_v1`. The HD-REPEAT Observation Array must not modify, redefine, or embed itself into REPEAT core authority. Its role is to produce a longitudinal, replayable measurement record and evidence packages whose integrity and provenance can be verified at the existing boundary.
