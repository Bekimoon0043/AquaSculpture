"""Structural v1 (PLAN.md §6 — structural, simplified hand calcs).

- Wind: q = 0.613 * V^2 (Pa), V from wind_zone map; force on the bbox
  projected area with shape factor 1.2; overturning moment at the base.
- Base plate + 4-bolt anchor tension check (simplified couple model).
- Foundation pad sized heuristically from the moment; rebar at 110 kg/m3.
- Internal armature mass: 25% of shell mass, scaled by slenderness (h/w).

PRELIMINARY — requires licensed engineer review (PLAN.md §10).
"""

WIND_ZONE_MS = {"low": 35.0, "moderate": 45.0, "high": 55.0, "extreme": 65.0}
SHAPE_FACTOR = 1.2
BOLT_COUNT = 4
BOLT_ALLOWABLE_KN = 25.0          # M16 gr.8.8 simplified allowable tension
REBAR_KG_PER_M3 = 110.0
ARMATURE_MASS_FRACTION = 0.25


def wind_pressure_pa(wind_zone: str, indoor: bool = False) -> tuple[float, float]:
    """(wind speed m/s, velocity pressure Pa)."""
    if indoor:
        return 0.0, 0.0
    v = WIND_ZONE_MS.get(wind_zone, WIND_ZONE_MS["moderate"])
    return v, 0.613 * v**2


def compute_structural(brief: dict, geo: dict, sculpture_meta: dict) -> dict:
    constraints = brief.get("constraints") or {}
    wind_zone = constraints.get("wind_zone", "moderate")
    indoor = bool(constraints.get("indoor", False))
    wind_speed, q_pa = wind_pressure_pa(wind_zone, indoor)

    size = geo["bounding_box"]["size"]
    height_m = max(size[1], 0.1)
    width_m = max(size[0], size[2], 0.1)
    projected_area_m2 = width_m * height_m

    force_kn = q_pa * projected_area_m2 * SHAPE_FACTOR / 1000.0
    lever_m = height_m / 2.0
    moment_knm = force_kn * lever_m

    # Base plate + anchor bolts (couple model: tension pair resists moment).
    plate_side_m = min(max(0.4, width_m * 0.8), 2.0)
    bolt_spacing_m = plate_side_m * 0.7
    bolt_tension_kn = (moment_knm / (2.0 * bolt_spacing_m)
                       if bolt_spacing_m > 0 else 0.0)
    bolts_ok = bolt_tension_kn <= BOLT_ALLOWABLE_KN

    # Foundation pad heuristic from overturning moment.
    pad_side_m = max(1.0, 1.5 * (moment_knm / 25.0) ** (1.0 / 3.0))
    pad_depth_m = max(0.5, 0.4 * pad_side_m)
    concrete_m3 = pad_side_m**2 * pad_depth_m
    rebar_kg = concrete_m3 * REBAR_KG_PER_M3

    # Armature: shell fraction scaled by slenderness (tall thin = more steel).
    slenderness = height_m / width_m
    slenderness_factor = min(max(slenderness / 3.0, 1.0), 2.0)
    armature_kg = (sculpture_meta["mass_kg"] * ARMATURE_MASS_FRACTION
                   * slenderness_factor)

    return {
        "wind_zone": wind_zone,
        "indoor": indoor,
        "wind_speed_ms": wind_speed,
        "velocity_pressure_pa": round(q_pa, 1),
        "shape_factor": SHAPE_FACTOR,
        "projected_area_m2": round(projected_area_m2, 3),
        "wind_force_kn": round(force_kn, 3),
        "overturning_moment_knm": round(moment_knm, 3),
        "base_plate": {
            "side_m": round(plate_side_m, 3),
            "bolt_count": BOLT_COUNT,
            "bolt_spacing_m": round(bolt_spacing_m, 3),
            "bolt_tension_kn": round(bolt_tension_kn, 3),
            "bolt_allowable_kn": BOLT_ALLOWABLE_KN,
            "bolts_ok": bolts_ok,
        },
        "foundation": {
            "pad_side_m": round(pad_side_m, 3),
            "pad_depth_m": round(pad_depth_m, 3),
            "concrete_m3": round(concrete_m3, 3),
            "rebar_kg": round(rebar_kg, 1),
        },
        "armature": {
            "slenderness": round(slenderness, 3),
            "slenderness_factor": round(slenderness_factor, 3),
            "steel_kg": round(armature_kg, 2),
        },
        "disclaimer": "Preliminary — requires licensed engineer review.",
    }
