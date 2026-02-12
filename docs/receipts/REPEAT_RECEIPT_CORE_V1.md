# REPEAT Receipt Core v1

## Overview

The **REPEAT Receipt Core v1** defines the mandatory contract that all REPEAT subsystems must follow when emitting verification receipts. This ensures consistency, interoperability, and trustworthiness across the REPEAT ecosystem.

Every subsystem **must emit** receipts that conform to this contract or a **strict superset** of it.

## Schema Location

```
schemas/repeat_receipt.v1.schema.json
```

## Required Fields

All receipts must include the following mandatory fields:

### `receipt_version`
- **Type:** String (constant)
- **Value:** `"1.0"`
- **Description:** Identifies the receipt schema version. Must be exactly `"1.0"` for this version.

### `receipt_type`
- **Type:** String
- **Description:** Subsystem-defined identifier for the type of receipt.
- **Examples:**
  - `"genotype"` - Genotype analysis receipt
  - `"quality_check"` - Quality control receipt
  - `"pipeline_run"` - Pipeline execution receipt
  - `"hd_cag_analysis"` - Huntington's Disease CAG repeat analysis
- **Note:** Each subsystem defines its own receipt types. This field allows downstream systems to route and process receipts appropriately.

### `subject`
- **Type:** Object
- **Description:** The entity being verified or processed.
- **Required Properties:**
  - `id` (String): Unique identifier for the subject (e.g., sample ID, file ID, job ID)
  - `hash` (String): Cryptographic hash of the subject
- **Hash Format:** Must include the algorithm prefix (e.g., `sha256:abc123...`, `sha512:def456...`)
- **Additional Properties:** Subsystems may add extra fields (e.g., `name`, `type`, `metadata`)

### `verifier`
- **Type:** Object
- **Description:** Information about the system or component that performed the verification.
- **Required Properties:**
  - `id` (String): Identifier of the verifier (e.g., system name, service name, component name)
  - `version` (String): Version of the verifier software
- **Examples:**
  - `{"id": "repeat-hd-pipeline", "version": "2.1.0"}`
  - `{"id": "quality-gate-service", "version": "1.3.2"}`
- **Additional Properties:** Subsystems may add extra fields (e.g., `environment`, `config_hash`)

### `result`
- **Type:** Object
- **Description:** The verification result.
- **Required Properties:**
  - `pass` (Boolean): Whether verification passed (`true`) or failed (`false`)
  - `reason` (String): Human-readable explanation of the result
- **Note:** The `reason` field may be an empty string but is always required. For passing results, it might describe what was verified. For failing results, it should explain why verification failed.
- **Additional Properties:** Subsystems may add extra fields (e.g., `confidence`, `score`, `details`)

### `evidence`
- **Type:** Object
- **Description:** Evidence supporting this receipt.
- **Required Properties:**
  - `hash` (String): Hash of the evidence bundle, canonicalized payload, or evidence collection
  - `artifacts` (Array of Strings): References to artifacts (e.g., file paths, URIs, artifact IDs)
- **Hash Format:** Must include the algorithm prefix (e.g., `sha256:...`)
- **Artifacts:** May be an empty array if no artifacts are referenced, but the field is required
- **Additional Properties:** Subsystems may add extra fields (e.g., `size`, `location`, `type`)

### `timestamp_utc`
- **Type:** String
- **Description:** UTC timestamp when the receipt was generated
- **Format:** ISO-8601 format is **strongly recommended** (e.g., `2026-02-12T12:41:29Z`)
- **Note:** While any string is technically valid, ISO-8601 ensures machine-readability and avoids ambiguity

## Subsystem Extensions

Subsystems are **encouraged** to extend this schema with additional fields specific to their domain. The core schema explicitly permits this via `"additionalProperties": true` at both the root level and within nested objects.

### Extension Guidelines

1. **Maintain Core Contract:** All required fields must be present and valid
2. **Add Domain-Specific Fields:** Add fields that make sense for your subsystem
3. **Document Extensions:** Document your subsystem's extended schema
4. **Avoid Conflicts:** Don't override or redefine core fields with incompatible meanings

