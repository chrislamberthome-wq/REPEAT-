"""Tests for the spintronics module."""

import pytest
import math
import json
from repeat_hd.spintronics import (
    SpinSymbol,
    SpinExperiment,
    SpinReading,
    VerificationResult,
    TracePacket,
    encode_spin_symbol,
    encode_experiment,
    decode_spin_reading,
    verify_bloch_sphere_survival,
    verify_pulse_integrity,
    verify_task_outcome,
    compute_trace_hash,
    create_receipt,
    run_repeat_protocol,
)
from repeat_hd.codec_3d import EPSILON


class TestSpinSymbol:
    """Tests for SpinSymbol data structure."""
    
    def test_spin_symbol_creation(self):
        """Test creating a SpinSymbol."""
        symbol = SpinSymbol(
            binary=0,
            theta=0.0,
            phi=0.0,
            platonic_angles=(0.0, 0.1, 0.2, 0.3, 0.4)
        )
        assert symbol.binary == 0
        assert symbol.theta == 0.0
        assert symbol.phi == 0.0
        assert len(symbol.platonic_angles) == 5
    
    def test_spin_symbol_to_dict(self):
        """Test converting SpinSymbol to dictionary."""
        symbol = SpinSymbol(
            binary=1,
            theta=math.pi,
            phi=0.0,
            platonic_angles=(1.0, 2.0, 3.0, 4.0, 5.0)
        )
        data = symbol.to_dict()
        assert data['binary'] == 1
        assert data['theta'] == math.pi
        assert isinstance(data['platonic_angles'], list)
    
    def test_spin_symbol_from_dict(self):
        """Test creating SpinSymbol from dictionary."""
        data = {
            'binary': 0,
            'theta': 0.5,
            'phi': 1.0,
            'platonic_angles': [0.1, 0.2, 0.3, 0.4, 0.5]
        }
        symbol = SpinSymbol.from_dict(data)
        assert symbol.binary == 0
        assert symbol.theta == 0.5
        assert symbol.phi == 1.0


class TestEncodeSpinSymbol:
    """Tests for encode_spin_symbol function."""
    
    def test_encode_binary_0(self):
        """Test encoding binary 0 to spin symbol."""
        symbol = encode_spin_symbol(0)
        assert symbol.binary == 0
        assert symbol.theta == 0.0  # North pole
        assert len(symbol.platonic_angles) == 5
        
        # Check majority of platonic angles have cos >= 0
        positive_count = sum(1 for a in symbol.platonic_angles if math.cos(a) >= 0)
        assert positive_count > 2
    
    def test_encode_binary_1(self):
        """Test encoding binary 1 to spin symbol."""
        symbol = encode_spin_symbol(1)
        assert symbol.binary == 1
        assert symbol.theta == math.pi  # South pole
        assert len(symbol.platonic_angles) == 5
        
        # Check majority of platonic angles have cos < 0
        negative_count = sum(1 for a in symbol.platonic_angles if math.cos(a) < 0)
        assert negative_count > 2
    
    def test_encode_invalid_binary(self):
        """Test encoding with invalid binary value."""
        with pytest.raises(ValueError):
            encode_spin_symbol(2)
        with pytest.raises(ValueError):
            encode_spin_symbol(-1)


