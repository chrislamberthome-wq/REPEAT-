"""
verifier/compute_volume.py

Computes the signed volume of a tetrahedron from its four vertex
coordinates using the scalar triple-product formula:

    V = det(v2-v1, v3-v1, v4-v1) / 6

A positive result means the vertices are arranged with right-hand
(positive) orientation; a negative result means left-hand (negative)
orientation.  Zero means the four points are coplanar (degenerate).
"""


def _subtract(a, b):
    """Return the vector difference a - b for two 3-element sequences."""
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _dot(a, b):
    """Return the dot product of two 3-element sequences."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    """Return the cross product of two 3-element sequences."""
    return [
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    ]


def compute_signed_volume(v1, v2, v3, v4):
    """
    Compute the signed volume of a tetrahedron.

    Parameters
    ----------
    v1, v2, v3, v4 : sequence of three floats
        Cartesian coordinates [x, y, z] of the four vertices.

    Returns
    -------
    float
        Signed volume.  Positive → right-hand (positive) orientation;
        negative → left-hand (negative) orientation; zero → degenerate.

    Notes
    -----
    Uses the scalar triple-product identity::

        V = (1/6) * dot(v2-v1, cross(v3-v1, v4-v1))

    which equals ``det([v2-v1, v3-v1, v4-v1]) / 6``.
    """
    a = _subtract(v2, v1)
    b = _subtract(v3, v1)
    c = _subtract(v4, v1)
    return _dot(a, _cross(b, c)) / 6.0
