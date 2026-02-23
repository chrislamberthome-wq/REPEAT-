"""
REPEAT receipt verifier package.

Run as: python -m verifier <receipts.jsonl>

Exit codes:
  0 = all receipts valid
  1 = validation failure (schema violation, hash mismatch, or failed verdict)
  2 = runtime error (file not found, JSON parse error, etc.)
"""
