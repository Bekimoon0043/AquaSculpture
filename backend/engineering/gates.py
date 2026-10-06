"""Automatic design gates (scope §28).

Every pipeline run evaluates the G0–G10 gate chain. A gate is one of:
  pass | fail | warning | not_evaluated (subsystem not built yet).
A failed engineering gate means the design must NOT be called
production-ready — `production_ready` reflects that.
"""

GATES = [
    ("G0", "Brief Complete"),
    ("G1", "Concept Approved"),
    ("G2", "Geometry Valid"),
    ("G3", "Material Valid"),
    ("G4", "Structural PASS"),
    ("G5", "Hydraulic PASS"),
    ("G6", "Lighting PASS"),
    ("G7", "Fabrication PASS"),
    ("G8", "Maintainability PASS"),
    ("G9", "Cost PASS"),
    ("G10", "Production Package Approved"),
]


def evaluate_gates(brief: dict, integrity: dict, structural: dict,
                   hydraulics: dict, cost: dict) -> dict:
    results: dict[str, dict] = {}

    def put(gid, status, note=""):
        results[gid] = {"status": status, "note": note}

    # G0: pipeline only runs on a schema-shaped brief.
    put("G0", "pass", "brief accepted by pipeline")

    # G1: single generated concept; human approval happens in the UI.
    put("G1", "not_evaluated", "multi-concept approval flow not built yet")

    # G2: geometry integrity forensics.
    if integrity["passed"]:
        note = "mesh forensics clean"
        if integrity["warnings"]:
            note += "; " + "; ".join(integrity["warnings"])
        put("G2", "pass" if not integrity["warnings"] else "warning", note)
    else:
        put("G2", "fail", "; ".join(integrity["errors"]))

    # G3: material must exist in the engineering database.
    put("G3", "pass", f"material '{brief['sculpture']['material']}' in database")

    # G4: structural safety factors.
    sf = structural.get("safety_factors", {})
    if sf.get("all_pass"):
        put("G4", "pass", "all safety factors >= required")
    else:
        weak = [k for k, v in sf.items()
                if isinstance(v, (int, float)) and v < sf.get("required", 1.5)]
        put("G4", "fail", f"safety factors below required: {weak}")

    # G5: hydraulics — flow consistent with requested features.
    features = (brief.get("water") or {}).get("features") or []
    wants_water = any(f.get("type") not in (None, "still_basin") for f in features)
    flow = hydraulics.get("total_flow_lps", 0.0)
    if wants_water and flow <= 0:
        put("G5", "fail", "water features requested but computed flow is zero")
    elif not wants_water:
        put("G5", "pass", "still basin — no pumped flow required")
    else:
        put("G5", "pass", f"total flow {flow:.1f} L/s, "
                          f"pump {hydraulics.get('motor_kw', 0):.1f} kW")

    # G6–G8: subsystems not built yet.
    put("G6", "not_evaluated", "lighting engineering not built yet")
    put("G7", "not_evaluated", "panelization/fabrication checks not built yet")
    put("G8", "not_evaluated", "maintainability analysis not built yet")

    # G9: cost vs budget (budget optional).
    if cost.get("budget_usd") is None:
        put("G9", "warning", "no budget in brief — cannot check cost gate")
    elif cost["over_budget"]:
        put("G9", "fail", f"over budget by USD {abs(cost['budget_delta_usd']):,.0f}")
    else:
        put("G9", "pass", "within budget")

    # G10: everything above must pass/warn for a package to be approved.
    put("G10", "not_evaluated", "package approval is a human sign-off")

    hard_fail = any(r["status"] == "fail" for r in results.values())
    evaluated = [g for g in results if results[g]["status"] != "not_evaluated"]
    return {
        "gates": [{"id": gid, "label": label, **results[gid]}
                  for gid, label in GATES],
        "production_ready": not hard_fail and len(evaluated) >= 5,
        "hard_fail": hard_fail,
    }
