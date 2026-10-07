"""Structural skeleton generator (scope §15, §17).

Converts the artistic shell into a buildable internal frame:

    vertical SHS spine at the cross-section centroid
    + horizontal rib spokes reaching toward the shell at regular stations
    + base frame ring on the base plate

Member sizing is load-driven: the required section modulus comes from the
structural base moment (S_req = M / sigma_allow), and the smallest catalog
SHS satisfying it is selected. The generated steel weight replaces the
structural module's heuristic armature estimate in the BOM.

Output doubles as visualization: members are emitted as capped cylinder
meshes so the viewer can toggle a skeleton/x-ray mode.
"""

import math

import numpy as np

STEEL_DENSITY = 7850.0
ARMATURE_FY_PA = 250e6
SF = 1.5
RIB_SPACING_M = 0.6
RIB_REACH_FRACTION = 0.85       # stop inside the shell
RIB_TUBE_RADIUS_M = 0.02        # 40 mm OD rib tubes
BASE_FRAME_MARGIN_M = 0.05

# SHS catalog (side mm, wall mm), smallest first.
SHS_CATALOG = [(50, 3), (60, 3), (60, 4), (80, 4), (100, 5), (120, 5),
               (150, 6), (200, 8), (250, 10), (300, 12), (400, 16)]


def shs_properties(side_mm: float, wall_mm: float) -> dict:
    """Thin-wall-exact SHS section properties (SI)."""
    b = side_mm / 1000.0
    t = wall_mm / 1000.0
    bi = b - 2.0 * t
    area_m2 = b * b - bi * bi
    i_m4 = (b**4 - bi**4) / 12.0
    z_m3 = i_m4 / (b / 2.0)
    return {"area_m2": area_m2, "i_m4": i_m4, "z_m3": z_m3,
            "kg_per_m": area_m2 * STEEL_DENSITY}


def select_shs(moment_knm: float) -> tuple[tuple[int, int], dict]:
    """Smallest catalog SHS with Z >= M / sigma_allow."""
    s_req = moment_knm * 1000.0 / (ARMATURE_FY_PA / SF)
    for section in SHS_CATALOG:
        props = shs_properties(*section)
        if props["z_m3"] >= s_req:
            return section, props
    section = SHS_CATALOG[-1]
    return section, shs_properties(*section)


