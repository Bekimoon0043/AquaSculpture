"""Ribbon knot / flame loop (PLAN.md §5.1, reproduces P4/P7).

A rectangular-section ribbon swept along a vertical freeform centerline.
Centerline presets: "figure_eight", "flame", "wave". Width/thickness taper
along the length; the section twists `twist_deg` over the full sweep.
Watertight via end caps.
"""

import math

import numpy as np

from geometry.archetypes._common import finalize

PRESETS = ("figure_eight", "flame", "wave")
PARAM_CHOICES = {"preset": PRESETS}  # exposed to the UI parameter form


def _centerline(preset: str, height_m: float, stations: int) -> np.ndarray:
    t = np.linspace(0.0, 1.0, stations)
    if preset == "figure_eight":
        ang = 2.0 * math.pi * t
        x = 0.30 * height_m * np.sin(ang)
        z = 0.16 * height_m * np.sin(2.0 * ang)
        y = 0.05 * height_m + 0.9 * height_m * t
    elif preset == "flame":
        turns = 2.5
        ang = turns * 2.0 * math.pi * t
        r = 0.25 * height_m * (1.0 - 0.8 * t)
        x = r * np.cos(ang)
        z = r * np.sin(ang)
        y = height_m * t
    elif preset == "wave":
        x = 0.20 * height_m * np.sin(3.0 * math.pi * t)
        z = np.zeros_like(t)
        y = height_m * t
    else:
        raise ValueError(f"unknown preset '{preset}' — one of {PRESETS}")
    return np.stack([x, y, z], axis=1)


def generate_ribbon_knot(
    height_m: float = 4.0,
    width_m: float = 0.6,
    thickness_m: float = 0.08,
    preset: str = "figure_eight",
    taper: float = 0.3,
    twist_deg: float = 180.0,
    segments: int = 96,
    shell_thickness_m: float | None = None,
    material: str = "bronze",
) -> dict:
    if height_m <= 0:
        raise ValueError("height_m must be positive")
    if not 0.0 <= taper < 1.0:
        raise ValueError("taper must be in [0, 1)")
    if segments < 4:
        raise ValueError("segments must be >= 4")

    stations = segments + 1
    centers = _centerline(preset, height_m, stations)

    # Tangents via central differences.
    tangents = np.gradient(centers, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)

    ref = np.array([0.0, 0.0, 1.0])
    fallback = np.array([1.0, 0.0, 0.0])

    f = np.linspace(0.0, 1.0, stations)
    widths = width_m * (1.0 - taper * f)
    thicknesses = thickness_m * (1.0 - 0.5 * taper * f)
    twist = np.radians(twist_deg) * f

    vertices = np.zeros((stations, 4, 3))
    for i in range(stations):
        t_vec = tangents[i]
        side = np.cross(t_vec, ref)
        if np.linalg.norm(side) < 1e-6:
            side = np.cross(t_vec, fallback)
        side /= np.linalg.norm(side)
        up = np.cross(t_vec, side)
        up /= np.linalg.norm(up)
        # Twist the section frame about the tangent.
        c, s = math.cos(twist[i]), math.sin(twist[i])
        side_t = c * side + s * up
        up_t = -s * side + c * up
        hw, ht = widths[i] / 2.0, thicknesses[i] / 2.0
        vertices[i, 0] = centers[i] + hw * side_t + ht * up_t
        vertices[i, 1] = centers[i] + hw * side_t - ht * up_t
        vertices[i, 2] = centers[i] - hw * side_t - ht * up_t
        vertices[i, 3] = centers[i] - hw * side_t + ht * up_t

    faces: list[list[int]] = []
    for i in range(segments):
        for k in range(4):
            k1 = (k + 1) % 4
            a = i * 4 + k
            b = (i + 1) * 4 + k
            c = (i + 1) * 4 + k1
            d = i * 4 + k1
            faces.append([a, b, c])
            faces.append([a, c, d])

    # End caps (flat quads as two triangles); ensure_outward fixes orientation.
    faces.append([0, 1, 2])
    faces.append([0, 2, 3])
    e = segments * 4
    faces.append([e, e + 2, e + 1])
    faces.append([e, e + 3, e + 2])

    verts = vertices.reshape(-1, 3)

    # Arc length for fabrication metadata.
    seg_len = np.linalg.norm(np.diff(centers, axis=0), axis=1)
    arc_length = float(seg_len.sum())

    return finalize(verts, faces, "ribbon_knot", material, shell_thickness_m,
                    extra={
                        "height_m": height_m,
                        "preset": preset,
                        "taper": taper,
                        "twist_deg": twist_deg,
                        "arc_length_m": arc_length,
                    })
