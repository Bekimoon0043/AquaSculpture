"""Parametric basin/pool geometry (PLAN.md §5.3 — basin).

Circular basins are solids of revolution from a closed wall/floor profile;
rectangular basins are assembled from quads. Both emit watertight
vertices/faces like the archetype generators, plus engineering metadata:
water volume, wetted surface area, perimeter-weir length and bubbler
placement. Y is up; the basin floor bottom sits at y=0.
"""

import math

import numpy as np

WALL_THICKNESS_M = 0.15
FLOOR_THICKNESS_M = 0.15
FREEBOARD_M = 0.10
DEFAULT_SEGMENTS = 72


# ---------------------------------------------------------------- circular

def _revolve_profile(profile: list[tuple[float, float]], segments: int):
    """Revolve a closed (r, y) profile around the Y axis -> watertight mesh.

    Profile points with r == 0 become single pole vertices shared by all
    segments so edges stay balanced.
    """
    n = len(profile)
    angles = np.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
    cos_a, sin_a = np.cos(angles), np.sin(angles)

    vertices: list[list[float]] = []
    rings: list[list[int]] = []  # vertex indices per profile point
    for r, y in profile:
        if abs(r) < 1e-12:
            rings.append([len(vertices)])
            vertices.append([0.0, y, 0.0])
        else:
            ring = []
            for j in range(segments):
                ring.append(len(vertices))
                vertices.append([r * cos_a[j], y, r * sin_a[j]])
            rings.append(ring)

    faces: list[list[int]] = []
    for i in range(n):
        a = rings[i]
        b = rings[(i + 1) % n]
        if len(a) == 1 and len(b) == 1:
            continue  # degenerate pole-to-pole edge
        if len(a) == 1:
            for j in range(segments):
                j1 = (j + 1) % segments
                faces.append([a[0], b[j], b[j1]])
        elif len(b) == 1:
            for j in range(segments):
                j1 = (j + 1) % segments
                faces.append([a[j], b[0], a[j1]])
        else:
            for j in range(segments):
                j1 = (j + 1) % segments
                faces.append([a[j], b[j], b[j1]])
                faces.append([a[j], b[j1], a[j1]])
    return vertices, faces


def _circular(diameter_m: float, depth_m: float, segments: int):
    r_i = diameter_m / 2.0
    r_o = r_i + WALL_THICKNESS_M
    # Closed loop: bottom center -> outer wall -> rim -> inner wall -> floor.
    profile = [
        (0.0, 0.0),
        (r_o, 0.0),
        (r_o, depth_m),
        (r_i, depth_m),
        (r_i, FLOOR_THICKNESS_M),
        (0.0, FLOOR_THICKNESS_M),
    ]
    vertices, faces = _revolve_profile(profile, segments)
    water_depth = depth_m - FLOOR_THICKNESS_M - FREEBOARD_M
    water_volume = math.pi * r_i**2 * water_depth
    wetted_area = math.pi * r_i**2 + 2.0 * math.pi * r_i * water_depth
    weir_length = 2.0 * math.pi * r_i
    inner = {"radius_m": r_i}
    return vertices, faces, water_volume, wetted_area, weir_length, inner


# ------------------------------------------------------------- rectangular

def _add_quad(vertices: list, faces: list, corners: list[tuple[float, float, float]]):
    """Append a quad (4 corners CCW seen from outside) as two triangles."""
    idx = []
    for c in corners:
        idx.append(len(vertices))
        vertices.append(list(c))
    faces.append([idx[0], idx[1], idx[2]])
    faces.append([idx[0], idx[2], idx[3]])


def _rectangular(length_m: float, width_m: float, depth_m: float):
    li, wi = length_m, width_m
    lo, wo = length_m + 2 * WALL_THICKNESS_M, width_m + 2 * WALL_THICKNESS_M
    h, tf = depth_m, FLOOR_THICKNESS_M
    xi, zi = li / 2.0, wi / 2.0
    xo, zo = lo / 2.0, wo / 2.0

    vertices: list = []
    faces: list = []

    # Outer shell: bottom and four walls (normals outward).
    _add_quad(vertices, faces, [(-xo, 0, -zo), (xo, 0, -zo), (xo, 0, zo), (-xo, 0, zo)])
    _add_quad(vertices, faces, [(-xo, 0, -zo), (-xo, h, -zo), (xo, h, -zo), (xo, 0, -zo)])
    _add_quad(vertices, faces, [(xo, 0, zo), (xo, h, zo), (-xo, h, zo), (-xo, 0, zo)])
    _add_quad(vertices, faces, [(-xo, 0, zo), (-xo, h, zo), (-xo, h, -zo), (-xo, 0, -zo)])
    _add_quad(vertices, faces, [(xo, 0, -zo), (xo, h, -zo), (xo, h, zo), (xo, 0, zo)])

    # Rim: frame between outer and inner rectangle at y = h (normal +y).
    _add_quad(vertices, faces, [(-xo, h, -zo), (-xi, h, -zi), (xi, h, -zi), (xo, h, -zo)])
    _add_quad(vertices, faces, [(xo, h, -zo), (xi, h, -zi), (xi, h, zi), (xo, h, zo)])
    _add_quad(vertices, faces, [(xo, h, zo), (xi, h, zi), (-xi, h, zi), (-xo, h, zo)])
    _add_quad(vertices, faces, [(-xo, h, zo), (-xi, h, zi), (-xi, h, -zi), (-xo, h, -zo)])

    # Inner cavity walls (normals into the water) and floor.
    _add_quad(vertices, faces, [(-xi, tf, -zi), (xi, tf, -zi), (xi, h, -zi), (-xi, h, -zi)])
    _add_quad(vertices, faces, [(xi, tf, zi), (-xi, tf, zi), (-xi, h, zi), (xi, h, zi)])
    _add_quad(vertices, faces, [(-xi, tf, zi), (-xi, tf, -zi), (-xi, h, -zi), (-xi, h, zi)])
    _add_quad(vertices, faces, [(xi, tf, -zi), (xi, tf, zi), (xi, h, zi), (xi, h, -zi)])
    _add_quad(vertices, faces, [(-xi, tf, -zi), (-xi, tf, zi), (xi, tf, zi), (xi, tf, -zi)])

    water_depth = depth_m - FLOOR_THICKNESS_M - FREEBOARD_M
    water_volume = li * wi * water_depth
    wetted_area = li * wi + 2.0 * (li + wi) * water_depth
    weir_length = 2.0 * (li + wi)
    inner = {"length_m": li, "width_m": wi}
    return vertices, faces, water_volume, wetted_area, weir_length, inner


