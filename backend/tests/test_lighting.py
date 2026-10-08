import pytest

from engineering import geo_calc, lighting
from geometry.archetypes import generate

BRIEF = {
    "project": {"name": "s", "budget_usd": 100000},
    "sculpture": {"family": "open_ring", "height_m": 4.0,
                  "material": "stainless_316l", "finish": "mirror_polish_8"},
    "water": {"features": []},
    "lighting": {"sculpture_uplights": 4, "submersible_rgb": 6},
    "constraints": {"wind_zone": "moderate", "indoor": False},
}

BASIN_META = {"floor_thickness_m": 0.15,
              "inner": {"radius_m": 3.0}}


def _ring():
    mesh = generate("open_ring", {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                  "opening_deg": 60, "segments": 24},
                    "stainless_316l", 4.0)
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    return mesh, geo


def test_fixture_placement_counts_and_positions():
    mesh, geo = _ring()
    fixtures = lighting.place_fixtures(BRIEF, geo, BASIN_META)
    up = [f for f in fixtures if f["catalog"] == "uplight_36w_rgbw"]
    sub = [f for f in fixtures if f["catalog"] == "submersible_12w_rgb"]
    assert len(up) == 4 and len(sub) == 6
    for f in fixtures:
        assert len(f["position"]) == 3 and len(f["aim"]) == 3
        assert abs(sum(a * a for a in f["aim"]) - 1.0) < 1e-3  # ~unit aim


def test_illumination_numbers():
    mesh, geo = _ring()
    fixtures = lighting.place_fixtures(BRIEF, geo, BASIN_META)
    illum = lighting.illuminate(fixtures, mesh["vertices"], mesh["faces"])
    assert illum["avg_lux"] > 0
    assert illum["max_lux"] >= illum["avg_lux"]
    assert 0 <= illum["coverage_pct"] <= 100


def test_flux_scales_with_fixture_power():
    # Same position, two identical fixtures -> doubles the flux on lit faces.
    mesh, geo = _ring()
    one = lighting.place_fixtures({**BRIEF, "lighting":
                                   {"sculpture_uplights": 1, "submersible_rgb": 0}},
                                  geo, None)
    two = one + [{**one[0]}]
    l_one = lighting.illuminate(one, mesh["vertices"], mesh["faces"])
    l_two = lighting.illuminate(two, mesh["vertices"], mesh["faces"])
    assert l_two["avg_lux"] == pytest.approx(2 * l_one["avg_lux"], rel=1e-3)


def test_wasted_fixture_detection():
    # A fixture aimed away from the shell must be flagged as wasted.
    mesh, geo = _ring()
    bad = [{"id": "X01", "catalog": "uplight_36w_rgbw",
            "position": [5.0, 0.05, 0.0], "aim": [1.0, 0.0, 0.0]}]
    illum = lighting.illuminate(bad, mesh["vertices"], mesh["faces"])
    assert illum["wasted_fixtures"] == 1


def test_dmx_and_psu_math():
    mesh, geo = _ring()
    fixtures = lighting.place_fixtures(BRIEF, geo, BASIN_META)
    ctrl = lighting.control_engineering(fixtures, BASIN_META)
    # 4 x 36W + 6 x 12W = 216 W
    assert ctrl["total_load_w"] == pytest.approx(216.0)
    assert ctrl["psu_count"] >= 1
    # 4x4ch + 6x3ch = 34 channels, addresses sequential
    assert ctrl["dmx_channels_used"] == 34
    assert ctrl["dmx_universes"] == 1
    addrs = [r["dmx_address"] for r in ctrl["schedule"]]
    assert addrs[0] == 1 and addrs[-1] == 32
    assert isinstance(ctrl["voltage_drop_ok"], bool)


def test_g6_gate_live():
    from engineering import gates, structural
    mesh, geo = _ring()
    struct = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    light = lighting.design_lighting(BRIEF, geo, mesh["vertices"], mesh["faces"],
                                     BASIN_META)
    g = gates.evaluate_gates(BRIEF, {"passed": True, "warnings": [], "errors": []},
                             struct, {"total_flow_lps": 0.0, "motor_kw": 0.0},
                             {"budget_usd": None, "over_budget": False},
                             lighting=light)
    g6 = {x["id"]: x for x in g["gates"]}["G6"]
    assert g6["status"] in ("pass", "warning")


def test_face_lux_heatmap_present():
    mesh, geo = _ring()
    fixtures = lighting.place_fixtures(BRIEF, geo, BASIN_META)
    illum = lighting.illuminate(fixtures, mesh["vertices"], mesh["faces"])
    assert len(illum["face_lux"]) == len(mesh["faces"])
    assert max(illum["face_lux"]) == pytest.approx(illum["max_lux"], abs=0.2)


def test_auto_aim_and_hotspots():
    mesh, geo = _ring()
    out = lighting.design_lighting(BRIEF, geo, mesh["vertices"],
                                   mesh["faces"], BASIN_META)
    illum = out["illumination"]
    assert isinstance(illum["hotspots"]["count"], int)
    assert illum["hotspots"]["max_ratio"] >= 1.0
