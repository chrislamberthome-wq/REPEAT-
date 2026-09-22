#!/usr/bin/env python3
"""Small, standalone Evidence Node V0.1 artifact tool.

This is not a REPEAT_CORE implementation or schema.  It captures exported
sensor samples, creates a hash-chained immutable artifact, and replays it
offline.  No network or device access is used by receipt/replay.
"""
import argparse
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_jsonl(path):
    with Path(path).open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def capture(args):
    source = read_jsonl(args.input)
    start, end = map(float, args.operator_mark.split(","))
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    previous = "0" * 64
    with out.open("w", encoding="utf-8", newline="\n") as fh:
        for sequence, sample in enumerate(source):
            try:
                record = {
                    "record_id": f"{args.device_id}:{sequence:08d}",
                    "device_id": args.device_id,
                    "config_id": args.config_id,
                    "sequence": sequence,
                    "observed_at": sample.get("observed_at", utc_now()),
                    "clock_status": "export-time-only" if "observed_at" not in sample else "provided",
                    "input": {"id": "adxl345", "kind": "vibration", "unit": "m/s^2",
                              "x": float(sample["x"]), "y": float(sample["y"]), "z": float(sample["z"])},
                    "quality": "valid",
                    "operator_event": "stimulus" if start <= float(sequence) / args.rate < end else None,
                    "previous_digest": previous,
                }
            except (KeyError, TypeError, ValueError) as exc:
                record = {"sequence": sequence, "quality": "invalid", "error": str(exc),
                          "previous_digest": previous}
            record["record_digest"] = digest(record)
            previous = record["record_digest"]
            fh.write(canonical(record) + "\n")
    print(str(out))


def verify_chain(records):
    previous = "0" * 64
    reasons = []
    for expected, record in enumerate(records):
        saved = record.get("record_digest")
        body = dict(record)
        body.pop("record_digest", None)
        if record.get("sequence") != expected or record.get("previous_digest") != previous:
            reasons.append("sequence or hash-chain discontinuity")
        if saved != digest(body):
            reasons.append(f"record {expected} digest mismatch")
        previous = saved or ""
    return reasons, previous


def inspect(records, stimulus):
    start, end = stimulus
    baseline, active, recovery = [], [], []
    reasons = []
    for record in records:
        if record.get("quality") != "valid" or "input" not in record:
            reasons.append("invalid or incomplete sample")
            continue
        v = record["input"]
        magnitude = math.sqrt(sum(float(v[k]) ** 2 for k in ("x", "y", "z")))
        # Remove the static gravity component for a simple vibration measure.
        value = magnitude - 9.80665
        t = record["sequence"] / 100.0
        (active if start <= t < end else baseline if t < start else recovery).append(value)
    def rms(values):
        return math.sqrt(sum(x * x for x in values) / len(values)) if values else None
    b, a, r = rms(baseline), rms(active), rms(recovery)
    if min((len(baseline), len(active), len(recovery)), default=0) < 100:
        return "UNRESOLVED", reasons + ["fewer than 100 samples in one required window"], (b, a, r)
    if any(x is None for x in (b, a, r)):
        return "UNRESOLVED", reasons + ["missing measurement window"], (b, a, r)
    if reasons:
        return "UNRESOLVED", reasons, (b, a, r)
    passed = b <= 0.50 and r <= 0.50 and a >= 1.00 and a >= 2 * max(b, r)
    return ("PASS" if passed else "FAIL"), (["threshold not met"] if not passed else []), (b, a, r)


def artifact_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def receipt(args):
    records = read_jsonl(args.observations)
    chain_reasons, tip = verify_chain(records)
    result, reasons, metrics = inspect(records, tuple(map(float, args.stimulus.split(","))))
    payload = {"schema": "evidence-node-v0.1-prototype",
               "device_id": records[0].get("device_id") if records else None,
               "config_id": records[0].get("config_id") if records else None,
               "artifact": {"path": Path(args.observations).name, "sha256": artifact_sha(args.observations),
                            "records": len(records), "chain_tip": tip},
               "inspection": {"result": result, "reasons": chain_reasons + reasons,
                              "baseline_rms": metrics[0], "stimulus_rms": metrics[1], "recovery_rms": metrics[2],
                              "stimulus_seconds": args.stimulus},
               "created_at": utc_now()}
    Path(args.output).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(result)


def replay(args):
    receipt = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    records = read_jsonl(args.observations)
    reasons, tip = verify_chain(records)
    if artifact_sha(args.observations) != receipt["artifact"]["sha256"]:
        reasons.append("artifact SHA-256 mismatch")
    if tip != receipt["artifact"]["chain_tip"]:
        reasons.append("chain tip mismatch")
    result, inspection_reasons, metrics = inspect(records, tuple(map(float, receipt["inspection"]["stimulus_seconds"].split(","))))
    reasons += inspection_reasons
    if reasons and result == "PASS":
        result = "UNRESOLVED"
    print(json.dumps({"result": result, "reasons": reasons, "metrics": metrics}, indent=2))
    return 0 if result == "PASS" else 2


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("capture"); p.add_argument("--input", required=True); p.add_argument("--output", required=True); p.add_argument("--device-id", required=True); p.add_argument("--config-id", required=True); p.add_argument("--operator-mark", required=True); p.add_argument("--rate", type=float, default=100.0); p.set_defaults(fn=capture)
    p = sub.add_parser("receipt"); p.add_argument("--observations", required=True); p.add_argument("--output", required=True); p.add_argument("--stimulus", required=True); p.set_defaults(fn=receipt)
    p = sub.add_parser("replay"); p.add_argument("--observations", required=True); p.add_argument("--receipt", required=True); p.set_defaults(fn=replay)
    args = parser.parse_args(); result = args.fn(args); return result if isinstance(result, int) else 0

if __name__ == "__main__":
    sys.exit(main())
