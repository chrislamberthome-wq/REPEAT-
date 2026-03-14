import numpy as np

# Function to construct the Kitaev chain Hamiltonian
def kitaev_chain_hamiltonian(N, mu, t, delta):
    H = np.zeros((2 * N, 2 * N))

    for j in range(N):
        H[j, j] = -mu
        H[j + N, j + N] = mu

    for j in range(N - 1):
        H[j, j + 1] = -t
        H[j + 1, j] = -t

        H[j + N, j + 1 + N] = t
        H[j + 1 + N, j + N] = t

        H[j, j + 1 + N] = delta
        H[j + 1, j + N] = -delta
        H[j + N, j + 1] = delta
        H[j + 1 + N, j] = -delta

    return H

# Function to compute the eigenvalues of the Hamiltonian
def compute_spectrum(N=40, mu=0.0, t=1.0, delta=1.0):
    H = kitaev_chain_hamiltonian(N, mu, t, delta)
    eigvals = np.linalg.eigvalsh(H)
    return np.sort(eigvals)

# Main script for execution
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Compute Kitaev chain spectrum.")
    parser.add_argument("-N", type=int, default=40, help="Number of lattice sites.")
    parser.add_argument("-mu", type=float, default=0.0, help="Chemical potential.")
    parser.add_argument("-t", type=float, default=1.0, help="Hopping amplitude.")
    parser.add_argument("-delta", type=float, default=1.0, help="Superconducting pairing.")
    parser.add_argument("--tol", type=float, default=1e-6, help="Tolerance for near-zero modes.")

    args = parser.parse_args()

    # Compute the spectrum
    spectrum = compute_spectrum(N=args.N, mu=args.mu, t=args.t, delta=args.delta)

    # Count near-zero modes based on the tolerance
    near_zero_modes = np.sum(np.abs(spectrum) < args.tol)

    # Output results
    print("Lowest eigenvalues:", spectrum[:6])
    print("Number of near-zero modes:", near_zero_modes)
    print("Minimum absolute eigenvalue:", np.min(np.abs(spectrum)))

if __name__ == "__main__":
    main()