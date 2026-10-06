import pytest

from engineering import hydraulics


def _brief(features, height_m=4.0):
    return {
        "sculpture": {"family": "open_ring", "height_m": height_m,
                      "material": "stainless_316l", "finish": "mirror_polish_8"},
        "water": {"features": features},
    }


def test_weir_flow_analytic():
    assert hydraulics.weir_flow_m3s(2.0, 0.02) == pytest.approx(1.84 * 2.0 * 0.02**1.5)


def test_jet_flow_k_sqrt_p():
    assert hydraulics.jet_flow_lps("bubbler_dn25", 1.0) == pytest.approx(1.2)
    assert hydraulics.jet_flow_lps("foam_jet_dn40", 4.0) == pytest.approx(2.5 * 2.0)


def test_pipe_selection_known_flow():
    # 10 L/s: DN65 -> 3.01 m/s (too fast), DN80 -> 1.99 m/s.
    assert hydraulics.select_pipe_dn(0.010)["dn"] == 80
    # 0.5 L/s fits DN25 at ~1.0 m/s.
    assert hydraulics.select_pipe_dn(0.0005)["dn"] == 25


def test_tdh_monotonic_in_flow():
    # Hazen-Williams friction is strictly increasing in flow for a fixed pipe.
    d = 0.08
    assert (hydraulics.hazen_williams_headloss_m(0.012, 20.0, d)
            > hydraulics.hazen_williams_headloss_m(0.007, 20.0, d))
    # System TDH rises with flow while both stay in the same DN band (DN65).
    small = hydraulics.compute_hydraulics(
        _brief([{"type": "bubbler_field", "count": 5}]))
    large = hydraulics.compute_hydraulics(
        _brief([{"type": "bubbler_field", "count": 6}]))
    assert large["main_pipe"]["dn"] == small["main_pipe"]["dn"] == 65
    assert large["total_flow_lps"] > small["total_flow_lps"]
    assert large["tdh_m"] > small["tdh_m"]
    assert large["motor_kw"] > small["motor_kw"]


def test_turnover_calc():
    basin_meta = {"water_volume_m3": 12.0}
    result = hydraulics.compute_hydraulics(
        _brief([{"type": "bubbler_field", "count": 10}]), basin_meta)
    expected_min = 12.0 / (result["total_flow_lps"] / 1000.0) / 60.0
    assert result["turnover_min"] == pytest.approx(expected_min)


def test_curtain_feature_uses_sculpture_height_and_weir():
    result = hydraulics.compute_hydraulics(
        _brief([{"type": "curtain_between_elements", "spill_edge_length_m": 4.0,
                 "head_m": 0.02}]))
    feat = result["features"][0]
    assert feat["flow_lps"] == pytest.approx(1.84 * 4.0 * 0.02**1.5 * 1000.0)
    assert result["static_lift_m"] == 4.0


def test_no_water_features():
    result = hydraulics.compute_hydraulics(_brief([]))
    assert result["total_flow_lps"] == 0.0
    assert result["motor_kw"] == 0.0
    assert result["main_pipe"] is None
