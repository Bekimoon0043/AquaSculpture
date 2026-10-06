"""Maintainability analysis (scope §21, design gate G8).

Every design gets an access/serviceability verdict per component class:
pump, nozzles, lighting, valves, drainage, internal access, cleaning,
corrosion inspection. Anything unmaintainable after assembly is flagged —
the scope's explicit "component inaccessible after assembly" rule.
"""

WADEABLE_DEPTH_M = 0.6   # basin depth a technician can wade for nozzle service


def analyze_maintainability(brief: dict, basin_meta: dict | None,
                            hydraulics: dict, lighting: dict | None,
                            routing: dict) -> dict:
    checks: list[dict] = []
    flags: list[str] = []

    def add(item, ok, note):
        checks.append({"item": item, "ok": ok, "note": note})
        if not ok:
            flags.append(f"{item}: {note}")

    # Pump / filtration: assumed plant room adjacent to basin.
    has_pump = hydraulics.get("motor_kw", 0) > 0
    add("pump_access", True,
        "plant room beside basin" if has_pump else "no pump (still basin)")

    # Nozzle access: wadeable basin or from the water surface.
    features = hydraulics.get("features", [])
    has_jets = any(f.get("nozzle") for f in features)
    depth = (basin_meta or {}).get("depth_m", 0.0)
    if has_jets:
        ok = depth <= WADEABLE_DEPTH_M
        add("nozzle_access", ok,
            f"basin depth {depth:.2f} m — wadeable" if ok
            else f"basin depth {depth:.2f} m too deep to wade; needs drain-down or diving")

    # Lighting replacement: external fixtures OK; internal LEDs need a hatch.
    internal_led = (routing or {}).get("internal_lighting_cable")
    if internal_led and (routing or {}).get("inspection_hatches", 0) == 0:
        add("lighting_access", False,
            "internal LED lighting but no inspection hatch")
    else:
        add("lighting_access", True,
            "all fixtures externally serviceable" if not internal_led
            else "internal LEDs reachable via hatches")

    # Valve access: valves sit on the manifold in the plant space.
    valves = hydraulics.get("schedules", {}).get("valves", [])
    add("valve_access", True,
        f"{len(valves)} valves in manifold chamber" if valves else "no valves")

    # Drainage.
    drains = (routing or {}).get("drain_points", 0)
    add("drain_points", drains >= 1, f"{drains} drain point(s)")

    # Internal access for tall hollow sculptures.
    hatches = (routing or {}).get("inspection_hatches", 0)
    height = (brief.get("sculpture") or {}).get("height_m", 0.0)
    if height > 2.0:
        add("internal_access", hatches >= 1,
            f"{hatches} inspection hatch(es)" if hatches
            else "no inspection hatch into the sculpture")
    else:
        add("internal_access", True, "small sculpture — no internal access needed")

    # Cleaning + corrosion inspection (water-exposed metal).
    water_features = any(f.get("flow_lps", 0) > 0 for f in features)
    add("cleaning", True,
        "jet strainers + basin sweep" if water_features else "still basin sweep")
    material = (brief.get("sculpture") or {}).get("material", "")
    add("corrosion_inspection", True,
        "annual visual + patina check" if material in ("bronze", "brass", "corten_steel")
        else "annual visual inspection")

    return {
        "checks": checks,
        "flags": flags,
        "passed": len(flags) == 0,
    }
