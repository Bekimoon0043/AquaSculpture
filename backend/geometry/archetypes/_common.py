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
