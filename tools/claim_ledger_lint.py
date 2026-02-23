#!/usr/bin/env python3
"""
Claim-ledger linter for REPEAT-bounded autotonomy governance.

Reads governance/claim_ledger.v1.jsonl and enforces:
- Every VERIFIED claim has at least one evidence reference.
- No claim is labeled VERIFIED without a file:/test:/receipt:/cite: ref.
- In --strict mode, any violation causes a non-zero exit (fail-closed).

Usage:
    python tools/claim_ledger_lint.py [--strict]
"""

import argparse
import json
import sys
from pathlib import Path

LEDGER_PATH = Path(__file__).parent.parent / "governance" / "claim_ledger.v1.jsonl"
EVIDENCE_PREFIXES = ("file:", "test:", "receipt:", "cite:")


def lint_ledger(path: Path, strict: bool) -> int:
    """
    Lint the claim ledger.

    Returns:
        0 -- PASS: no violations found and ledger is readable (or ledger absent in non-strict mode)
        1 -- FAIL: violations found, or ledger absent/unreadable in --strict mode (fail-closed)
    """
    if not path.exists():
        if strict:
            print(f"ERROR: ledger not found: {path}", file=sys.stderr)
            return 1
        print(f"WARNING: ledger not found: {path} (skipping)", file=sys.stderr)
        return 0

    violations = []
    line_num = 0

    with open(path, encoding="utf-8") as fh:
        for raw_line in fh:
            line_num += 1
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                entry = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                violations.append(f"line {line_num}: invalid JSON -- {exc}")
                continue

            label = entry.get("label", "").upper()
            if label != "VERIFIED":
                continue

            evidence = entry.get("evidence", [])
            if not isinstance(evidence, list):
                evidence = [evidence] if evidence else []

            has_ref = any(
                isinstance(e, str) and e.startswith(EVIDENCE_PREFIXES)
                for e in evidence
            )
            if not has_ref:
                claim_text = entry.get("claim", "<no claim text>")[:80]
                violations.append(
                    f"line {line_num}: VERIFIED claim lacks evidence ref -- \"{claim_text}\""
                )

    if violations:
        print(f"Claim-ledger lint FAILED ({len(violations)} violation(s)):", file=sys.stderr)
        for v in violations:
            print(f"  {v}", file=sys.stderr)
        return 1

    print(f"Claim-ledger lint PASSED -- {line_num} line(s) checked.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint the REPEAT claim ledger")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail with non-zero exit on any violation (fail-closed mode)",
    )
    args = parser.parse_args()
    return lint_ledger(LEDGER_PATH, strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())
