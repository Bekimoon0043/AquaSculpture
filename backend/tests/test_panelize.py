import numpy as np
import pytest

from cost import estimator
from deliverables import dxf
from engineering import gates, geo_calc, structural
from fabrication import panelize
from geometry.archetypes import generate

BRIEF = {
    "project": {"name": "s", "budget_usd": 100000},
    "sculpture": {"family": "open_ring", "height_m": 4.0,
                  "material": "stainless_316l", "finish": "mirror_polish_8"},
    "water": {"features": []},
    "lighting": {},
    "constraints": {"wind_zone": "moderate", "indoor": False},
}


def _ring(height_m=4.0):
    mesh = generate("open_ring", {"diameter_m": height_m, "tube_radius_m": 0.15,
                                  "opening_deg": 60, "segments": 24},
                    "stainless_316l", height_m)
    return mesh


def test_panels_cover_all_faces():
    mesh = _ring()
    p = panelize.panelize_shell(mesh["vertices"], mesh["faces"])
    covered = sum(x["face_count"] for x in p["panels"])
    assert covered == len(mesh["faces"])
    assert p["panel_count"] > 4


def test_weld_seam_and_curvature():
    mesh = _ring()
    p = panelize.panelize_shell(mesh["vertices"], mesh["faces"])
    assert p["total_weld_seam_m"] > 0
    classes = {x["curvature"] for x in p["panels"]}
    assert classes <= {"flat", "single_curved", "double_curved"}
    for x in p["panels"]:
        assert x["area_m2"] > 0
        assert len(x["flat_outline"]) >= 3
        assert x["weld_seam_m"] > 0


def test_flat_patterns_fit_stock_sheet_for_small_sculpture():
    mesh = _ring(2.0)
    p = panelize.panelize_shell(mesh["vertices"], mesh["faces"])
    assert p["oversized_panels"] == []


def test_dxf_writer_produces_valid_r12():
    mesh = _ring()
    p = panelize.panelize_shell(mesh["vertices"], mesh["faces"])
    text = dxf.flat_patterns_dxf(p["panels"])
    assert text.startswith("0\nSECTION")
    assert text.rstrip().endswith("EOF")
    assert text.count("LWPOLYLINE") == sum(
        1 for x in p["panels"] if len(x["flat_outline"]) >= 3)


def test_cost_adds_cutting_and_welding():
    mesh = _ring()
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    struct = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    p = panelize.panelize_shell(mesh["vertices"], mesh["faces"])
    hyd = {"motor_kw": 0.0, "features": []}
    cost = estimator.estimate(BRIEF, mesh["metadata"], None, hyd,
                              structural=struct, panels=p)
    labels = [i["label"] for s in cost["sections"] for i in s["items"]]
    assert any("CNC cutting" in l for l in labels)
    assert any("Welding" in l for l in labels)


def test_gate_g7_evaluates_panels():
    mesh = _ring()
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    struct = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    p = panelize.panelize_shell(mesh["vertices"], mesh["faces"])
    cost = {"budget_usd": None, "over_budget": False}
    hyd = {"total_flow_lps": 0.0, "motor_kw": 0.0}
    integ = {"passed": True, "warnings": [], "errors": []}
    g = gates.evaluate_gates(BRIEF, integ, struct, hyd, cost, panels=p)
    g7 = {x["id"]: x for x in g["gates"]}["G7"]
    assert g7["status"] in ("pass", "warning")
    # Oversized panel -> hard fail
    bad = {**p, "oversized_panels": ["P001"]}
    g = gates.evaluate_gates(BRIEF, integ, struct, hyd, cost, panels=bad)
    assert {x["id"]: x for x in g["gates"]}["G7"]["status"] == "fail"
    assert g["hard_fail"] is True
