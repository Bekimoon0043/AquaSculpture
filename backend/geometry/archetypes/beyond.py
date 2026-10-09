"""Beyond-portfolio archetypes (PLAN §5.2): forms outside the reference
portfolio — torus knots, möbius ribbons, wave surfaces, spiral columns,
geodesic shells. All watertight, all parameterized, all engineering-ready.
"""

import math

import numpy as np

from geometry.archetypes._common import (_swept_tube, combine_meshes, finalize,
                                         revolve_profile)


def generate_torus_knot(
    p: int = 2, q: int = 3,
    major_radius_m: float = 1.4,
    tube_radius_m: float = 0.16,
    knot_amplitude: float = 0.5,
    segments: int = 160,
    tube_sides: int = 12,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    """(p,q) torus knot: tube swept along the knot centerline."""
    if p < 1 or q < 1:
        raise ValueError("p and q must be >= 1")
    t = np.linspace(0.0, 2.0 * math.pi * min(p, q) * 2, segments)
    r = major_radius_m + knot_amplitude * np.cos(q * t)
    path = np.stack([r * np.cos(p * t),
                     knot_amplitude * np.sin(q * t) * 0.8,
                     r * np.sin(p * t)], axis=1)
    # Close the loop: repeat the first point.
    path = np.vstack([path, path[:1]])
    v, f = _swept_tube(path, tube_radius_m, sides=tube_sides)
    return finalize(v, f, "torus_knot", material, shell_thickness_m,
                    extra={"p": p, "q": q,
                           "major_radius_m": major_radius_m,
                           "tube_radius_m": tube_radius_m})


def generate_mobius_ribbon(
    radius_m: float = 1.2,
    width_m: float = 0.5,
    thickness_m: float = 0.05,
    segments: int = 96,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    """Solid Möbius band: a rectangular section swept once around a circle
    with a half-turn. A Möbius surface has one side, so it cannot be built as
    "top skin + bottom skin"; instead the last station closes onto the first
    through the 180° corner permutation (corner k -> corner k+2), which gives
    one watertight, consistently wound solid.
    """
    if segments < 8:
        raise ValueError("segments must be >= 8")
    hw, ht = width_m / 2.0, thickness_m / 2.0
    corners = [(-hw, -ht), (hw, -ht), (hw, ht), (-hw, ht)]  # CCW in (w, t)
    n = segments
    vertices: list[list[float]] = []
    for i in range(n):
        uu = 2.0 * math.pi * i / n
        radial = np.array([math.cos(uu), 0.0, math.sin(uu)])  # y is up
        up = np.array([0.0, 1.0, 0.0])
        a = uu / 2.0  # half-turn over one revolution
        wdir = math.cos(a) * radial + math.sin(a) * up
        tdir = -math.sin(a) * radial + math.cos(a) * up
        centre = radius_m * radial + np.array([0.0, radius_m + hw, 0.0])
        for w, t in corners:
            vertices.append((centre + w * wdir + t * tdir).tolist())

    faces: list[list[int]] = []
    for i in range(n):
        i1 = (i + 1) % n
        shift = 2 if i1 == 0 else 0  # seam: frame has rotated by pi
        for k in range(4):
            k1 = (k + 1) % 4
            a0, a1 = 4 * i + k, 4 * i + k1
            b0, b1 = 4 * i1 + (k + shift) % 4, 4 * i1 + (k1 + shift) % 4
            faces += [[a0, a1, b1], [a0, b1, b0]]
    return finalize(vertices, faces, "mobius_ribbon", material,
                    shell_thickness_m,
                    extra={"radius_m": radius_m, "width_m": width_m,
                           "thickness_m": thickness_m})


def generate_wave_surface(
    width_m: float = 3.0,
    depth_m: float = 1.2,
    height_m: float = 2.5,
    waves: int = 3,
    amplitude_m: float = 0.35,
    thickness_m: float = 0.05,
    segments: int = 48,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    """Undulating vertical ribbon wall: two offset skins + boundary walls."""
    u = np.linspace(0.0, 1.0, segments)        # along width
    vv = np.linspace(0.0, 1.0, segments)       # up height
    U, V = np.meshgrid(u, vv)

    def surface(off):
        x = U * width_m
        y = V * height_m
        z = amplitude_m * np.sin(waves * 2 * math.pi * U) * (0.3 + 0.7 * V) + off
        return np.stack([x, y, z], axis=-1).reshape(-1, 3)

    top = surface(thickness_m / 2.0)
    bottom = surface(-thickness_m / 2.0)
    n = segments * segments
    vertices = np.vstack([top, bottom])
    faces: list[list[int]] = []

    def quad(a, b, c, d, flip=False):
        if flip:
            faces.extend([[a, d, c], [a, c, b]])
        else:
            faces.extend([[a, b, c], [a, c, d]])

    for j in range(segments - 1):
        for i in range(segments - 1):
            a = j * segments + i
            b = a + 1
            c = a + segments
            d = c + 1
            quad(a, b, d, c)                       # top skin
            quad(n + a, n + b, n + d, n + c, flip=True)  # bottom skin
    # boundary walls
    for i in range(segments - 1):
        a, b = i, i + 1                                    # bottom edge (v=0)
        quad(a, n + a, n + b, b, flip=True)
        a, b = (segments - 1) * segments + i, (segments - 1) * segments + i + 1
        quad(a, b, n + b, n + a, flip=True)                # top edge
        a, b = i * segments, (i + 1) * segments            # left edge
        quad(a, b, n + b, n + a, flip=True)
        a, b = i * segments + segments - 1, (i + 1) * segments + segments - 1
        quad(a, n + a, n + b, b, flip=True)                # right edge
    return finalize(vertices, faces, "wave_surface", material,
                    shell_thickness_m,
                    extra={"width_m": width_m, "height_m": height_m,
                           "waves": waves, "amplitude_m": amplitude_m})


def generate_spiral_column(
    height_m: float = 3.0,
    radius_m: float = 0.8,
    turns: float = 3.0,
    tube_radius_m: float = 0.12,
    segments: int = 120,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    """Helical tube rising around a vertical axis."""
    t = np.linspace(0.0, 1.0, segments)
    path = np.stack([
        radius_m * np.cos(turns * 2 * math.pi * t),
        t * height_m,
        radius_m * np.sin(turns * 2 * math.pi * t),
    ], axis=1)
    v, f = _swept_tube(path, tube_radius_m)
    return finalize(v, f, "spiral_column", material, shell_thickness_m,
                    extra={"turns": turns, "radius_m": radius_m,
                           "height_m": height_m})


def generate_geodesic_shell(
    diameter_m: float = 3.0,
    subdivisions: int = 2,
    shell_thickness_m: float | None = None,
    material: str = "stainless_316l",
) -> dict:
    """Geodesic sphere from subdivided icosahedron (watertight)."""
    t = (1.0 + math.sqrt(5.0)) / 2.0
    verts = np.array([
        [-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0],
        [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t],
        [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1],
    ], dtype=float)
    faces = [
        [0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11],
        [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
        [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9],
        [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1],
    ]
    verts = verts / np.linalg.norm(verts, axis=1, keepdims=True)

    for _ in range(subdivisions):
        new_faces = []
        new_verts = list(verts)
        mid_cache: dict[tuple[int, int], int] = {}

        def midpoint(a, b):
            key = (min(a, b), max(a, b))
            if key not in mid_cache:
                m = (verts[a] + verts[b]) / 2.0
                m /= np.linalg.norm(m)
                mid_cache[key] = len(new_verts)
                new_verts.append(m)
            return mid_cache[key]

        for a, b, c in faces:
            ab = midpoint(a, b)
            bc = midpoint(b, c)
            ca = midpoint(c, a)
            new_faces += [[a, ab, ca], [b, bc, ab], [c, ca, bc],
                          [ab, bc, ca]]
        verts = np.asarray(new_verts)
        faces = new_faces

    verts = verts * (diameter_m / 2.0)
    verts[:, 1] += diameter_m / 2.0    # sit on the ground plane
    return finalize(verts, np.asarray(faces), "geodesic_shell", material,
                    shell_thickness_m,
                    extra={"diameter_m": diameter_m,
                           "subdivisions": subdivisions})
