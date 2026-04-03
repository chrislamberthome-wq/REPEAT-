"""Ionic channel model for blood-analog (saline) experiments.

The model simulates the voltage response of an ionic medium excited by a
bounded pulse.  All parameters are intentionally simple so that the channel
is fully deterministic when seeded.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChannelParams:
    """Physical parameters describing one ionic channel configuration."""

    # Gaussian noise standard deviation on the received peak (mV)
    noise_std_mv: float = 5.0
    # Signal attenuation factor (0 < gain <= 1)
    gain: float = 0.85
    # Baseline receiver offset (mV)
    baseline_mv: float = 0.0
    # RC-like settling time multiplier (dimensionless)
    settle_factor: float = 0.8


def default_params() -> ChannelParams:
    """Return the default channel parameters for a saline baseline experiment."""
    return ChannelParams()


def params_for_trial(
    base: ChannelParams,
    trial_index: int,
    noise_schedule_mv: list[float] | None = None,
) -> ChannelParams:
    """Return a *new* :class:`ChannelParams` with noise adjusted for *trial_index*.

    Parameters
    ----------
    base:
        Base channel parameters to start from.
    trial_index:
        Zero-based index of the current trial.
    noise_schedule_mv:
        Optional list of noise standard deviation values (mV), one per trial.
        When *noise_schedule_mv* is provided the noise for *trial_index* is
        ``base.noise_std_mv + noise_schedule_mv[i]`` where *i* is clamped to
        the last element when *trial_index* exceeds the list length.
        When *None*, *base* is returned unchanged.
    """
    if noise_schedule_mv is None or len(noise_schedule_mv) == 0:
        return base

    idx = min(trial_index, len(noise_schedule_mv) - 1)
    delta = noise_schedule_mv[idx]
    return ChannelParams(
        noise_std_mv=max(0.0, base.noise_std_mv + delta),
        gain=base.gain,
        baseline_mv=base.baseline_mv,
        settle_factor=base.settle_factor,
    )


def simulate_symbol(
    tx_bit: int,
    pulse_voltage_v: float,
    pulse_width_ms: float,
    params: ChannelParams,
    rng: random.Random,
) -> dict[str, Any]:
    """Simulate one symbol transmission and return the raw measurements.

    Returns a dict with keys: ``rx_peak_mv``, ``rx_settle_ms``.
    """
    pulse_mv = pulse_voltage_v * 1000.0  # convert V → mV

    if tx_bit == 1:
        signal_mv = pulse_mv * params.gain
    else:
        signal_mv = 0.0

    noise = rng.gauss(0.0, params.noise_std_mv) if params.noise_std_mv > 0 else 0.0
    rx_peak_mv = params.baseline_mv + signal_mv + noise

    settle_ms = pulse_width_ms * params.settle_factor * rng.uniform(0.9, 1.1)

    return {
        "rx_peak_mv": round(rx_peak_mv, 4),
        "rx_settle_ms": round(settle_ms, 4),
    }
