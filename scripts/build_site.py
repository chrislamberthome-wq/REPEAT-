#!/usr/bin/env python3
"""
REPEAT site projection build script.

Reads the projection contract from site/projection.contract.yaml, converts each
markdown source file into HTML using site/templates/base.html, writes outputs to
the stable paths declared in the contract, then emits site/receipt.json containing
SHA-256 digests for every source and rendered file together with PASS/FAIL status
for each mapping.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import markdown
import yaml


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
CONTRACT_PATH = REPO_ROOT / "site" / "projection.contract.yaml"
TEMPLATE_PATH = REPO_ROOT / "site" / "templates" / "base.html"
RECEIPT_PATH = REPO_ROOT / "site" / "receipt.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sha256_of_file(path: Path) -> str:
    """Return the lowercase hex SHA-256 digest of the file at *path*."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def markdown_to_html(md_text: str) -> str:
    """Convert *md_text* to an HTML fragment (no outer <html> wrapper)."""
    return markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code"],
    )


def first_heading(md_text: str) -> str:
    """Extract the first ATX heading from *md_text*, or return 'REPEAT'."""
    match = re.search(r"^#{1,6}\s+(.+)$", md_text, re.MULTILINE)
    return match.group(1).strip() if match else "REPEAT"


def build_breadcrumb(title: str, is_home: bool, base_path: str) -> str:
    """Return an HTML breadcrumb string for the page."""
    home_link = f'<a href="{base_path}/index.html">Home</a>'
    if is_home:
        return f"{home_link}"
    return f"{home_link}<span>›</span>{title}"


def render_page(md_source: Path, output_path: Path, template: str) -> None:
    """Render a single markdown source file into HTML at *output_path*."""
    md_text = md_source.read_text(encoding="utf-8")
    title = first_heading(md_text)
    content_html = markdown_to_html(md_text)
    is_home = output_path.name == "index.html"

    # Compute relative base path from the output file to the site/build root.
    # site/build/index.html          → base_path = "."
    # site/build/docs/anything.html  → base_path = ".."
    build_root = output_path.parent
    while build_root.name != "build":
        build_root = build_root.parent
    try:
        rel = output_path.parent.relative_to(build_root)
        depth = len(rel.parts)
    except ValueError:
        depth = 0
    base_path = "/".join([".."] * depth) if depth else "."

    breadcrumb = build_breadcrumb(title, is_home, base_path)

    html = (
        template
        .replace("{{title}}", title)
        .replace("{{base_path}}", base_path)
        .replace("{{breadcrumb}}", breadcrumb)
        .replace("{{content}}", content_html)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")


def verify_token_subset(source_path: Path, rendered_path: Path, allowlist: list) -> bool:
    """
    Verify that every semantic content token from the source markdown appears in
    the rendered HTML.  Structural markdown elements that do not translate to HTML
    text content are excluded from the source token set before comparison:

    - Fenced code-block language identifiers (e.g. ```bash)
    - Ordered-list number prefixes (e.g. "1. ", "3. ") which become implicit
      counter-generated content in <ol> tags, not literal text nodes.

    Tokens from the allowlist (navigation chrome) are also excluded from both
    sets to avoid false failures caused by stable wrappers added during rendering.
    """
    src_text = source_path.read_text(encoding="utf-8").lower()
    rendered_text = rendered_path.read_text(encoding="utf-8").lower()

    # Remove fenced code-block language identifiers (```python, ```bash, etc.)
    # These become class="language-xxx" attributes in the HTML, not visible text.
    src_text = re.sub(r"```[a-z0-9_+-]+", "```", src_text)

    # Remove ordered-list number prefixes at the start of a line (e.g. "1. ", "42. ")
    # HTML <ol><li> elements generate the numbers as CSS counters, not text nodes.
    src_text = re.sub(r"^\d+\.\s+", "", src_text, flags=re.MULTILINE)

    # Strip HTML tags from rendered output for token comparison (text nodes only)
    stripped = re.sub(r"<[^>]+>", " ", rendered_text)

    # Tokenise: only alphanumeric runs
    def tokenise(text: str) -> set:
        tokens = set(re.findall(r"[a-z0-9]+", text))
        for item in allowlist:
            tokens.discard(item.lower())
        return tokens

    src_tokens = tokenise(src_text)
    rendered_tokens = tokenise(stripped)

    missing = src_tokens - rendered_tokens
    if missing:
        # Report the first few missing tokens to aid debugging without being noisy
        sample = sorted(missing)[:10]
        print(f"  [WARN] token_subset: {len(missing)} source token(s) not found in "
              f"rendered output. Sample: {sample}", file=sys.stderr)
        return False
    return True


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    # Load contract
    if not CONTRACT_PATH.exists():
        print(f"ERROR: contract not found at {CONTRACT_PATH}", file=sys.stderr)
        return 1

    with open(CONTRACT_PATH, encoding="utf-8") as fh:
        contract = yaml.safe_load(fh)

    mappings = contract.get("traceability", {}).get("mappings", [])
    if not mappings:
        print("ERROR: no mappings found in contract", file=sys.stderr)
        return 1

    # Load template
    if not TEMPLATE_PATH.exists():
        print(f"ERROR: template not found at {TEMPLATE_PATH}", file=sys.stderr)
        return 1

    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    receipt_entries = []
    overall_pass = True

    for mapping in mappings:
        source_rel = mapping["source"]
        rendered_rel = mapping["rendered"]
        allowlist = mapping.get("allowlist", [])

        source_path = REPO_ROOT / source_rel
        rendered_path = REPO_ROOT / rendered_rel

        print(f"Building: {source_rel} → {rendered_rel}")

        # Check source exists
        if not source_path.exists():
            print(f"  ERROR: source file missing: {source_path}", file=sys.stderr)
            receipt_entries.append({
                "invariant_id": mapping.get("invariant_id"),
                "source": source_rel,
                "rendered": rendered_rel,
                "source_sha256": None,
                "rendered_sha256": None,
                "status": "FAIL",
                "reason": "source file missing",
            })
            overall_pass = False
            continue

        # Render
        render_page(source_path, rendered_path, template)

        # Hash both files
        source_sha = sha256_of_file(source_path)
        rendered_sha = sha256_of_file(rendered_path)

        # Verify token subset invariant
        status_ok = verify_token_subset(source_path, rendered_path, allowlist)
        status = "PASS" if status_ok else "FAIL"
        if not status_ok:
            overall_pass = False

        print(f"  {status}  source={source_sha[:16]}…  rendered={rendered_sha[:16]}…")

        receipt_entries.append({
            "invariant_id": mapping.get("invariant_id"),
            "source": source_rel,
            "source_sha256": source_sha,
            "rendered": rendered_rel,
            "rendered_sha256": rendered_sha,
            "status": status,
        })

    # Emit receipt
    receipt = {
        "contract_id": contract.get("contract_id"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "PASS" if overall_pass else "FAIL",
        "mappings": receipt_entries,
    }

    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RECEIPT_PATH, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, indent=2)
        fh.write("\n")

    print(f"\nReceipt written to {RECEIPT_PATH}")
    print(f"Overall status: {receipt['overall_status']}")

    return 0 if overall_pass else 1


if __name__ == "__main__":
    sys.exit(main())
