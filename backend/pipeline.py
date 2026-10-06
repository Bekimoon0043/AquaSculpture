"""Shared deterministic pipeline: brief -> geometry + basin + hydraulics
+ structural + cost.

Used by /api/geometry/generate, /api/engineering/run and
/api/deliverables/package. Families dispatch through the archetype registry.
"""

from fastapi import HTTPException

from cost import estimator
from engineering import gates, geo_calc, hydraulics, integrity, structural
from geometry.archetypes import GENERATORS, generate
from geometry.basin import generate_basin


def generate_sculpture(brief: dict) -> dict:
    """Brief sculpture section -> mesh + metadata (any registered family)."""
    try:
        sculpture = brief["sculpture"]
    except (KeyError, TypeError):
        raise HTTPException(status_code=422, detail="brief.sculpture is required")

    family = sculpture.get("family")
    if family not in GENERATORS:
        raise HTTPException(
            status_code=400,
            detail=f"family '{family}' not supported — known: {sorted(GENERATORS)}",
        )

    try:
        return generate(family, sculpture.get("parameters") or {},
                        sculpture.get("material", "stainless_316l"),
                        sculpture.get("height_m", 0.0))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


def geo_quantities(mesh: dict) -> dict:
    vertices, faces = mesh["vertices"], mesh["faces"]
    return {
        "surface_area_m2": geo_calc.surface_area(vertices, faces),
        "volume_m3": geo_calc.volume(vertices, faces),
        "bounding_box": geo_calc.bounding_box(vertices),
        "center_of_gravity_m": geo_calc.center_of_gravity(vertices, faces),
    }


def run_pipeline(brief: dict) -> dict:
    ring = generate_sculpture(brief)
    geo = geo_quantities(ring)

    # Basin (optional) + hydraulics + structural + cost.
    water = brief.get("water") or {}
    basin = None
    if water.get("basin"):
        bbox = geo["bounding_box"]["size"]
        footprint = max(0.3, min(bbox[0], bbox[2]) / 2.0)
        try:
            basin = generate_basin(water["basin"], water.get("features"),
                                   footprint_radius_m=footprint)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    basin_meta = basin["metadata"] if basin else None

    hyd = hydraulics.compute_hydraulics(brief, basin_meta)
    struct = structural.compute_structural(brief, geo, ring["metadata"],
                                           hydraulics=hyd)
    # Geometry forensics + design gates (scope §3, §28).
    integ = integrity.validate_mesh(ring["vertices"], ring["faces"])

    # Fabrication: internal skeleton sized from the structural base moment
    # (scope §15, §17). Its real steel weight feeds the BOM.
    from fabrication import panelize, skeleton
    skel = skeleton.generate_skeleton(brief, geo, struct,
                                      shell_vertices=ring["vertices"])

    # Panelization (scope §16/§18): shell -> manufacturable panels.
    panels = panelize.panelize_shell(ring["vertices"], ring["faces"])

    # Lighting engineering (scope §11/§12/§15).
    from engineering import lighting
    light = lighting.design_lighting(brief, geo, ring["vertices"], ring["faces"],
                                     basin_meta)

    cost = estimator.estimate(brief, ring["metadata"], basin_meta, hyd,
                              structural=struct, skeleton=skel, panels=panels,
                              lighting=light)

    # Internal services routing (scope §18/§20) + maintainability (§21).
    from engineering import maintainability
    from fabrication import routing
    route = routing.design_routing(brief, geo, hyd, skel, light)
    maint = maintainability.analyze_maintainability(brief, basin_meta, hyd,
                                                    light, route)
    gate_result = gates.evaluate_gates(brief, integ, struct, hyd, cost,
                                       panels=panels, lighting=light,
                                       routing=route, maintainability=maint)

    # Lift the sculpture so its base sits on the basin floor (or y=0).
    base_y = geo["bounding_box"]["min"][1]
    floor_y = basin_meta["floor_thickness_m"] if basin_meta else 0.0
    sculpture_offset_m = floor_y - base_y + 0.02

    return {
        "brief": brief,
        "sculpture": {"mesh": {"vertices": ring["vertices"], "faces": ring["faces"]},
                      "metadata": ring["metadata"]},
        "basin": basin,
        "geo_quantities": geo,
        "hydraulics": hyd,
        "structural": struct,
        "integrity": integ,
        "skeleton": skel,
        "panelization": {k: v for k, v in panels.items() if k != "panels"},
        "panels": panels["panels"],
        "lighting": light,
        "routing": route,
        "maintainability": maint,
        "gates": gate_result,
        "cost": cost,
        "sculpture_offset_m": sculpture_offset_m,
    }
