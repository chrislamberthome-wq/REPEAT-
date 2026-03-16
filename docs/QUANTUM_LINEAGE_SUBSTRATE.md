## Digest Algorithm Definition

SHA-256 with lowercase hexadecimal encoding is used for digest calculations. The output is formatted as a 64-character string representing the hash value in lowercase hex.

## Canonical JSON Rules

- Trailing whitespace is explicitly forbidden.
- All representations must be in UTF-8 byte format before hashing.
- The deterministic serialization format is defined using `json.dumps`.

## Generator Digest Definition

The generator digest is calculated as:  
`sha256(canonical_json_bytes(spec_object_without_generator_digest))`.

## Chain-Hash Concatenation Rule

The `prev_hash` must be encoded as UTF-8 bytes before concatenation with the canonical JSON bytes.

## Trace Canonicalization Scope

Note: The trace file itself is not canonicalized, but each individual entry is.

## Best Energy Selection

When determining the best energy, the minimum energy is selected. In case of ties, the earliest `shot_index` is used to break them.

## Zero Digest Constant

The zero digest is defined as follows:  
`ZERO_DIGEST = "0" * 64`  
This constant is used before the first trace entry.

## Tightened PASS Rules

Replace permissive language with normative language throughout the document:
"A verifier MUST emit …"

## Negative Corpus Expansion

Included a case for `trace_missing_field.jsonl` that tests `MISSING_REQUIRED_FIELD`.

## Implementation Independence

Emphasize that the specification is implementation-independent and that identical digests must be produced for identical inputs.