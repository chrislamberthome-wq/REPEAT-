"""Entry point for `python -m verifier`.

Usage:
    python -m verifier <receipts.jsonl>

Exit codes:
    0 - All receipts passed integrity checks (PASS)
    1 - Error (missing file, parse error, unexpected exception)
    2 - Verification failed (schema or hash check failed)
"""
import argparse
import sys

from verifier.mram_receipts import VerificationError, verify_receipts_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify MRAM receipt JSONL files for schema compliance and hash integrity."
    )
    parser.add_argument("receipts_file", help="Path to JSONL receipts file")
    args = parser.parse_args()

    try:
        result = verify_receipts_file(args.receipts_file)
        if result.passed:
            print(f"PASS: {result.count} receipts verified")
            sys.exit(0)
        else:
            print(f"FAIL: {result.message}", file=sys.stderr)
            sys.exit(2)
    except VerificationError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
