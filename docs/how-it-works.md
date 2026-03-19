# How It Works

REPEAT enforces deterministic verification through a contract-driven traceability engine.

## Pipeline

```
source document → tokenization → token subset check → receipt generation → CI enforcement
```

Each step is deterministic, schema-validated, and produces auditable artifacts.

## Contracts

A contract declares the invariants that must hold between source documents and their built projections. Contracts are YAML files validated against a JSON schema.

Example contract entry:

```yaml
- source: README.md
  target: site/build/index.html
  allowlist: []
```

The `comparison_mode: token_subset` setting means every significant token extracted from the source document must appear in the target HTML. Missing tokens cause the mapping to fail.

## Token Extraction

Tokens are extracted from source markdown and target HTML by:

1. Stripping markup (markdown formatting or HTML tags)
2. Splitting on whitespace and punctuation boundaries
3. Lowercasing and normalizing
4. Filtering tokens shorter than three characters
5. Removing common structural words

The result is a set of semantically meaningful tokens from each document.

## Allowlists

Each mapping may declare an explicit allowlist of tokens that are permitted to be absent from the target. Allowlists must be kept short and explicit. A long allowlist is a signal that the projection is semantically incomplete.

## Receipt Generation

After evaluating all mappings, the verifier writes:

- `site/receipt.json` — per-mapping pass/fail status with timestamp
- `site/input.manifest.json` — SHA-256 digests of all source files
- `site/output.manifest.json` — SHA-256 digests of all target files

The receipt is the authoritative certification artifact. It is schema-validated before being written.

## Verification Command

```bash
python site/verify_projection.py verify
```

Exit code 0 indicates all mappings passed. Exit code 1 indicates a schema or mapping failure. Exit code 2 indicates an unexpected error.

## CI Enforcement

The `verify-site` job in CI:

1. Checks out the repository
2. Builds the site HTML from source markdown
3. Runs the projection verifier
4. Uploads the receipt as a CI artifact

The `verify-policy` job runs after `verify-site` and evaluates release governance policies. Policy evaluation is separate from artifact certification.

## Extending Coverage

To add a new mapping, add one entry to `site/invariants.contract.yaml`:

```yaml
- source: docs/new-page.md
  target: site/build/docs/new-page.html
  allowlist: []
```

No changes to the verifier are required. The engine processes all declared mappings generically.
