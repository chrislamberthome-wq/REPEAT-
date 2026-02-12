# REPEAT C14N v1 (Canonical JSON + sha256_c14n)

Purpose: deterministic byte-for-byte canonicalization of JSON evidence so any implementation
(Python/Node/Go/etc.) computes identical `receipt.sha256_c14n`.

## Normative algorithm (JCS / RFC 8785)
REPEAT C14N v1 uses JSON Canonicalization Scheme (JCS, RFC 8785).

## C14N rules (MUST)
1. Encoding: UTF-8, no BOM.
2. Top-level: MUST be a JSON object `{}`.
3. Key order: objects sorted lexicographically by Unicode codepoint (ascending).
4. Whitespace: no insignificant whitespace (no spaces after `:` or `,`; no newlines/indentation).
5. Numbers: shortest JSON form preserving value; no NaN/Infinity; no leading `+`; no leading zeros (except `0`).
6. Strings: strict JSON escaping.
7. Arrays: preserve order.
8. Duplicate keys: illegal (verifier FAIL).
9. Receipt exclusion: compute sha256 over the object with `receipt` removed (or at least `receipt.sha256_c14n` removed).
10. Hash format: "sha256:" + 64 lowercase hex.

## Receipt procedure (MUST)
- Let `obj` be the evidence JSON object.
- Let `obj'` be `obj` with `receipt` removed.
- Let `bytes = canonical_json(obj')` per JCS.
- Let `digest = sha256(bytes)`.
- Set `receipt.sha256_c14n = "sha256:" + hex_lower(digest).
