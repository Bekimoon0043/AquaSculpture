import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from engineering import geo_calc, kinetics, structural, wind_drift
from fabrication import skeleton
from geometry.archetypes import generate
from main import app

client = TestClient(app)

BRIEF = {
    "project": {"name": "s", "budget_usd": 100000},
    "sculpture": {"family": "open_ring", "height_m": 4.0,
                  "material": "stainless_316l", "finish": "mirror_polish_8"},
    "water": {"features": [{"type": "bubbler_field", "count": 12}]},
    "lighting": {},
    "constraints": {"wind_zone": "high", "indoor": False, "public_access": True},
}
BASIN_META = {"water_volume_m3": 6.0, "depth_m": 0.45,
              "floor_thickness_m": 0.15, "inner": {"radius_m": 3.0}}


def _ring():
    mesh = generate("open_ring", {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                  "opening_deg": 60, "segments": 16},
                    "stainless_316l", 4.0)
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    return mesh, geo


def test_wind_drift_exclusion_zone():
    hyd = {"features": [{"type": "bubbler_field", "jet_height_m": 8.0}]}
    d = wind_drift.analyze_drift(BRIEF, hyd)
    assert d["per_feature"][0]["drift_m"] > 0
    assert d["max_exclusion_radius_m"] > 2.0
    indoor = wind_drift.analyze_drift(
        {**BRIEF, "constraints": {"indoor": True}}, hyd)
    assert indoor["max_exclusion_radius_m"] == 0.0


def test_site_wind_speed_overrides_zone():
    mesh, geo = _ring()
    s1 = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    b2 = {**BRIEF, "constraints": {**BRIEF["constraints"], "site_wind_ms": 25.0}}
    s2 = structural.compute_structural(b2, geo, mesh["metadata"])
    assert s2["wind_speed_ms"] == 25.0
    assert s2["wind_force_kn"] < s1["wind_force_kn"]


def test_snow_and_maintenance_loads():
    mesh, geo = _ring()
    s = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    assert s["loads"]["snow_kn"] > 0
    assert s["loads"]["maintenance_kn"] == 0.9
    assert s["loads"]["thermal"]["expansion_mm"] > 0


def test_kinetic_collision_check():
    mesh, geo = _ring()
    brief = {"kinetics": {"motion": "rotation", "axis": "y", "rpm": 2.0}}
    k = kinetics.design_kinetics(brief, geo, mesh["vertices"], mesh["faces"],
                                 400.0, basin_meta=BASIN_META)
    assert k["collision"]["clearance_ok"] is True
    tight = {**BASIN_META, "inner": {"radius_m": 1.8}}
    k2 = kinetics.design_kinetics(brief, geo, mesh["vertices"], mesh["faces"],
                                  400.0, basin_meta=tight)
    assert k2["collision"]["clearance_ok"] is False


def test_skeleton_has_braces():
    mesh, geo = _ring()
    struct = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    skel = skeleton.generate_skeleton(BRIEF, geo, struct,
                                      shell_vertices=mesh["vertices"])
    kinds = {m["kind"] for m in skel["members"]}
    assert "brace" in kinds


def test_boq_and_currency():
    brief = {**EXAMPLE_BRIEF,
             "project": {**EXAMPLE_BRIEF["project"], "currency": "ETB",
                         "currency_rate": 155.0},
             "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                           "parameters": {"diameter_m": 4.0,
                                          "tube_radius_m": 0.15,
                                          "opening_deg": 90, "segments": 12}}}
    resp = client.post("/api/engineering/run", json=brief)
    assert resp.status_code == 200
    cost = resp.json()["cost"]
    assert cost["display_currency"] == "ETB"
    assert cost["total_display"] == pytest.approx(cost["total_usd"] * 155.0,
                                                  rel=1e-3)
    assert len(cost["boq"]) > 10
    assert {"category", "item", "qty", "unit", "rate_usd",
            "amount_usd"} <= set(cost["boq"][0].keys())
