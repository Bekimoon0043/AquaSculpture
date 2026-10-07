"""Geometry integrity validation (scope §3, design gate G2).

Deterministic mesh forensics run on every generated sculpture:

- open edges (holes)            — edge used by != 2 faces
- non-manifold edges            — edge shared by > 2 faces
- degenerate faces              — zero-area triangles
- floating components           — disconnected bodies (vertex union-find)
- minimum feature size          — smallest edge vs a fabrication floor

Self-intersection detection is NOT implemented yet (needs a BVH/triangle
pair engine) and is reported as not_checked rather than guessed at.

Gate rule: any ERROR fails G2. Multiple components are a WARNING — stacked
compositions legitimately assemble from separate welded bodies, but the
fabrication plan must then show the hidden supports (scope §3 hard rule is
about *fabrication connectivity*, not visual overlap).
"""

import math

import numpy as np

MIN_FEATURE_M = 0.002  # 2 mm — below this, geometry is un-fabricatable
MAX_FOLD_DEG = 150.0   # dihedral angle beyond which panels can't be formed


def validate_mesh(vertices, faces) -> dict:
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)

    errors: list[str] = []
    warnings: list[str] = []

    # ── Edge analysis ───────────────────────────────────────────────────
    edge_count: dict[tuple[int, int], int] = {}
    for a, b, c in f:
        for e in ((a, b), (b, c), (c, a)):
            key = (min(e), max(e))
            edge_count[key] = edge_count.get(key, 0) + 1
    open_edges = sum(1 for n in edge_count.values() if n != 2)
    non_manifold = sum(1 for n in edge_count.values() if n > 2)
    if open_edges:
        errors.append(f"{open_edges} open edges (mesh has holes)")
    if non_manifold:
        errors.append(f"{non_manifold} non-manifold edges")

    # ── Degenerate faces ────────────────────────────────────────────────
    tris = v[f]
    areas = 0.5 * np.linalg.norm(
        np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1)
    degenerate = int((areas < 1e-12).sum())
    if degenerate:
        errors.append(f"{degenerate} degenerate (zero-area) faces")

    # ── Floating components (union-find over vertices) ──────────────────
    parent = list(range(len(v)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, c in f:
        ra, rb, rc = find(a), find(b), find(c)
        parent[ra] = parent[rb] = rc
    roots = {find(i) for tri in f for i in tri}
    components = len(roots)
    if components > 1:
        warnings.append(
            f"{components} disconnected bodies — fabrication plan must show "
            "connecting members/supports")

    # ── Minimum feature size ────────────────────────────────────────────
    edges = np.array(list(edge_count.keys()))
    lengths = np.linalg.norm(v[edges[:, 0]] - v[edges[:, 1]], axis=1)
    min_edge = float(lengths.min()) if len(lengths) else 0.0
    if min_edge < MIN_FEATURE_M:
        warnings.append(f"smallest edge {min_edge * 1000:.2f} mm is below the "
                        f"{MIN_FEATURE_M * 1000:.0f} mm fabrication floor")

    # ── Fold severity (scope §3: excessively tight curvature) ───────────
    # Dihedral angle across shared edges; beyond MAX_FOLD_DEG the shell
    # cannot be brake-pressed or rolled and needs re-design.
    tris = v[f]
    fnorms = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    fnorms /= np.linalg.norm(fnorms, axis=1, keepdims=True).clip(1e-15)
    edge_faces2: dict[tuple[int, int], list[int]] = {}
    for fi, (a, b, c) in enumerate(f):
        for e in ((a, b), (b, c), (c, a)):
            edge_faces2.setdefault((min(e), max(e)), []).append(fi)
    worst_fold = 0.0
    for owners in edge_faces2.values():
        if len(owners) == 2:
            dot = float(np.clip(fnorms[owners[0]] @ fnorms[owners[1]],
                                -1.0, 1.0))
            fold = math.degrees(math.acos(abs(dot)))
            worst_fold = max(worst_fold, fold)
    if worst_fold > MAX_FOLD_DEG:
        errors.append(f"fold angle {worst_fold:.0f} deg exceeds formable "
                      f"limit ({MAX_FOLD_DEG:.0f} deg)")

    return {
        "watertight": open_edges == 0,
        "open_edges": open_edges,
        "non_manifold_edges": non_manifold,
        "degenerate_faces": degenerate,
        "components": components,
        "min_edge_m": round(min_edge, 5),
        "worst_fold_deg": round(worst_fold, 1),
        "self_intersection": "not_checked",  # needs BVH pair engine (later)
        "errors": errors,
        "warnings": warnings,
        "passed": len(errors) == 0,
    }
