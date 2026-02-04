#!/usr/bin/env python3
"""
Gift Log Verifier (Gift Processing QA) — Single File

Reads a gift log CSV and runs practical gift-processing QA checks.
Writes a Markdown QA report and returns CI-friendly exit codes.

Exit codes:
  0 = PASS
  1 = FAIL (issues found)
  2 = ERROR (runtime / file / schema error)

Usage:
  python3 repeat_devops_gift_processing/verify_giftlog.py \
    --input repeat_devops_gift_processing/giftlog_sample.csv \
    --report repeat_devops_gift_processing/report.md

Optional:
  --strict  # treat medium/low issues as FAIL (default: only high issues fail)
  --no-normalization-note  # suppress low-severity notes about gift_id normalization
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


# -------------------------
# Configuration / Rules
# -------------------------

# Gift ID format: uppercase G + exactly 5 digits (e.g., G12345)
GIFT_ID_RE = re.compile(r"^G\d{5}$")

# Whitespace anywhere (spaces/tabs/newlines/non-breaking)
WS_RE = re.compile(r"\s+")

REQUIRED_FIELDS = [
    "gift_id",
    "received_date",
    "amount",
    "currency",
    "donor_name",
    "designation",
    "source_channel",
    "entered_by",
]

ALLOWED_SOURCE_CHANNEL = {"online", "mail", "event", "wire", "ach", "stock", "other"}
ALLOWED_ACK_STATUS = {"pending", "sent", "n/a", ""}  # allow blank
ALLOWED_RECON_STATUS = {"pending", "pass", "fail", ""}  # allow blank


# -------------------------
# Data Structures
# -------------------------

dataclass
class Issue:
    gift_id: str
    field: str
    rule: str
    severity: str  # low / medium / high
    details: str


# -------------------------
# Helpers
# -------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify giftlog CSV for gift processing QA.")
    p.add_argument("--input", required=True, help="Path to input giftlog CSV")
    p.add_argument("--report", required=True, help="Path to output markdown report")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any issue (low/medium/high). Default: only high issues fail.",
    )
    p.add_argument(
        "--no-normalization-note",
        action="store_true",
        help="Do not emit a low-severity 'normalized_gift_id' issue when input is cleaned.",
    )
    return p.parse_args()


def read_csv(path: str) -> Tuple[List[Dict[str, str]], List[str]]:
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames

