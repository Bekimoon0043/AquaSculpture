import pytest

from engineering import geo_calc, hydraulics, lighting, maintainability
from fabrication import routing, skeleton
from engineering import structural
from geometry.archetypes import generate

BRIEF = {
    "project": {"name": "s", "budget_usd": 100000},
    "sculpture": {"family": "open_ring", "height_m": 4.0,
                  "material": "stainless_316l", "finish": "mirror_polish_8"},
    "water": {"features": [
        {"type": "bubbler_field", "count": 12},
        {"type": "curtain_from_sculpture", "spill_edge_length_m": 5.0,
         "head_m": 0.02},
    ]},
    "lighting": {"sculpture_uplights": 4},
    "constraints": {"wind_zone": "moderate", "indoor": False},
}
BASIN_META = {"water_volume_m3": 6.0, "depth_m": 0.45,
              "floor_thickness_m": 0.15, "inner": {"radius_m": 3.0}}


def _setup():
    mesh = generate("open_ring", {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                  "opening_deg": 60, "segments": 16},
                    "stainless_316l", 4.0)
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    hyd = hydraulics.compute_hydraulics(BRIEF, BASIN_META)
    struct = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    skel = skeleton.generate_skeleton(BRIEF, geo, struct)
    light = lighting.design_lighting(BRIEF, geo, mesh["vertices"], mesh["faces"],
                                     BASIN_META)
    return mesh, geo, hyd, struct, skel, light


def test_routing_water_and_electrical_separated():
    _, geo, hyd, _, skel, light = _setup()
    r = routing.design_routing(BRIEF, geo, hyd, skel, light)
    water = [x for x in r["routes"] if x["service"] == "water"]
    elec = [x for x in r["routes"] if x["service"] in ("power", "data_dmx")]
    assert len(water) == 1           # one sculpture-borne feature -> one riser
    assert len(elec) == 2            # power + DMX
    assert water[0]["bend_radius_ok"] is True
    # Water offset +x, electrical -x: separation enforced by construction.
    assert water[0]["path"][0][0] > elec[0]["path"][0][0]
    assert r["passed"] is True


def test_penetrations_and_drainage():
    _, geo, hyd, _, skel, light = _setup()
    r = routing.design_routing(BRIEF, geo, hyd, skel, light)
    kinds = {p["kind"] for p in r["penetrations"]}
    assert kinds == {"water_supply", "power", "data_dmx"}
    assert r["drain_points"] >= 1
    assert r["inspection_hatches"] >= 1   # 4 m tall sculpture


def test_maintainability_pass_on_good_design():
    _, geo, hyd, _, skel, light = _setup()
    route = routing.design_routing(BRIEF, geo, hyd, skel, light)
    m = maintainability.analyze_maintainability(BRIEF, BASIN_META, hyd, light,
                                                route)
    assert m["passed"] is True
    assert m["flags"] == []
    items = {c["item"] for c in m["checks"]}
    assert {"pump_access", "nozzle_access", "lighting_access", "drain_points",
            "internal_access"} <= items


def test_maintainability_flags_deep_basin():
    _, geo, hyd, _, skel, light = _setup()
    route = routing.design_routing(BRIEF, geo, hyd, skel, light)
    deep = {**BASIN_META, "depth_m": 1.5}
    m = maintainability.analyze_maintainability(BRIEF, deep, hyd, light, route)
    assert m["passed"] is False
    assert any("nozzle_access" in f for f in m["flags"])
