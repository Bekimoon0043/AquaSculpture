"""Geometric quantities from a triangle mesh (PLAN.md §6 — geo_calc).

All functions accept vertices as (N, 3) array-like and faces as (M, 3)
array-like of vertex indices. Volume/CoG assume a closed mesh with
consistently outward-facing winding (signed values are handled via abs/sum).
"""

import numpy as np


def _as_arrays(vertices, faces):
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    return v, f


def surface_area(vertices, faces) -> float:
    """Total triangle surface area in m^2."""
    v, f = _as_arrays(vertices, faces)
    tris = v[f]
    areas = 0.5 * np.linalg.norm(
        np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1)
    return float(areas.sum())


def volume(vertices, faces) -> float:
    """Enclosed volume in m^3 via the divergence theorem."""
    v, f = _as_arrays(vertices, faces)
    tris = v[f]
    signed = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])) / 6.0
    return float(abs(signed.sum()))


def bounding_box(vertices, faces=None) -> dict:
    """Axis-aligned bounding box: min, max and size per axis (meters)."""
    v = np.asarray(vertices, dtype=float)
    lo = v.min(axis=0)
    hi = v.max(axis=0)
    return {
        "min": lo.tolist(),
        "max": hi.tolist(),
        "size": (hi - lo).tolist(),
    }


def center_of_gravity(vertices, faces) -> list[float]:
    """Volume-weighted centroid of the enclosed solid (uniform density)."""
    v, f = _as_arrays(vertices, faces)
    tris = v[f]
    signed_vols = np.einsum("ij,ij->i", tris[:, 0], np.cross(tris[:, 1], tris[:, 2])) / 6.0
    # Centroid of the tetrahedron (origin, a, b, c) is (a + b + c) / 4.
    tet_centroids = tris.sum(axis=1) / 4.0
    total = signed_vols.sum()
    if abs(total) < 1e-12:
        raise ValueError("mesh encloses no volume — cannot compute center of gravity")
    cog = (tet_centroids * signed_vols[:, None]).sum(axis=0) / total
    return cog.tolist()
