"""Stacked open rings / disks composition (PLAN.md §5.1, reproduces P8/P9).

Vertical totem of C-rings (open_ring segments) and flat disks/saucers,
stacked with per-element gaps. Increasing diameters supported.
"""

import numpy as np

from geometry.archetypes._common import combine_meshes, finalize, revolve_profile
from geometry.archetypes.open_ring import generate_open_ring

DEFAULT_ELEMENTS = [
    {"type": "ring", "diameter_m": 2.0, "opening_deg": 90.0, "thickness_m": 0.12,
     "z_gap_m": 0.30},
    {"type": "disk", "diameter_m": 1.6, "thickness_m": 0.06, "z_gap_m": 0.30},
    {"type": "ring", "diameter_m": 2.6, "opening_deg": 90.0, "thickness_m": 0.14,
     "z_gap_m": 0.30},
    {"type": "disk", "diameter_m": 2.0, "thickness_m": 0.06, "z_gap_m": 0.30},
    {"type": "ring", "diameter_m": 3.2, "opening_deg": 90.0, "thickness_m": 0.16,
     "z_gap_m": 0.0},
]


def _disk(diameter_m: float, thickness_m: float, segments: int):
    r = diameter_m / 2.0
    profile = [(0.0, 0.0), (r, 0.0), (r, thickness_m), (0.0, thickness_m)]
    return revolve_profile(profile, segments)


def generate_stacked_rings(
    elements: list | None = None,
    segments: int = 48,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    elements = elements or DEFAULT_ELEMENTS
    if not elements:
        raise ValueError("elements list must not be empty")

    parts: list[tuple[np.ndarray, np.ndarray]] = []
    y_cursor = 0.0
    total_height = 0.0
    for idx, el in enumerate(elements):
        etype = el.get("type")
        diameter_m = el.get("diameter_m")
        thickness_m = el.get("thickness_m", 0.1)
        if not diameter_m or diameter_m <= 0:
            raise ValueError(f"element {idx}: diameter_m required")
        if etype == "ring":
            sub = generate_open_ring(
                diameter_m=diameter_m,
                tube_radius_m=thickness_m / 2.0,
                opening_deg=el.get("opening_deg", 90.0),
                segments=segments,
            )
            v = np.asarray(sub["vertices"], dtype=float)
            f = np.asarray(sub["faces"], dtype=int)
        elif etype == "disk":
            v, f = _disk(diameter_m, thickness_m, segments)
        else:
            raise ValueError(f"element {idx}: unknown type '{etype}'")

        v = v - np.array([0.0, v[:, 1].min(), 0.0])  # seat element base at 0
        part_height = float(v[:, 1].max())
        v = v + np.array([0.0, y_cursor, 0.0])
        parts.append((v, f))
        total_height = y_cursor + part_height
        y_cursor = total_height + el.get("z_gap_m", 0.0)

    vertices, faces = combine_meshes(parts)
    return finalize(vertices, faces, "stacked_rings", material, shell_thickness_m,
                    extra={
                        "element_count": len(elements),
                        "total_height_m": total_height,
                        "elements": elements,
                    })
