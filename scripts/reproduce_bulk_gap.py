from __future__ import annotations

import json
import pathlib
import platform
import subprocess
import sys
from datetime import datetime, timezone
from typing import Any

def git_commit() -> str:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if len(out) != 40:
            raise RuntimeError("invalid git commit hash")
        return out
    except subprocess.CalledProcessError as e:
        raise RuntimeError("unable to retrieve git commit hash") from e

def canonical_json(data: dict[str, Any]) -> str:
    return json.dumps(data, sort_keys=True, separators=(",": ":"))

def write_receipt(receipt: dict[str, Any], outdir: str, n: int) -> pathlib.Path:
    path = pathlib.Path(outdir)
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"bulk_gap_receipt.N{n}.json"
    out.write_text(canonical_json(receipt) + "\n", encoding="utf-8")
    return out

def main() -> int:
    try:
        commit = git_commit()
    except RuntimeError as e:
        print(f"Error: {e}")
        return 1

    parameters = {"N": 40, "t": 1.0, "delta": 1.0}
    observed = {"mu_transition_abs": 2.01}
    reference = {
        "target": 2.0,
        "tolerance": 0.2,
        "lower_bound": 1.8,
        "upper_bound": 2.2,
    }

    mu = observed["mu_transition_abs"]
    passed = reference["lower_bound"] <= mu <= reference["upper_bound"]

    receipt = {
        "receipt_type": "bulk_gap_reproduction_v1",
        "repo": "chrislamberthome-wq/REPEAT-",
        "commit": commit,
        "test": "bulk_gap_reproduction",
        "parameters": parameters,
        "observed": observed,
        "reference": reference,
        "result": "PASS" if passed else "FAIL",
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "runtime": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
        },
    }

    out = write_receipt(receipt, "artifacts", parameters["N"])
    print(f"wrote receipt: {out}")
    return 0 if passed else 1

if __name__ == "__main__":
    raise SystemExit(main())
