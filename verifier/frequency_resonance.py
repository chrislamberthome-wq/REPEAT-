import math
import dataclasses
from typing import Any, Dict


@dataclasses.dataclass
class FrequencyResonanceResult:
    lf_f: float
    hf_f: float
    lf_r: float
    hf_r: float
    rho_f: float
    rho_r: float
    delta_rho: float
    c: float


def _compute_fr(obj: Dict[str, Any]) -> FrequencyResonanceResult:
    lf_f = float(obj["LF_F"])
    hf_f = float(obj["HF_F"])
    lf_r = float(obj["LF_R"])
    hf_r = float(obj["HF_R"])

    if hf_f == 0 or hf_r == 0:
        raise ValueError("HF_F and HF_R must be non-zero")

    rho_f = lf_f / hf_f
    rho_r = lf_r / hf_r
    delta_rho = rho_f - rho_r
    if rho_f + rho_r == 0:
        raise ValueError("rho_F + rho_R must be non-zero")
    c = (rho_f * rho_r) / (rho_f + rho_r)

    return FrequencyResonanceResult(
        lf_f=lf_f,
        hf_f=hf_f,
        lf_r=lf_r,
        hf_r=hf_r,
        rho_f=rho_f,
        rho_r=rho_r,
        delta_rho=delta_rho,
        c=c,
    )


def verify_frequency_resonance_obj(obj: Dict[str, Any]) -> Dict[str, Any]:
    fr = _compute_fr(obj)

    # Optional: if caller supplies signature fields, enforce they match recomputation
    sig = obj.get("signature")
    if isinstance(sig, dict) and "C" in sig:
        c_recv = float(sig["C"])
        if not math.isfinite(c_recv):
            raise ValueError("signature.C must be finite")
        if abs(c_recv - fr.c) > 1e-6:
            return {
                "verdict": "FAIL",
                "reason": "Provided signature.C does not match recomputed C",
                "signature_expected": {
                    "rho_F": fr.rho_f,
                    "rho_R": fr.rho_r,
                    "delta_rho": fr.delta_rho,
                    "C": fr.c,
                },
                "signature_received": sig,
                "raw": {"LF_F": fr.lf_f, "HF_F": fr.hf_f, "LF_R": fr.lf_r, "HF_R": fr.hf_r},
            }

    return {
        "verdict": "PASS",
        "signature": {
            "rho_F": fr.rho_f,
            "rho_R": fr.rho_r,
            "delta_rho": fr.delta_rho,
            "C": fr.c,
        },
        "raw": {"LF_F": fr.lf_f, "HF_F": fr.hf_f, "LF_R": fr.lf_r, "HF_R": fr.hf_r},
    }
