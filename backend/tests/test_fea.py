import pytest

from engineering import fea
from fabrication.skeleton import shs_properties


def test_cantilever_matches_theory():
    # Single vertical SHS 100x5, 4 m tall, 1 kN lateral tip load.
    # Exact Euler-Bernoulli: delta = P L^3 / (3 E I)
    props = shs_properties(100, 5)
    L, P, E = 4.0, 1000.0, 200e9
    expected_mm = P * L**3 / (3 * E * props["i_m4"]) * 1000.0
    out = fea.solve_frame(
        [{"from": [0, 0, 0], "to": [0, L, 0], "length_m": L}],
        (100, 5), lateral_load_n=P, dead_load_n=0.0, load_height_m=L)
    assert out["max_displacement_mm"] == pytest.approx(expected_mm, rel=0.02)


def test_two_segment_beam_still_exact():
    props = shs_properties(100, 5)
    L, P, E = 4.0, 1000.0, 200e9
    expected_mm = P * L**3 / (3 * E * props["i_m4"]) * 1000.0
    out = fea.solve_frame(
        [{"from": [0, 0, 0], "to": [0, 2, 0], "length_m": 2},
         {"from": [0, 2, 0], "to": [0, 4, 0], "length_m": 2}],
        (100, 5), lateral_load_n=P, dead_load_n=0.0, load_height_m=L)
    assert out["max_displacement_mm"] == pytest.approx(expected_mm, rel=0.02)


def test_stress_under_axial_dead_load():
    # 1 m column, 190 kN dead load on top nodes: stress ~= P/A = 100 MPa.
    props = shs_properties(100, 5)
    out = fea.solve_frame(
        [{"from": [0, 0, 0], "to": [0, 1, 0], "length_m": 1}],
        (100, 5), lateral_load_n=0.0, dead_load_n=190000.0, load_height_m=1.0)
    assert out["max_stress_mpa"] == pytest.approx(100.0, rel=0.05)


def test_empty_frame_rejected():
    with pytest.raises(ValueError):
        fea.solve_frame([], (100, 5), 0.0, 0.0, 1.0)


def test_pipeline_includes_fea():
    from fastapi.testclient import TestClient
    from api.routes.brief import EXAMPLE_BRIEF
    from main import app
    brief = {**EXAMPLE_BRIEF,
             "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                           "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                          "opening_deg": 90, "segments": 12}}}
    resp = TestClient(app).post("/api/engineering/run", json=brief)
    assert resp.status_code == 200
    fea_block = resp.json()["structural"]["fea"]
    assert "error" not in fea_block
    assert fea_block["max_displacement_mm"] > 0
    assert fea_block["max_stress_mpa"] > 0


def test_axial_bar_matches_theory():
    # Vertical bar, axial dead load: delta = P L / (E A)
    props = shs_properties(100, 5)
    L, P, E = 2.0, 50000.0, 200e9
    expected_mm = P * L / (E * props["area_m2"]) * 1000.0
    out = fea.solve_frame(
        [{"from": [0, 0, 0], "to": [0, L, 0], "length_m": L}],
        (100, 5), lateral_load_n=0.0, dead_load_n=P, load_height_m=L)
    assert out["max_displacement_mm"] == pytest.approx(expected_mm, rel=0.02)


def test_mesh_convergence():
    # 1-element vs 4-element cantilever: same answer within 3%.
    props = shs_properties(100, 5)
    L, P = 4.0, 1000.0
    one = fea.solve_frame([{"from": [0, 0, 0], "to": [0, L, 0], "length_m": L}],
                          (100, 5), P, 0.0, L)
    four = fea.solve_frame(
        [{"from": [0, i, 0], "to": [0, i + 1, 0], "length_m": 1}
         for i in range(4)],
        (100, 5), P, 0.0, L)
    assert four["max_displacement_mm"] == pytest.approx(
        one["max_displacement_mm"], rel=0.03)


def test_per_element_results_and_displacements_are_exposed():
    L = 3.0
    out = fea.solve_frame(
        [{"from": [0, 0, 0], "to": [0, L, 0], "length_m": L}],
        (100, 5), lateral_load_n=1000.0, dead_load_n=0.0, load_height_m=L)
    assert len(out["member_results"]) == out["elements"]
    assert len(out["node_displacements"]) == out["nodes"]
    worst = max(m["stress_mpa"] for m in out["member_results"])
    assert worst == out["max_stress_mpa"]
    m = out["member_results"][0]
    assert m["nodes"] == [0, 1] and m["from"] == [0, 0, 0] and m["to"] == [0, L, 0]
    assert m["utilization"] == round(m["stress_mpa"] * 1.5 / 250.0, 3)
    tip = max(out["node_displacements"], key=lambda d: d["pos"][1])
    assert abs(tip["d_mm"][0]) > 0            # lateral load -> x displacement
    assert tip["d_mm"][0] <= out["max_displacement_mm"] + 1e-6