class TestEncodeExperiment:
    """Tests for encode_experiment function."""
    
    def test_encode_mram_experiment(self):
        """Test encoding MRAM experiment."""
        exp = encode_experiment(binary=0, device_type="MRAM")
        assert exp.symbol.binary == 0
        assert exp.device_type == "MRAM"
        assert exp.pulse_amplitude > 0
        assert exp.pulse_duration > 0
        assert exp.temperature > 0
        assert len(exp.timestamp) > 0
    
    def test_encode_racetrack_experiment(self):
        """Test encoding racetrack experiment."""
        exp = encode_experiment(
            binary=1,
            device_type="racetrack",
            pulse_amplitude=0.8,
            pulse_duration=50.0,
            temperature=77.0
        )
        assert exp.symbol.binary == 1
        assert exp.device_type == "racetrack"
        assert exp.pulse_amplitude == 0.8
        assert exp.pulse_duration == 50.0
        assert exp.temperature == 77.0
    
    def test_encode_skyrmion_experiment(self):
        """Test encoding skyrmion experiment."""
        exp = encode_experiment(binary=0, device_type="skyrmion")
        assert exp.device_type == "skyrmion"
    
    def test_encode_magnonic_experiment(self):
        """Test encoding magnonic experiment."""
        exp = encode_experiment(binary=1, device_type="magnonic")
        assert exp.device_type == "magnonic"


class TestDecodeSpinReading:
    """Tests for decode_spin_reading function."""
    
    def test_decode_mram_low_resistance(self):
        """Test decoding MRAM with low resistance (parallel, binary 0)."""
        exp = encode_experiment(binary=0, device_type="MRAM")
        reading = SpinReading(resistance=1000.0)  # Low resistance
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 0
    
    def test_decode_mram_high_resistance(self):
        """Test decoding MRAM with high resistance (antiparallel, binary 1)."""
        exp = encode_experiment(binary=1, device_type="MRAM")
        reading = SpinReading(resistance=2000.0)  # High resistance
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 1
    
    def test_decode_racetrack_position(self):
        """Test decoding racetrack with position measurement."""
        exp = encode_experiment(binary=0, device_type="racetrack")
        reading = SpinReading(position=0.2)  # Low position
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 0
        
        reading = SpinReading(position=0.8)  # High position
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 1
    
    def test_decode_skyrmion_topological_charge(self):
        """Test decoding skyrmion with topological charge."""
        exp = encode_experiment(binary=1, device_type="skyrmion")
        reading = SpinReading(topological_charge=1)  # Positive charge
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 1
        
        reading = SpinReading(topological_charge=-1)  # Negative charge
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 0
    
    def test_decode_magnonic_phase(self):
        """Test decoding magnonic with phase measurement."""
        exp = encode_experiment(binary=0, device_type="magnonic")
        reading = SpinReading(phase=0.5)  # Small phase
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 0
        
        reading = SpinReading(phase=2.5)  # Large phase
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 1
    
    def test_decode_with_measured_theta(self):
        """Test decoding using measured theta angle."""
        exp = encode_experiment(binary=0, device_type="MRAM")
        reading = SpinReading(measured_theta=0.1)  # Near north pole
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 0
        
        reading = SpinReading(measured_theta=3.0)  # Near south pole
        decoded = decode_spin_reading(reading, exp)
        assert decoded == 1
    
    def test_decode_no_reading(self):
        """Test decoding with no valid reading."""
        exp = encode_experiment(binary=0, device_type="MRAM")
        reading = SpinReading()  # Empty reading
        decoded = decode_spin_reading(reading, exp)
        assert decoded is None


class TestVerifyBlochSphereSurvival:
    """Tests for verify_bloch_sphere_survival function."""
    
    def test_verify_bloch_sphere_pass(self):
        """Test Bloch sphere verification passes."""
        exp = encode_experiment(binary=0)
        reading = SpinReading(measured_theta=0.01)  # Close to expected 0.0
        result = verify_bloch_sphere_survival(exp, reading)
        
        assert result.layer == 1
        assert result.layer_name == "Bloch Sphere Symbol Survival"
        assert result.passed is True
    
    def test_verify_bloch_sphere_fail(self):
        """Test Bloch sphere verification fails."""
        exp = encode_experiment(binary=0)
        reading = SpinReading(measured_theta=math.pi)  # Wrong pole
        result = verify_bloch_sphere_survival(exp, reading)
        
        assert result.layer == 1
        assert result.passed is False
    
    def test_verify_bloch_sphere_no_measurement(self):
        """Test Bloch sphere verification with no measurement."""
        exp = encode_experiment(binary=0)
        reading = SpinReading()
        result = verify_bloch_sphere_survival(exp, reading)
        
        assert result.layer == 1
        assert result.passed is False
        assert "No theta measurement" in result.message


