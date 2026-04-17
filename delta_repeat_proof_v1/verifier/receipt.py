"""Receipt loader and verifier."""
import hashlib
import json
import pathlib
from typing import Any, Dict, List, Tuple


def _file_sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return "sha256:" + digest


def verify_receipt(
    events: List[Dict[str, Any]],  # noqa: ARG001  (reserved for future checks)
    base: pathlib.Path,
) -> Tuple[bool, str]:
    """Return ``(True, 'ok')`` when the receipt is valid, ``(False, reason)`` otherwise."""
    receipt_path = base / "receipt" / "receipt.json"
    try:
        with open(receipt_path, encoding="utf-8") as fh:
            receipt = json.load(fh)
    except Exception as exc:  # noqa: BLE001
        return False, f"cannot load receipt.json: {exc}"

    if receipt.get("status") != "PASS":
        return False, f"receipt status is {receipt.get('status')!r}"

    trace_path = base / "trace" / "trace.jsonl"
    actual_hash = _file_sha256(trace_path)
    stored_hash = receipt.get("trace_sha256", "")
    if actual_hash != stored_hash:
        return False, (
            f"trace_sha256 mismatch: receipt={stored_hash!r} actual={actual_hash!r}"
        )

    return True, "ok"
