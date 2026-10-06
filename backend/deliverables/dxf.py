"""Minimal ASCII DXF (R12) writer for flat-pattern cutting sheets.

Dependency-free; entities: LWPOLYLINE (closed outlines) + TEXT labels.
Units: meters. Layout: panels placed left-to-right in rows.
"""

import io

GAP_M = 0.2
ROW_HEIGHT_M = 2.0
ROW_WIDTH_M = 40.0


def _fmt(x: float) -> str:
    return f"{x:.4f}"


def flat_patterns_dxf(panels: list[dict]) -> str:
    """All panel flat outlines laid out on one DXF cutting sheet."""
    lines: list[str] = ["0", "SECTION", "2", "ENTITIES"]
    x_cursor = GAP_M
    y_cursor = GAP_M

    for p in panels:
        outline = p["flat_outline"]
        if len(outline) < 3:
            continue
        w, h = p["flat_dims_m"]
        if x_cursor + w > ROW_WIDTH_M:
            x_cursor = GAP_M
            y_cursor += ROW_HEIGHT_M

        lines += ["0", "LWPOLYLINE", "8", "PANELS", "90", str(len(outline)),
                  "70", "1"]
        for x, y in outline:
            lines += ["10", _fmt(x + x_cursor), "20", _fmt(y + y_cursor)]

        lines += [
            "0", "TEXT", "8", "LABELS",
            "10", _fmt(x_cursor), "20", _fmt(y_cursor + h + 0.05),
            "40", "0.08",
            "1", (f"{p['id']} {p['curvature']} "
                  f"{p['flat_dims_m'][0]:.2f}x{p['flat_dims_m'][1]:.2f}m"),
        ]
        x_cursor += w + GAP_M

    lines += ["0", "ENDSEC", "0", "EOF"]
    return "\n".join(lines) + "\n"


def flat_patterns_bytes(panels: list[dict]) -> bytes:
    return flat_patterns_dxf(panels).encode("ascii", errors="replace")
