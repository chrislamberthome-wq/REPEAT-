"""Threshold management for ionic channel symbol decoding."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThresholdConfig:
    """Pre-registered decoding threshold for a single experiment run."""

    threshold_mv: float
    baseline_mv: float
    drift_limit_mv: float = 5.0

    def decode(self, rx_peak_mv: float) -> int:
        """Return the decoded bit for a received peak voltage."""
        return 1 if rx_peak_mv >= self.threshold_mv else 0

    def baseline_ok(self, measured_baseline_mv: float) -> bool:
        """Return True when baseline drift is within the registered limit."""
        return abs(measured_baseline_mv - self.baseline_mv) <= self.drift_limit_mv
