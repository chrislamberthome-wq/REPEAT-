#!/usr/bin/env python3
"""
SITE-INV-01 Projection Verifier.

Reads invariants.contract.yaml, checks that source document tokens are a
subset of target HTML tokens (comparison_mode: token_subset), and writes
site/receipt.json, site/input.manifest.json, and site/output.manifest.json.

Usage:
    python site/verify_projection.py verify
"""

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"

CONTRACT_PATH = SITE_DIR / "invariants.contract.yaml"
CONTRACT_SCHEMA_PATH = SITE_DIR / "invariants.contract.schema.json"
RECEIPT_SCHEMA_PATH = SITE_DIR / "receipt.schema.json"
RECEIPT_PATH = SITE_DIR / "receipt.json"
INPUT_MANIFEST_PATH = SITE_DIR / "input.manifest.json"
OUTPUT_MANIFEST_PATH = SITE_DIR / "output.manifest.json"

RECEIPT_VERSION = "1"

# Tokens shorter than this are ignored.
MIN_TOKEN_LEN = 3

# Common structural words excluded from the token set.
STOP_WORDS = frozenset(
    {
        "the", "and", "for", "are", "but", "not", "you", "all", "can",
        "her", "was", "one", "our", "had", "his", "how", "its", "has",
        "any", "may", "use", "new", "two", "more", "also", "that", "this",
        "with", "from", "they", "will", "been", "each", "than", "when",
        "who", "now", "only", "into", "other", "some", "over", "such",
        "their", "there", "these", "those", "which", "where", "while",
        "both", "then", "than", "them", "what", "have", "must", "very",
        "after", "about", "every", "first", "would", "could", "should",
        "being", "before", "below", "above",
    }
)

_TAG_RE = re.compile(r"<[^>]+>")
_MD_CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_MD_INLINE_CODE_RE = re.compile(r"`[^`]+`")
_MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MD_HEADING_RE = re.compile(r"^#+\s*", re.MULTILINE)
_NON_WORD_RE = re.compile(r"[^\w]+")


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML document is not an object: {path}")
    return data


def write_canonical_json(data: object, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")


def validate_instance(instance: object, schema_path: Path) -> None:
    schema = load_json(schema_path)
    jsonschema.validate(instance=instance, schema=schema)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Tokenisation
# ---------------------------------------------------------------------------

def extract_tokens_from_markdown(text: str) -> frozenset:
    """Return the set of significant tokens from a markdown document."""
    # Remove fenced code blocks (preserve identifiers but not syntax)
    text = _MD_CODE_FENCE_RE.sub(" ", text)
    # Remove inline code
    text = _MD_INLINE_CODE_RE.sub(" ", text)
    # Keep link text, drop URL
    text = _MD_LINK_RE.sub(r"\1", text)
    # Remove heading markers
    text = _MD_HEADING_RE.sub(" ", text)
    return _tokenize(text)


def extract_tokens_from_html(text: str) -> frozenset:
    """Return the set of significant tokens from an HTML document."""
    text = _TAG_RE.sub(" ", text)
    return _tokenize(text)


def _tokenize(text: str) -> frozenset:
    parts = _NON_WORD_RE.split(text.lower())
    return frozenset(
        t for t in parts if len(t) >= MIN_TOKEN_LEN and t not in STOP_WORDS
    )


# ---------------------------------------------------------------------------
# Contract loading and validation
# ---------------------------------------------------------------------------

def load_and_validate_contract() -> dict:
    contract = load_yaml(CONTRACT_PATH)
    validate_instance(contract, CONTRACT_SCHEMA_PATH)
    return contract


# ---------------------------------------------------------------------------
# Mapping evaluation
# ---------------------------------------------------------------------------

def evaluate_mapping(mapping: dict) -> dict:
    source_rel = mapping["source"]
    target_rel = mapping["target"]
    allowlist = frozenset(t.lower() for t in mapping.get("allowlist", []))

    source_path = REPO_ROOT / source_rel
    target_path = REPO_ROOT / target_rel

    if not source_path.exists():
        return {
            "source": source_rel,
            "target": target_rel,
            "status": "FAIL",
            "missing_tokens": [f"<source file missing: {source_rel}>"],
        }

    if not target_path.exists():
        return {
            "source": source_rel,
            "target": target_rel,
            "status": "FAIL",
            "missing_tokens": [f"<target file missing: {target_rel}>"],
        }

    source_text = source_path.read_text(encoding="utf-8")
    target_text = target_path.read_text(encoding="utf-8")

    source_tokens = extract_tokens_from_markdown(source_text)
    target_tokens = extract_tokens_from_html(target_text)

    missing = sorted(source_tokens - target_tokens - allowlist)
    passed = len(missing) == 0

    result = {
        "source": source_rel,
        "target": target_rel,
        "status": "PASS" if passed else "FAIL",
    }
    if missing:
        result["missing_tokens"] = missing
    return result


# ---------------------------------------------------------------------------
# Manifest construction
# ---------------------------------------------------------------------------

def build_manifests(contract: dict) -> tuple[dict, dict]:
    input_entries = {}
    output_entries = {}

    for mapping in contract["mappings"]:
        src = REPO_ROOT / mapping["source"]
        tgt = REPO_ROOT / mapping["target"]
        if src.exists():
            input_entries[mapping["source"]] = sha256_file(src)
        if tgt.exists():
            output_entries[mapping["target"]] = sha256_file(tgt)

    return (
        {"version": RECEIPT_VERSION, "files": input_entries},
        {"version": RECEIPT_VERSION, "files": output_entries},
    )


# ---------------------------------------------------------------------------
# Main verification flow
# ---------------------------------------------------------------------------

def run_verify() -> int:
    try:
        contract = load_and_validate_contract()
    except jsonschema.ValidationError as exc:
        print(f"FAIL: contract schema validation error: {exc.message}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    mapping_results = [evaluate_mapping(m) for m in contract["mappings"]]
    overall = "PASS" if all(r["status"] == "PASS" for r in mapping_results) else "FAIL"

    receipt = {
        "version": RECEIPT_VERSION,
        "invariant_id": contract["id"],
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mappings": mapping_results,
    }

    try:
        validate_instance(receipt, RECEIPT_SCHEMA_PATH)
    except jsonschema.ValidationError as exc:
        print(f"FAIL: receipt schema validation error: {exc.message}", file=sys.stderr)
        return 1

    write_canonical_json(receipt, RECEIPT_PATH)
    print(f"Receipt written: {RECEIPT_PATH.relative_to(REPO_ROOT)}")

    input_manifest, output_manifest = build_manifests(contract)
    write_canonical_json(input_manifest, INPUT_MANIFEST_PATH)
    write_canonical_json(output_manifest, OUTPUT_MANIFEST_PATH)
    print(f"Manifests written.")

    for r in mapping_results:
        status = r["status"]
        print(f"  [{status}] {r['source']} -> {r['target']}")
        if r.get("missing_tokens"):
            for tok in r["missing_tokens"]:
                print(f"         missing: {tok}", file=sys.stderr)

    if overall == "FAIL":
        print(f"FAIL: one or more mappings did not pass.", file=sys.stderr)
        return 1

    print("PASS: all mappings verified.")
    return 0


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] != "verify":
        print(f"Usage: {sys.argv[0]} verify", file=sys.stderr)
        return 2
    try:
        return run_verify()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
