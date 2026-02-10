# Spintronics Example Packets

This directory contains example packets and receipts demonstrating the spintronics REPEAT + Platoputer protocol.

## Example Files

### 1. Spin Configuration (`example_spin_configuration.json`)
Demonstrates a 4x4 spin lattice with periodic boundary conditions:
- 16 spins in row-major order
- Nearest neighbor ferromagnetic interaction (J = -1.0)
- Room temperature (300 K) operation

### 2. Pulse Trace (`example_pulse_trace.json`)
Demonstrates a write-read-write-read pulse sequence:
- 4 pulses total
- Write pulses: 1.5V amplitude, 10ns duration
- Read pulses: 0.5V amplitude, 5ns duration
- Total trace duration: 30ns
- SHA-256 integrity checksum

### 3. MRAM Receipt (`example_mram_receipt.json`)
Demonstrates a successful MRAM write/read operation:
- Write bit 1 to address 0x1000
- Rectangular pulse: 1.8V, 10ns
- Read resistance: 5000Ω (high state)
- Threshold verification with TMR ratio 1.5

## Usage

Verify examples using the verifier scripts:

```bash
# Verify spin configuration
python -m spintronics.verifiers.verify_state_survival_macrospin examples/example_spin_configuration.json

# Verify pulse trace
python -m spintronics.verifiers.verify_trace_integrity examples/example_pulse_trace.json

# Verify MRAM receipt
python -m spintronics.verifiers.verify_mram_write_read examples/example_mram_receipt.json
```

## Creating New Packets

Follow the JSON schema specifications in `../schemas/` directory:
- `state_survival_macrospin_v1.schema.json`
- `trace_integrity_v1.schema.json`
- `mram_write_read_v1.schema.json`
