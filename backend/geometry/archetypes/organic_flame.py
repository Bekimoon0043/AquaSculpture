"""Organic flame — stacked flowing lobes (PLAN.md §5.1, reproduces P3/P5).

A lofted vertical form: elliptical rings stacked along a swaying centerline,
radius modulated into lobes, with optional sinusoidal surface ribbing.
Capped at base and tip. Metadata carries integral spill-lip edge lengths
for the hydraulics engine (water sheeting off the body, P5-style).
"""

import math

import numpy as np

from geometry.archetypes._common import finalize

SPILL_LIP_FRACTIONS = (0.35, 0.7)  # heights where integral spill lips sit


def _radius_at(base_radius_m: float, height_m: float, lobe_count: int,
               f: float) -> float:
    shrink = 1.0 - 0.85 * f
    lobes = 1.0 + 0.22 * math.sin(math.pi * lobe_count * f)
    return max(0.02, base_radius_m * shrink * lobes)


def generate_organic_flame(
    height_m: float = 4.0,
    base_radius_m: float = 0.8,
    lobe_count: int = 4,
    flow_m: float = 0.3,
    rib_amplitude: float = 0.05,
    rib_count: int = 12,
    segments: int = 48,
    radial_segments: int = 24,
    spill_lips: bool = True,
    shell_thickness_m: float | None = None,
    material: str = "bronze",
) -> dict:
    if height_m <= 0 or base_radius_m <= 0:
        raise ValueError("height_m and base_radius_m must be positive")
    if lobe_count < 1 or segments < 4 or radial_segments < 3:
        raise ValueError("lobe_count >= 1, segments >= 4, radial_segments >= 3")
    if not 0.0 <= rib_amplitude < 0.5:
        raise ValueError("rib_amplitude must be in [0, 0.5)")

    stations = segments + 1
    phi = np.linspace(0.0, 2.0 * math.pi, radial_segments, endpoint=False)
    cos_p, sin_p = np.cos(phi), np.sin(phi)
    rib = 1.0 + rib_amplitude * np.cos(rib_count * phi)

    vertices: list[list[float]] = []
    for i in range(stations):
        f = i / segments
        y = height_m * f
        cx = flow_m * math.sin(3.0 * math.pi * f)
        cz = flow_m * math.sin(2.0 * math.pi * f + 1.0)
        r = _radius_at(base_radius_m, height_m, lobe_count, f)
        for j in range(radial_segments):
            rr = r * rib[j]
            vertices.append([cx + rr * cos_p[j], y, cz + rr * sin_p[j]])

    faces: list[list[int]] = []
    for i in range(segments):
        for j in range(radial_segments):
            j1 = (j + 1) % radial_segments
            a = i * radial_segments + j
            b = (i + 1) * radial_segments + j
            c = (i + 1) * radial_segments + j1
            d = i * radial_segments + j1
            faces.append([a, b, c])
            faces.append([a, c, d])

    # Base and tip caps as centroid fans.
    base_ring = vertices[:radial_segments]
    base_c = len(vertices)
    vertices.append([float(np.mean([v[0] for v in base_ring])), 0.0,
                     float(np.mean([v[2] for v in base_ring]))])
    tip_c = len(vertices)
    top_ring = vertices[segments * radial_segments: base_c]
    vertices.append([float(np.mean([v[0] for v in top_ring])), height_m,
                     float(np.mean([v[2] for v in top_ring]))])
    for j in range(radial_segments):
        j1 = (j + 1) % radial_segments
        faces.append([base_c, j, j1])  # base faces down
        top_j = segments * radial_segments + j
        top_j1 = segments * radial_segments + j1
        faces.append([tip_c, top_j1, top_j])  # tip faces up

    extra = {
        "height_m": height_m,
        "base_radius_m": base_radius_m,
        "lobe_count": lobe_count,
        "flow_m": flow_m,
        "rib_amplitude": rib_amplitude,
    }
    if spill_lips:
        extra["spill_edges_m"] = [
            round(math.pi * _radius_at(base_radius_m, height_m, lobe_count, f), 3)
            for f in SPILL_LIP_FRACTIONS
        ]

    return finalize(np.asarray(vertices, dtype=float), faces, "organic_flame",
                    material, shell_thickness_m, extra=extra)
