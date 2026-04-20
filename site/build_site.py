#!/usr/bin/env python3
"""
Build site HTML from markdown source documents.

Reads the mappings declared in site/invariants.contract.yaml and converts
each source document to its target HTML file using the Python markdown
library. Requires: pip install markdown pyyaml
"""

import sys
from pathlib import Path

import yaml

try:
    import markdown as _markdown_lib

    def _md_to_html(text: str) -> str:
        return _markdown_lib.markdown(
            text, extensions=["fenced_code", "tables", "toc"]
        )

except ImportError:
    import re

    _TAG_CHARS_RE = re.compile(r"[<>&]")
    _ENTITY_MAP = {"<": "&lt;", ">": "&gt;", "&": "&amp;"}

    def _md_to_html(text: str) -> str:  # type: ignore[misc]
        escaped = _TAG_CHARS_RE.sub(lambda m: _ENTITY_MAP[m.group()], text)
        return f"<pre>{escaped}</pre>"


REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = REPO_ROOT / "site"
CONTRACT_PATH = SITE_DIR / "invariants.contract.yaml"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""


def load_contract() -> dict:
    with CONTRACT_PATH.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Contract YAML is not an object.")
    return data


def build_page(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    content = source.read_text(encoding="utf-8")
    title = source.stem.replace("-", " ").replace("_", " ").title()
    body = _md_to_html(content)
    html = HTML_TEMPLATE.format(title=title, body=body)
    target.write_text(html, encoding="utf-8", newline="\n")
    print(f"  built: {source.relative_to(REPO_ROOT)} -> {target.relative_to(REPO_ROOT)}")


def main() -> int:
    try:
        contract = load_contract()
    except Exception as exc:
        print(f"ERROR loading contract: {exc}", file=sys.stderr)
        return 2

    for mapping in contract.get("mappings", []):
        source = REPO_ROOT / mapping["source"]
        target = REPO_ROOT / mapping["target"]
        if not source.exists():
            print(f"WARN: source not found, skipping: {mapping['source']}", file=sys.stderr)
            continue
        build_page(source, target)

    return 0


if __name__ == "__main__":
    sys.exit(main())