# -------------------------------------------------------------- public API

def place_bubblers(count: int, footprint_radius_m: float, inner: dict,
                   clearance_m: float = 0.6, min_spacing_m: float = 0.8,
                   edge_clearance_m: float = 0.4) -> list[list[float]]:
    """Ring layout of `count` jets around the sculpture footprint.

    Rings at footprint + clearance + k*min_spacing; jets on a ring keep
    >= min_spacing along the chord and stay inside the basin inner bounds
    minus edge_clearance. Raises ValueError if they cannot be placed.
    """
    if count <= 0:
        return []
    positions: list[list[float]] = []
    ring = 0
    while len(positions) < count and ring < 20:
        r = footprint_radius_m + clearance_m + ring * min_spacing_m
        if "radius_m" in inner:
            if r > inner["radius_m"] - edge_clearance_m:
                break
        else:
            if (r > inner["length_m"] / 2.0 - edge_clearance_m
                    or r > inner["width_m"] / 2.0 - edge_clearance_m):
                break
        capacity = max(1, int(2.0 * math.pi * r // min_spacing_m))
        take = min(capacity, count - len(positions))
        for j in range(take):
            a = 2.0 * math.pi * j / take + ring * 0.35  # stagger rings
            positions.append([r * math.cos(a), FLOOR_THICKNESS_M, r * math.sin(a)])
        ring += 1
    if len(positions) < count:
        raise ValueError(
            f"cannot place {count} jets with {clearance_m} m clearance / "
            f"{min_spacing_m} m spacing in this basin")
    return positions


def generate_basin(basin_brief: dict, features: list | None = None,
                   footprint_radius_m: float = 0.5,
                   segments: int = DEFAULT_SEGMENTS) -> dict:
    """Generate basin mesh + metadata from brief.water.basin.

    `features` is brief.water.features — bubbler fields get jet positions;
    overflow == perimeter_weir reports the weir length.
    """
    shape = basin_brief.get("shape")
    depth_m = basin_brief.get("depth_m", 0.45)

    if shape == "circular":
        diameter_m = basin_brief.get("diameter_m")
        if not diameter_m:
            raise ValueError("circular basin requires diameter_m")
        vertices, faces, vol, wet, weir, inner = _circular(diameter_m, depth_m, segments)
    elif shape == "rectangular":
        length_m = basin_brief.get("length_m")
        width_m = basin_brief.get("width_m")
        if not length_m or not width_m:
            raise ValueError("rectangular basin requires length_m and width_m")
        vertices, faces, vol, wet, weir, inner = _rectangular(length_m, width_m, depth_m)
    else:
        raise ValueError(f"unsupported basin shape '{shape}'")

    overflow = basin_brief.get("overflow")
    nozzles: list[list[float]] = []
    nozzle_notes: list[str] = []
    for feat in features or []:
        if feat.get("type") in ("bubbler_field", "foam_jet_field") and feat.get("count"):
            wanted = feat["count"]
            placed = None
            for clearance, edge in ((0.6, 0.4), (0.4, 0.3), (0.3, 0.2)):
                for n in range(wanted, 0, -1):
                    try:
                        placed = place_bubblers(n, footprint_radius_m, inner,
                                                clearance_m=clearance,
                                                edge_clearance_m=edge)
                        break
                    except ValueError:
                        continue
                if placed is not None:
                    break
            if placed is None:
                nozzle_notes.append(
                    f"no {feat['type']} jets fit around a {footprint_radius_m:.2f} m "
                    f"footprint in this basin")
            else:
                if len(placed) < wanted:
                    nozzle_notes.append(
                        f"{feat['type']}: placed {len(placed)} of {wanted} requested "
                        f"jets (basin/footprint too tight)")
                nozzles.extend(placed)

    metadata = {
        "shape": shape,
        "depth_m": depth_m,
        "wall_thickness_m": WALL_THICKNESS_M,
        "floor_thickness_m": FLOOR_THICKNESS_M,
        "freeboard_m": FREEBOARD_M,
        "water_volume_m3": vol,
        "wetted_area_m2": wet,
        "weir_length_m": weir if overflow == "perimeter_weir" else None,
        "overflow": overflow,
        "inner": inner,
        "nozzle_positions": nozzles,
        "nozzle_notes": nozzle_notes,
        "vertex_count": len(vertices),
        "face_count": len(faces),
    }
    return {"vertices": np.asarray(vertices, dtype=float).tolist(),
            "faces": np.asarray(faces, dtype=int).tolist(),
            "metadata": metadata}
