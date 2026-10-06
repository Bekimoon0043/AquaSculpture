import pytest

from cost import estimator
from engineering import geo_calc, structural
from geometry.archetypes import generate

BRIEF = {
    "project": {"name": "s", "budget_usd": 100000},
    "sculpture": {"family": "open_ring", "height_m": 4.0,
                  "material": "stainless_316l", "finish": "mirror_polish_8"},
    "water": {"features": []},
    "lighting": {},
    "constraints": {"wind_zone": "moderate", "indoor": False},
}


def _ring(height_m):
    mesh = generate("open_ring", {"diameter_m": height_m, "tube_radius_m": 0.15,
                                  "opening_deg": 60, "segments": 16},
                    "stainless_316l", height_m)
    geo = {
        "bounding_box": geo_calc.bounding_box(mesh["vertices"]),
    }
    return mesh, geo


def test_wind_pressure_map():
    assert structural.wind_pressure_pa("low")[0] == 35.0
    assert structural.wind_pressure_pa("high")[1] > structural.wind_pressure_pa("low")[1]
    assert structural.wind_pressure_pa("high", indoor=True) == (0.0, 0.0)


def test_higher_wind_higher_moment():
    mesh, geo = _ring(4.0)
    low = structural.compute_structural(
        {**BRIEF, "constraints": {"wind_zone": "low", "indoor": False}},
        geo, mesh["metadata"])
    high = structural.compute_structural(
        {**BRIEF, "constraints": {"wind_zone": "high", "indoor": False}},
        geo, mesh["metadata"])
    assert high["overturning_moment_knm"] > low["overturning_moment_knm"]
    assert high["wind_force_kn"] > low["wind_force_kn"]
    assert high["foundation"]["concrete_m3"] > low["foundation"]["concrete_m3"]


def test_indoor_no_wind():
    mesh, geo = _ring(4.0)
    result = structural.compute_structural(
        {**BRIEF, "constraints": {"indoor": True}}, geo, mesh["metadata"])
    assert result["wind_force_kn"] == 0.0
    assert result["overturning_moment_knm"] == 0.0


def test_taller_sculpture_more_armature():
    # Same material/thickness: taller ring -> larger shell and slenderness.
    short, short_geo = _ring(2.0)
    tall, tall_geo = _ring(6.0)
    s_short = structural.compute_structural(BRIEF, short_geo, short["metadata"])
    s_tall = structural.compute_structural(BRIEF, tall_geo, tall["metadata"])
    assert s_tall["armature"]["steel_kg"] > s_short["armature"]["steel_kg"]


def test_rebar_and_bolt_check():
    mesh, geo = _ring(4.0)
    s = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    fdn = s["foundation"]
    assert fdn["rebar_kg"] == pytest.approx(fdn["concrete_m3"] * 110.0, rel=1e-3)
    assert isinstance(s["base_plate"]["bolts_ok"], bool)
    assert s["base_plate"]["bolt_count"] == 4


def test_estimator_uses_structural_numbers():
    mesh, geo = _ring(4.0)
    s = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    hyd = {"motor_kw": 0.0, "features": []}
    cost = estimator.estimate(BRIEF, mesh["metadata"], None, hyd, structural=s)
    by_key = {sec["key"]: sec for sec in cost["sections"]}
    assert by_key["armature"]["items"][0]["qty"] == pytest.approx(
        s["armature"]["steel_kg"], rel=1e-3)
    concrete_item = by_key["foundation"]["items"][0]
    assert concrete_item["qty"] == pytest.approx(s["foundation"]["concrete_m3"],
                                                 rel=1e-3)
    assert any("anchors" in i["label"] for i in by_key["foundation"]["items"])


def test_solidity_reduces_wind_force():
    # Same geometry: open ring (solidity 0.15) must catch far less wind
    # than a solid panel (solidity 0.95).
    mesh, geo = _ring(4.0)
    open_meta = {**mesh["metadata"], "family": "open_ring"}
    solid_meta = {**mesh["metadata"], "family": "relief_panel"}
    s_open = structural.compute_structural(BRIEF, geo, open_meta)
    s_solid = structural.compute_structural(BRIEF, geo, solid_meta)
    assert s_open["solidity"] < s_solid["solidity"]
    assert s_open["wind_force_kn"] < 0.3 * s_solid["wind_force_kn"]


def test_jet_reaction_adds_moment():
    mesh, geo = _ring(4.0)
    hyd = {"total_flow_lps": 20.0, "nozzle_pressure_head_m": 8.0}
    dry = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    wet = structural.compute_structural(BRIEF, geo, mesh["metadata"],
                                        hydraulics=hyd)
    assert wet["loads"]["jet_reaction_kn"] > 0
    assert wet["total_base_moment_knm"] > dry["total_base_moment_knm"]


def test_analysis_block_and_safety_factors():
    mesh, geo = _ring(4.0)
    s = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    ana = s["analysis"]
    assert ana["deflection_mm"] > 0
    assert ana["natural_frequency_hz"] > 0
    assert isinstance(ana["resonance_risk"], bool)
    sf = s["safety_factors"]
    for key in ("overturning", "sliding", "anchor_tension", "buckling", "yield"):
        assert key in sf
    assert sf["buckling"] is None or sf["buckling"] > 1.0
    assert isinstance(sf["all_pass"], bool)


def test_taller_means_more_deflection():
    short, short_geo = _ring(2.0)
    tall, tall_geo = _ring(6.0)
    s_short = structural.compute_structural(BRIEF, short_geo, short["metadata"])
    s_tall = structural.compute_structural(BRIEF, tall_geo, tall["metadata"])
    assert s_tall["analysis"]["deflection_mm"] > s_short["analysis"]["deflection_mm"]


def test_indoor_all_horizontal_loads_zero():
    mesh, geo = _ring(4.0)
    s = structural.compute_structural(
        {**BRIEF, "constraints": {"indoor": True}}, geo, mesh["metadata"])
    assert s["loads"]["total_horizontal_kn"] == 0.0
    assert s["safety_factors"]["all_pass"] is True
    assert s["foundation"]["bearing_kpa"] > 0
