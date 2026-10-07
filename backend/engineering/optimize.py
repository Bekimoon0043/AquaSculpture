"""Design optimization engine (scope §27).

Goal-driven search over design variants: scale factors x section tweaks,
every candidate run through the FULL pipeline and judged by the design
gates. A candidate that fails any engineering gate is rejected, not ranked
— optimization never trades away safety (scope §28 rule).

Goals: cost | weight | pump_power | weld_length
"""

from engineering.copilot import scaled_brief

SCALE_GRID = (0.8, 0.9, 1.0, 1.1, 1.2)
SECTION_SHAVES = (1.0, 0.85, 0.7)  # shell thickness multiplier per variant

GOAL_METRIC = {
    "cost": lambda r: r["cost"]["total_usd"],
    "weight": lambda r: (r["sculpture"]["metadata"]["mass_kg"]
                         + r["skeleton"]["total_steel_kg"]),
    "pump_power": lambda r: r["hydraulics"]["motor_kw"],
    "weld_length": lambda r: r["panelization"]["total_weld_seam_m"],
}


def _variant_brief(brief: dict, scale: float, shave: float) -> dict:
    b = scaled_brief(brief, scale)
    if shave != 1.0:
        params = b["sculpture"].setdefault("parameters", {})
        for k in ("tube_radius_m", "section_width_m", "section_depth_m",
                  "thickness_m"):
            if isinstance(params.get(k), (int, float)):
                params[k] = round(params[k] * shave, 4)
    return b


def optimize(brief: dict, goal: str, run_pipeline) -> dict:
    if goal not in GOAL_METRIC:
        raise ValueError(f"unknown goal '{goal}'; choose from {sorted(GOAL_METRIC)}")

    metric = GOAL_METRIC[goal]
    candidates = []
    for scale in SCALE_GRID:
        for shave in SECTION_SHAVES:
            vb = _variant_brief(brief, scale, shave)
            try:
                r = run_pipeline(vb)
            except Exception:
                continue
            candidates.append({
                "scale": scale, "section_shave": shave,
                "gates_pass": not r["gates"]["hard_fail"],
                "over_budget": r["cost"]["over_budget"],
                "value": round(metric(r), 2),
                "total_usd": round(r["cost"]["total_usd"]),
                "mass_kg": round(r["sculpture"]["metadata"]["mass_kg"]
                                 + r["skeleton"]["total_steel_kg"], 1),
            })

    passing = [c for c in candidates if c["gates_pass"] and not c["over_budget"]]
    passing.sort(key=lambda c: c["value"])

    base = next((c for c in candidates
                 if c["scale"] == 1.0 and c["section_shave"] == 1.0), None)
    best = passing[0] if passing else None
    return {
        "goal": goal,
        "candidates": sorted(candidates, key=lambda c: c["value"]),
        "evaluated": len(candidates),
        "gate_passing": len(passing),
        "base": base,
        "best": best,
        "improvement_pct": (round((base["value"] - best["value"])
                                  / base["value"] * 100.0, 1)
                            if base and best else None),
        "rule": "gate-failing candidates are rejected, never ranked",
    }
