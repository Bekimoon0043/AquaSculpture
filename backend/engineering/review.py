"""Multi-agent design review (scope §26).

Six domain reviewers + a Chief Engineer, rule-based for now (the LLM layer
wraps these verdicts in natural language when provider keys are funded).

Each reviewer returns findings: severity (info/warning/critical), message,
recommendation. The Chief Engineer resolves conflicts with one hard rule:
safety and engineering feasibility outrank aesthetics and cost — matching
the scope's example (frame visibility vs wind loading -> upsize the member).
"""

SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


def _finding(severity, message, recommendation):
    return {"severity": severity, "message": message,
            "recommendation": recommendation}


def designer_review(brief: dict, result: dict) -> list[dict]:
    findings = []
    size = result["geo_quantities"]["bounding_box"]["size"]
    h, w = size[1], max(size[0], size[2])
    ratio = h / max(w, 1e-6)
    if ratio > 4:
        findings.append(_finding(
            "warning", f"very slender form (h/w = {ratio:.1f})",
            "consider widening the base or reducing height for presence"))
    elif ratio < 0.4:
        findings.append(_finding(
            "info", f"low, wide form (h/w = {ratio:.1f})",
            "reads as landscape furniture; consider a vertical accent"))
    panels = result["panelization"]["panel_count"]
    if panels > 60:
        findings.append(_finding(
            "warning", f"{panels} panels will read as faceted, not smooth",
            "increase panel target size or accept visible seams as a feature"))
    if not findings:
        findings.append(_finding("info", "proportions within classic ranges",
                                 "no design changes needed"))
    return findings


def structural_review(brief: dict, result: dict) -> list[dict]:
    sf = result["structural"]["safety_factors"]
    findings = []
    for key in ("anchor_tension", "buckling", "yield", "deflection",
                "yield_fea", "deflection_fea"):
        v = sf.get(key)
        if v is not None and v < sf["required"]:
            findings.append(_finding(
                "critical", f"{key} safety factor {v} < {sf['required']}",
                "upsize members / foundation — DO NOT reduce for aesthetics"))
    fea = result["structural"].get("fea") or {}
    if fea.get("passed") is False:
        findings.append(_finding(
            "critical", "frame FEA failed after max upsizing",
            "redesign skeleton layout (more members, triangulation)"))
    if not findings:
        findings.append(_finding("info", "all structural factors adequate",
                                 f"frame: {result['skeleton']['section']}"))
    return findings


def hydraulic_review(brief: dict, result: dict) -> list[dict]:
    hyd = result["hydraulics"]
    findings = []
    if hyd["motor_kw"] > 15:
        findings.append(_finding(
            "warning", f"pump {hyd['motor_kw']:.1f} kW is large for a sculpture",
            "split into two duty pumps or reduce feature flow"))
    turnover = hyd.get("turnover_min")
    if turnover and turnover < 30:
        findings.append(_finding(
            "info", f"very fast turnover ({turnover:.0f} min)",
            "filtration oversized relative to need — energy waste"))
    if not findings:
        findings.append(_finding("info", "hydraulic network balanced",
                                 f"TDH {hyd['tdh_m']:.1f} m, "
                                 f"{hyd['total_flow_lps']:.1f} L/s"))
    return findings


def lighting_review(brief: dict, result: dict) -> list[dict]:
    illum = result["lighting"]["illumination"]
    findings = []
    if illum["coverage_pct"] < 60:
        findings.append(_finding(
            "warning", f"coverage {illum['coverage_pct']:.0f}% of shell",
            "reposition fixtures toward the form's mid-height faces"))
    if illum["wasted_fixtures"]:
        findings.append(_finding(
            "warning", f"{illum['wasted_fixtures']} fixture(s) miss the sculpture",
            "remove or re-aim — wasted power and glare"))
    if not findings:
        findings.append(_finding("info", "illumination adequate",
                                 f"avg {illum['avg_lux']:.0f} lux"))
    return findings


def fabrication_review(brief: dict, result: dict) -> list[dict]:
    p = result["panelization"]
    findings = []
    if p["oversized_panels"]:
        findings.append(_finding(
            "critical", f"panels exceed stock sheet: {p['oversized_panels']}",
            "re-panelize with smaller target size"))
    if p["double_curved_share"] > 0.3:
        findings.append(_finding(
            "warning", f"{p['double_curved_share']:.0%} double-curved panels",
            "needs stamping/hydroforming — price accordingly"))
    if not findings:
        findings.append(_finding("info", "panels fit stock sheets",
                                 f"{p['panel_count']} panels"))
    return findings


def cost_review(brief: dict, result: dict) -> list[dict]:
    cost = result["cost"]
    findings = []
    if cost.get("budget_usd") is not None:
        if cost["over_budget"]:
            findings.append(_finding(
                "critical", f"over budget by USD {abs(cost['budget_delta_usd']):,.0f}",
                "run /api/optimize with goal=cost before client review"))
        elif cost["budget_delta_usd"] > 0.4 * cost["budget_usd"]:
            findings.append(_finding(
                "info", "large budget headroom",
                "client may accept a taller/premium-finish option"))
    if not findings:
        findings.append(_finding("info", "cost within expectations", ""))
    return findings


REVIEWERS = {
    "designer": designer_review,
    "structural": structural_review,
    "hydraulic": hydraulic_review,
    "lighting": lighting_review,
    "fabrication": fabrication_review,
    "cost": cost_review,
}


def chief_engineer(reviews: dict[str, list[dict]]) -> dict:
    """Resolve conflicts: safety first, then feasibility, then cost, then
    aesthetics (scope §26 precedence)."""
    criticals = [f for r in reviews.values() for f in r
                 if f["severity"] == "critical"]
    warnings = [f for r in reviews.values() for f in r
                if f["severity"] == "warning"]
    verdict = ("REJECTED — resolve critical findings"
               if criticals
               else "APPROVED WITH CONDITIONS" if warnings
               else "APPROVED")
    actions = [f["recommendation"] for f in criticals + warnings
               if f["recommendation"]]
    return {
        "verdict": verdict,
        "critical_count": len(criticals),
        "warning_count": len(warnings),
        "actions": actions,
        "precedence": "safety > feasibility > cost > aesthetics",
    }


def review_design(brief: dict, run_pipeline) -> dict:
    result = run_pipeline(brief)
    reviews = {name: fn(brief, result) for name, fn in REVIEWERS.items()}
    return {"reviews": reviews, "chief_engineer": chief_engineer(reviews)}
