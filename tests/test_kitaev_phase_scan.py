import numpy as np

from simulations.kitaev_chain_spectrum import compute_spectrum


def near_zero_mode_count(eigvals, tol=1e-3):
    return int(np.sum(np.abs(eigvals) < tol))

def bulk_gap_proxy(eigvals, tol=1e-3):
    abs_sorted = np.sort(np.abs(eigvals))
    nz = near_zero_mode_count(eigvals, tol=tol)
    if nz >= len(abs_sorted):
        raise ValueError("All modes classified as near-zero; tolerance too large.")
    return abs_sorted[nz]

def test_phase_transition():
    N = 40
    t = 1.0
    delta = 1.0
    mus = np.linspace(-3.0, 3.0, 45)

    gaps = []
    for mu in mus:
        eigvals = compute_spectrum(N=N, mu=mu, t=t, delta=delta)
        gaps.append(bulk_gap_proxy(eigvals, tol=1e-3))

    gaps = np.array(gaps)

    left_mask = mus < 0
    right_mask = mus > 0

    mu_left = mus[left_mask][np.argmin(gaps[left_mask])]
    mu_right = mus[right_mask][np.argmin(gaps[right_mask])]

    assert np.isclose(abs(mu_left), 2.0, atol=0.3), f"Expected left transition near -2t, got {mu_left}"
    assert np.isclose(abs(mu_right), 2.0, atol=0.3), f"Expected right transition near +2t, got {mu_right}"