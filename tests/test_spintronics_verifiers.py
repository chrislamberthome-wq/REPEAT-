"""Tests for spintronics verifier modules."""

import pytest
import json
import os
from spintronics.verifiers import (
    verify_spin_configuration,
    verify_state_survival,
    compute_nearest_neighbor_energy,
    verify_trace_integrity,
    verify_pulse_sequence,
    compute_trace_checksum,
    verify_mram_write_read,
    verify_threshold_parameters,
    decode_resistance_to_bit,
)


class TestVerifySpinConfiguration:
    """Tests for spin configuration verification."""
    
    def test_valid_packet(self):
        """Test verification of valid spin packet."""
        packet = {
            "schema_version": "state_survival_macrospin_v1",
            "spin_configuration": {
                "lattice_size": {"x": 2, "y": 2},
                "spins": [0, 1, 1, 0]
            },
            "nearest_neighbors": {
                "interaction_strength": -1.0,
                "boundary_conditions": "periodic"
            }
        }
        is_valid, errors = verify_spin_configuration(packet)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_schema(self):
        """Test rejection of wrong schema version."""
        packet = {
            "schema_version": "wrong_version",
            "spin_configuration": {
                "lattice_size": {"x": 2, "y": 2},
                "spins": [0, 1, 1, 0]
            }
        }
        is_valid, errors = verify_spin_configuration(packet)
        assert is_valid is False
        assert any("schema" in e.lower() for e in errors)
    
    def test_spin_count_mismatch(self):
        """Test detection of wrong spin count."""
        packet = {
            "schema_version": "state_survival_macrospin_v1",
            "spin_configuration": {
                "lattice_size": {"x": 2, "y": 2},
                "spins": [0, 1, 1]  # Should be 4 spins
            },
            "nearest_neighbors": {
                "interaction_strength": -1.0,
                "boundary_conditions": "periodic"
            }
        }
        is_valid, errors = verify_spin_configuration(packet)
        assert is_valid is False
        assert any("mismatch" in e.lower() for e in errors)


class TestComputeNearestNeighborEnergy:
    """Tests for energy computation."""
    
    def test_ferromagnetic_aligned(self):
        """Test energy of aligned ferromagnetic spins."""
        spins = [1, 1, 1, 1]  # All up
        energy = compute_nearest_neighbor_energy(
            spins, (2, 2), -1.0, "periodic"
        )
        # All aligned with J=-1.0 should give negative energy
        assert energy < 0
    
    def test_antiferromagnetic_checkerboard(self):
        """Test checkerboard pattern."""
        spins = [0, 1, 1, 0]  # Checkerboard
        energy = compute_nearest_neighbor_energy(
            spins, (2, 2), -1.0, "periodic"
        )
        # Checkerboard with ferromagnetic J=-1.0 gives positive energy
        assert energy > 0


class TestVerifyPulseSequence:
    """Tests for pulse sequence verification."""
    
    def test_valid_sequence(self):
        """Test verification of valid pulse sequence."""
        pulses = [
            {"index": 0, "amplitude": 1.5, "duration": 10.0, "pulse_type": "write"},
            {"index": 1, "amplitude": 0.5, "duration": 5.0, "pulse_type": "read"}
        ]
        is_valid, errors = verify_pulse_sequence(pulses)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_missing_field(self):
        """Test detection of missing required field."""
        pulses = [
            {"index": 0, "amplitude": 1.5, "duration": 10.0}  # Missing pulse_type
        ]
        is_valid, errors = verify_pulse_sequence(pulses)
        assert is_valid is False
        assert any("pulse_type" in e.lower() for e in errors)
    
    def test_invalid_pulse_type(self):
        """Test rejection of invalid pulse type."""
        pulses = [
            {"index": 0, "amplitude": 1.5, "duration": 10.0, "pulse_type": "invalid"}
        ]
        is_valid, errors = verify_pulse_sequence(pulses)
        assert is_valid is False


