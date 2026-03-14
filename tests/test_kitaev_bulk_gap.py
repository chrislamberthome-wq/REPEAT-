import numpy as np

from simulations.kitaev_chain_periodic import compute_periodic_spectrum


def test_periodic_bulk_gap_transition():
    N = 40
    t = 1.0
    delta = 1.0

    mus = np.linspace(-3, 3, 60)
    gaps = []

    for mu in mus:
        eigvals = compute_periodic_spectrum(N, mu, t, delta)
        gaps.append(np.min(np.abs(eigvals)))

    mu_transition = mus[np.argmin(gaps)]

    assert np.isclose(abs(mu_transition), 2.0, atol=0.2)