class TestVerifyPulseIntegrity:
    """Tests for verify_pulse_integrity function."""
    
    def test_verify_pulse_integrity_pass(self):
        """Test pulse integrity verification passes."""
        exp = encode_experiment(
            binary=0,
            pulse_amplitude=0.5,
            pulse_duration=10.0,
            temperature=300.0
        )
        reading = SpinReading()
        result = verify_pulse_integrity(exp, reading)
        
        assert result.layer == 2
        assert result.layer_name == "Pulse and Trace Integrity"
        assert result.passed is True
    
    def test_verify_pulse_integrity_fail_amplitude(self):
        """Test pulse integrity fails for invalid amplitude."""
        exp = encode_experiment(binary=0, pulse_amplitude=5.0)  # Too high
        reading = SpinReading()
        result = verify_pulse_integrity(exp, reading)
        
        assert result.layer == 2
        assert result.passed is False
        assert "amplitude" in result.message.lower()
    
    def test_verify_pulse_integrity_fail_duration(self):
        """Test pulse integrity fails for invalid duration."""
        exp = encode_experiment(binary=0, pulse_duration=2000.0)  # Too high
        reading = SpinReading()
        result = verify_pulse_integrity(exp, reading)
        
        assert result.layer == 2
        assert result.passed is False
    
    def test_verify_pulse_integrity_fail_temperature(self):
        """Test pulse integrity fails for invalid temperature."""
        exp = encode_experiment(binary=0, temperature=500.0)  # Too high
        reading = SpinReading()
        result = verify_pulse_integrity(exp, reading)
        
        assert result.layer == 2
        assert result.passed is False


class TestVerifyTaskOutcome:
    """Tests for verify_task_outcome function."""
    
    def test_verify_task_outcome_pass(self):
        """Test task outcome verification passes."""
        exp = encode_experiment(binary=0, device_type="MRAM")
        reading = SpinReading(resistance=1000.0)
        decoded = 0
        result = verify_task_outcome(exp, reading, decoded)
        
        assert result.layer == 3
        assert result.passed is True
        assert "MRAM" in result.layer_name
    
    def test_verify_task_outcome_fail(self):
        """Test task outcome verification fails."""
        exp = encode_experiment(binary=0, device_type="MRAM")
        reading = SpinReading(resistance=2000.0)
        decoded = 1  # Wrong binary
        result = verify_task_outcome(exp, reading, decoded)
        
        assert result.layer == 3
        assert result.passed is False
    
    def test_verify_task_outcome_no_decode(self):
        """Test task outcome with no decoded value."""
        exp = encode_experiment(binary=0, device_type="MRAM")
        reading = SpinReading()
        result = verify_task_outcome(exp, reading, None)
        
        assert result.layer == 3
        assert result.passed is False
        assert "Decoding failed" in result.message


class TestComputeTraceHash:
    """Tests for compute_trace_hash function."""
    
    def test_compute_trace_hash(self):
        """Test computing trace hash."""
        exp = encode_experiment(binary=0)
        reading = SpinReading(resistance=1000.0)
        trace_hash = compute_trace_hash(exp, reading)
        
        assert isinstance(trace_hash, str)
        assert len(trace_hash) == 64  # SHA-256 hex digest
        assert all(c in '0123456789abcdef' for c in trace_hash)
    
    def test_trace_hash_deterministic(self):
        """Test trace hash is deterministic."""
        exp = encode_experiment(binary=0, pulse_amplitude=0.5)
        reading = SpinReading(resistance=1000.0)
        
        hash1 = compute_trace_hash(exp, reading)
        hash2 = compute_trace_hash(exp, reading)
        
        assert hash1 == hash2
    
    def test_trace_hash_different_experiments(self):
        """Test different experiments produce different hashes."""
        exp1 = encode_experiment(binary=0)
        exp2 = encode_experiment(binary=1)
        reading = SpinReading(resistance=1000.0)
        
        hash1 = compute_trace_hash(exp1, reading)
        hash2 = compute_trace_hash(exp2, reading)
        
        assert hash1 != hash2


