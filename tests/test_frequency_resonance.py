import pytest
from verifier.frequency_resonance import verify_frequency_resonance_obj


def test_fail_if_signature_c_mismatch():
    out = verify_frequency_resonance_obj({
        "LF_F": 2.0, "HF_F": 1.0, "LF_R": 3.0, "HF_R": 2.0,
        "signature": {"C": 0.774}
    })
    assert out["verdict"] == "FAIL"
