"""Standing draped figure with a raised torch — figurative archetype v2
(Liberty-type monument). Stylized-maquette quality like `buddha_seated`:
closed primitive sub-meshes (fold-modulated lathe for the robe, lathes for
pedestal/crown, ellipsoids for head/flame, swept tubes for arms/rays, an
extruded slab for the tablet). Parts intersect, so volume slightly
over-counts overlaps; surface area and bbox are exact.

This is exactly the construction the real monument uses — hammered sheet
over an internal armature — so the downstream skeleton / panelization /
wind engineering applies without special cases. Proportions follow the
Statue of Liberty: head top ≈ 0.74 of torch-tip height, robe hem ≈ 0.28 H
wide, raised right arm, tablet in the left hand, seven-ray crown.
"""

import math

import numpy as np

from geometry.archetypes._common import (_ellipsoid, _swept_tube,
                                         combine_meshes, extrude_polygon,
                                         finalize, revolve_profile)


def _lathe_folds(profile, segments: int, folds: int, depth: float,
                 fade_y: float):
    """Revolve an (r, y) profile with sinusoidal drapery folds around the
    circumference. Fold amplitude is `depth` at y=0 fading to zero at
    `fade_y`, so the hem is deeply pleated and the shoulders are smooth."""
    angles = np.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
    vertices: list[list[float]] = []
    rings: list[list[int]] = []
    for r, y in profile:
        if abs(r) < 1e-12:
            rings.append([len(vertices)])
            vertices.append([0.0, y, 0.0])
            continue
        amp = depth * max(0.0, 1.0 - y / fade_y) if fade_y > 0 else 0.0
        ring = []
        for j, a in enumerate(angles):
            rr = r * (1.0 + amp * math.sin(folds * a + 0.6 * y))
            ring.append(len(vertices))
            vertices.append([rr * math.cos(a), y, rr * math.sin(a)])
        rings.append(ring)
    n = len(profile)
    faces: list[list[int]] = []
    for i in range(n):
        a, b = rings[i], rings[(i + 1) % n]
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


def _translate(part, dx, dy, dz):
    v, f = part
    v = v.copy()
    v[:, 0] += dx
    v[:, 1] += dy
    v[:, 2] += dz
    return v, f


