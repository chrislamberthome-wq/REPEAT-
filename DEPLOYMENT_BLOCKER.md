# REPEAT Deployment Blocker — Replit Publish Gate

## STATUS: VERIFIED SYSTEM / BLOCKED DEPLOY

This system has passed all internal invariants and is producing deterministic, reproducible outputs.

The failure is not in the verifier, protocol, or HTTP surface.

The failure is in the Replit deployment layer.

---

## VERIFIED INVARIANTS (PASS)

### 1. Runtime Binding
- FastAPI server runs successfully
- Bound to: 0.0.0.0:8000
- Foreground process confirmed

### 2. Health Endpoint

GET /api/healthz
→ {“status”:“ok”}

### 3. Deterministic Verifier Surface
- POST /api/verify returns stable output
- Byte-preserving input via `--data-binary`
- No mutation of:
  - key order
  - whitespace
  - numeric formatting

### 4. Reproducible Test Vector
- Fixed input: docs/fixture.json
- Fixed output fields:
  - receipt_sha256
  - canonical_hash
  - canonical_bytes_length
  - result
- CLI equivalence maintained

---

## FAILURE CONDITION

Replit UI displays:

> “Published apps not available — There is an issue preventing you from publishing”

Observed state:
- Domain reserved: definitive-state.replit.app
- App recognized as publishable type
- No Publish button available
- Deploy pane present but blocked

---

## CLASSIFICATION (REPEAT)

This is a **FAIL-CLOSED infrastructure gate**.

System behavior:

INPUT: Valid, deterministic, reproducible system
VERIFIER: PASS
DEPLOYMENT: DENIED
RESULT: EXTERNAL FAIL (non-protocol)

This is not:
- a schema failure
- a runtime failure
- a verifier failure

This is:
→ **Platform entitlement / deploy binding failure**

---

## ROOT CAUSE CANDIDATES

1. Deploy service not attaching to runtime
2. Account entitlement not applied
3. Repl misclassified (non-web-service state)

All are external to the REPEAT system.

---

## REPRO STEPS (DETERMINISTIC)

1. Start server:

uvicorn server.main:app –host 0.0.0.0 –port 8000

2. Verify:

curl http://0.0.0.0:8000/api/healthz
→ {“status”:“ok”}

3. Open Replit Publish pane

Observed result:
→ Publish blocked

---

## EXPECTED BEHAVIOR

Given:
- active web server
- bound to public interface
- valid HTTP responses

System should expose:
→ Publish button

---

## ACTUAL BEHAVIOR

→ Publish not available  
→ Deployment blocked upstream  

---

## REPEAT INTERPRETATION

This event demonstrates:

> “REPEAT makes messages across time and space verifiable.”

The system is verifiable.

The platform is not.

---

## CONCLUSION

The REPEAT system is:
- operational
- deterministic
- externally testable

The deployment failure is:
- non-deterministic
- external
- unverifiable within system boundaries

---

## ACTION REQUIRED (PLATFORM)

Replit must:
- verify deployment entitlement
- attach runtime to Deploy system
- correct repl classification

---

## FINAL STATE

SYSTEM: PASS
DEPLOYMENT: FAIL (external)
CERTIFICATION: BLOCKED BY PLATFORM
