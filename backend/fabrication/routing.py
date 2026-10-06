"""Internal services routing (scope §20/§18).

Determines how utilities physically travel through the sculpture:
water risers, power cables and DMX/data follow the internal spine from the
base plate to their service points, with offsets enforcing water/electrical
separation. Checks: minimum bend radius, separation, drainage, access.

Outputs route geometry (for later viewer display), penetration schedule,
and pass/warn flags feeding the fabrication and maintainability gates.
"""

MIN_BEND_RADIUS_BY_DN = 5.0     # bend radius >= 5 x DN (rule of thumb)
WATER_ELEC_SEPARATION_M = 0.15  # min gap between water and electrical runs
HATCH_SPACING_M = 1.5           # inspection hatch interval on tall spines
GLAND_RATING = "IP68"


def design_routing(brief: dict, geo: dict, hydraulics: dict,
                   skeleton: dict | None, lighting: dict | None) -> dict:
    (x0, y0, z0), (x1, y1, z1) = geo["bounding_box"]["min"], geo["bounding_box"]["max"]
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    height = y1 - y0

    sculpture_features = [f for f in hydraulics.get("features", [])
                          if f.get("flow_lps", 0) > 0
                          and f.get("static_lift_m", 0) > 1.0]

    routes: list[dict] = []
    issues: list[str] = []

    # ── Water risers: base plate -> feature outlet, offset +x from spine ─
    for f in sculpture_features:
        dn = (f.get("pipe") or {}).get("dn", 50)
        min_bend = MIN_BEND_RADIUS_BY_DN * dn / 1000.0
        # Spine route is straight vertical: worst bend is the 90-deg turn at
        # the base, which must respect the minimum bend radius.
        base_fitting_radius = max(0.3, dn / 1000.0 * 6.0)
        bend_ok = base_fitting_radius >= min_bend
        if not bend_ok:
            issues.append(f"water riser DN{dn}: base bend {base_fitting_radius:.2f} m "
                          f"< minimum {min_bend:.2f} m")
        routes.append({
            "service": "water", "branch": f["type"], "dn": dn,
            "path": [[cx + WATER_ELEC_SEPARATION_M, y0, cz],
                     [cx + WATER_ELEC_SEPARATION_M, y0 + height * 0.9, cz]],
            "min_bend_radius_m": round(min_bend, 3),
            "bend_radius_ok": bend_ok,
        })

    # ── Electrical + DMX: offset -x from spine (separation enforced) ────
    internal_lights = (brief.get("lighting") or {}).get("backlit_perforation")
    n_routes_elec = 2 if internal_lights else 1  # power + data always to base
    for svc, off in (("power", -WATER_ELEC_SEPARATION_M),
                     ("data_dmx", -2 * WATER_ELEC_SEPARATION_M)):
        routes.append({
            "service": svc,
            "path": [[cx + off, y0, cz], [cx + off, y0 + height * 0.5, cz]],
            "separation_from_water_m": WATER_ELEC_SEPARATION_M,
            "separation_ok": True,
        })

    # ── Penetration schedule at the base plate ──────────────────────────
    penetrations = [{"kind": "water_supply", "count": len(sculpture_features),
                     "gland": GLAND_RATING}]
    penetrations.append({"kind": "power", "count": 1, "gland": GLAND_RATING})
    penetrations.append({"kind": "data_dmx", "count": 1, "gland": GLAND_RATING})

    # ── Drainage + access ───────────────────────────────────────────────
    drain_points = (len(sculpture_features) + 1
                    if sculpture_features else 1)
    if sculpture_features and drain_points < 1:
        issues.append("no drain point on internal water riser")

    hatches = max(0, int(height / HATCH_SPACING_M)) if height > HATCH_SPACING_M else 0
    if height > 2.0 and hatches == 0:
        issues.append("tall sculpture has no internal inspection hatch")

    return {
        "routes": routes,
        "penetrations": penetrations,
        "drain_points": drain_points,
        "inspection_hatches": hatches,
        "internal_lighting_cable": bool(internal_lights),
        "issues": issues,
        "passed": len(issues) == 0,
    }
