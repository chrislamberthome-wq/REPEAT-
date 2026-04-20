#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"

POLICY_CONTRACT_PATH = SITE_DIR / "policy.contract.yaml"
POLICY_CONTRACT_SCHEMA_PATH = SITE_DIR / "policy.contract.schema.json"
POLICY_REPORT_PATH = SITE_DIR / "policy.report.json"
POLICY_REPORT_SCHEMA_PATH = SITE_DIR / "policy.report.schema.json"

REQUIRED_ARTIFACTS = [
    SITE_DIR / "receipt.json",
    SITE_DIR / "input.manifest.json",
    SITE_DIR / "output.manifest.json",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8", newline="") as f:
        return json.load(f)


def load_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8", newline="") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"YAML document is not an object: {path}")
    return data


def write_canonical_json(data: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        f.write("\n")


def validate_instance(instance: dict, schema_path: Path) -> None:
    schema = load_json(schema_path)
    jsonschema.validate(instance=instance, schema=schema)


def git_stdout(args: list[str]) -> str:
    return subprocess.check_output(
        args,
        cwd=REPO_ROOT,
        text=True,
        stderr=subprocess.DEVNULL,
    ).strip()


def load_and_validate_policy_contract() -> dict:
    contract = load_yaml(POLICY_CONTRACT_PATH)
    validate_instance(contract, POLICY_CONTRACT_SCHEMA_PATH)
    return contract


def resolve_head_tags() -> list[str]:
    out = git_stdout(["git", "tag", "--points-at", "HEAD"])
    if not out:
        return []
    tags = [line.strip() for line in out.splitlines() if line.strip()]
    tags.sort()
    return tags


def evaluate_site_pol_01() -> dict:
    tags = resolve_head_tags()
    if len(tags) != 1:
        return {
            "id": "SITE-POL-01",
            "passed": False,
            "details": f"Expected exactly one tag at HEAD; found {len(tags)}: {tags}",
        }

    tag = tags[0]
    objtype = git_stdout(["git", "tag", "-l", "--format=%(objecttype)", tag])

    passed = objtype == "tag"
    details = (
        f"Tag {tag} is annotated."
        if passed
        else f"Tag {tag} is not annotated (objecttype={objtype!r})."
    )

    return {
        "id": "SITE-POL-01",
        "passed": passed,
        "details": details,
    }


def evaluate_site_pol_03() -> dict:
    out = git_stdout(["git", "status", "--porcelain"])
    passed = out == ""
    details = (
        "Working tree is clean."
        if passed
        else "Working tree is not clean."
    )
    return {
        "id": "SITE-POL-03",
        "passed": passed,
        "details": details,
    }


def evaluate_site_pol_04() -> dict:
    missing = [str(p.relative_to(REPO_ROOT)) for p in REQUIRED_ARTIFACTS if not p.exists()]
    passed = len(missing) == 0
    details = (
        "Required release artifacts are present."
        if passed
        else "Missing required release artifacts: " + ", ".join(missing)
    )
    return {
        "id": "SITE-POL-04",
        "passed": passed,
        "details": details,
    }


def evaluate_policy(policy_id: str) -> dict:
    if policy_id == "SITE-POL-01":
        return evaluate_site_pol_01()
    if policy_id == "SITE-POL-03":
        return evaluate_site_pol_03()
    if policy_id == "SITE-POL-04":
        return evaluate_site_pol_04()

    return {
        "id": policy_id,
        "passed": False,
        "details": f"Unknown policy id: {policy_id}",
    }


def build_policy_report(contract: dict) -> dict:
    policy_results = []
    failed_required = []

    for policy in contract["policies"]:
        result = evaluate_policy(policy["id"])
        policy_results.append(result)

        if policy["level"] == "required" and not result["passed"]:
            failed_required.append(policy["id"])

    report = {
        "report_version": contract["version"],
        "policies": policy_results,
    }

    validate_instance(report, POLICY_REPORT_SCHEMA_PATH)
    write_canonical_json(report, POLICY_REPORT_PATH)

    if failed_required:
        raise RuntimeError(
            "Required policy failure(s): " + ", ".join(failed_required)
        )

    return report


def main() -> int:
    try:
        contract = load_and_validate_policy_contract()
        build_policy_report(contract)
        return 0
    except jsonschema.ValidationError as exc:
        print(f"FAIL: schema validation error: {exc.message}", file=sys.stderr)
        return 1
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
