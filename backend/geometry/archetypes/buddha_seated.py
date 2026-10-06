"""Seated Buddha (dhyana mudra) — figurative archetype v1.

Stylized-maquette quality (PLAN.md §4 risk note): the figure is composed of
closed primitive sub-meshes — lathe profiles for pedestal/legs/torso,
ellipsoids for head/knees/hands/ears, swept tubes for arms. Parts intersect,
so the combined mesh is not globally watertight and signed volume slightly
over-counts overlaps; surface area and bbox are exact. Proportions follow
classical seated-Buddha canon relative to total height H.
"""

import numpy as np

from geometry.archetypes._common import (combine_meshes, finalize,
                                         revolve_profile)


def _ellipsoid(rx: float, ry: float, rz: float, center: tuple,
               seg_u: int = 24, seg_v: int = 16):
    """Closed UV ellipsoid, poles shared."""
    vertices: list[list[float]] = []
    rings: list[list[int]] = []
    for i in range(seg_v + 1):
        phi = -np.pi / 2 + np.pi * i / seg_v  # -90..90 deg
        r = np.cos(phi)
        y = ry * np.sin(phi)
        if abs(r) < 1e-12:
            rings.append([len(vertices)])
            vertices.append([center[0], center[1] + y, center[2]])
        else:
            ring = []
            for j in range(seg_u):
                a = 2 * np.pi * j / seg_u
                ring.append(len(vertices))
                vertices.append([center[0] + rx * r * np.cos(a),
                                 center[1] + y,
                                 center[2] + rz * r * np.sin(a)])
            rings.append(ring)
    faces: list[list[int]] = []
    for i in range(seg_v):
        a, b = rings[i], rings[i + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for j in range(seg_u):
                faces.append([a[0], b[(j + 1) % seg_u], b[j]])
        elif len(b) == 1:
            for j in range(seg_u):
                faces.append([a[j], b[0], a[(j + 1) % seg_u]])
        else:
            for j in range(seg_u):
                j1 = (j + 1) % seg_u
                faces.append([a[j], b[j], b[j1]])
                faces.append([a[j], b[j1], a[j1]])
    return np.array(vertices), np.array(faces, dtype=int)


def _swept_tube(path: np.ndarray, radius: float, sides: int = 12):
    """Capped tube swept along a 3D polyline (parallel-transport frames)."""
    n = len(path)
    tangents = np.gradient(path, axis=0)
    tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)

    # Initial frame: any vector not parallel to the first tangent.
    t0 = tangents[0]
    ref = np.array([0.0, 0.0, 1.0]) if abs(t0[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    normal = ref - np.dot(ref, t0) * t0
    normal /= np.linalg.norm(normal)

    vertices: list[list[float]] = []
    for i in range(n):
        t = tangents[i]
        normal = normal - np.dot(normal, t) * t  # parallel transport
        normal /= np.linalg.norm(normal)
        binormal = np.cross(t, normal)
        for j in range(sides):
            a = 2 * np.pi * j / sides
            p = path[i] + radius * (np.cos(a) * normal + np.sin(a) * binormal)
            vertices.append(p.tolist())

    faces: list[list[int]] = []
    for i in range(n - 1):
        for j in range(sides):
            j1 = (j + 1) % sides
            a0, b0 = i * sides + j, (i + 1) * sides + j
            c0, d0 = (i + 1) * sides + j1, i * sides + j1
            faces.append([a0, b0, c0])
            faces.append([a0, c0, d0])
    # End caps (centroid fans).
    base_c = len(vertices)
    vertices.append(path[0].tolist())
    tip_c = len(vertices)
    vertices.append(path[-1].tolist())
    for j in range(sides):
        j1 = (j + 1) % sides
        faces.append([base_c, j1, j])  # base faces -tangent
        e = (n - 1) * sides
        faces.append([tip_c, e + j, e + j1])  # tip faces +tangent
    return np.array(vertices), np.array(faces, dtype=int)


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
