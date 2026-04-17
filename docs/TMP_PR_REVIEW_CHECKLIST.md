# TMP PR REVIEW CHECKLIST

### **CHANGE SURFACE**
- [ ] touches `schemas/tmp_mesh.schema.json`
- [ ] touches `docs/CANONICALIZATION.md`
- [ ] touches `verifier/**`
- [ ] touches `scripts/certify_tmp_v1.py`
- [ ] touches `tests/vectors/tmp/**`
- [ ] touches only non-certified/supporting files

---

### **SCHEMA**
- [ ] schema diff reviewed line-by-line
- [ ] required fields unchanged, or change explicitly justified
- [ ] field semantics unchanged, or version bump proposed
- [ ] schema examples updated
- [ ] PASS/FAIL/ERROR vectors updated if needed

---

### **CANONICALIZATION**
- [ ] canonicalization rules unchanged
- [ ] if changed, deterministic rationale documented
- [ ] hash projection unchanged
- [ ] array ordering rules unchanged
- [ ] normalization rules unchanged
- [ ] golden digests regenerated only if explicitly authorized

---

### **VERIFIER**
- [ ] verifier diff reviewed line-by-line
- [ ] exit semantics still `0=PASS`, `1=FAIL`, `2=ERROR`
- [ ] no silent fallback behavior introduced
- [ ] no inference-based repair introduced
- [ ] diagnostics improved without altering verdict semantics
- [ ] semantic drift assessed against the certification anchor

---

### **VECTORS**
- [ ] PASS vectors still `PASS`
- [ ] FAIL vectors still `FAIL`
- [ ] ERROR vectors still `ERROR`
- [ ] replay produces identical `canonical_sha256` on repeated runs
- [ ] tampered certified vector does not `PASS`

---

### **CERT GATE**
- [ ] `scripts/certify_tmp_v1.py` runs successfully
- [ ] `TMP_CERT_CHECKLIST` is all `PASS`
- [ ] `TMP_CERT_DECISION` is `CERTIFY`
- [ ] CI workflow passes on this PR

---

### **DECISION**
- [ ] `MERGE`
- [ ] `DO_NOT_MERGE`

---

### **NOTES**
- certification anchor: [commit hash or tagged version]
- semantic drift summary: [description of any observed drift, or "none"]
- required follow-ups: [list of action items, or "none"]

---

### Review Rules:
1. If any of the following files are modified, assume `DO_NOT_MERGE` until re-certification:
   - `schemas/tmp_mesh.schema.json`
   - `docs/CANONICALIZATION.md`
   - `verifier/**`

2. Minimum PR evidence for protocol-sensitive changes:
   - `git diff --stat <anchor>..HEAD -- schemas/tmp_mesh.schema.json docs/CANONICALIZATION.md verifier scripts/certify_tmp_v1.py tests/vectors/tmp`
   - `python scripts/certify_tmp_v1.py`
   - `pytest -q`
   - `git diff <anchor>..HEAD -- verifier`
   - `git diff <anchor>..HEAD -- schemas/tmp_mesh.schema.json`
   - `git diff <anchor>..HEAD -- docs/CANONICALIZATION.md`

3. Merge Rule:
   - If protocol-sensitive files are changed without re-certification evidence: `DO_NOT_MERGE`.

### PR Comment Template:
TMP REVIEW RESULT
```
scope: protocol-sensitive | non-protocol-sensitive
schema_drift: PASS|FAIL
canonicalization_drift: PASS|FAIL
verifier_semantic_drift: PASS|FAIL
vector_suite: PASS|FAIL
cert_gate: PASS|FAIL

decision: MERGE|DO_NOT_MERGE
reason:
```

---

This checklist will turn PR reviews into deterministic audits rather than informal interpretation.
