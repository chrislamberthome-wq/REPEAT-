# GYRO-IPHN-0001 — Stabilized Visual Receiver Probe Spec (v0)

## Table of Contents
- [0. Purpose](#0-purpose)
- [1. Probe Identity](#1-probe-identity)
- [2. Hardware](#2-hardware)
- [3. Mount Transform Convention](#3-mount-transform-convention)
- [4. Operating Modes](#4-operating-modes)
- [5. Primary Use Cases](#5-primary-use-cases)
- [6. Capture Requirements (Normative)](#6-capture-requirements-normative)
- [7. Evidence Artifacts](#7-evidence-artifacts)
- [8. Known Limitations (v0)](#8-known-limitations-v0)
- [9. Planned Upgrades](#9-planned-upgrades)

## 0. Purpose

GYRO-IPHN-0001 defines a stabilized camera probe (iPhone mounted to a 3-axis gyro-stick/gimbal)
to support REPEAT visual-channel experiments: geometric addressing, face-ID recovery,
visual-binary packets, and auditable pass/fail verification.

This probe spec exists to make capture runs repeatable, comparable, and verifiable across time.

## 1. Probe Identity

- probe_id: GYRO-IPHN-0001
- class: stabilized_visual_receiver
- version: v0
- owner: Chris Lambert
- timezone: America/Chicago

## 2. Hardware

### 2.1 Receiver
- device: iPhone (model: unknown/variable)
- sensors: camera + gyro + accelerometer (IMU)
- clock: device system time (not synchronized by default)

### 2.2 Stabilizer
- device: handheld gyro-stick / 3-axis gimbal
- stabilization: active (3-axis), model/firmware unspecified

### 2.3 Mount
- mount_type: clamp
- mount_lock: MUST be mechanically tight (no slip)
- lens: rear camera preferred (stability + quality)

## 3. Mount Transform Convention

We define a right-handed probe frame P:

- +Pz: camera optical axis pointing forward (out of the lens)
- +Px: image plane right direction (screen right when viewing preview upright)
- +Py: image plane down direction (down in the image)

Mount transform is the mapping from gimbal frame G to probe frame P.

- mount_transform: UNKNOWN (v0)
- requirement: operator MUST keep phone mounted in the same orientation for a given run

**Mount proxy rule (locks v1 behavior without code):**
“rear camera, screen facing operator, volume buttons up, lens top-left in preview.”

## 4. Operating Modes

- MODE_STILL: stabilized still images at defined waypoints
- MODE_SWEEP: continuous video with controlled yaw/pitch sweeps
- MODE_TURNAROUND: controlled “orbit” around target at constant radius

## 5. Primary Use Cases

- UC1: face-ID / upright recovery (geometric addressing)
- UC2: visual-binary packets (preamble → payload → crc)
- UC3: decoder tolerance envelope testing (blur/rotation/lighting)
- UC4: field validation of “receiver in the wild” assumptions

## 6. Capture Requirements (Normative)

- R1: MUST record lighting conditions (indoor/outdoor, shadows, backlight).
- R2: MUST avoid digital zoom unless explicitly testing zoom.
- R3: MUST hold exposure/AE lock if available for the capture session.
- R4: MUST keep stabilization ON for stabilized runs.
- R5: MUST record at least one “calibration frame” (static, centered target) per run.
- R6: MUST store raw files with sha256 in a manifest for audit.

## 7. Evidence Artifacts

Each run SHOULD produce:
- media: .MOV/.MP4 and/or .JPG/.HEIC
- run manifest: manifest.json (sha256 of each evidence file)
- audit trace: audit.jsonl with pass/fail checks + hashes

## 8. Known Limitations (v0)

- No calibrated mount_transform constant yet
- No external time sync (UTC drift possible)
- No guaranteed access to raw IMU telemetry

## 9. Planned Upgrades

- v1: lock mount_transform constant with a written physical orientation rule
- v2: add time sync strategy (NTP snapshot, clap marker, or external reference)
- v3: IMU log integration (if supported by app)