# REPEAT FPGA Interface v0.1

**Status: `SPECIFICATION_ONLY — NO RTL/CI/TOOLCHAIN AUTHORIZATION`**  
**Document type:** boundary specification / decision register  
**Repository:** `chrislamberthome-wq/REPEAT-`  
**Path:** `docs/fpga/REPEAT_FPGA_INTERFACE_v0.1.md`

## 1. Purpose and non-authority

This document records the currently observed repository context and establishes a review boundary for a possible FPGA-to-software interface. It is not an RTL specification, implementation plan, pinout, timing closure target, device-selection record, toolchain configuration, or CI authorization.

No FPGA interface is authorized by this document. Any item not explicitly stated as an observed fact below is either a new decision proposed for review or `UNSPECIFIED`.

## 2. Observed repository facts

The following are observations from the repository at the time this document was drafted; they are not FPGA design decisions:

- The repository is `chrislamberthome-wq/REPEAT-`.
- The default branch observed for this request is `main`.
- The repository contains existing top-level `Makefile`, `.github/`, `schema/`, `schemas/`, and `node_zero_v1/` paths.
- The repository contains documentation concerning deterministic verification, audit traces, schema governance, and related system concepts.
- `DEPLOYMENT_BLOCKER.md` describes a deterministic verifier surface and receipt-related outputs, including `receipt_sha256`, `canonical_hash`, `canonical_bytes_length`, and `result`. This document does not establish an FPGA wire format.
- `README.md` describes an experimental research protocol involving binary framing, CRC16 verification, signal processing, classification, and deterministic JSONL audit traces. It does not establish an FPGA interface.
- Existing repository schemas, workflows, `Makefile`, and `node_zero_v1` are intentionally not modified by this change.
- No inspected repository fact establishes an FPGA vendor, device, board, package, electrical standard, connector, clock frequency, reset polarity, bus protocol, register map, telemetry encoding, or physical pinout.

Repository facts above must not be treated as requirements for RTL. The authoritative source for each existing software schema and receipt field remains `UNSPECIFIED` within this FPGA boundary document unless separately resolved by the responsible owners.

## 3. New decisions recorded by this document

These are boundary decisions made for this specification artifact only:

1. FPGA implementation is out of scope until the FREEZE GATE in Section 12 is closed.
2. The FPGA must not silently redefine, normalize, truncate, reorder, or reinterpret software receipt data.
3. Software remains the authority for receipt acceptance, canonicalization, cryptographic verification, policy evaluation, and externally visible verification results unless an approved future decision explicitly assigns an operation to hardware.
4. FPGA-originated measurements are observations, not verified receipts, unless software verifies them against an approved schema and verification procedure.
5. Every interface property not resolved in this document is `UNSPECIFIED`; implementers must not infer a value from common FPGA practice.
6. This document authorizes documentation only. It authorizes no RTL, generated HDL, testbench, constraint file, synthesis project, CI job, toolchain install, device programming, or Makefile/workflow change.

## 4. Scope and trust boundary

### 4.1 In scope

- The conceptual boundary between an FPGA subsystem and software.
- The categories of data that may cross that boundary.
- Questions that must be answered before implementation.
- Verification ownership and receipt-field mapping responsibilities.

### 4.2 Out of scope

- FPGA family, part number, board, package, voltage, I/O standard, or pin assignment: **UNSPECIFIED**.
- Physical transport (USB, PCIe, Ethernet, serial, memory-mapped bus, GPIO, or other): **UNSPECIFIED**.
- RTL language, module hierarchy, IP cores, synthesis, place-and-route, bitstream format, programming flow, and timing constraints: **UNSPECIFIED**.
- A normative telemetry schema or a normative receipt schema: **UNSPECIFIED**.

### 4.3 Explicit FPGA ↔ software trust boundary

The FPGA is an untrusted or not-yet-attested observation source at this boundary. Software is the trust-boundary owner for:

- framing and transport integrity checks;
- schema/version acceptance;
- byte ordering and numeric interpretation;
- canonicalization and hash calculation;
- receipt construction and cryptographic verification;
- freshness, replay, sequence, range, and policy checks;
- handling malformed, incomplete, duplicated, stale, or contradictory data;
- final `PASS`, `FAIL`, `NACK`, or equivalent externally visible result.

The FPGA may perform acquisition, signal conditioning, measurement, buffering, and preliminary integrity metadata only after those responsibilities and their failure behavior are approved. FPGA-generated status, CRC, counters, timestamps, or hashes must not be treated as proof of software receipt validity by implication. The exact division of cryptographic and integrity operations is **UNSPECIFIED**.

