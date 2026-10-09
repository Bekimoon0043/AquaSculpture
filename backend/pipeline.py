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
    # Wind drift / splash exclusion (scope §10).
    from engineering import wind_drift
    hyd["wind_drift"] = wind_drift.analyze_drift(brief, hyd)
    struct = structural.compute_structural(brief, geo, ring["metadata"],
                                           hydraulics=hyd)

    # Geometry forensics + design gates (scope §3, §28).
    integ = integrity.validate_mesh(ring["vertices"], ring["faces"])

    # Fabrication: internal skeleton sized from the structural base moment
    # (scope §15, §17). Its real steel weight feeds the BOM.
    from fabrication import panelize, skeleton
    skel = skeleton.generate_skeleton(brief, geo, struct,
                                      shell_vertices=ring["vertices"])

    # Mini-FEA on the generated skeleton (scope §6): direct stiffness frame
    # analysis. If the frame is overstressed or too flexible, upsize the
    # section and re-run — a real design loop, not a warning sticker.
    from engineering import fea
    from fabrication.skeleton import SHS_CATALOG
    fea_result = None
    for _attempt in range(4):
        shs = skel["section"].replace("SHS ", "").split("x")  # "SHS 100x100x5"
        section = (int(shs[0]), int(shs[2]))
        try:
            fea_result = fea.solve_frame(
                skel["members"], section,
                lateral_load_n=struct["loads"]["total_horizontal_kn"] * 1000.0,
                dead_load_n=struct["loads"]["dead_kn"] * 1000.0,
                load_height_m=geo["bounding_box"]["size"][1] / 2.0)
        except Exception as e:  # FEA must never break the pipeline
            fea_result = {"error": str(e)}
            break
        h_mm = geo["bounding_box"]["size"][1] * 1000.0
        fea_result["stress_ok"] = bool(fea_result["max_stress_mpa"] * 1.5 <= 250.0)
        fea_result["deflection_ok"] = bool(
            fea_result["max_displacement_mm"] <= h_mm / 100.0)
        fea_result["passed"] = bool(fea_result["stress_ok"]
                                    and fea_result["deflection_ok"])
        fea_result["section"] = skel["section"]
        if fea_result["passed"]:
            break
        idx = SHS_CATALOG.index(section) if section in SHS_CATALOG else -1
        if idx + 1 >= len(SHS_CATALOG):
            fea_result["passed"] = False
            break
        bigger = SHS_CATALOG[idx + 1]
        from fabrication import skeleton as _skel_mod
        skel = _skel_mod.generate_skeleton(brief, geo, struct,
                                           shell_vertices=ring["vertices"],
                                           force_section=bigger)
    struct = {**struct, "fea": fea_result}
    if fea_result and "error" not in fea_result:
        sf = dict(struct["safety_factors"])
        sf["yield_fea"] = round(250.0 / max(fea_result["max_stress_mpa"], 1e-9), 2)
        sf["deflection_fea"] = round(
            (geo["bounding_box"]["size"][1] * 1000.0 / 100.0)
            / max(fea_result["max_displacement_mm"], 1e-9), 2)
        sf["all_pass"] = bool(sf["all_pass"] and fea_result["passed"])
        struct["safety_factors"] = sf

    # Panelization (scope §16/§18): shell -> manufacturable panels.
    panels = panelize.panelize_shell(ring["vertices"], ring["faces"],
                                     shell_thickness_m=ring["metadata"]
                                     ["shell_thickness_m"])

    # Lighting engineering (scope §11/§12/§15).
    from engineering import lighting
    light = lighting.design_lighting(brief, geo, ring["vertices"], ring["faces"],
                                     basin_meta)

    # Kinetic drive engineering (scope §16) when the brief asks for motion.
    from engineering import kinetics
    kin = None
    if brief.get("kinetics"):
        kin = kinetics.design_kinetics(brief, geo, ring["vertices"],
                                       ring["faces"], ring["metadata"]["mass_kg"]
                                       + skel["total_steel_kg"],
                                       basin_meta=basin_meta)

    cost = estimator.estimate(brief, ring["metadata"], basin_meta, hyd,
                              structural=struct, skeleton=skel, panels=panels,
                              lighting=light, kinetics=kin)

    # Internal services routing (scope §18/§20) + maintainability (§21).
    from engineering import maintainability
    from fabrication import routing
    route = routing.design_routing(brief, geo, hyd, skel, light)
    maint = maintainability.analyze_maintainability(brief, basin_meta, hyd,
                                                    light, route)

    # Dynamic light show timeline (scope §14) — authored here, played by
    # AquaFlow via the LUXEXCHANGE envelope (§31).
    from engineering import light_timeline
    try:
        show = light_timeline.compile_show(brief, light)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    gate_result = gates.evaluate_gates(brief, integ, struct, hyd, cost,
                                       panels=panels, lighting=light,
                                       routing=route, maintainability=maint,
                                       approvals=brief.get("approvals"))

    # Lift the sculpture so its base sits on the basin floor (or y=0).
    base_y = geo["bounding_box"]["min"][1]
    floor_y = basin_meta["floor_thickness_m"] if basin_meta else 0.0
    sculpture_offset_m = floor_y - base_y + 0.02

    # Water visualization payload (scope §10): water surface level, ballistic
    # jet definitions, curtain sheets — the viewer animates these.
    water_viz = None
    if basin_meta:
        inner = basin_meta["inner"]
        water_level = basin_meta["depth_m"] - basin_meta["freeboard_m"]
        jets = []
        jet_feats = [f for f in hyd["features"] if f.get("jet_height_m")]
        if jet_feats and basin_meta.get("nozzle_positions"):
            v0 = jet_feats[0]["exit_velocity_ms"]
            h = jet_feats[0]["jet_height_m"]
            sr = jet_feats[0].get("splash_radius_m")
            for pos in basin_meta["nozzle_positions"]:
                jets.append({"position": pos, "exit_velocity_ms": v0,
                             "jet_height_m": h, "splash_radius_m": sr})
        bbox = geo["bounding_box"]["size"]
        curtains = [{"radius_m": round(max(bbox[0], bbox[2]) / 2 * 0.9, 3),
                     "top_y": round(bbox[1] * 0.9 + sculpture_offset_m, 3),
                     "bottom_y": water_level}
                    for f in hyd["features"]
                    if f["type"] in ("curtain_from_sculpture",
                                     "curtain_between_elements",
                                     "water_sheet", "rain_curtain")
                    and f["flow_lps"] > 0]
        water_viz = {
            "water_level_m": water_level,
            "basin_inner": inner,
            "jets": jets,
            "curtains": curtains,
        }

    result = {
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
        "light_show": show,
        "routing": route,
        "maintainability": maint,
        "kinetics": kin,
        "water_viz": water_viz,
        "gates": gate_result,
        "cost": cost,
        "sculpture_offset_m": sculpture_offset_m,
    }

    # Fabrication method statement (scope §22) — ordered build sequence.
    from fabrication import sequencing
    result["method_statement"] = sequencing.generate_method_statement(result)
    return result
