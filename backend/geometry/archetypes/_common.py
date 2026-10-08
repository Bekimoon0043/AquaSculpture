"""Shared helpers for archetype generators.

Every generator returns {"vertices", "faces", "metadata"}; `finalize` fills in
the standard metadata (shell mass via data/materials.json density) and
guarantees outward face winding via the signed-volume test.
"""

import json
import math
from pathlib import Path

import numpy as np

from config import DATA_DIR
MATERIALS_PATH = DATA_DIR / "materials.json"
DEFAULT_SHELL_THICKNESS_M = 0.003


def load_material(material: str) -> dict:
    with MATERIALS_PATH.open("r", encoding="utf-8") as f:
        catalog = json.load(f)
    return catalog.get(material, catalog["stainless_316l"])


def mesh_surface_area(vertices: np.ndarray, faces: np.ndarray) -> float:
    tris = vertices[faces]
    return float(0.5 * np.linalg.norm(
        np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1).sum())


def signed_volume(vertices: np.ndarray, faces: np.ndarray) -> float:
    tris = vertices[faces]
    return float(np.einsum("ij,ij->i", tris[:, 0],
                           np.cross(tris[:, 1], tris[:, 2])).sum() / 6.0)


def ensure_outward(vertices: np.ndarray, faces: np.ndarray) -> np.ndarray:
    """Flip all triangle windings if the mesh is inside-out."""
    if signed_volume(vertices, faces) < 0:
        return faces[:, [0, 2, 1]]
    return faces


def combine_meshes(parts: list[tuple[np.ndarray, np.ndarray]]):
    """Merge (vertices, faces) parts into single arrays."""
    verts: list[np.ndarray] = []
    faces: list[np.ndarray] = []
    offset = 0
    for v, f in parts:
        verts.append(np.asarray(v, dtype=float))
        faces.append(np.asarray(f, dtype=int) + offset)
        offset += len(verts[-1])
    return np.vstack(verts), np.vstack(faces)


def revolve_profile(profile: list[tuple[float, float]], segments: int):
    """Revolve a closed (r, y) profile around the Y axis -> watertight mesh.

    r == 0 points become shared pole vertices so edges stay balanced.
    """
    n = len(profile)
    angles = np.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
    cos_a, sin_a = np.cos(angles), np.sin(angles)

    vertices: list[list[float]] = []
    rings: list[list[int]] = []
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
            continue
        if len(a) == 1:
            for j in range(segments):
                faces.append([a[0], b[j], b[(j + 1) % segments]])
        elif len(b) == 1:
            for j in range(segments):
                faces.append([a[j], b[0], a[(j + 1) % segments]])
        else:
            for j in range(segments):
                j1 = (j + 1) % segments
                faces.append([a[j], b[j], b[j1]])
                faces.append([a[j], b[j1], a[j1]])
    return np.asarray(vertices, dtype=float), np.asarray(faces, dtype=int)


def polygon_area_2d(outline: list[tuple[float, float]]) -> float:
    """Signed shoelace area (positive for CCW)."""
    area = 0.0
    n = len(outline)
    for i in range(n):
        x0, y0 = outline[i]
        x1, y1 = outline[(i + 1) % n]
        area += x0 * y1 - x1 * y0
    return area / 2.0


def extrude_polygon(outline: list[tuple[float, float]], thickness_m: float):
    """Extrude a 2D XY polygon along Z by thickness_m -> watertight solid.

    Caps are centroid fans (outline must be star-shaped about its centroid).
    """
    if len(outline) < 3:
        raise ValueError("outline needs at least 3 points")
    pts = [(float(x), float(y)) for x, y in outline]
    if polygon_area_2d(pts) < 0:  # force CCW
        pts = pts[::-1]
    n = len(pts)
    hz = thickness_m / 2.0
    cx = sum(p[0] for p in pts) / n
    cy = sum(p[1] for p in pts) / n

    vertices = [[x, y, hz] for x, y in pts]          # front ring 0..n-1
    vertices += [[x, y, -hz] for x, y in pts]        # back ring n..2n-1
    vertices.append([cx, cy, hz])                    # front centroid 2n
    vertices.append([cx, cy, -hz])                   # back centroid 2n+1

    faces: list[list[int]] = []
    for i in range(n):
        i1 = (i + 1) % n
        faces.append([2 * n, i, i1])                 # front cap (+z)
        faces.append([2 * n + 1, n + i1, n + i])     # back cap (-z)
        faces.append([i, n + i, n + i1])             # side
        faces.append([i, n + i1, i1])
    return np.asarray(vertices, dtype=float), np.asarray(faces, dtype=int)


def finalize(vertices, faces, family: str, material: str,
             shell_thickness_m: float | None, extra: dict | None = None) -> dict:
    """Standard generator return: outward winding + engineering metadata."""
    v = np.asarray(vertices, dtype=float)
    f = ensure_outward(v, np.asarray(faces, dtype=int))

    surface_area = mesh_surface_area(v, f)
    mat = load_material(material)
    thickness = shell_thickness_m if shell_thickness_m else mat.get(
        "default_shell_thickness_m", DEFAULT_SHELL_THICKNESS_M)

    metadata = {
        "family": family,
        "material": material,
        "shell_thickness_m": thickness,
        "surface_area_m2": surface_area,
        "volume_m3": abs(signed_volume(v, f)),
        "mass_kg": surface_area * thickness * mat["density_kg_m3"],
        "vertex_count": int(len(v)),
        "face_count": int(len(f)),
    }
    if extra:
        metadata.update(extra)
    return {"vertices": v.tolist(), "faces": f.tolist(), "metadata": metadata}
