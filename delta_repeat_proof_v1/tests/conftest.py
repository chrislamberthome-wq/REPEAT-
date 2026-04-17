"""pytest configuration for delta_repeat_proof_v1 tests.

Adds the artifact root to sys.path so ``verifier`` is importable without
installation.
"""
import pathlib
import sys

# Ensure delta_repeat_proof_v1/ is on sys.path (parent of tests/)
_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