class TestComputeTraceChecksum:
    """Tests for trace checksum computation."""
    
    def test_sha256_checksum(self):
        """Test SHA-256 checksum computation."""
        pulses = [{"index": 0, "amplitude": 1.0}]
        checksum = compute_trace_checksum(pulses, 'sha256')
        assert len(checksum) == 64
    
    def test_deterministic(self):
        """Test checksum is deterministic."""
        pulses = [{"index": 0, "amplitude": 1.0}]
        checksum1 = compute_trace_checksum(pulses, 'sha256')
        checksum2 = compute_trace_checksum(pulses, 'sha256')
        assert checksum1 == checksum2


class TestDecodeResistanceToBit:
    """Tests for resistance decoding."""
    
    def test_low_resistance_decode(self):
        """Test decoding of low resistance (bit 0)."""
        bit, valid = decode_resistance_to_bit(1500.0, 2000.0, 5000.0)
        assert bit == 0
        assert valid is True
    
    def test_high_resistance_decode(self):
        """Test decoding of high resistance (bit 1)."""
        bit, valid = decode_resistance_to_bit(5500.0, 2000.0, 5000.0)
        assert bit == 1
        assert valid is True
    
    def test_ambiguous_resistance(self):
        """Test detection of ambiguous resistance."""
        # Right at midpoint
        bit, valid = decode_resistance_to_bit(3500.0, 2000.0, 5000.0)
        assert valid is False


class TestVerifyThresholdParameters:
    """Tests for threshold parameter verification."""
    
    def test_valid_thresholds(self):
        """Test verification of valid threshold parameters."""
        params = {
            "low_resistance_threshold": 2000.0,
            "high_resistance_threshold": 5000.0,
            "switching_margin": 3000.0,
            "tmr_ratio": 1.5
        }
        is_valid, errors = verify_threshold_parameters(params)
        assert is_valid is True
        assert len(errors) == 0
    
    def test_invalid_order(self):
        """Test rejection of high < low threshold."""
        params = {
            "low_resistance_threshold": 5000.0,
            "high_resistance_threshold": 2000.0,
            "switching_margin": 3000.0
        }
        is_valid, errors = verify_threshold_parameters(params)
        assert is_valid is False
    
    def test_negative_threshold(self):
        """Test rejection of negative thresholds."""
        params = {
            "low_resistance_threshold": -100.0,
            "high_resistance_threshold": 5000.0,
            "switching_margin": 5100.0
        }
        is_valid, errors = verify_threshold_parameters(params)
        assert is_valid is False


class TestVerifyMramWriteRead:
    """Tests for complete MRAM verification."""
    
    def test_valid_write_read(self):
        """Test verification of valid MRAM operation."""
        packet = {
            "schema_version": "mram_write_read_v1",
            "write_operation": {
                "data_bit": 1
            },
            "read_operation": {
                "resistance_state": 4800.0,
                "decoded_bit": 1
            },
            "threshold_verification": {
                "low_resistance_threshold": 2000.0,
                "high_resistance_threshold": 5000.0,
                "switching_margin": 3000.0,
                "tmr_ratio": 1.5
            }
        }
        is_valid, details = verify_mram_write_read(packet)
        assert is_valid is True
        assert details["write_read_consistent"] is True
    
    def test_write_read_mismatch(self):
        """Test detection of write/read mismatch."""
        packet = {
            "schema_version": "mram_write_read_v1",
            "write_operation": {
                "data_bit": 1
            },
            "read_operation": {
                "resistance_state": 1500.0,  # Low resistance = bit 0
                "decoded_bit": 0
            },
            "threshold_verification": {
                "low_resistance_threshold": 2000.0,
                "high_resistance_threshold": 5000.0,
                "switching_margin": 3000.0
            }
        }
        is_valid, details = verify_mram_write_read(packet)
        assert is_valid is False
        assert details["write_read_consistent"] is False
