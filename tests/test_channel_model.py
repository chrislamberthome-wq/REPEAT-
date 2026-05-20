"""Tests for blood_ion_repeat.channel_model, including params_for_trial."""
from __future__ import annotations

import random

import pytest

from blood_ion_repeat.channel_model import (
    ChannelParams,
    default_params,
    params_for_trial,
    simulate_symbol,
)


class TestDefaultParams:
    def test_returns_channel_params(self):
        p = default_params()
        assert isinstance(p, ChannelParams)

    def test_default_noise_positive(self):
        p = default_params()
        assert p.noise_std_mv > 0

    def test_default_gain_in_range(self):
        p = default_params()
        assert 0 < p.gain <= 1


class TestParamsForTrial:
    def test_no_schedule_returns_base(self):
        base = default_params()
        result = params_for_trial(base, trial_index=0, noise_schedule_mv=None)
        assert result is base

    def test_empty_schedule_returns_base(self):
        base = default_params()
        result = params_for_trial(base, trial_index=0, noise_schedule_mv=[])
        assert result is base

    def test_noise_increased_by_positive_delta(self):
        base = ChannelParams(noise_std_mv=5.0)
        result = params_for_trial(base, trial_index=0, noise_schedule_mv=[3.0])
        assert result.noise_std_mv == pytest.approx(8.0)

    def test_noise_decreased_by_negative_delta(self):
        base = ChannelParams(noise_std_mv=5.0)
        result = params_for_trial(base, trial_index=0, noise_schedule_mv=[-4.0])
        assert result.noise_std_mv == pytest.approx(1.0)

    def test_noise_floor_is_zero(self):
        """Noise cannot go below 0 even with a large negative delta."""
        base = ChannelParams(noise_std_mv=2.0)
        result = params_for_trial(base, trial_index=0, noise_schedule_mv=[-100.0])
        assert result.noise_std_mv == 0.0

    def test_per_trial_different_values(self):
        base = ChannelParams(noise_std_mv=5.0)
        schedule = [0.0, -10.0, -30.0]
        r0 = params_for_trial(base, 0, schedule)
        r1 = params_for_trial(base, 1, schedule)
        r2 = params_for_trial(base, 2, schedule)
        assert r0.noise_std_mv == pytest.approx(5.0)
        assert r1.noise_std_mv == pytest.approx(0.0)  # 5 - 10 clamped at 0? No: 5+(-10) = -5 → 0
        assert r2.noise_std_mv == pytest.approx(0.0)

    def test_index_clamped_to_last(self):
        """When trial_index exceeds schedule length, last entry is used."""
        base = ChannelParams(noise_std_mv=5.0)
        schedule = [1.0, 2.0]
        result_out_of_bounds = params_for_trial(base, trial_index=99, noise_schedule_mv=schedule)
        result_last = params_for_trial(base, trial_index=1, noise_schedule_mv=schedule)
        assert result_out_of_bounds.noise_std_mv == result_last.noise_std_mv

    def test_other_params_unchanged(self):
        base = ChannelParams(noise_std_mv=5.0, gain=0.7, baseline_mv=2.0, settle_factor=0.6)
        result = params_for_trial(base, 0, [1.0])
        assert result.gain == pytest.approx(0.7)
        assert result.baseline_mv == pytest.approx(2.0)
        assert result.settle_factor == pytest.approx(0.6)

    def test_returns_new_instance(self):
        base = ChannelParams(noise_std_mv=5.0)
        result = params_for_trial(base, 0, [1.0])
        assert result is not base


class TestSimulateSymbol:
    def test_bit1_produces_positive_peak(self):
        """A '1' bit with no noise should produce a positive peak."""
        params = ChannelParams(noise_std_mv=0.0, gain=0.85, baseline_mv=0.0)
        rng = random.Random(42)
        result = simulate_symbol(1, pulse_voltage_v=0.2, pulse_width_ms=100, params=params, rng=rng)
        assert result["rx_peak_mv"] > 0

    def test_bit0_produces_near_zero(self):
        """A '0' bit with no noise should produce ~0 peak."""
        params = ChannelParams(noise_std_mv=0.0, gain=0.85, baseline_mv=0.0)
        rng = random.Random(42)
        result = simulate_symbol(0, pulse_voltage_v=0.2, pulse_width_ms=100, params=params, rng=rng)
        assert abs(result["rx_peak_mv"]) < 0.001

    def test_deterministic_with_seeded_rng(self):
        params = default_params()
        r1 = simulate_symbol(1, 0.2, 100, params, random.Random(7))
        r2 = simulate_symbol(1, 0.2, 100, params, random.Random(7))
        assert r1 == r2

    def test_result_keys(self):
        params = default_params()
        result = simulate_symbol(1, 0.2, 100, params, random.Random(0))
        assert "rx_peak_mv" in result
        assert "rx_settle_ms" in result
