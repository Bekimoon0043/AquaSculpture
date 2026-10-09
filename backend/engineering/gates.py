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
                   hydraulics: dict, cost: dict, panels: dict | None = None,
                   lighting: dict | None = None, routing: dict | None = None,
                   maintainability: dict | None = None,
                   approvals: dict | None = None) -> dict:
    results: dict[str, dict] = {}
    approvals = approvals or {}

    def approved(gid):
        a = approvals.get(gid)
        if not a or not a.get("by"):
            return None
        return f"approved by {a['by']}" + (f" on {a['at'][:10]}" if a.get("at") else "")

    def put(gid, status, note=""):
        results[gid] = {"status": status, "note": note}

    # G0: pipeline only runs on a schema-shaped brief.
    put("G0", "pass", "brief accepted by pipeline")

    # G1: concept approval is a human decision, recorded in brief.approvals.
    if approved("G1"):
        put("G1", "pass", approved("G1"))
    else:
        put("G1", "not_evaluated", "awaiting concept approval (Concepts tab)")

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
                if isinstance(v, (int, float)) and not isinstance(v, bool)
                and k != "required" and v < sf.get("required", 1.5)]
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

    # G6: lighting engineering (scope §11–§15).
    if lighting is None:
        put("G6", "not_evaluated", "lighting engineering not run")
    elif lighting["controls"]["fixture_count"] == 0:
        put("G6", "warning", "no fixtures in brief — sculpture unlit at night")
    else:
        illum = lighting["illumination"]
        ctrl = lighting["controls"]
        if not ctrl["voltage_drop_ok"]:
            put("G6", "fail",
                f"voltage drop {ctrl['max_voltage_drop_v']} V exceeds limit")
        elif illum["coverage_pct"] < 60:
            put("G6", "warning",
                f"only {illum['coverage_pct']:.0f}% of surface above "
                f"{illum['min_lux_target']:.0f} lux"
                + (f"; {illum['wasted_fixtures']} fixture(s) miss the sculpture"
                   if illum["wasted_fixtures"] else ""))
        else:
            put("G6", "pass",
                f"{ctrl['fixture_count']} fixtures, {illum['avg_lux']:.0f} lux avg, "
                f"{illum['coverage_pct']:.0f}% coverage, "
                f"{ctrl['dmx_universes']} DMX universe(s)")

    # G7: panelization/fabrication feasibility (scope §16–§19).
    if panels is None:
        put("G7", "not_evaluated", "panelization not run")
    elif panels["oversized_panels"]:
        put("G7", "fail",
            f"panels exceed stock sheet {panels['sheet_max_m']}: "
            f"{panels['oversized_panels']}")
    elif panels["double_curved_share"] > 0.3:
        put("G7", "warning",
            f"{panels['double_curved_share']:.0%} double-curved panels need "
            "stamping/hydroforming")
    else:
        put("G7", "pass",
            f"{panels['panel_count']} panels, all fit stock sheet, "
            f"weld {panels['total_weld_seam_m']:.1f} m")

    # G8: maintainability (scope §21).
    if maintainability is None:
        put("G8", "not_evaluated", "maintainability analysis not run")
    elif maintainability["passed"]:
        put("G8", "pass", "all service classes accessible")
    else:
        put("G8", "fail", "; ".join(maintainability["flags"]))

    # Routing problems also surface on G7 (fabrication feasibility).
    if routing is not None and not routing["passed"]:
        g7 = results.get("G7")
        if g7 and g7["status"] == "pass":
            results["G7"] = {"status": "warning",
                             "note": "; ".join(routing["issues"])}

    # G9: cost vs budget (budget optional).
    if cost.get("budget_usd") is None:
        put("G9", "warning", "no budget in brief — cannot check cost gate")
    elif cost["over_budget"]:
        put("G9", "fail", f"over budget by USD {abs(cost['budget_delta_usd']):,.0f}")
    else:
        put("G9", "pass", "within budget")

    # G10: human sign-off, but it is void the moment any engineering gate
    # fails — approval never overrides the engine (scope §28).
    engineering_fail = any(r["status"] == "fail" for r in results.values())
    if approved("G10") and engineering_fail:
        put("G10", "fail", "approval void — an engineering gate is failing")
    elif approved("G10"):
        put("G10", "pass", approved("G10"))
    else:
        put("G10", "not_evaluated", "package approval is a human sign-off (Export tab)")

    hard_fail = any(r["status"] == "fail" for r in results.values())
    evaluated = [g for g in results if results[g]["status"] != "not_evaluated"]
    return {
        "gates": [{"id": gid, "label": label, **results[gid]}
                  for gid, label in GATES],
        "production_ready": (not hard_fail and len(evaluated) >= 5
                             and results["G10"]["status"] == "pass"),
        "hard_fail": hard_fail,
    }