## 5. Conceptual data products

The following names are descriptive placeholders, not wire-level field names:

- **Command/configuration:** software-to-FPGA requests, parameters, enablement, and lifecycle control. Structure, authorization, and mutability are **UNSPECIFIED**.
- **Telemetry sample/frame:** FPGA-to-software observation data plus metadata needed for interpretation. Exact contents and encoding are **UNSPECIFIED**.
- **Event/error:** FPGA-to-software fault, overflow, loss, invalid input, or state transition notification. Event taxonomy and delivery guarantees are **UNSPECIFIED**.
- **Receipt association:** identifiers that allow software to associate observations with a command, acquisition, run, or receipt. Required identifiers and ownership are **UNSPECIFIED**.

No command, telemetry, event, or receipt field is currently a committed interface field.

## 6. Telemetry frame: unresolved structure

A telemetry frame is expected to need enough information for software to determine what was observed, when/where it was observed, how it was encoded, and whether it is complete. The following candidate categories are recorded for resolution only:

| Candidate category | Requirement/status |
|---|---|
| Frame magic/version | `UNSPECIFIED` |
| Frame type/subtype | `UNSPECIFIED` |
| Header length and total length | `UNSPECIFIED` |
| Schema identifier and schema version | `UNSPECIFIED`; schema authority unresolved |
| Device/instance/channel identity | `UNSPECIFIED` |
| Sequence number and loss detection | `UNSPECIFIED` |
| Acquisition timestamp/clock domain | `UNSPECIFIED` |
| Sample count, payload encoding, units, and scale | `UNSPECIFIED` |
| Payload byte order and alignment | `UNSPECIFIED` |
| Integrity field (CRC/hash/MAC/other) | `UNSPECIFIED` |
| Completion/end marker | `UNSPECIFIED` |
| Extension/forward-compatibility rules | `UNSPECIFIED` |

**Schema authority is unresolved.** It is not decided whether an existing repository schema, a new schema, a software-owned schema, or a separately governed FPGA schema will be normative. This document does not modify `schema/` or `schemas/`.

## 7. Clock, reset, CDC, and interface semantics

- FPGA reference clock source(s), frequency/frequency tolerance, phase relationship, and duty cycle: **UNSPECIFIED**.
- Software/transport clock relationship: **UNSPECIFIED**.
- Reset source(s), polarity, synchronization, assertion/deassertion behavior, and reset scope: **UNSPECIFIED**.
- Power-up state, initialization completion indication, and behavior during reset: **UNSPECIFIED**.
- Clock-domain crossings, synchronizers, asynchronous FIFOs, metastability assumptions, and CDC sign-off method: **UNSPECIFIED**.
- Interface signaling (including `valid`, `ready`, `start`, `done`, `busy`, backpressure, and idle semantics): **UNSPECIFIED**.
- Whether `valid` is permitted without `ready`, whether data must remain stable while stalled, and whether bubbles are legal: **UNSPECIFIED**.
- Buffer depth, overflow policy, underflow policy, packetization, and drop accounting: **UNSPECIFIED**.

No implementation may assume an AXI-style, streaming, memory-mapped, FIFO, or ready/valid protocol from the terms used here.

## 8. Latency, throughput, and error semantics

- End-to-end latency budget: **UNSPECIFIED**.
- FPGA acquisition-to-frame latency: **UNSPECIFIED**.
- Transport latency and software service-time budget: **UNSPECIFIED**.
- Minimum, maximum, and sustainable telemetry throughput: **UNSPECIFIED**.
- Burst size, maximum frame size, maximum outstanding frames, and ordering guarantee: **UNSPECIFIED**.
- Backpressure behavior and whether loss is permitted: **UNSPECIFIED**.
- Error classes, severity, recoverability, retry behavior, and fail-safe state: **UNSPECIFIED**.
- Semantics for malformed frames, CRC/integrity failure, timeout, reset during frame, clock loss, overflow, and sequence gaps: **UNSPECIFIED**.
- Whether errors are in-band, out-of-band, sticky, counted, latched, or receipt-visible: **UNSPECIFIED**.

Until resolved, software must assume that no latency, throughput, ordering, or loss guarantee exists.

## 9. Receipt-field mapping and verification ownership

No FPGA field mapping is approved. The following ownership matrix prevents an observation from being mistaken for a verified receipt:

