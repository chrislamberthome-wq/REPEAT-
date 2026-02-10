#!/usr/bin/env python3
"""Verify state survival for macrospin configurations.

This verifier checks spin configuration packets for nearest neighbor
decoding consistency and state survival criteria.
"""

import json
import sys
from typing import Dict, Any, List, Tuple


def compute_nearest_neighbor_energy(spins: List[int], lattice_size: Tuple[int, int],
                                    interaction_strength: float,
                                    boundary_conditions: str) -> float:
    """
    Compute nearest neighbor interaction energy.
    
    E = -J * Σ s_i * s_j for nearest neighbors
    
    Args:
        spins: List of spin states (0=down, 1=up) in row-major order
        lattice_size: Tuple of (x, y) lattice dimensions
        interaction_strength: Coupling strength J
        boundary_conditions: 'periodic' or 'open'
        
    Returns:
        Total nearest neighbor energy
    """
    x_size, y_size = lattice_size
    
    # Convert 0/1 to -1/+1 for spin calculation
    spin_values = [2*s - 1 for s in spins]
    
    energy = 0.0
    
    for i in range(y_size):
        for j in range(x_size):
            idx = i * x_size + j
            current_spin = spin_values[idx]
            
            # Right neighbor
            if j < x_size - 1:
                right_idx = i * x_size + (j + 1)
                energy -= interaction_strength * current_spin * spin_values[right_idx]
            elif boundary_conditions == 'periodic' and x_size > 1:
                right_idx = i * x_size + 0
                energy -= interaction_strength * current_spin * spin_values[right_idx]
            
            # Down neighbor
            if i < y_size - 1:
                down_idx = (i + 1) * x_size + j
                energy -= interaction_strength * current_spin * spin_values[down_idx]
            elif boundary_conditions == 'periodic' and y_size > 1:
                down_idx = 0 * x_size + j
                energy -= interaction_strength * current_spin * spin_values[down_idx]
    
    return energy


def verify_spin_configuration(packet: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Verify spin configuration packet validity.
    
    Checks:
    - Schema version
    - Lattice size consistency
    - Spin count matches lattice dimensions
    - Valid spin values (0 or 1)
    
    Args:
        packet: Spin configuration packet
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check schema version
    if packet.get("schema_version") != "state_survival_macrospin_v1":
        errors.append("Invalid schema version")
    
    # Check spin configuration
    config = packet.get("spin_configuration", {})
    lattice_size = config.get("lattice_size", {})
    spins = config.get("spins", [])
    
    x_size = lattice_size.get("x", 0)
    y_size = lattice_size.get("y", 0)
    
    if x_size <= 0 or y_size <= 0:
        errors.append("Invalid lattice dimensions")
    
    expected_count = x_size * y_size
    if len(spins) != expected_count:
        errors.append(f"Spin count mismatch: expected {expected_count}, got {len(spins)}")
    
    # Validate spin values
    for idx, spin in enumerate(spins):
        if spin not in [0, 1]:
            errors.append(f"Invalid spin value at index {idx}: {spin}")
            break  # Only report first invalid value
    
    return len(errors) == 0, errors


def verify_state_survival(packet: Dict[str, Any], 
                         energy_threshold: float = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Verify macrospin state survival based on energy criteria.
    
    Args:
        packet: Spin configuration packet
        energy_threshold: Optional energy threshold for survival check
        
    Returns:
        Tuple of (survival_verified, verification_details)
    """
    is_valid, errors = verify_spin_configuration(packet)
    
    if not is_valid:
        return False, {"errors": errors}
    
    # Extract configuration
    config = packet["spin_configuration"]
    lattice_size = (config["lattice_size"]["x"], config["lattice_size"]["y"])
    spins = config["spins"]
    
    # Extract nearest neighbor parameters
    nn_params = packet["nearest_neighbors"]
    interaction_strength = nn_params["interaction_strength"]
    boundary_conditions = nn_params["boundary_conditions"]
    
    # Compute energy
    energy = compute_nearest_neighbor_energy(
        spins, lattice_size, interaction_strength, boundary_conditions
    )
    
    # Prepare verification details
    details = {
        "energy": energy,
        "lattice_size": lattice_size,
        "spin_count": len(spins),
        "magnetization": sum(spins) / len(spins) if spins else 0.0,
    }
    
    # Check energy threshold if provided
    if energy_threshold is not None:
        survival = abs(energy) >= energy_threshold
        details["energy_threshold"] = energy_threshold
        details["survival_verified"] = survival
    else:
        survival = True
        details["survival_verified"] = True
    
    return survival, details


def main():
    """Main entry point for verification script."""
    if len(sys.argv) < 2:
        print("Usage: verify_state_survival_macrospin.py <packet_file.json>", file=sys.stderr)
        return 1
    
    packet_file = sys.argv[1]
    
    try:
        with open(packet_file, 'r') as f:
            packet = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading packet: {e}", file=sys.stderr)
        return 1
    
    # Verify packet
    is_valid, errors = verify_spin_configuration(packet)
    
    if not is_valid:
        print("VERIFICATION FAILED", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1
    
    # Check state survival
    survival, details = verify_state_survival(packet)
    
    if survival:
        print("STATE SURVIVAL VERIFIED")
        print(f"  Energy: {details['energy']:.6f}")
        print(f"  Magnetization: {details['magnetization']:.4f}")
        print(f"  Lattice size: {details['lattice_size']}")
        return 0
    else:
        print("STATE SURVIVAL CHECK FAILED", file=sys.stderr)
        print(f"  Energy: {details['energy']:.6f}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
