"""Arc-fin radial array (PLAN.md §5.1, reproduces P1).

Curved tapered fins arranged radially on a base plate. Each fin is a thin
plate swept along a circular arc spine (vertical at the base, bowing
outward), tapering from base_width to tip_width. Fins are capped at both
ends; the array sits on a circular base plate. Metadata notes the LED
channel groove along each fin spine.
"""

import math

import numpy as np

from geometry.archetypes._common import combine_meshes, finalize, revolve_profile


def _fin(height_m: float, arc_radius_m: float, base_width_m: float,
         tip_width_m: float, thickness_m: float, stations: int):
    """One fin in local coords: base at origin, spine in the (x, y) plane,
    width along local z. Returns (vertices, faces)."""
    ratio = min(height_m / arc_radius_m, 0.95)
    a_max = math.asin(ratio)
    # Spine: x = R(1 - cos a), y = R sin a  -> vertical tangent at the base,
    # tip at exactly height_m.
    s = np.linspace(0.0, 1.0, stations)
    a = a_max * s
    spine_x = arc_radius_m * (1.0 - np.cos(a))
    spine_y = arc_radius_m * np.sin(a) * (height_m / (arc_radius_m * math.sin(a_max)))

    # In-plane frame: tangent (sin a?, ...) — dx/da = R sin a, dy/da = R cos a.
    tx, ty = np.sin(a), np.cos(a)          # tangent (normalized)
    nx, ny = np.cos(a), -np.sin(a)         # in-plane normal (thickness dir)

    widths = base_width_m + (tip_width_m - base_width_m) * s
    ht = thickness_m / 2.0

    vertices = np.zeros((stations, 4, 3))
    for i in range(stations):
        hw = widths[i] / 2.0
        corners = [
            (+hw, +ht), (+hw, -ht), (-hw, -ht), (-hw, +ht),
        ]
        for k, (w, t) in enumerate(corners):
            vertices[i, k] = [spine_x[i] + t * nx[i],
                              spine_y[i] + t * ny[i],
                              w]
    faces: list[list[int]] = []
    for i in range(stations - 1):
        for k in range(4):
            k1 = (k + 1) % 4
            a0, b0 = i * 4 + k, (i + 1) * 4 + k
            c0, d0 = (i + 1) * 4 + k1, i * 4 + k1
            faces.append([a0, b0, c0])
            faces.append([a0, c0, d0])
    faces += [[0, 1, 2], [0, 2, 3]]  # base cap (faces -tangent)
    e = (stations - 1) * 4
    faces += [[e, e + 2, e + 1], [e, e + 3, e + 2]]  # tip cap (faces +tangent)
    return vertices.reshape(-1, 3), faces


def generate_arc_fin_array(
    fin_count: int = 8,
    arc_radius_m: float = 3.0,
    height_m: float = 2.0,
    base_width_m: float = 0.5,
    tip_width_m: float = 0.15,
    thickness_m: float = 0.02,
    layout_diameter_m: float = 2.0,
    base_plate_diameter_m: float | None = None,
    base_plate_thickness_m: float = 0.05,
    fin_segments: int = 12,
    shell_thickness_m: float | None = None,
    material: str = "stainless_304",
) -> dict:
    if fin_count < 1:
        raise ValueError("fin_count must be >= 1")
    if height_m <= 0 or arc_radius_m <= 0:
        raise ValueError("height_m and arc_radius_m must be positive")
    if fin_segments < 2:
        raise ValueError("fin_segments must be >= 2")

    layout_r = layout_diameter_m / 2.0
    fin_v, fin_f = _fin(height_m, arc_radius_m, base_width_m, tip_width_m,
                        thickness_m, fin_segments + 1)

    parts: list[tuple[np.ndarray, np.ndarray]] = []
    for k in range(fin_count):
        ang = 2.0 * math.pi * k / fin_count
        rot = np.array([
            [math.cos(ang), 0.0, math.sin(ang)],
            [0.0, 1.0, 0.0],
            [-math.sin(ang), 0.0, math.cos(ang)],
        ])
        v = fin_v @ rot.T + np.array([layout_r * math.cos(ang), 0.0,
                                      layout_r * math.sin(ang)])
        parts.append((v, fin_f))

    plate_d = base_plate_diameter_m or (layout_diameter_m + 2.0 * base_width_m + 0.4)
    pr = plate_d / 2.0
    plate_profile = [(0.0, 0.0), (pr, 0.0), (pr, base_plate_thickness_m),
                     (0.0, base_plate_thickness_m)]
    plate_v, plate_f = revolve_profile(plate_profile, 48)
    plate_v = plate_v - np.array([0.0, base_plate_thickness_m, 0.0])  # top at y=0
    parts.append((plate_v, plate_f))

    vertices, faces = combine_meshes(parts)

    return finalize(vertices, faces, "arc_fin_array", material, shell_thickness_m,
                    extra={
                        "fin_count": fin_count,
                        "height_m": height_m,
                        "arc_radius_m": arc_radius_m,
                        "layout_diameter_m": layout_diameter_m,
                        "base_plate_diameter_m": plate_d,
                        "led_channel_grooves": fin_count,  # one spine groove per fin
                    })
