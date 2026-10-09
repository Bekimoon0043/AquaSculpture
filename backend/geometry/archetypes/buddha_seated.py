"""Seated Buddha (dhyana mudra) — figurative archetype v1.

Stylized-maquette quality (PLAN.md §4 risk note): the figure is composed of
closed primitive sub-meshes — lathe profiles for pedestal/legs/torso,
ellipsoids for head/knees/hands/ears, swept tubes for arms. Parts intersect,
so the combined mesh is not globally watertight and signed volume slightly
over-counts overlaps; surface area and bbox are exact. Proportions follow
classical seated-Buddha canon relative to total height H.
"""

import numpy as np

from geometry.archetypes._common import (_ellipsoid, _swept_tube,
                                         combine_meshes, finalize,
                                         revolve_profile)


def generate_buddha_seated(
    height_m: float = 2.0,
    pedestal: bool = True,
    segments: int = 48,
    shell_thickness_m: float | None = None,
    material: str = "bronze",
) -> dict:
    if height_m <= 0:
        raise ValueError("height_m must be positive")

    H = height_m
    parts: list[tuple[np.ndarray, np.ndarray]] = []

    # ── Double-lotus pedestal (0 .. 0.16H) ──────────────────────────────
    if pedestal:
        r = 0.30 * H
        lotus = [
            (0.0, 0.0),
            (0.86 * r, 0.0),
            (r, 0.03 * H),          # lower petal flare
            (0.92 * r, 0.07 * H),
            (0.80 * r, 0.09 * H),   # waist between the two lotus tiers
            (0.95 * r, 0.12 * H),   # upper petal flare
            (0.90 * r, 0.15 * H),
            (0.0, 0.16 * H),        # seat
        ]
        parts.append(revolve_profile(lotus, segments))
    seat_y = 0.16 * H if pedestal else 0.0

    # ── Crossed legs: broad lap mound + two knees ───────────────────────
    lap = [
        (0.0, seat_y),
        (0.24 * H, seat_y),
        (0.28 * H, seat_y + 0.05 * H),
        (0.24 * H, seat_y + 0.10 * H),
        (0.0, seat_y + 0.12 * H),
    ]
    parts.append(revolve_profile(lap, segments))
    for side in (-1, 1):
        parts.append(_ellipsoid(0.09 * H, 0.07 * H, 0.09 * H,
                                (side * 0.20 * H, seat_y + 0.05 * H, 0.06 * H)))

    # ── Torso with shoulders and neck (lathe) ───────────────────────────
    torso = [
        (0.0, seat_y + 0.06 * H),
        (0.16 * H, seat_y + 0.06 * H),
        (0.14 * H, seat_y + 0.18 * H),   # waist
        (0.155 * H, seat_y + 0.30 * H),  # chest
        (0.16 * H, seat_y + 0.40 * H),   # shoulders
        (0.10 * H, seat_y + 0.455 * H),  # shoulder round-off
        (0.05 * H, seat_y + 0.48 * H),   # neck
        (0.05 * H, seat_y + 0.52 * H),
        (0.0, seat_y + 0.52 * H),
    ]
    parts.append(revolve_profile(torso, segments))

    # ── Arms: swept tubes shoulder -> elbow -> hands in lap ─────────────
    for side in (-1, 1):
        path = np.array([
            [side * 0.15 * H, seat_y + 0.42 * H, 0.0],          # shoulder
            [side * 0.19 * H, seat_y + 0.28 * H, 0.04 * H],     # upper arm
            [side * 0.17 * H, seat_y + 0.14 * H, 0.08 * H],     # elbow
            [side * 0.09 * H, seat_y + 0.10 * H, 0.13 * H],     # forearm
            [side * 0.03 * H, seat_y + 0.115 * H, 0.15 * H],    # wrist
        ])
        parts.append(_swept_tube(path, 0.038 * H))

    # ── Hands resting in lap (dhyana mudra) ─────────────────────────────
    parts.append(_ellipsoid(0.085 * H, 0.028 * H, 0.055 * H,
                            (0.0, seat_y + 0.12 * H, 0.15 * H)))

    # ── Head + ushnisha + elongated earlobes ────────────────────────────
    head_y = seat_y + 0.60 * H
    parts.append(_ellipsoid(0.085 * H, 0.10 * H, 0.09 * H, (0.0, head_y, 0.0)))
    parts.append(_ellipsoid(0.045 * H, 0.045 * H, 0.045 * H,
                            (0.0, head_y + 0.11 * H, 0.0)))     # ushnisha
    for side in (-1, 1):
        parts.append(_ellipsoid(0.018 * H, 0.055 * H, 0.025 * H,
                                (side * 0.092 * H, head_y - 0.03 * H, 0.0)))

    vertices, faces = combine_meshes(parts)

    # Normalize: the canonical proportions above reach ~0.92 H; scale so the
    # finished figure is exactly height_m tall, base at y=0.
    y0 = float(vertices[:, 1].min())
    vertices[:, 1] -= y0
    scale = H / float(vertices[:, 1].max())
    vertices *= scale

    return finalize(vertices, faces, "buddha_seated", material, shell_thickness_m,
                    extra={"height_m": H, "pose": "dhyana_mudra",
                           "pedestal": pedestal,
                           "note": "stylized figurative v1; parts intersect — "
                                   "volume slightly over-counted"})
