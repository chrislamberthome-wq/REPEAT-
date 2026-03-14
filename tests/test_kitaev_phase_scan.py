import numpy as np
from simulations.kitaev_chain_spectrum import compute_spectrum

# Test cases for Kitaev chain spectrum and phase scan
def test_topological_point():
    """
    Test that a topological point produces 2 near-zero modes.
    """
    N = 40
    t = 1.0
    delta = 1.0
    mu = 0.0
    tol = 1e-6

    spectrum = compute_spectrum(N=N, mu=mu, t=t, delta=delta)
    near_zero_mode_count = np.sum(np.abs(spectrum) < tol)

    assert near_zero_mode_count == 2, f"Expected 2 near-zero modes, got {near_zero_mode_count}"

def test_trivial_point():
    """
    Test that a trivial point produces 0 near-zero modes.
    """
    N = 40
    t = 1.0
    delta = 1.0
    mu = 3.0
    tol = 1e-6

    spectrum = compute_spectrum(N=N, mu=mu, t=t, delta=delta)
    near_zero_mode_count = np.sum(np.abs(spectrum) < tol)

    assert near_zero_mode_count == 0, f"Expected 0 near-zero modes, got {near_zero_mode_count}"

def test_phase_transition():
    """
    Test that the minimum absolute eigenvalue dips near the phase transition.
    """
    N = 40
    t = 1.0
    delta = 1.0
    mu_values = np.linspace(-3.0, 3.0, 100)
    transition_region = 2 * t

    min_abs_eigenvalues = []
    for mu in mu_values:
        spectrum = compute_spectrum(N=N, mu=mu, t=t, delta=delta)
        min_abs_eigenvalues.append(np.min(np.abs(spectrum)))

    min_abs_eigenvalues = np.array(min_abs_eigenvalues)
    min_mu = mu_values[np.argmin(min_abs_eigenvalues)]

    assert np.isclose(abs(min_mu), transition_region, atol=0.2), (
        f"Expected transition near ±2t, got {min_mu}")