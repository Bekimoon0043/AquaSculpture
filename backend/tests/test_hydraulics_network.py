import pytest

from engineering import hydraulics

BRIEF = {
    "project": {"name": "s"},
    "sculpture": {"family": "open_ring", "height_m": 4.0},
    "water": {
        "features": [
            {"type": "bubbler_field", "count": 12},
            {"type": "curtain_from_sculpture", "spill_edge_length_m": 5.0,
             "head_m": 0.02},
        ],
    },
}

BASIN_META = {"water_volume_m3": 6.0}


def test_branch_network_and_fittings():
    r = hydraulics.compute_hydraulics(BRIEF, BASIN_META)
    for f in r["features"]:
        assert f["pipe"] is not None
        assert f["branch_loss_m"] == pytest.approx(
            f["branch_friction_m"] + f["fitting_loss_m"], rel=1e-3)
        assert f["fitting_loss_m"] > 0
        assert f["valve"]["dn"] == f["pipe"]["dn"]
    # TDH now includes the worst branch loss on top of v1 terms.
    assert r["tdh_m"] > r["static_lift_m"] + r["friction_head_m"] \
        + r["nozzle_pressure_head_m"]


def test_jet_trajectory_estimate():
    r = hydraulics.compute_hydraulics(BRIEF, BASIN_META)
    bubbler = next(f for f in r["features"] if f["type"] == "bubbler_field")
    assert bubbler["exit_velocity_ms"] > 0
    assert bubbler["jet_height_m"] > 0
    # Jet height must not exceed the ideal h = v^2/2g (air loss derates it).
    ideal = bubbler["exit_velocity_ms"]**2 / (2 * 9.81)
    assert bubbler["jet_height_m"] < ideal


def test_manifold_and_schedules():
    many = {"type": "foam_jet_field", "count": 6}
    brief = {**BRIEF, "water": {"features": [
        *BRIEF["water"]["features"], many]}}
    r = hydraulics.compute_hydraulics(brief, BASIN_META)
    assert r["manifold"]["branches"] == 3
    assert r["manifold"]["dn"] >= r["main_pipe"]["dn"]
    s = r["schedules"]
    assert s["pump"]["duty_flow_lps"] == pytest.approx(r["total_flow_lps"], rel=0.01)
    assert len(s["nozzles"]) == 2        # bubbler + foam jet branches
    assert len(s["valves"]) == 3
    assert len(s["pipes"]) == 4          # main + 3 branches


def test_filtration_sizing():
    r = hydraulics.compute_hydraulics(BRIEF, BASIN_META)
    filt = r["filtration"]
    assert filt is not None
    assert filt["flow_m3h"] == pytest.approx(r["total_flow_lps"] * 3.6, rel=0.01)
    assert filt["filter_area_m2"] in hydraulics.FILTER_SIZES_M2


def test_still_basin_no_network():
    r = hydraulics.compute_hydraulics(
        {**BRIEF, "water": {"features": [{"type": "still_basin"}]}}, BASIN_META)
    assert r["total_flow_lps"] == 0.0
    assert r["manifold"] is None
    assert r["filtration"] is None
    assert r["schedules"]["pump"] is None


def test_splash_zone_grows_with_jet_height():
    r = hydraulics.compute_hydraulics(BRIEF, BASIN_META)
    bubbler = next(f for f in r["features"] if f["type"] == "bubbler_field")
    assert bubbler["splash_radius_m"] > 0.35
