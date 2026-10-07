"""Twisted torus / möbius-seed loop (PLAN.md §5.1, reproduces P2).

Closed torus in the vertical XY plane whose section rotates `twist_count`
times around the centerline. `morph` interpolates the section from round
(0) to a pointed lens (1). Closed in both directions — no caps needed.
"""

import math

import numpy as np

from geometry.archetypes._common import finalize


def generate_twisted_torus(
    major_radius_m: float = 2.0,
    section_width_m: float = 0.4,
    section_depth_m: float = 0.25,
    twist_count: int = 2,
    tilt_deg: float = 0.0,
    morph: float = 0.0,
    aspect_xy: float = 1.0,
    segments: int = 96,
    tube_segments: int = 16,
    shell_thickness_m: float | None = None,
    material: str = "grc",
) -> dict:
    if major_radius_m <= 0:
        raise ValueError("major_radius_m must be positive")
    if not 0.0 <= morph <= 1.0:
        raise ValueError("morph must be in [0, 1]")
    if segments < 3 or tube_segments < 3:
        raise ValueError("segments and tube_segments must be >= 3")

    a = section_width_m / 2.0   # radial half-extent
    b = section_depth_m / 2.0   # axial half-extent
    if major_radius_m - a <= 0:
        raise ValueError("section too wide for the major radius")

    thetas = np.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
    phi = np.linspace(0.0, 2.0 * math.pi, tube_segments, endpoint=False)

    # Section polygon with round->lens morph (pinches at phi = pi/2, 3pi/2).
    pinch = (1.0 - morph) + morph * np.abs(np.cos(phi))
    sec_u = a * np.cos(phi) * pinch   # radial
    sec_v = b * np.sin(phi) * pinch   # axial

    cos_t, sin_t = np.cos(thetas), np.sin(thetas)
    centers = np.stack([major_radius_m * cos_t, major_radius_m * sin_t,
                        np.zeros_like(thetas)], axis=1)
    radial_dir = np.stack([cos_t, sin_t, np.zeros_like(thetas)], axis=1)
    z_axis = np.array([0.0, 0.0, 1.0])

    # Twist: rotate the section about the centerline tangent.
    psi = twist_count * thetas  # 2*pi*twist_count over the full loop
    u = sec_u[None, :] * np.cos(psi)[:, None] - sec_v[None, :] * np.sin(psi)[:, None]
    w = sec_u[None, :] * np.sin(psi)[:, None] + sec_v[None, :] * np.cos(psi)[:, None]

    vertices = (
        centers[:, None, :]
        + u[:, :, None] * radial_dir[:, None, :]
        + w[:, :, None] * z_axis[None, None, :]
    ).reshape(-1, 3)

    faces: list[list[int]] = []
    for i in range(segments):
        i1 = (i + 1) % segments
        for j in range(tube_segments):
            j1 = (j + 1) % tube_segments
            faces.append([i * tube_segments + j, i1 * tube_segments + j,
                          i1 * tube_segments + j1])
            faces.append([i * tube_segments + j, i1 * tube_segments + j1,
                          i * tube_segments + j1])

    vertices = np.asarray(vertices, dtype=float)
    if aspect_xy != 1.0:
        if aspect_xy <= 0:
            raise ValueError("aspect_xy must be positive")
        vertices[:, 0] *= aspect_xy  # elliptical loop: narrower than tall
    if tilt_deg:
        tilt = math.radians(tilt_deg)
        rot = np.array([
            [1.0, 0.0, 0.0],
            [0.0, math.cos(tilt), -math.sin(tilt)],
            [0.0, math.sin(tilt), math.cos(tilt)],
        ])
        vertices = vertices @ rot.T

    # Section area via shoelace (rotation-invariant), volume via Pappus.
    area = 0.5 * abs(float(np.sum(sec_u * np.roll(sec_v, -1)
                                  - np.roll(sec_u, -1) * sec_v)))
    volume = 2.0 * math.pi * major_radius_m * area

    return finalize(vertices, faces, "twisted_torus", material, shell_thickness_m,
                    extra={
                        "major_radius_m": major_radius_m,
                        "section_width_m": section_width_m,
                        "section_depth_m": section_depth_m,
                        "twist_count": twist_count,
                        "tilt_deg": tilt_deg,
                        "morph": morph,
                        "aspect_xy": aspect_xy,
                        "section_area_m2": area,
                        "volume_m3": volume,
                    })
