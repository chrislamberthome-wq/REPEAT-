import numpy as np

from simulations.kitaev_chain_spectrum import kitaev_chain_hamiltonian


def kitaev_chain_periodic_hamiltonian(N, mu, t, delta):
    H = kitaev_chain_hamiltonian(N, mu, t, delta)

    # periodic hopping
    H[0, N-1] = -t
    H[N-1, 0] = -t

    H[N, 2*N-1] = t
    H[2*N-1, N] = t

    # periodic pairing: follows the open-chain convention H[j, j+1+N]=delta,
    # H[j+1, j+N]=-delta for j=N-1 wrapping to j+1=0
    H[N-1, N] = delta
    H[0, 2*N-1] = -delta
    H[2*N-1, 0] = delta
    H[N, N-1] = -delta

    return H


def compute_periodic_spectrum(N=40, mu=0.0, t=1.0, delta=1.0):
    H = kitaev_chain_periodic_hamiltonian(N, mu, t, delta)
    eigvals = np.linalg.eigvalsh(H)
    return np.sort(eigvals)