### Example: Genotype Receipt Extension

```json
{
  "receipt_version": "1.0",
  "receipt_type": "genotype",
  "subject": {
    "id": "sample-12345",
    "hash": "sha256:abc123...",
    "sample_type": "blood"
  },
  "verifier": {
    "id": "hd-genotyper",
    "version": "3.2.1",
    "lab": "Lab-XYZ"
  },
  "result": {
    "pass": true,
    "reason": "CAG repeat successfully called",
    "cag_count": 42,
    "confidence": 0.98
  },
  "evidence": {
    "hash": "sha256:def456...",
    "artifacts": ["raw_data.fastq", "alignment.bam"],
    "quality_score": 35.2
  },
  "timestamp_utc": "2026-02-12T14:30:00Z"
}
```

## Hash Algorithm Requirements

All hash fields (`subject.hash`, `evidence.hash`) **must** include the algorithm name as a prefix.

### Supported Formats

- `sha256:` followed by hex-encoded hash
- `sha512:` followed by hex-encoded hash
- `blake2b:` followed by hex-encoded hash
- Other standard algorithms with clear prefixes

### Why Algorithm Prefixes?

1. **Prevents ambiguity** - Hash values alone don't indicate the algorithm used
2. **Enables verification** - Downstream systems know how to recompute and verify hashes
3. **Future-proofs** - Allows migration to stronger algorithms without breaking compatibility
4. **Industry standard** - Follows practices from Docker, IPFS, and other systems

### Examples

✅ **Good:**
```json
"subject": {
  "id": "sample-001",
  "hash": "sha256:a3b2c1d4e5f6..."
}
```

❌ **Bad:**
```json
"subject": {
  "id": "sample-001",
  "hash": "a3b2c1d4e5f6..."
}
```

## Validation

### Automated Validation

All `*.receipt.json` files in the repository are automatically validated against this schema.

**Run validation locally:**
```bash
make verify-receipts
```

Or directly with pytest:
```bash
pytest -q tests/test_repeat_receipt_contract.py
```

### CI Integration

The validation tests run in CI and will **fail the build** if any receipt violates the contract. Error messages include:
- File path
- Field causing the error
- Validation message
- Schema path

### Initial Adoption

If no `*.receipt.json` files exist in your repository, the validation tests will skip gracefully with a message indicating this is acceptable during initial schema adoption.

## Subsystem Responsibilities

### When Emitting Receipts

1. **Include all required fields** - Every field listed above must be present
2. **Use correct types** - Strings, booleans, objects, arrays must match the schema
3. **Set receipt_version** - Always `"1.0"` for this version
4. **Define receipt_type** - Choose or define a meaningful type for your subsystem
5. **Include algorithm in hashes** - Always prefix hashes with the algorithm name
6. **Use ISO-8601 timestamps** - For maximum interoperability
7. **Provide meaningful reasons** - Help operators understand results
8. **Reference evidence** - Enable audit trails and reproducibility

### When Extending the Schema

1. **Document your extension** - Maintain subsystem-specific schema documentation
2. **Validate extensions** - Test your extended receipts still pass core validation
3. **Consider backwards compatibility** - New fields should not break existing consumers
4. **Share learnings** - If an extension proves valuable, propose it for the core schema

## Examples

### Minimal Valid Receipt

```json
{
  "receipt_version": "1.0",
  "receipt_type": "quality_check",
  "subject": {
    "id": "job-789",
    "hash": "sha256:fedcba9876543210..."
  },
  "verifier": {
    "id": "qc-service",
    "version": "1.0.0"
  },
  "result": {
    "pass": true,
    "reason": "All quality metrics passed"
  },
  "evidence": {
    "hash": "sha256:1234567890abcdef...",
    "artifacts": []
  },
  "timestamp_utc": "2026-02-12T12:00:00Z"
}
```

### Extended Receipt (Passing)

