"""Crescent ring with suspended inner silhouette (PLAN.md §5.1, reproduces P6).

Open crescent (open_ring logic) plus an extruded 2D silhouette hanging inside
the aperture with a suspension gap. Silhouette presets: "bird" (asymmetric
leaf), "boat" (hull-like). The inner profile is star-shaped so caps can be
centroid fans.
"""

import math

import numpy as np

from geometry.archetypes._common import combine_meshes, extrude_polygon, finalize
from geometry.archetypes.open_ring import generate_open_ring


def _silhouette_outline(shape: str, size_m: float, points: int = 24) -> list:
    """Normalized parametric outline scaled to fit in size_m, centered at 0."""
    phi = np.linspace(0.0, 2.0 * math.pi, points, endpoint=False)
    if shape == "bird":
        # Asymmetric leaf/bird: wider lower lobe, swept tip.
        x = 0.50 * np.cos(phi) * (1.0 + 0.25 * np.sin(phi))
        y = 0.62 * np.sin(phi) + 0.10 * np.sin(2.0 * phi)
    elif shape == "boat":
        # Hull: flat-ish top, rounded bottom keel.
        x = 0.55 * np.cos(phi)
        y = np.where(np.sin(phi) >= 0, 0.18 * np.sin(phi), 0.45 * np.sin(phi))
    else:
        raise ValueError(f"unknown inner shape '{shape}' — bird | boat")
    outline = np.stack([x, y], axis=1)
    outline -= outline.mean(axis=0)
    span = float((outline.max(axis=0) - outline.min(axis=0)).max())
    outline *= size_m / span
    return outline.tolist()


def generate_crescent_inner(
    diameter_m: float = 2.0,
    tube_radius_m: float = 0.10,
    opening_deg: float = 90.0,
    inner_shape: str = "bird",
    suspension_gap_m: float = 0.15,
    inner_thickness_m: float = 0.05,
    segments: int = 48,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    if diameter_m <= 0:
        raise ValueError("diameter_m must be positive")

    ring = generate_open_ring(diameter_m=diameter_m, tube_radius_m=tube_radius_m,
                              opening_deg=opening_deg, segments=segments)
    ring_v = np.asarray(ring["vertices"], dtype=float)
    ring_f = np.asarray(ring["faces"], dtype=int)

    aperture_m = diameter_m - 4.0 * tube_radius_m
    inner_size = aperture_m - 2.0 * suspension_gap_m
    if inner_size <= 0:
        raise ValueError("suspension_gap_m too large for the aperture")

    outline = _silhouette_outline(inner_shape, inner_size)
    inner_v, inner_f = extrude_polygon(outline, inner_thickness_m)

    vertices, faces = combine_meshes([(ring_v, ring_f), (inner_v, inner_f)])

    return finalize(vertices, faces, "crescent_inner", material, shell_thickness_m,
                    extra={
                        "diameter_m": diameter_m,
                        "opening_deg": opening_deg,
                        "inner_shape": inner_shape,
                        "suspension_gap_m": suspension_gap_m,
                        "inner_size_m": round(inner_size, 4),
                    })
