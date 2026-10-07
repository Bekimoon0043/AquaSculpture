"""GA drawings (scope §29): plan / front elevation / side elevation DXF.

Orthographic projections of the sculpture + basin with silhouette (contour)
edges only — an edge is drawn when its two adjacent faces flip sign against
the view direction — plus overall dimensions and a title block. Laid out
side by side on one DXF sheet, metres, layer VIEWS.
"""

import numpy as np

# view name -> (drop axis, view direction)  e.g. plan looks down -y.
VIEWS = {
    "PLAN": {"drop": 1, "dir": np.array([0.0, -1.0, 0.0])},
    "FRONT": {"drop": 2, "dir": np.array([0.0, 0.0, -1.0])},
    "SIDE": {"drop": 0, "dir": np.array([-1.0, 0.0, 0.0])},
}
VIEW_GAP_M = 1.0


def _silhouette_edges(vertices, faces, view_dir):
    """Edges where adjacent faces flip visibility wrt the view direction."""
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    normals = np.cross(v[f][:, 1] - v[f][:, 0], v[f][:, 2] - v[f][:, 0])
    facing = normals @ view_dir

    edge_faces: dict[tuple[int, int], list[int]] = {}
    for fi, (a, b, c) in enumerate(f):
        for e in ((a, b), (b, c), (c, a)):
            edge_faces.setdefault((min(e), max(e)), []).append(fi)

    segments = []
    for (a, b), owners in edge_faces.items():
        if len(owners) == 2 and (facing[owners[0]] > 0) != (facing[owners[1]] > 0):
            segments.append((a, b))
    return segments


def _project(vertices, segments, drop_axis):
    v = np.asarray(vertices, dtype=float)
    keep = [i for i in range(3) if i != drop_axis]
    out = []
    for a, b in segments:
        out.append(((v[a][keep[0]], v[a][keep[1]]),
                    (v[b][keep[0]], v[b][keep[1]])))
    return out


def build_ga_drawing(sculpture_mesh: dict, basin_mesh: dict | None,
                     title: str = "GA Drawing") -> str:
    """One DXF sheet: PLAN / FRONT / SIDE + dimensions + title block."""
    lines = ["0", "SECTION", "2", "ENTITIES"]

    meshes = [sculpture_mesh] + ([basin_mesh] if basin_mesh else [])
    all_v = []
    for m in meshes:
        all_v.extend(m["vertices"])
    all_v = np.asarray(all_v, dtype=float)
    mn, mx = all_v.min(axis=0), all_v.max(axis=0)
    size = mx - mn

    x_cursor = mn[0]
    label_y = mn[1] - 0.5

    def emit_segment(p, q, off_x, off_y):
        lines.extend(["0", "LINE", "8", "VIEWS",
                      "10", f"{p[0] + off_x:.4f}", "20", f"{p[1] + off_y:.4f}",
                      "11", f"{q[0] + off_x:.4f}", "21", f"{q[1] + off_y:.4f}"])

    def emit_text(x, y, h, text):
        lines.extend(["0", "TEXT", "8", "LABELS",
                      "10", f"{x:.4f}", "20", f"{y:.4f}",
                      "40", f"{h:.3f}", "1", text])

    for name, cfg in VIEWS.items():
        segs = []
        for m in meshes:
            sil = _silhouette_edges(m["vertices"], m["faces"], cfg["dir"])
            segs.extend(_project(m["vertices"], sil, cfg["drop"]))
        width = size[0] if name != "SIDE" else size[2]
        height = size[1] if name != "PLAN" else size[2]
        for p, q in segs:
            emit_segment(p, q, x_cursor, 0.0)
        emit_text(x_cursor, label_y, 0.15,
                  f"{name}  {width:.2f} x {height:.2f} m")
        x_cursor = mx[0] + VIEW_GAP_M

    emit_text(mn[0], label_y - 0.6, 0.25, title)
    emit_text(mn[0], label_y - 1.0, 0.12,
              "LuxuryForm Studio — preliminary, not for construction")
    lines.extend(["0", "ENDSEC", "0", "EOF"])
    return "\n".join(lines) + "\n"


def ga_drawing_bytes(sculpture_mesh: dict, basin_mesh: dict | None,
                     title: str) -> bytes:
    return build_ga_drawing(sculpture_mesh, basin_mesh, title).encode(
        "ascii", errors="replace")
