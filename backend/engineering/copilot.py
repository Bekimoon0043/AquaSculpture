"""Engineering copilot — deterministic core (scope §25).

Without any LLM: re-run the pipeline at a modified scale and diff every
engineering consequence — mass, wind, overturning, deflection, cost, pump.
The AI layer later wraps this in natural language ("make it 20% taller" →
this diff → explained trade-offs).
"""

import copy

SIZE_PARAMS = ("diameter_m", "major_radius_m", "height_m", "section_width_m",
               "section_depth_m", "tube_radius_m")


def scaled_brief(brief: dict, factor: float) -> dict:
    """Scale the sculpture by `factor`; site/basin stay fixed."""
    b = copy.deepcopy(brief)
    b.pop("approvals", None)  # a new variant is unapproved
    sc = b["sculpture"]
    if sc.get("height_m"):
        sc["height_m"] = round(sc["height_m"] * factor, 4)
    for k, v in (sc.get("parameters") or {}).items():
        if k in SIZE_PARAMS and isinstance(v, (int, float)):
            sc["parameters"][k] = round(v * factor, 4)
    return b


def scale_consequences(brief: dict, factor: float, run_pipeline) -> dict:
    """Run the pipeline at both scales and diff the consequences."""
    base = run_pipeline(brief)
    scaled = run_pipeline(scaled_brief(brief, factor))

    def pct(a, b):
        return round((b - a) / a * 100.0, 1) if a else None

    m0 = base["sculpture"]["metadata"]["mass_kg"]
    m1 = scaled["sculpture"]["metadata"]["mass_kg"]
    mom0 = base["structural"]["total_base_moment_knm"]
    mom1 = scaled["structural"]["total_base_moment_knm"]
    c0 = base["cost"]["total_usd"]
    c1 = scaled["cost"]["total_usd"]
    d0 = base["structural"]["analysis"]["deflection_mm"]
    d1 = scaled["structural"]["analysis"]["deflection_mm"]

    consequences = [
        {"metric": "shell_mass", "base": round(m0, 1), "scaled": round(m1, 1),
         "change_pct": pct(m0, m1)},
        {"metric": "overturning_moment", "base": round(mom0, 2),
         "scaled": round(mom1, 2), "change_pct": pct(mom0, mom1)},
        {"metric": "deflection_mm", "base": round(d0, 2), "scaled": round(d1, 2),
         "change_pct": pct(d0, d1)},
        {"metric": "total_cost_usd", "base": round(c0), "scaled": round(c1),
         "change_pct": pct(c0, c1)},
        {"metric": "pump_kw",
         "base": round(base["hydraulics"]["motor_kw"], 2),
         "scaled": round(scaled["hydraulics"]["motor_kw"], 2),
         "change_pct": pct(base["hydraulics"]["motor_kw"],
                           scaled["hydraulics"]["motor_kw"])},
    ]

    notes = []
    if scaled["structural"]["safety_factors"]["all_pass"] is False:
        weak = [k for k, v in scaled["structural"]["safety_factors"].items()
                if isinstance(v, (int, float)) and v < 1.5]
        notes.append(f"scaled design FAILS structural gate: {weak}")
    if scaled["cost"]["over_budget"]:
        notes.append("scaled design exceeds budget")
    if scaled["skeleton"]["section"] != base["skeleton"]["section"]:
        notes.append(f"skeleton upsizes {base['skeleton']['section']} -> "
                     f"{scaled['skeleton']['section']}")
    if not notes:
        notes.append("scaled design remains within all gates")

    return {
        "factor": factor,
        "consequences": consequences,
        "notes": notes,
        "base_gates_pass": not base["gates"]["hard_fail"],
        "scaled_gates_pass": not scaled["gates"]["hard_fail"],
    }
