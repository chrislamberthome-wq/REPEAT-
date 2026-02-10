"""Spintronics module for REPEAT + Platoputer applications.

This module implements:
1. Spin texture codebook based on Platonic solids
2. REPEAT protocol layering (Encode, Decode, Verify, Repeat)
3. Multi-layer verification system
4. Adoption scenarios for MRAM, domain walls, skyrmions, and magnonics
"""

import math
import hashlib
import json
from typing import Tuple, Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

from .codec_3d import encode_3d_solids, decode_3d_solids_rule_a, EPSILON


# Spin texture symbols on Bloch sphere
@dataclass
class SpinSymbol:
    """Represents a spin texture symbol on the Bloch sphere.
    
    The Bloch sphere maps spin states to points on a unit sphere:
    - theta (θ): polar angle [0, π] 
    - phi (φ): azimuthal angle [0, 2π]
    """
    binary: int  # 0 or 1
    theta: float  # Polar angle in radians
    phi: float  # Azimuthal angle in radians
    platonic_angles: Tuple[float, float, float, float, float]  # 5 Platonic solid angles
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'binary': self.binary,
            'theta': self.theta,
            'phi': self.phi,
            'platonic_angles': list(self.platonic_angles)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpinSymbol':
        """Create from dictionary."""
        return cls(
            binary=data['binary'],
            theta=data['theta'],
            phi=data['phi'],
            platonic_angles=tuple(data['platonic_angles'])
        )


@dataclass
class SpinExperiment:
    """Represents a spintronics experiment with device parameters."""
    
    symbol: SpinSymbol
    pulse_amplitude: float  # Magnetic field amplitude (Tesla)
    pulse_duration: float  # Pulse duration (nanoseconds)
    pulse_geometry: str  # e.g., "in-plane", "perpendicular", "tilted"
    temperature: float  # Kelvin
    device_type: str  # e.g., "MRAM", "racetrack", "skyrmion", "magnonic"
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'symbol': self.symbol.to_dict(),
            'pulse_amplitude': self.pulse_amplitude,
            'pulse_duration': self.pulse_duration,
            'pulse_geometry': self.pulse_geometry,
            'temperature': self.temperature,
            'device_type': self.device_type,
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpinExperiment':
        """Create from dictionary."""
        return cls(
            symbol=SpinSymbol.from_dict(data['symbol']),
            pulse_amplitude=data['pulse_amplitude'],
            pulse_duration=data['pulse_duration'],
            pulse_geometry=data['pulse_geometry'],
            temperature=data['temperature'],
            device_type=data['device_type'],
            timestamp=data['timestamp']
        )


@dataclass
class SpinReading:
    """Represents device readings from spintronics measurement."""
    
    resistance: Optional[float] = None  # For MRAM (Ohms)
    position: Optional[float] = None  # For racetrack (micrometers)
    topological_charge: Optional[int] = None  # For skyrmions (±1)
    phase: Optional[float] = None  # For magnonics (radians)
    measured_theta: Optional[float] = None  # Measured polar angle
    measured_phi: Optional[float] = None  # Measured azimuthal angle
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpinReading':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class VerificationResult:
    """Result of verification at one layer."""
    
    layer: int
    layer_name: str
    passed: bool
    message: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class TracePacket:
    """Complete trace packet for spintronics experiment with verification."""
    
    experiment: SpinExperiment
    reading: SpinReading
    verifications: List[VerificationResult]
    decoded_binary: Optional[int]
    trace_hash: str
    receipt: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'experiment': self.experiment.to_dict(),
            'reading': self.reading.to_dict(),
            'verifications': [v.to_dict() for v in self.verifications],
            'decoded_binary': self.decoded_binary,
            'trace_hash': self.trace_hash,
            'receipt': self.receipt
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TracePacket':
        """Create from dictionary."""
        return cls(
            experiment=SpinExperiment.from_dict(data['experiment']),
            reading=SpinReading.from_dict(data['reading']),
            verifications=[VerificationResult(**v) for v in data['verifications']],
            decoded_binary=data['decoded_binary'],
            trace_hash=data['trace_hash'],
            receipt=data['receipt']
        )


