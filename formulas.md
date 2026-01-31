# Formulas

## 3D Codec Binary Output (5-Solids Frame Methodology)

### Overview
The 3D codec produces binary outputs using the contact points of 5 Platonic solids and their stopping angles.

### Platonic Solids
The 5 Platonic solids used in order:
- **T**: Tetrahedron (4 faces)
- **C**: Cube (6 faces)
- **O**: Octahedron (8 faces)
- **D**: Dodecahedron (12 faces)
- **I**: Icosahedron (20 faces)

### Contact Points
For each frame, record the contact points for all 5 solids:
```
v_T, v_C, v_O, v_D, v_I ∈ ℝ³
```

### Stopping Angle Computation
For each solid s, compute the stopping angle:
```
α_s = atan2(y_s, x_s)
```
where (x_s, y_s, z_s) are the coordinates of the contact point v_s.

### Binary Bit Encoding

#### Rule A (Majority Voting)
1. For each solid, compute the vote:
   ```
   vote_s = { 0  if cos(α_s) ≥ 0
            { 1  if cos(α_s) < 0
   ```

2. Decide the bit by majority vote:
   ```
   bit = { 1  if Σ vote_s ≥ 3
         { 0  otherwise
   ```

#### Rule B (Threshold)
1. Compute the sum of cosines:
   ```
   S = Σ cos(α_s)  for all 5 solids
   ```

2. Decide the bit by threshold:
   ```
   bit = { 0  if S ≥ 0
         { 1  if S < 0
   ```

### Verification

#### Repeatability Check
For all repeated runs, verify that outcomes are stable within tolerance ε = 0.08:
```
||v_s − v'_s||₂ ≤ ε  for all solids s
```
where ||·||₂ is the Euclidean (L2) norm in ℝ³.

#### Rule Agreement
Require that Rule A and Rule B produce the same bit, unless erasure/retransmission is applied:
```
bit_A = bit_B  (required)
```

### Angular Consistency
Use the `wrap_angle` helper to handle circular angular differences by normalizing angles to the range [-π, π].
