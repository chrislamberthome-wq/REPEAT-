"""Convenience entry-point for verify_run: ``python verify_run.py <trace.jsonl>``."""
from __future__ import annotations

import sys
from blood_ion_repeat.verifier import main

if __name__ == "__main__":
    sys.exit(main())