| Concern / receipt-related value | Candidate source | Verification owner | Status |
|---|---|---|---|
| Raw observation bytes | FPGA or upstream source | Software ingestion and schema validator | Source and encoding `UNSPECIFIED` |
| Frame integrity indicator | FPGA/transport/software | Software | Algorithm and authority `UNSPECIFIED` |
| Canonical bytes | Software | Software | Canonicalization rules `UNSPECIFIED` here; existing rules must be explicitly referenced |
| `canonical_bytes_length` | Software-derived | Software | Mapping to any FPGA length `UNSPECIFIED` |
| `canonical_hash` | Software-derived or supplied input | Software | Hash algorithm/source authority `UNSPECIFIED` here |
| `receipt_sha256` | Software receipt pipeline | Software | FPGA production/verification is not authorized |
| `result` | Software verifier | Software | FPGA status must not substitute for this result |
| Sequence/freshness/replay evidence | FPGA/transport plus software state | Software | Fields and acceptance rules `UNSPECIFIED` |
| Device identity/attestation | FPGA/board/platform | Software/policy owner | Mechanism and authority `UNSPECIFIED` |

The exact receipt schema, field names, requiredness, canonicalization, hash algorithms, and mapping rules must be resolved by the existing schema/verification owners before any hardware contract is frozen. A future mapping must identify source bytes, transformation (if any), validation rule, and the owner of each check.

## 10. Compatibility and versioning

- Interface version encoding: **UNSPECIFIED**.
- Compatibility policy for readers and writers: **UNSPECIFIED**.
- Unknown-field handling: **UNSPECIFIED**.
- Schema migration and deprecation process: **UNSPECIFIED**.
- Whether telemetry is self-describing: **UNSPECIFIED**.

A version number must not be invented or assigned by an RTL implementation task.

## 11. Verification ownership and evidence

Before implementation, owners must define at minimum:

- a normative byte-level frame specification and test vectors;
- schema authority and change-control ownership;
- software validation and receipt-verification tests;
- FPGA property/assertion, simulation, CDC, and reset verification ownership;
- transport/integration tests, including stalls, loss, reset, malformed input, and boundary sizes;
- acceptance evidence for latency, throughput, ordering, and error behavior;
- traceability from each approved field to its producer, consumer, and verifier.

The repository's existing verification artifacts remain authoritative only within their documented scope; this document does not extend them to FPGA behavior.

## 12. FREEZE GATE — required before RTL implementation

**All items below must be resolved, reviewed, and recorded before RTL, constraints, a bitstream project, or FPGA CI is authorized:**

1. Define the FPGA use case, boundary, and accountable owners.
2. Select and record the exact FPGA device/board, electrical requirements, clock sources, reset sources, and pinout.
3. Select the physical/software transport and provide its normative interface/register/packet specification.
4. Freeze telemetry frame layout: fields, widths, signedness, units, scaling, byte order, alignment, framing, maximum size, and versioning.
5. Resolve schema authority and approve the normative telemetry and receipt schemas without silently modifying existing schemas.
6. Define command/configuration semantics, lifecycle states, permissions, and reconfiguration behavior.
7. Define `valid/ready` or equivalent transfer semantics, including stalls, bubbles, backpressure, buffering, overflow, underflow, and loss accounting.
8. Define all clocks, reset behavior, CDC strategy, metastability assumptions, and sign-off evidence.
9. Freeze latency, throughput, ordering, burst, timestamp, and freshness guarantees.
10. Define error taxonomy and exact semantics for malformed data, integrity failure, timeout, reset, clock loss, overflow, and recovery.
11. Approve receipt-field mapping, canonicalization boundaries, cryptographic responsibilities, and verification ownership.
12. Define security/trust assumptions, including device identity, attestation, replay protection, and treatment of FPGA output as untrusted observation.
13. Produce golden vectors and independent software/FPGA conformance tests.
14. Define RTL language/version, toolchain/device versions, lint/simulation/formal/CDC requirements, and artifact reproducibility rules.
15. Obtain explicit repository governance approval before changing RTL paths, CI/workflows, Makefile, schemas, or `node_zero_v1`.

Until every item is closed, status remains **`SPECIFICATION_ONLY — NO RTL/CI/TOOLCHAIN AUTHORIZATION`**.

## 13. Change control

Changes to this document must preserve the separation between observed facts and decisions. New facts require a source and observation date; new interface decisions require an owner, rationale, compatibility impact, and approval record. Resolving an `UNSPECIFIED` item does not authorize implementation in itself; the FREEZE GATE must still be closed.
