"""Open ring / crescent sculpture generator (PLAN.md §5.1, reproduces P6/P7 bases).

Pure numpy — emits a capped tube swept along a circular arc with an opening gap
centered at the bottom. The ring stands in the vertical XY plane; `tilt_deg`
rotates the whole form about the X axis.

Every sculpture is a hollow shell: `mass_kg` = surface area x shell thickness x
material density (densities in backend/data/materials.json).
"""

import json
import math
from pathlib import Path

import numpy as np

from config import DATA_DIR
MATERIALS_PATH = DATA_DIR / "materials.json"

DEFAULT_SHELL_THICKNESS_M = 0.003


def _load_material(material: str) -> dict:
    with MATERIALS_PATH.open("r", encoding="utf-8") as f:
        catalog = json.load(f)
    return catalog.get(material, catalog["stainless_316l"])


def _section_offsets(tube_segments: int, radial_half: float, axial_half: float,
                     rectangular: bool) -> np.ndarray:
    """Cross-section perimeter offsets in (radial, axial) coordinates."""
    phi = np.linspace(0.0, 2.0 * math.pi, tube_segments, endpoint=False)
    radial = radial_half * np.cos(phi)
    axial = axial_half * np.sin(phi)
    if rectangular:
        # Project the ellipse sample onto the rectangle boundary.
        scale = np.maximum(np.abs(radial) / radial_half, np.abs(axial) / axial_half)
        scale[scale == 0.0] = 1.0
        radial = radial / scale
        axial = axial / scale
    return np.stack([radial, axial], axis=1)


def generate_open_ring(
    diameter_m: float = 4.0,
    tube_radius_m: float | None = 0.15,
    width_m: float | None = None,
    depth_m: float | None = None,
    opening_deg: float = 60.0,
    tilt_deg: float = 0.0,
    segments: int = 64,
    tube_segments: int = 12,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    """Generate an open-ring mesh.

    `diameter_m` is the overall outer diameter. Section is circular when
    `tube_radius_m` is given, rectangular (width radial x depth axial) when
    `width_m`/`depth_m` are given instead.

    Returns {"vertices": [[x, y, z], ...], "faces": [[a, b, c], ...],
             "metadata": {...}} with outward-facing triangle winding and
    capped ends (watertight).
    """
    if diameter_m <= 0:
        raise ValueError("diameter_m must be positive")
    if not 0.0 <= opening_deg < 360.0:
        raise ValueError("opening_deg must be in [0, 360)")
    if segments < 3 or tube_segments < 3:
        raise ValueError("segments and tube_segments must be >= 3")

    rectangular = tube_radius_m is None
    if rectangular:
        if not width_m or not depth_m:
            raise ValueError("rectangular section requires width_m and depth_m")
        radial_half, axial_half = width_m / 2.0, depth_m / 2.0
    else:
        radial_half = axial_half = float(tube_radius_m)

    radius = diameter_m / 2.0 - radial_half
    if radius <= 0:
        raise ValueError("section is too large for the diameter")

    # Arc sweep: gap of opening_deg centered at the bottom (theta = 270 deg).
    sweep = math.radians(360.0 - opening_deg)
    theta0 = math.radians(270.0 + opening_deg / 2.0)
    thetas = np.linspace(theta0, theta0 + sweep, segments + 1)

    cos_t, sin_t = np.cos(thetas), np.sin(thetas)
    centers = np.stack([radius * cos_t, radius * sin_t, np.zeros_like(thetas)], axis=1)

    offsets = _section_offsets(tube_segments, radial_half, axial_half, rectangular)
    # vertex(i, j) = center(i) + radial(j) * radial_dir(i) + axial(j) * z-axis
    radial_dir = np.stack([cos_t, sin_t, np.zeros_like(thetas)], axis=1)
    z_axis = np.array([0.0, 0.0, 1.0])

    vertices = (
        centers[:, None, :]
        + offsets[None, :, 0:1] * radial_dir[:, None, :]
        + offsets[None, :, 1:2] * z_axis[None, None, :]
    ).reshape(-1, 3)

    faces: list[list[int]] = []
    for i in range(segments):
        for j in range(tube_segments):
            j1 = (j + 1) % tube_segments
            a = i * tube_segments + j
            b = (i + 1) * tube_segments + j
            c = (i + 1) * tube_segments + j1
            d = i * tube_segments + j1
            faces.append([a, b, c])
            faces.append([a, c, d])

    # End caps (fan around a center vertex) make the mesh watertight.
    start_center = len(vertices)
    vertices = np.vstack([vertices, centers[0], centers[-1]])
    end_center = start_center + 1
    for j in range(tube_segments):
        j1 = (j + 1) % tube_segments
        faces.append([start_center, j, j1])  # start cap faces -tangent
        faces.append([end_center, segments * tube_segments + j1,
                      segments * tube_segments + j])  # end cap faces +tangent

    vertices = np.asarray(vertices, dtype=float)

    if tilt_deg:
        tilt = math.radians(tilt_deg)
        rot = np.array([
            [1.0, 0.0, 0.0],
            [0.0, math.cos(tilt), -math.sin(tilt)],
            [0.0, math.sin(tilt), math.cos(tilt)],
        ])
        vertices = vertices @ rot.T

    faces_arr = np.asarray(faces, dtype=int)

    # Surface area (triangle cross products) and solid swept volume.
    tris = vertices[faces_arr]
    surface_area = float(0.5 * np.linalg.norm(
        np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1).sum())
    if rectangular:
        section_area = (2.0 * radial_half) * (2.0 * axial_half)
    else:
        section_area = math.pi * radial_half**2
    volume = float(radius * sweep * section_area)

    mat = _load_material(material)
    thickness = shell_thickness_m if shell_thickness_m else mat.get(
        "default_shell_thickness_m", DEFAULT_SHELL_THICKNESS_M)
    mass_kg = surface_area * thickness * mat["density_kg_m3"]

    metadata = {
        "family": "open_ring",
        "diameter_m": diameter_m,
        "opening_deg": opening_deg,
        "tilt_deg": tilt_deg,
        "section": "rectangular" if rectangular else "circular",
        "material": material,
        "shell_thickness_m": thickness,
        "surface_area_m2": surface_area,
        "volume_m3": volume,
        "mass_kg": mass_kg,
        "vertex_count": int(len(vertices)),
        "face_count": int(len(faces_arr)),
    }

    return {
        "vertices": vertices.tolist(),
        "faces": faces_arr.tolist(),
        "metadata": metadata,
    }