class TestCreateReceipt:
    """Tests for create_receipt function."""
    
    def test_create_receipt(self):
        """Test creating receipt."""
        exp = encode_experiment(binary=0)
        reading = SpinReading(measured_theta=0.01, resistance=1000.0)
        verifications = [
            VerificationResult(1, "Layer 1", True, "Pass", {}),
            VerificationResult(2, "Layer 2", True, "Pass", {}),
            VerificationResult(3, "Layer 3", True, "Pass", {}),
        ]
        trace_hash = "abc123"
        
        receipt = create_receipt(exp, reading, verifications, trace_hash)
        
        assert receipt['trace_hash'] == "abc123"
        assert receipt['device_type'] == exp.device_type
        assert receipt['all_verifications_passed'] is True
        assert receipt['protocol_version'] == "REPEAT-v1.0"
        assert 'timestamp' in receipt
    
    def test_create_receipt_failed_verification(self):
        """Test creating receipt with failed verification."""
        exp = encode_experiment(binary=0)
        reading = SpinReading()
        verifications = [
            VerificationResult(1, "Layer 1", False, "Fail", {}),
            VerificationResult(2, "Layer 2", True, "Pass", {}),
            VerificationResult(3, "Layer 3", False, "Fail", {}),
        ]
        trace_hash = "xyz789"
        
        receipt = create_receipt(exp, reading, verifications, trace_hash)
        
        assert receipt['all_verifications_passed'] is False
        assert receipt['verification_summary']['layer_1'] is False
        assert receipt['verification_summary']['layer_2'] is True
        assert receipt['verification_summary']['layer_3'] is False


class TestRunRepeatProtocol:
    """Tests for run_repeat_protocol function."""
    
    def test_run_repeat_protocol_mram_success(self):
        """Test complete REPEAT protocol for MRAM with successful verification."""
        reading = SpinReading(resistance=1000.0, measured_theta=0.01)
        
        packet = run_repeat_protocol(
            binary=0,
            reading=reading,
            device_type="MRAM"
        )
        
        assert isinstance(packet, TracePacket)
        assert packet.experiment.symbol.binary == 0
        assert packet.decoded_binary == 0
        assert len(packet.verifications) == 3
        assert packet.receipt['all_verifications_passed'] is True
        assert len(packet.trace_hash) == 64
    
    def test_run_repeat_protocol_racetrack(self):
        """Test REPEAT protocol for racetrack device."""
        reading = SpinReading(position=0.3, measured_theta=0.05)
        
        packet = run_repeat_protocol(
            binary=0,
            reading=reading,
            device_type="racetrack",
            pulse_amplitude=0.7,
            pulse_duration=20.0
        )
        
        assert packet.experiment.device_type == "racetrack"
        assert packet.decoded_binary == 0
    
    def test_run_repeat_protocol_skyrmion(self):
        """Test REPEAT protocol for skyrmion device."""
        reading = SpinReading(topological_charge=1, measured_theta=3.0)
        
        packet = run_repeat_protocol(
            binary=1,
            reading=reading,
            device_type="skyrmion"
        )
        
        assert packet.experiment.device_type == "skyrmion"
        assert packet.decoded_binary == 1
    
    def test_run_repeat_protocol_magnonic(self):
        """Test REPEAT protocol for magnonic device."""
        reading = SpinReading(phase=2.8, measured_theta=3.1)
        
        packet = run_repeat_protocol(
            binary=1,
            reading=reading,
            device_type="magnonic"
        )
        
        assert packet.experiment.device_type == "magnonic"
        assert packet.decoded_binary == 1
    
    def test_run_repeat_protocol_serialization(self):
        """Test that TracePacket can be serialized to JSON."""
        reading = SpinReading(resistance=1000.0, measured_theta=0.01)
        
        packet = run_repeat_protocol(
            binary=0,
            reading=reading,
            device_type="MRAM"
        )
        
        # Convert to dict and then to JSON
        packet_dict = packet.to_dict()
        json_str = json.dumps(packet_dict, indent=2)
        
        assert isinstance(json_str, str)
        assert len(json_str) > 0
        
        # Verify we can parse it back
        parsed = json.loads(json_str)
        assert parsed['decoded_binary'] == 0
        assert parsed['trace_hash'] == packet.trace_hash


