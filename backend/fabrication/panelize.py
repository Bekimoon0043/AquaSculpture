"""Panelization engine (scope §16, §18).

Subdivides the sculpture shell into manufacturable panels by angular
sectors x height bands around the vertical axis. For each panel:

- area, flat-pattern outline (PCA best-fit plane + convex hull)
- curvature class (flat / single-curved / double-curved) from normal spread
- weld seam length (edges shared with a different panel)
- sheet-fit check against the standard stock sheet size

Outputs feed the BOM (cutting + welding length), the fabrication DXF
package, and design gate G7.
"""

import math

import numpy as np

SECTORS = 16
TARGET_PANEL_M = 1.2          # aim for panels near this size
SHEET_MAX_M = (1.5, 3.0)      # standard stock sheet
FLAT_NORMAL_DEG = 15.0        # below -> flat panel
SINGLE_CURVED_DEG = 60.0      # below -> single curvature (rollable)


def _convex_hull_2d(points: np.ndarray) -> np.ndarray:
    """Andrew monotone chain; input (n,2), returns hull vertices CCW."""
    pts = sorted(set(map(tuple, points)))
    if len(pts) <= 2:
        return np.asarray(pts)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return np.asarray(lower[:-1] + upper[:-1])


def panelize_shell(vertices, faces, shell_thickness_m: float = 0.003) -> dict:
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)

    tris = v[f]
    centroids = tris.mean(axis=1)
    norms = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    lengths = np.linalg.norm(norms, axis=1)
    lengths[lengths < 1e-15] = 1e-15
    unit_normals = norms / lengths[:, None]
    face_areas = 0.5 * lengths

    y0, y1 = float(v[:, 1].min()), float(v[:, 1].max())
    height = max(y1 - y0, 1e-6)
    bands = max(1, math.ceil(height / TARGET_PANEL_M))
    cx, cz = float(v[:, 0].mean()), float(v[:, 2].mean())

    # Assign each face to (sector, band).
    angles = np.arctan2(centroids[:, 2] - cz, centroids[:, 0] - cx)
    sector_idx = (((angles + math.pi) / (2 * math.pi)) * SECTORS).astype(int)
    sector_idx = np.clip(sector_idx, 0, SECTORS - 1)
    band_idx = np.clip(((centroids[:, 1] - y0) / height) * bands, 0,
                       bands - 1).astype(int)
    keys = sector_idx * 1000 + band_idx

    # Edge -> owning faces, for weld seams (panel boundary edges).
    edge_faces: dict[tuple[int, int], list[int]] = {}
    for fi, (a, b, c) in enumerate(f):
        for e in ((a, b), (b, c), (c, a)):
            edge_faces.setdefault((min(e), max(e)), []).append(fi)

    panels: list[dict] = []
    total_weld_m = 0.0
    for key in sorted(set(keys)):
        member = np.nonzero(keys == key)[0]
        panel_set = set(member.tolist())

        area = float(face_areas[member].sum())

        # Curvature: worst normal deviation inside the panel.
        n = unit_normals[member]
        dots = np.clip(n @ n.T, -1.0, 1.0)
        spread_deg = math.degrees(math.acos(float(dots.min()))) \
            if len(member) > 1 else 0.0
        curvature = ("flat" if spread_deg < FLAT_NORMAL_DEG
                     else "single_curved" if spread_deg < SINGLE_CURVED_DEG
                     else "double_curved")

        # Weld seams: edges where exactly one adjacent face is in the panel.
        seam_m = 0.0
        for (a, b), owners in edge_faces.items():
            inside = sum(1 for o in owners if o in panel_set)
            if inside == 1:
                seam_m += float(np.linalg.norm(v[a] - v[b]))
        total_weld_m += seam_m

        # Flat pattern: PCA plane projection + convex hull outline.
        # Single-curved panels additionally measure width as ARC LENGTH along
        # the sorted principal direction (developable approximation — the
        # pattern that actually fits when rolled, not the chord).
        pverts = np.unique(f[member].ravel())
        pts = v[pverts]
        centroid = pts.mean(axis=0)
        cov = np.cov((pts - centroid).T)
        eigvals, eigvecs = np.linalg.eigh(cov)
        plane = eigvecs[:, 1:]                      # two largest axes
        proj = (pts - centroid) @ plane
        if curvature == "single_curved":
            order = np.argsort(proj[:, 0])
            p_sorted = proj[order]
            arc = np.concatenate(
                [[0.0], np.cumsum(np.linalg.norm(np.diff(p_sorted, axis=0),
                                                 axis=1))])
            proj = np.stack([arc, p_sorted[:, 1]], axis=1)
        hull = _convex_hull_2d(proj)
        if len(hull) >= 2:
            dims = hull.max(axis=0) - hull.min(axis=0)
        else:
            dims = np.zeros(2)

        panels.append({
            "id": f"P{len(panels) + 1:03d}",
            "sector": int(key // 1000), "band": int(key % 1000),
            "face_count": int(len(member)),
            "area_m2": round(area, 4),
            "curvature": curvature,
            "normal_spread_deg": round(spread_deg, 1),
            "flat_dims_m": [round(float(dims[0]), 3), round(float(dims[1]), 3)],
            "flat_outline": [[round(float(x), 4), round(float(y), 4)]
                             for x, y in hull],
            "weld_seam_m": round(seam_m, 2),
            "fits_stock_sheet": bool(
                min(dims) <= SHEET_MAX_M[0] and max(dims) <= SHEET_MAX_M[1]),
        })

    oversized = [p["id"] for p in panels if not p["fits_stock_sheet"]]
    dc_share = (sum(1 for p in panels if p["curvature"] == "double_curved")
                / max(len(panels), 1))

    # Welding engineering (scope §19): butt seams, size from plate
    # thickness, multi-pass count, electrode consumption.
    t_mm = shell_thickness_m * 1000.0
    weld_size_mm = round(max(t_mm, 3.0), 1)
    passes = max(1, math.ceil(weld_size_mm / 3.0))
    seam_total = round(total_weld_m, 2)
    welding = {
        "weld_type": "butt, full penetration, ground flush",
        "weld_size_mm": weld_size_mm,
        "passes": passes,
        "total_length_m": seam_total,
        "electrode_kg": round(seam_total * weld_size_mm * 0.55 * passes, 1),
        "sequence": "tack at 300 mm centres -> root -> fill -> cap; "
                    "alternate sides to balance distortion",
        "post_weld": "grind flush -> passivate (stainless) / patina (bronze)",
    }

    return {
        "panel_count": len(panels),
        "panels": panels,
        "total_weld_seam_m": seam_total,
        "welding": welding,
        "double_curved_share": round(dc_share, 3),
        "oversized_panels": oversized,
        "sheet_max_m": list(SHEET_MAX_M),
    }