# REPEAT Protocol: Encode
def encode_spin_symbol(binary: int, device_type: str = "MRAM") -> SpinSymbol:
    """Encode binary value into a spin texture symbol.
    
    Uses Platonic solids codebook to determine spin orientation on Bloch sphere.
    
    Args:
        binary: Binary value (0 or 1)
        device_type: Type of spintronic device
        
    Returns:
        SpinSymbol with Bloch sphere coordinates and Platonic angles
    """
    if binary not in [0, 1]:
        raise ValueError(f"Binary input must be 0 or 1, got {binary}")
    
    # Get Platonic solid angles for this binary value
    platonic_angles = encode_3d_solids(binary)
    
    # Map to Bloch sphere coordinates
    # For binary 0: North pole region (θ ≈ 0)
    # For binary 1: South pole region (θ ≈ π)
    theta = 0.0 if binary == 0 else math.pi
    phi = 0.0  # Default azimuthal angle
    
    return SpinSymbol(
        binary=binary,
        theta=theta,
        phi=phi,
        platonic_angles=platonic_angles
    )


def encode_experiment(
    binary: int,
    pulse_amplitude: float = 0.5,
    pulse_duration: float = 10.0,
    pulse_geometry: str = "perpendicular",
    temperature: float = 300.0,
    device_type: str = "MRAM"
) -> SpinExperiment:
    """Encode a complete spintronics experiment.
    
    REPEAT Protocol - ENCODE step: Prepare device input with pulses,
    geometry, and environmental parameters.
    
    Args:
        binary: Binary value to encode (0 or 1)
        pulse_amplitude: Magnetic field amplitude in Tesla
        pulse_duration: Pulse duration in nanoseconds
        pulse_geometry: Pulse geometry type
        temperature: Temperature in Kelvin
        device_type: Type of spintronic device
        
    Returns:
        SpinExperiment with all parameters
    """
    symbol = encode_spin_symbol(binary, device_type)
    
    return SpinExperiment(
        symbol=symbol,
        pulse_amplitude=pulse_amplitude,
        pulse_duration=pulse_duration,
        pulse_geometry=pulse_geometry,
        temperature=temperature,
        device_type=device_type,
        timestamp=datetime.now(timezone.utc).isoformat()
    )


# REPEAT Protocol: Decode
def decode_spin_reading(reading: SpinReading, experiment: SpinExperiment) -> Optional[int]:
    """Decode binary value from device readings.
    
    REPEAT Protocol - DECODE step: Map device readings back to
    estimated texture/symbol.
    
    Args:
        reading: Device measurements
        experiment: Original experiment parameters
        
    Returns:
        Decoded binary value (0 or 1) or None if decoding fails
    """
    device_type = experiment.device_type
    
    if device_type == "MRAM":
        # MRAM: High resistance = parallel (0), Low resistance = antiparallel (1)
        if reading.resistance is not None:
            # Typical TMR values: parallel ~1kΩ, antiparallel ~2kΩ
            threshold = 1500.0  # Ohms
            return 0 if reading.resistance < threshold else 1
    
    elif device_type == "racetrack":
        # Racetrack: Position indicates domain wall location
        if reading.position is not None:
            # Position < midpoint = 0, position >= midpoint = 1
            threshold = 0.5  # micrometers (example)
            return 0 if reading.position < threshold else 1
    
    elif device_type == "skyrmion":
        # Skyrmion: Topological charge indicates stability
        if reading.topological_charge is not None:
            # Positive charge = stable (1), negative/zero = unstable (0)
            return 1 if reading.topological_charge > 0 else 0
    
    elif device_type == "magnonic":
        # Magnonics: Phase coherence indicates binary state
        if reading.phase is not None:
            # Phase near 0 = 0, phase near π = 1
            threshold = math.pi / 2
            return 0 if reading.phase < threshold else 1
    
    # Fallback: Use Platonic solids decoding if angles measured
    if reading.measured_theta is not None:
        # Measured theta near 0 = binary 0, near π = binary 1
        return 0 if reading.measured_theta < math.pi / 2 else 1
    
    return None


# REPEAT Protocol: Verify (Layer 1)
def verify_bloch_sphere_survival(
    experiment: SpinExperiment,
    reading: SpinReading,
    tolerance: float = EPSILON
) -> VerificationResult:
    """Verify symbol survival on Bloch sphere.
    
    REPEAT Protocol - VERIFY Layer 1: Check angular θ to confirm
    spin texture survived on the Bloch-like sphere.
    
    Args:
        experiment: Original experiment
        reading: Device measurements
        tolerance: Angular tolerance in radians
        
    Returns:
        VerificationResult for Layer 1
    """
    expected_theta = experiment.symbol.theta
    measured_theta = reading.measured_theta
    
    if measured_theta is None:
        return VerificationResult(
            layer=1,
            layer_name="Bloch Sphere Symbol Survival",
            passed=False,
            message="No theta measurement available",
            details={'expected_theta': expected_theta}
        )
    
    # Check if measured angle is within tolerance of expected
    angular_diff = abs(measured_theta - expected_theta)
    passed = angular_diff <= tolerance
    
    return VerificationResult(
        layer=1,
        layer_name="Bloch Sphere Symbol Survival",
        passed=passed,
        message=f"Angular difference: {angular_diff:.4f} rad ({'PASS' if passed else 'FAIL'})",
        details={
            'expected_theta': expected_theta,
            'measured_theta': measured_theta,
            'angular_diff': angular_diff,
            'tolerance': tolerance
        }
    )


