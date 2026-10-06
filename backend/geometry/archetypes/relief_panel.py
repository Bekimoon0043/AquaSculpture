"""Relief / silhouette panel (PLAN.md §5.1, reproduces the P1 centerpiece).

A 2D polygon outline (e.g. a simplified continent) extruded to a solid
panel. Perforation grid is reported as metadata (dot spacing, margin,
estimated dot count) for the electrical engine; dot geometry is a later
phase. The outline must be star-shaped about its centroid (caps are
centroid fans).
"""

import math

from geometry.archetypes._common import extrude_polygon, finalize, polygon_area_2d

# Simplified continent-ish default outline (roughly Africa), meters,
# centered near the origin, CCW.
DEFAULT_OUTLINE = [
    [-1.8, 1.6], [-0.9, 2.1], [0.2, 2.2], [1.1, 1.9], [1.7, 1.2],
    [1.9, 0.4], [1.5, -0.3], [1.2, -0.9], [0.8, -1.7], [0.3, -2.4],
    [-0.2, -2.6], [-0.6, -1.9], [-0.9, -1.2], [-1.4, -0.5],
    [-1.9, 0.3], [-2.0, 1.0],
]


def generate_relief_panel(
    outline: list | None = None,
    thickness_m: float = 0.10,
    perforation_dot_spacing_m: float = 0.05,
    perforation_margin_m: float = 0.10,
    shell_thickness_m: float | None = None,
    material: str = "stainless_304",
) -> dict:
    outline = outline or DEFAULT_OUTLINE
    if len(outline) < 3:
        raise ValueError("outline needs at least 3 points")
    if thickness_m <= 0:
        raise ValueError("thickness_m must be positive")

    vertices, faces = extrude_polygon(outline, thickness_m)
    # Stand the panel on the ground: shift so min y = 0.
    min_y = min(p[1] for p in outline)
    vertices = vertices.copy()
    vertices[:, 1] -= min_y

    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    width = max(xs) - min(xs)
    height = max(ys) - min(ys)
    area = abs(polygon_area_2d(outline))

    usable_w = max(0.0, width - 2.0 * perforation_margin_m)
    usable_h = max(0.0, height - 2.0 * perforation_margin_m)
    grid_cells = (int(usable_w / perforation_dot_spacing_m)
                  * int(usable_h / perforation_dot_spacing_m))
    fill = area / (width * height) if width * height > 0 else 0.0
    dot_count = int(grid_cells * fill)

    return finalize(vertices, faces, "relief_panel", material, shell_thickness_m,
                    extra={
                        "outline_points": len(outline),
                        "width_m": round(width, 4),
                        "height_m": round(height, 4),
                        "panel_area_m2": round(area, 4),
                        "thickness_m": thickness_m,
                        "perforation": {
                            "dot_spacing_m": perforation_dot_spacing_m,
                            "margin_m": perforation_margin_m,
                            "estimated_dot_count": dot_count,
                            "led_backlit": True,
                        },
                    })
