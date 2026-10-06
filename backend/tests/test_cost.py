import pytest

from cost import estimator

BRIEF = {
    "project": {"name": "t", "budget_usd": 50000},
    "sculpture": {"family": "open_ring", "height_m": 4.0,
                  "material": "stainless_316l", "finish": "mirror_polish_8"},
    "water": {"features": [], "basin": {"shape": "circular", "diameter_m": 6.0,
                                        "depth_m": 0.45, "material": "black_granite"}},
    "lighting": {"sculpture_uplights": 4, "submersible_rgb": 12},
}

SCULPTURE_META = {"mass_kg": 100.0, "surface_area_m2": 10.0}

HYD = {"motor_kw": 2.0, "features": []}


def test_rollup_math_deterministic():
    cost = estimator.estimate(BRIEF, SCULPTURE_META, None, HYD)
    by_key = {s["key"]: s for s in cost["sections"]}

    # Shell: 100 kg * 9 + panelization 10*4 h * 65 + polish 10*6 h * 65.
    assert by_key["shell"]["amount"] == pytest.approx(900.0 + 2600.0 + 3900.0)
    # Armature: 25 kg * 3.5.
    assert by_key["armature"]["amount"] == pytest.approx(87.5)
    # Foundation: side = max(1.5, 4*0.4) = 1.6; concrete 1.6^2*0.6 = 1.536 m3.
    concrete = 1.536 * 180.0
    rebar = 1.536 * 110.0 * 1.8
    assert by_key["foundation"]["amount"] == pytest.approx(concrete + rebar, rel=1e-4)
    # Electrical: 4*120 + 12*95 = 1620, +15% balance = 1863.
    assert by_key["electrical"]["amount"] == pytest.approx(1863.0)
    # Install: ceil(4/3) = 2 days * 1200.
    assert by_key["install"]["amount"] == pytest.approx(2400.0)

    subtotal = sum(s["amount"] for s in cost["sections"])
    assert cost["subtotal_usd"] == pytest.approx(subtotal)
    assert cost["contingency_usd"] == pytest.approx(subtotal * 0.10, abs=0.01)
    assert cost["margin_usd"] == pytest.approx(
        (subtotal + cost["contingency_usd"]) * 0.15, abs=0.01)
    assert cost["total_usd"] == pytest.approx(
        subtotal + cost["contingency_usd"] + cost["margin_usd"], abs=0.01)


def test_budget_flag_over_and_under():
    cost = estimator.estimate(BRIEF, SCULPTURE_META, None, HYD)
    assert cost["total_usd"] > 0

    under = estimator.estimate({**BRIEF, "project": {"budget_usd": 1e9}},
                               SCULPTURE_META, None, HYD)
    assert under["over_budget"] is False
    over = estimator.estimate({**BRIEF, "project": {"budget_usd": 1.0}},
                              SCULPTURE_META, None, HYD)
    assert over["over_budget"] is True
    assert over["budget_delta_usd"] == pytest.approx(over["total_usd"] - 1.0)


def test_opex_calc():
    cost = estimator.estimate(BRIEF, SCULPTURE_META, None, HYD)
    assert cost["opex_annual_usd"] == pytest.approx(2.0 * 10 * 365 * 0.15)


def test_basin_cladding_uses_basin_material():
    basin_meta = {"inner": {"radius_m": 3.0}, "wall_thickness_m": 0.15,
                  "wetted_area_m2": 40.0}
    cost = estimator.estimate(BRIEF, SCULPTURE_META, basin_meta, HYD)
    basin = next(s for s in cost["sections"] if s["key"] == "basin")
    cladding = basin["items"][0]
    assert cladding["unit_price"] == 180.0  # black_granite rate