def _tube_between(p1, p2, radius: float, sides: int = 10):
    """Capped cylinder mesh between two 3D points."""
    p1 = np.asarray(p1, dtype=float)
    p2 = np.asarray(p2, dtype=float)
    axis = p2 - p1
    length = float(np.linalg.norm(axis))
    if length < 1e-9:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=int)
    t = axis / length
    ref = np.array([0.0, 0.0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
    n = ref - np.dot(ref, t) * t
    n /= np.linalg.norm(n)
    b = np.cross(t, n)

    vertices: list[list[float]] = []
    for p in (p1, p2):
        for j in range(sides):
            a = 2 * math.pi * j / sides
            off = radius * (math.cos(a) * n + math.sin(a) * b)
            vertices.append((p + off).tolist())
    faces: list[list[int]] = []
    for j in range(sides):
        j1 = (j + 1) % sides
        faces.append([j, sides + j, sides + j1])
        faces.append([j, sides + j1, j1])
    c1, c2 = 2 * sides, 2 * sides + 1
    vertices += [p1.tolist(), p2.tolist()]
    for j in range(sides):
        j1 = (j + 1) % sides
        faces.append([c1, j1, j])
        faces.append([c2, sides + j, sides + j1])
    return np.asarray(vertices), np.asarray(faces, dtype=int)


def generate_skeleton(brief: dict, geo: dict, structural: dict,
                      shell_vertices=None,
                      force_section: tuple[int, int] | None = None) -> dict:
    bbox = geo["bounding_box"]
    (x0, y0, z0), (x1, y1, z1) = bbox["min"], bbox["max"]
    height_m = max(y1 - y0, 0.1)
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0

    moment_knm = structural.get("total_base_moment_knm",
                                structural.get("overturning_moment_knm", 0.0))
    if force_section is not None:
        section = force_section
        props = shs_properties(*section)
    else:
        section, props = select_shs(moment_knm)
    side_m = section[0] / 1000.0

    members: list[dict] = []

    # ── Spine: full-height SHS at the plan centroid ─────────────────────
    members.append({"kind": "spine", "section": f"SHS {section[0]}x{section[0]}x{section[1]}",
                    "from": [cx, y0, cz], "to": [cx, y1 * 0.95, cz],
                    "length_m": round(y1 * 0.95 - y0, 3)})

    # ── Ribs: spokes from spine toward the shell at regular stations ────
    band = max(0.05, height_m * 0.03)
    verts = np.asarray(shell_vertices, dtype=float) if shell_vertices is not None else None
    y = y0 + RIB_SPACING_M
    while y < y1 * 0.9:
        reach_x, reach_z = (x1 - x0) / 2.0, (z1 - z0) / 2.0
        if verts is not None and len(verts):
            mask = np.abs(verts[:, 1] - y) < band
            if mask.any():
                sel = verts[mask]
                reach_x = float(np.abs(sel[:, 0] - cx).max())
                reach_z = float(np.abs(sel[:, 2] - cz).max())
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            reach = (reach_x if dx else reach_z) * RIB_REACH_FRACTION
            if reach < side_m:
                continue
            members.append({
                "kind": "rib", "section": "tube 40x2",
                "from": [cx, y, cz],
                "to": [cx + dx * reach, y, cz + dz * reach],
                "length_m": round(reach, 3)})
        y += RIB_SPACING_M

    # ── Base frame: square ring at the base, tied to the spine foot ─────
    fw = (x1 - x0) / 2.0 * RIB_REACH_FRACTION
    fd = (z1 - z0) / 2.0 * RIB_REACH_FRACTION
    corners = [(cx - fw, y0, cz - fd),
               (cx + fw, y0, cz - fd),
               (cx + fw, y0, cz + fd),
               (cx - fw, y0, cz + fd)]
    for i in range(4):
        p1, p2 = corners[i], corners[(i + 1) % 4]
        length = float(np.linalg.norm(np.subtract(p2, p1)))
        members.append({"kind": "base_frame",
                        "section": f"SHS {section[0]}x{section[0]}x{section[1]}",
                        "from": list(p1), "to": list(p2),
                        "length_m": round(length, 3)})
        # Diagonal tie: corner -> spine foot (keeps the frame one mechanism-
        # free body — required for the FEA model to be determinate-stable).
        tie_len = float(np.linalg.norm(np.subtract(p1, (cx, y0, cz))))
        members.append({"kind": "base_tie",
                        "section": f"SHS {section[0]}x{section[0]}x{section[1]}",
                        "from": list(p1), "to": [cx, y0, cz],
                        "length_m": round(tie_len, 3)})

    # ── Weights ─────────────────────────────────────────────────────────
    rib_kg_per_m = shs_properties(40, 2)["kg_per_m"]
    total_kg = 0.0
    for m in members:
        kg_m = props["kg_per_m"] if m["section"].startswith("SHS") else rib_kg_per_m
        m["weight_kg"] = round(m["length_m"] * kg_m, 2)
        total_kg += m["weight_kg"]

    # ── Visualization mesh ──────────────────────────────────────────────
    parts = []
    for m in members:
        r = side_m / 2.0 if m["section"].startswith("SHS") else RIB_TUBE_RADIUS_M
        parts.append(_tube_between(m["from"], m["to"], r))
    sv = [p[0] for p in parts if len(p[0])]
    sf_ = [p[1] for p in parts if len(p[0])]
    if sv:
        from geometry.archetypes._common import combine_meshes
        mv, mf = combine_meshes(list(zip(sv, sf_)))
        mesh = {"vertices": mv.tolist(), "faces": mf.tolist()}
    else:
        mesh = {"vertices": [], "faces": []}

    return {
        "section": f"SHS {section[0]}x{section[0]}x{section[1]}",
        "section_z_cm3": round(props["z_m3"] * 1e6, 1),
        "required_z_cm3": round(moment_knm * 1000.0 / (ARMATURE_FY_PA / SF) * 1e6, 1),
        "section_adequate": props["z_m3"] * 1e6 >= round(
            moment_knm * 1000.0 / (ARMATURE_FY_PA / SF) * 1e6, 1),
        "member_count": len(members),
        "members": members,
        "total_steel_kg": round(total_kg, 1),
        "mesh": mesh,
    }