```json
{
  "receipt_version": "1.0",
  "receipt_type": "hd_cag_analysis",
  "subject": {
    "id": "patient-001",
    "hash": "sha256:abc123...",
    "sample_type": "genomic_dna",
    "collection_date": "2026-01-15"
  },
  "verifier": {
    "id": "hd-analyzer",
    "version": "2.5.0",
    "lab_id": "LAB-042",
    "operator": "technician-007"
  },
  "result": {
    "pass": true,
    "reason": "CAG repeat count within normal range",
    "cag_repeat_call": 18,
    "call_ci95": {
      "low": 17,
      "high": 19
    },
    "confidence": 0.99,
    "interruptions": {
      "present": false,
      "description": null
    }
  },
  "evidence": {
    "hash": "sha256:def456...",
    "artifacts": [
      "raw/patient-001.fastq.gz",
      "aligned/patient-001.bam",
      "reports/patient-001_analysis.pdf"
    ],
    "raw_data_hashes": {
      "sha256": ["789abc...", "012def..."]
    },
    "quality_scores": {
      "read_quality": 38.5,
      "coverage": 150
    }
  },
  "timestamp_utc": "2026-02-12T14:23:45.123Z",
  "processing_time_seconds": 327.5,
  "pipeline_config_hash": "sha256:config123..."
}
```

### Extended Receipt (Failing)

```json
{
  "receipt_version": "1.0",
  "receipt_type": "quality_check",
  "subject": {
    "id": "sample-999",
    "hash": "sha256:xyz789..."
  },
  "verifier": {
    "id": "qc-pipeline",
    "version": "1.2.0"
  },
  "result": {
    "pass": false,
    "reason": "Read quality below threshold (Q20: 85%, required: 90%)",
    "failed_checks": ["read_quality", "coverage_uniformity"],
    "metrics": {
      "q20_percentage": 85,
      "coverage_uniformity": 0.72
    }
  },
  "evidence": {
    "hash": "sha256:evidence456...",
    "artifacts": ["qc_report.html", "metrics.json"]
  },
  "timestamp_utc": "2026-02-12T15:00:00Z"
}
```

## FAQ

### Why a separate core receipt schema?

Different subsystems (genotyping, quality control, pipeline orchestration) need to emit receipts for different purposes, but all receipts should share a common structure for trust, auditability, and interoperability.

### Can I add custom fields?

**Yes!** The core schema explicitly allows additional properties. Add whatever fields make sense for your subsystem, as long as you include all required core fields.

### What if my subsystem needs to emit multiple receipt types?

Define multiple `receipt_type` values for your subsystem. Each type can have its own additional fields beyond the core schema.

### How do I version my subsystem's extended schema?

The `receipt_version` field is for the core schema version. For subsystem schema versioning, consider adding a field like `subsystem_schema_version` or encoding version information in your `receipt_type` value (e.g., `"genotype_v2"`).

### What should I put in evidence.hash?

Hash the evidence bundle in a way that makes sense for your subsystem:
- Hash of a tarball containing all artifacts
- Hash of a canonicalized JSON representation of evidence
- Hash of concatenated artifact hashes
- Merkle root of artifact hashes

The key requirement: the hash must be reproducible and verifiable.

### What if I don't have artifacts to reference?

Set `evidence.artifacts` to an empty array `[]`. The field is required but can be empty.

### Can I use a different timestamp format?

Technically yes (the schema accepts any string), but **ISO-8601 is strongly recommended** for interoperability. Most downstream systems expect ISO-8601 timestamps.

## See Also

- [schemas/repeat_receipt.v1.schema.json](../../schemas/repeat_receipt.v1.schema.json) - The actual JSON Schema
- [tests/test_repeat_receipt_contract.py](../../tests/test_repeat_receipt_contract.py) - Validation tests
- [Makefile](../../Makefile) - See the `verify-receipts` target

## Changelog

### v1.0 (2026-02-12)
- Initial release of REPEAT Receipt Core contract
- Defined mandatory fields: receipt_version, receipt_type, subject, verifier, result, evidence, timestamp_utc
- Added support for subsystem extensions via additionalProperties
- Implemented automated validation for all *.receipt.json files
