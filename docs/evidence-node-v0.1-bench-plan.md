# Evidence Node V0.1 — bench prototype plan

Status: implementation plan and standalone prototype tooling. This directory is outside `REPEAT_CORE`; no core files, schemas, authority, or verifiers are changed.

## 1. Specification used

`docs/evidence-node-v0.1.md` defines an observational, offline-first node with:

- one or more declared inputs plus an explicit operator input;
- local timestamps, sequence numbers, input identity, value/status, quality/error state;
- append-oriented nonvolatile storage, export without a network, and visible gaps/faults;
- a device/configuration identity and clock status;
- a human-readable receipt and machine-readable export;
- offline replay that does not contact or alter the node;
- integrity verification distinguished from truth or compliance claims;
- fail-closed handling of disconnects, invalid values, clock/storage problems, resets, and corrupt records;
- no actuation and no claim that the record proves external truth.

The prototype below deliberately implements only the smallest demonstrable path. It does not claim full compliance with every V0.1 requirement.

## 2. Selected process: vibration

Attach an accelerometer to a small rigid block. Record 10 seconds at 100 Hz:

1. 0–3 s: block at rest (baseline);
2. 3–7 s: operator taps or excites the block in a declared way;
3. 7–10 s: block at rest (recovery).

The measurable observation is acceleration magnitude variation in `m/s^2`. The inspection computes RMS variation for the stimulus window and both rest windows. The acceptance threshold is declared in the run configuration, not inferred after inspection.

This is an observation of the sensor, not a claim about the block's material, safety, or the cause of the vibration.

## 3. Minimum BOM

- Raspberry Pi Zero 2 W (or equivalent Linux SBC), powered by USB-C;
- ADXL345 breakout, I2C, mounted firmly to the test block;
- CR2032-backed RTC module (DS3231) if the SBC clock is not already reliable;
- momentary pushbutton on one GPIO for `operator_mark` (the first prototype may record a typed mark, but the button is the intended physical input);
- microSD card, 8 GB or larger;
- jumper wires, small breadboard, rigid block, tape/fastener, and a small enclosure;
- laptop with Python 3.10+ for offline replay and inspection.

No network, cloud service, actuator, or REPEAT_CORE dependency is required. Approximate bench cost: USD 60–150 depending on the SBC, enclosure, and existing equipment.

## 4. Complete evidence path

`sensor` → ADXL345 samples over I2C → append-only `observations.jsonl` with sequence, device/config identity, UTC time, clock status, vector and quality → SHA-256 of the exact byte artifact → `receipt.json` containing artifact hash, hash-chain tip, configuration, and declared inspection result → copy both files to a different laptop → replay recomputes the artifact hash and walks the sequence/hash chain without contacting the node → inspection computes the same vibration metrics and returns `PASS`, `FAIL`, or `UNRESOLVED`.

The receipt is a reproducible summary, not a signature and not proof of external truth. The original live I2C connection must be physically removed before replay.

## 5. Acceptance test

A run is **PASS** only when all conditions hold:

- the observation artifact hash matches the hash in the receipt and replay;
- sequence numbers are contiguous and each `previous_digest` matches;
- every sample is in range and marked `valid`;
- there are at least 100 samples in each of baseline, stimulus, and recovery windows;
- baseline and recovery RMS are at or below 0.50 `m/s^2`;
- stimulus RMS is at least 1.00 `m/s^2` and at least twice the larger rest RMS;
- the declared operator mark exists for the stimulus interval;
- no clock, storage, export, reset, or sensor fault is present.

It is **FAIL** when integrity is valid and a required measurable condition is demonstrably false. It is **UNRESOLVED** when the artifact is incomplete, tampered with, missing a mark, has a gap/fault, or does not contain enough samples to decide. The tooling intentionally does not convert an unresolved run into FAIL.

## 6. Implemented versus missing

### Already present in the repository

- The V0.1 product boundary and requirements: `docs/evidence-node-v0.1.md`.
- Several unrelated receipt/schema/verifier tracks and test suites.
- Existing example receipt and trace files, but no evidence-node physical acquisition path.
- Repository inventory and boundary audit explicitly warn that the authoritative `REPEAT_CORE_v1` surface is not established.

### Added by this bench scope

- Standalone JSONL capture/replay/inspection tooling in `prototype/evidence_node_v01.py`.
- This BOM, process definition, evidence path, and acceptance criteria.

### Still missing and intentionally not hidden

- Physical assembly and a dated run artifact from the selected hardware.
- ADXL345 driver exercise on the target SBC, RTC wiring, GPIO button wiring, and enclosure.
- Power-loss, storage-full, disconnect, reset, interrupted-export, and sensor-range fault tests.
- A real signed receipt, calibration traceability, tamper detection, production security, and any REPEAT_CORE integration.

Do not describe this scope as demonstrated until a dated physical run is copied to a second machine and independently replayed.

## 7. Run procedure

See `prototype/README.md`. The minimum evidence package is the exact `observations.jsonl`, `receipt.json`, the printed inspection output, and a short note identifying hardware, sensor mounting, thresholds, and operator actions.
