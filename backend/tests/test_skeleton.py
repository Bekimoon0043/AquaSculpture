import pytest

from cost import estimator
from engineering import geo_calc, structural
from fabrication import skeleton
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
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    struct = structural.compute_structural(BRIEF, geo, mesh["metadata"])
    return mesh, geo, struct


def test_skeleton_has_spine_ribs_and_base_frame():
    mesh, geo, struct = _ring(4.0)
    skel = skeleton.generate_skeleton(BRIEF, geo, struct,
                                      shell_vertices=mesh["vertices"])
    kinds = {m["kind"] for m in skel["members"]}
    assert "spine" in kinds
    assert "rib" in kinds
    assert "base_frame" in kinds
    assert skel["member_count"] > 5
    assert skel["total_steel_kg"] > 0
    assert len(skel["mesh"]["vertices"]) > 0


def test_members_stay_inside_bbox():
    mesh, geo, struct = _ring(4.0)
    skel = skeleton.generate_skeleton(BRIEF, geo, struct,
                                      shell_vertices=mesh["vertices"])
    (x0, y0, z0), (x1, y1, z1) = geo["bounding_box"]["min"], geo["bounding_box"]["max"]
    for m in skel["members"]:
        for p in (m["from"], m["to"]):
            assert x0 - 0.01 <= p[0] <= x1 + 0.01
            assert y0 - 0.01 <= p[1] <= y1 + 0.01
            assert z0 - 0.01 <= p[2] <= z1 + 0.01


def test_higher_moment_selects_larger_section():
    mesh, geo, struct = _ring(4.0)
    calm = skeleton.generate_skeleton(BRIEF, geo, struct)
    big_moment = {**struct, "total_base_moment_knm": 500.0}
    storm = skeleton.generate_skeleton(BRIEF, geo, big_moment)
    assert storm["section_z_cm3"] >= calm["section_z_cm3"]
    assert storm["section_z_cm3"] >= storm["required_z_cm3"]


def test_shs_properties_math():
    props = skeleton.shs_properties(100, 5)
    # Area: 100^2 - 90^2 mm2 = 1900 mm2 -> 7.85e3 * 1.9e-3 = 14.9 kg/m
    assert props["kg_per_m"] == pytest.approx(14.9, rel=0.05)
    assert props["z_m3"] > 0


def test_cost_uses_skeleton_weight():
    mesh, geo, struct = _ring(4.0)
    skel = skeleton.generate_skeleton(BRIEF, geo, struct)
    hyd = {"motor_kw": 0.0, "features": []}
    cost = estimator.estimate(BRIEF, mesh["metadata"], None, hyd,
                              structural=struct, skeleton=skel)
    by_key = {sec["key"]: sec for sec in cost["sections"]}
    assert by_key["armature"]["items"][0]["qty"] == pytest.approx(
        skel["total_steel_kg"], rel=1e-3)