def generate_standing_figure(
    height_m: float = 6.0,
    pedestal: bool = True,
    pedestal_ratio: float = 0.3,
    raised_arm: bool = True,
    torch: bool = True,
    crown_rays: int = 7,
    tablet: bool = True,
    drapery_folds: int = 9,
    fold_depth: float = 0.08,
    segments: int = 48,
    shell_thickness_m: float | None = None,
    material: str = "bronze",
) -> dict:
    """Standing draped figure (Liberty-type). `height_m` is the overall
    height including pedestal and torch; the figure is normalised to it."""
    if height_m <= 0:
        raise ValueError("height_m must be positive")
    if crown_rays < 0 or drapery_folds < 0:
        raise ValueError("crown_rays and drapery_folds must be >= 0")
    if not 0.0 <= pedestal_ratio < 0.8:
        raise ValueError("pedestal_ratio must be in [0, 0.8)")

    H = 1.0  # work in unit figure height, normalise at the end
    parts: list[tuple[np.ndarray, np.ndarray]] = []

    # ── Pedestal: stepped octagonal plinth ────────────────────────────
    if pedestal and pedestal_ratio > 0:
        P = pedestal_ratio * H / (1.0 - pedestal_ratio)  # so figure : pedestal ratio holds after normalising
        r = 0.22 * H
        plinth = [
            (0.0, 0.0), (1.15 * r, 0.0), (1.15 * r, 0.10 * P),
            (1.0 * r, 0.12 * P), (0.92 * r, 0.80 * P),
            (1.02 * r, 0.86 * P), (1.02 * r, 0.96 * P),
            (0.90 * r, P), (0.0, P),
        ]
        parts.append(revolve_profile(plinth, 8))
        base_y = P
    else:
        base_y = 0.0

    # ── Robe: fold-modulated lathe from hem to neck ───────────────────
    robe = [
        (0.0, 0.0), (0.145 * H, 0.0), (0.150 * H, 0.03 * H),   # hem
        (0.125 * H, 0.18 * H), (0.105 * H, 0.32 * H),           # skirt
        (0.080 * H, 0.45 * H),                                 # waist
        (0.095 * H, 0.56 * H), (0.112 * H, 0.64 * H),           # chest / shoulders
        (0.080 * H, 0.68 * H), (0.035 * H, 0.695 * H),          # shoulder round-off, neck
        (0.035 * H, 0.72 * H), (0.0, 0.72 * H),
    ]
    parts.append(_translate(
        _lathe_folds(robe, segments, drapery_folds, fold_depth, 0.60 * H),
        0.0, base_y, 0.0))

    # ── Head + crown band + rays ──────────────────────────────────────
    head_y = base_y + 0.76 * H
    parts.append(_ellipsoid(0.045 * H, 0.058 * H, 0.050 * H, (0.0, head_y, 0.0)))
    crown = [
        (0.0, head_y + 0.02 * H), (0.050 * H, head_y + 0.02 * H),
        (0.056 * H, head_y + 0.055 * H), (0.0, head_y + 0.065 * H),
    ]
    parts.append(revolve_profile(crown, max(12, segments // 2)))
    for i in range(crown_rays):
        # Rays fan across the frontal (XY) plane from -75° to +75° of vertical.
        if crown_rays == 1:
            ang = math.pi / 2
        else:
            ang = math.radians(15.0 + 150.0 * i / (crown_rays - 1))
        d = np.array([math.cos(ang), math.sin(ang), 0.0])
        root = np.array([0.0, head_y + 0.045 * H, 0.0]) + 0.045 * H * d
        path = np.vstack([root, root + 0.05 * H * d, root + 0.10 * H * d])
        parts.append(_swept_tube(path, 0.006 * H, sides=6))

    # ── Right arm raised with the torch ───────────────────────────────
    if raised_arm:
        arm = np.array([
            [0.09 * H, base_y + 0.63 * H, 0.0],       # shoulder
            [0.13 * H, base_y + 0.74 * H, 0.0],       # upper arm
            [0.135 * H, base_y + 0.84 * H, 0.0],      # elbow
            [0.12 * H, base_y + 0.92 * H, 0.0],       # hand
        ])
        parts.append(_swept_tube(arm, 0.028 * H))
        if torch:
            handle = np.array([[0.12 * H, base_y + 0.90 * H, 0.0],
                               [0.12 * H, base_y + 0.97 * H, 0.0]])
            parts.append(_swept_tube(handle, 0.014 * H, sides=8))
            parts.append(_ellipsoid(0.03 * H, 0.038 * H, 0.03 * H,
                                    (0.12 * H, base_y + 0.98 * H, 0.0)))  # flame
    else:
        arm = np.array([
            [0.09 * H, base_y + 0.63 * H, 0.0],
            [0.12 * H, base_y + 0.50 * H, 0.02 * H],
            [0.10 * H, base_y + 0.38 * H, 0.04 * H],
        ])
        parts.append(_swept_tube(arm, 0.028 * H))

    # ── Left arm cradling the tablet ──────────────────────────────────
    left = np.array([
        [-0.09 * H, base_y + 0.63 * H, 0.0],
        [-0.13 * H, base_y + 0.53 * H, 0.03 * H],
        [-0.11 * H, base_y + 0.50 * H, 0.08 * H],
    ])
    parts.append(_swept_tube(left, 0.028 * H))
    if tablet:
        w, h = 0.085 * H, 0.14 * H
        slab = extrude_polygon([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, h), (-w / 2, h)],
                               0.016 * H)
        parts.append(_translate(slab, -0.13 * H, base_y + 0.47 * H, 0.10 * H))

    vertices, faces = combine_meshes(parts)

    # Normalise: base at y=0, overall height exactly height_m.
    y0 = float(vertices[:, 1].min())
    vertices[:, 1] -= y0
    scale = height_m / float(vertices[:, 1].max())
    vertices *= scale

    return finalize(vertices, faces, "standing_figure", material, shell_thickness_m,
                    extra={"height_m": height_m, "pose": "torch_raised" if raised_arm else "arms_down",
                           "pedestal": pedestal, "crown_rays": crown_rays,
                           "tablet": tablet,
                           "note": "stylized figurative v2; parts intersect — "
                                   "volume slightly over-counted"})