# REPEAT Protocol: Verify (Layer 2)
def verify_pulse_integrity(
    experiment: SpinExperiment,
    reading: SpinReading
) -> VerificationResult:
    """Verify pulse and trace integrity.
    
    REPEAT Protocol - VERIFY Layer 2: Check experimental payload
    integrity and pulse parameters consistency.
    
    Args:
        experiment: Original experiment
        reading: Device measurements
        
    Returns:
        VerificationResult for Layer 2
    """
    checks = []
    passed = True
    
    # Check pulse amplitude is in valid range
    if not (0.0 <= experiment.pulse_amplitude <= 2.0):
        checks.append(f"Pulse amplitude {experiment.pulse_amplitude}T out of range")
        passed = False
    else:
        checks.append(f"Pulse amplitude {experiment.pulse_amplitude}T valid")
    
    # Check pulse duration is in valid range
    if not (0.1 <= experiment.pulse_duration <= 1000.0):
        checks.append(f"Pulse duration {experiment.pulse_duration}ns out of range")
        passed = False
    else:
        checks.append(f"Pulse duration {experiment.pulse_duration}ns valid")
    
    # Check temperature is in valid range
    if not (1.0 <= experiment.temperature <= 400.0):
        checks.append(f"Temperature {experiment.temperature}K out of range")
        passed = False
    else:
        checks.append(f"Temperature {experiment.temperature}K valid")
    
    return VerificationResult(
        layer=2,
        layer_name="Pulse and Trace Integrity",
        passed=passed,
        message="; ".join(checks),
        details={
            'pulse_amplitude': experiment.pulse_amplitude,
            'pulse_duration': experiment.pulse_duration,
            'temperature': experiment.temperature,
            'pulse_geometry': experiment.pulse_geometry
        }
    )


# REPEAT Protocol: Verify (Layer 3)
def verify_task_outcome(
    experiment: SpinExperiment,
    reading: SpinReading,
    decoded_binary: Optional[int]
) -> VerificationResult:
    """Verify task outcome based on device type.
    
    REPEAT Protocol - VERIFY Layer 3: Check task-specific outcomes
    like MRAM switching, domain wall motion, or skyrmion stability.
    
    Args:
        experiment: Original experiment
        reading: Device measurements
        decoded_binary: Decoded binary value
        
    Returns:
        VerificationResult for Layer 3
    """
    device_type = experiment.device_type
    expected_binary = experiment.symbol.binary
    
    if decoded_binary is None:
        return VerificationResult(
            layer=3,
            layer_name=f"Task Outcome ({device_type})",
            passed=False,
            message="Decoding failed - no binary value recovered",
            details={'device_type': device_type}
        )
    
    # Check if decoded matches expected
    passed = (decoded_binary == expected_binary)
    
    task_details = {
        'device_type': device_type,
        'expected_binary': expected_binary,
        'decoded_binary': decoded_binary
    }
    
    if device_type == "MRAM":
        task_details['task'] = "MRAM bit switching"
        task_details['resistance'] = reading.resistance
        message = f"MRAM switching: expected {expected_binary}, got {decoded_binary}"
    
    elif device_type == "racetrack":
        task_details['task'] = "Domain wall motion"
        task_details['position'] = reading.position
        message = f"Domain wall position: expected {expected_binary}, got {decoded_binary}"
    
    elif device_type == "skyrmion":
        task_details['task'] = "Skyrmion stability"
        task_details['topological_charge'] = reading.topological_charge
        message = f"Skyrmion topological charge: expected {expected_binary}, got {decoded_binary}"
    
    elif device_type == "magnonic":
        task_details['task'] = "Magnonic phase coherence"
        task_details['phase'] = reading.phase
        message = f"Magnonic interference: expected {expected_binary}, got {decoded_binary}"
    
    else:
        message = f"Generic verification: expected {expected_binary}, got {decoded_binary}"
    
    message += f" ({'PASS' if passed else 'FAIL'})"
    
    return VerificationResult(
        layer=3,
        layer_name=f"Task Outcome ({device_type})",
        passed=passed,
        message=message,
        details=task_details
    )


