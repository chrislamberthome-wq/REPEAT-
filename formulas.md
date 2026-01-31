# Formulas

This file contains formulas and specifications for the 3D codec system.

## Overview

The 3D codec system provides geometric encoding and decoding of binary messages using 2D and 3D representations.

## Constants

- **Tolerance (ε)**: 0.08 - Used for verification of decoded values
- **Default Radius (R)**: 1.0 - Default radius for 2D encoding

## Binary → 2D Codec

### Encoding

Takes a binary input (`0` or `1`) and maps it to a 2D point `(x, y)` using polar coordinates:

- **Binary to Angle Mapping**:
  - `b = 0` → `θ = 0`
  - `b = 1` → `θ = π`

- **Point Calculation**:
  - `x = R cos(θ)`
  - `y = R sin(θ)`

### Decoding

Extracts the binary value from a 2D point `(x, y)`:

1. Verify point is on circle: `|√(x² + y²) - R| ≤ ε`
2. Compute angle: `θ = atan2(y, x)`
3. Determine binary value:
   - If `|wrap_angle(θ - 0)| < ε` → `b = 0`
   - If `|wrap_angle(θ - π)| < ε` → `b = 1`
   - Otherwise → verification fails

## Binary → 3D Codec

### Mode 1: Seashell Curve

Uses a 3D logarithmic spiral with z-axis modulation.

**Encoding**:
- Compute radius: `r = r₀ × φᵗ`
- Compute x, y: `x = r cos(t)`, `y = r sin(t)`
- Modulate z based on binary:
  - `b = 0` → `z = -r` (negative)
  - `b = 1` → `z = +r` (positive)

**Decoding**:
- Extract binary from z-coordinate sign:
  - `z < 0` → `b = 0`
  - `z ≥ 0` → `b = 1`

### Mode 2: 5-Solids Frame

Uses the five Platonic solids with stopping angles.

**Encoding**:

Returns 5 stopping angles `(α_T, α_C, α_O, α_D, α_I)` representing:
- T: Tetrahedron
- C: Cube
- O: Octahedron
- D: Dodecahedron
- I: Icosahedron

**For b = 0**: Angles chosen so majority of `cos(α_s) ≥ 0`
**For b = 1**: Angles chosen so majority of `cos(α_s) < 0`

**Decoding - Rule A (Majority Voting)**:

For each solid s:
- `vote_s = 0` if `cos(α_s) ≥ 0`
- `vote_s = 1` if `cos(α_s) < 0`

Return majority vote from 5 solids.

**Decoding - Rule B (Sum Threshold)**:

Compute: `S = Σ cos(α_s)` for all solids

- If `S ≥ threshold` → `b = 0`
- If `S < threshold` → `b = 1`

Default threshold: 0.0

## Helper Functions

### wrap_angle(Δθ)

Computes minimum angular distance by wrapping to `[-π, π]` range:

```
while Δθ > π:
    Δθ = Δθ - 2π
while Δθ < -π:
    Δθ = Δθ + 2π
return Δθ
```

### verify_tolerance(expected, actual, ε)

Returns `True` if `|expected - actual| ≤ ε`, otherwise `False`.

## Usage Example

```python
from repeat_hd.codec_3d import (
    encode_2d, decode_2d,
    encode_3d_seashell, decode_3d_seashell,
    encode_3d_solids, decode_3d_solids_rule_a, decode_3d_solids_rule_b
)

# 2D encoding
point_2d = encode_2d(1)  # Returns (-1.0, 0.0) for b=1
binary = decode_2d(point_2d)  # Returns 1

# 3D seashell encoding
point_3d = encode_3d_seashell(0)  # Returns point with negative z
binary = decode_3d_seashell(point_3d)  # Returns 0

# 3D 5-solids encoding
angles = encode_3d_solids(1)  # Returns 5 angles
binary_a = decode_3d_solids_rule_a(angles)  # Returns 1 using majority vote
binary_b = decode_3d_solids_rule_b(angles)  # Returns 1 using sum threshold
```