class TestIntegration:
    """Integration tests for spintronics module."""
    
    def test_mram_manufacturing_scenario(self):
        """Test MRAM manufacturing scenario with encoded pulses and resistance readout."""
        # Encode binary 0 and 1
        for binary in [0, 1]:
            resistance = 1000.0 if binary == 0 else 2000.0
            reading = SpinReading(resistance=resistance, measured_theta=0.0 if binary == 0 else math.pi)
            
            packet = run_repeat_protocol(
                binary=binary,
                reading=reading,
                device_type="MRAM",
                pulse_amplitude=0.5,
                pulse_duration=10.0,
                temperature=300.0
            )
            
            assert packet.decoded_binary == binary
            assert packet.receipt['all_verifications_passed'] is True
    
    def test_domain_wall_racetrack_scenario(self):
        """Test domain-wall racetrack memory with positional verification."""
        # Test positional encoding
        reading = SpinReading(position=0.2, measured_theta=0.1)
        
        packet = run_repeat_protocol(
            binary=0,
            reading=reading,
            device_type="racetrack",
            pulse_amplitude=0.8,
            pulse_duration=50.0
        )
        
        assert packet.decoded_binary == 0
        # Layer 3 should verify domain wall motion
        assert "Domain wall" in packet.verifications[2].message
    
    def test_skyrmion_stability_scenario(self):
        """Test skyrmion stability verification with topological charge."""
        # Stable skyrmion with positive topological charge
        reading = SpinReading(topological_charge=1, measured_theta=3.1)
        
        packet = run_repeat_protocol(
            binary=1,
            reading=reading,
            device_type="skyrmion",
            temperature=4.0  # Low temperature for skyrmion stability
        )
        
        assert packet.decoded_binary == 1
        assert "Skyrmion" in packet.verifications[2].message
    
    def test_magnonic_phase_coherence_scenario(self):
        """Test magnonic phase-coherent computation with interference verification."""
        # Phase near π for binary 1
        reading = SpinReading(phase=2.9, measured_theta=3.0)
        
        packet = run_repeat_protocol(
            binary=1,
            reading=reading,
            device_type="magnonic",
            pulse_geometry="in-plane"
        )
        
        assert packet.decoded_binary == 1
        assert "Magnonic" in packet.verifications[2].message
    
    def test_trace_repeatability(self):
        """Test trace repeatability across multiple runs."""
        reading = SpinReading(resistance=1000.0, measured_theta=0.01)
        
        # Run protocol twice with same parameters
        packet1 = run_repeat_protocol(
            binary=0,
            reading=reading,
            device_type="MRAM",
            pulse_amplitude=0.5,
            pulse_duration=10.0,
            temperature=300.0
        )
        
        packet2 = run_repeat_protocol(
            binary=0,
            reading=reading,
            device_type="MRAM",
            pulse_amplitude=0.5,
            pulse_duration=10.0,
            temperature=300.0
        )
        
        # Hashes should be identical for same parameters and reading
        assert packet1.trace_hash == packet2.trace_hash