# REPEAT Protocol: Repeat (Trace Repeatability)
def compute_trace_hash(experiment: SpinExperiment, reading: SpinReading) -> str:
    """Compute hash of experiment trace for repeatability.
    
    REPEAT Protocol - REPEAT step: Ensure trace repeatability across
    runs/devices/labs through cryptographic hashing.
    
    Args:
        experiment: Experiment parameters
        reading: Device measurements
        
    Returns:
        SHA-256 hash of the trace
    """
    # Create deterministic representation
    trace_data = {
        'symbol_binary': experiment.symbol.binary,
        'platonic_angles': list(experiment.symbol.platonic_angles),
        'pulse_amplitude': experiment.pulse_amplitude,
        'pulse_duration': experiment.pulse_duration,
        'pulse_geometry': experiment.pulse_geometry,
        'temperature': experiment.temperature,
        'device_type': experiment.device_type,
        'reading': reading.to_dict()
    }
    
    # Convert to canonical JSON
    trace_json = json.dumps(trace_data, sort_keys=True, separators=(',', ':'))
    
    # Compute SHA-256 hash
    return hashlib.sha256(trace_json.encode('utf-8')).hexdigest()


def create_receipt(
    experiment: SpinExperiment,
    reading: SpinReading,
    verifications: List[VerificationResult],
    trace_hash: str
) -> Dict[str, Any]:
    """Create auditable receipt for the experiment.
    
    Args:
        experiment: Experiment parameters
        reading: Device measurements
        verifications: All verification results
        trace_hash: Hash of the trace
        
    Returns:
        Receipt dictionary with metadata
    """
    all_passed = all(v.passed for v in verifications)
    
    return {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'trace_hash': trace_hash,
        'device_type': experiment.device_type,
        'all_verifications_passed': all_passed,
        'verification_summary': {
            'layer_1': verifications[0].passed if len(verifications) > 0 else False,
            'layer_2': verifications[1].passed if len(verifications) > 1 else False,
            'layer_3': verifications[2].passed if len(verifications) > 2 else False,
        },
        'protocol_version': 'REPEAT-v1.0'
    }


# Complete REPEAT Protocol
def run_repeat_protocol(
    binary: int,
    reading: SpinReading,
    pulse_amplitude: float = 0.5,
    pulse_duration: float = 10.0,
    pulse_geometry: str = "perpendicular",
    temperature: float = 300.0,
    device_type: str = "MRAM"
) -> TracePacket:
    """Execute complete REPEAT protocol for spintronics.
    
    Performs all four steps:
    1. ENCODE: Prepare experiment
    2. DECODE: Extract binary from readings
    3. VERIFY: Check all three layers
    4. REPEAT: Generate hash and receipt
    
    Args:
        binary: Binary value to encode (0 or 1)
        reading: Device measurements
        pulse_amplitude: Magnetic field amplitude in Tesla
        pulse_duration: Pulse duration in nanoseconds
        pulse_geometry: Pulse geometry type
        temperature: Temperature in Kelvin
        device_type: Type of spintronic device
        
    Returns:
        Complete TracePacket with all results
    """
    # Step 1: ENCODE
    experiment = encode_experiment(
        binary=binary,
        pulse_amplitude=pulse_amplitude,
        pulse_duration=pulse_duration,
        pulse_geometry=pulse_geometry,
        temperature=temperature,
        device_type=device_type
    )
    
    # Step 2: DECODE
    decoded_binary = decode_spin_reading(reading, experiment)
    
    # Step 3: VERIFY - All three layers
    verifications = [
        verify_bloch_sphere_survival(experiment, reading),
        verify_pulse_integrity(experiment, reading),
        verify_task_outcome(experiment, reading, decoded_binary)
    ]
    
    # Step 4: REPEAT - Hash and receipt
    trace_hash = compute_trace_hash(experiment, reading)
    receipt = create_receipt(experiment, reading, verifications, trace_hash)
    
    return TracePacket(
        experiment=experiment,
        reading=reading,
        verifications=verifications,
        decoded_binary=decoded_binary,
        trace_hash=trace_hash,
        receipt=receipt
    )
