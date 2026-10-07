import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from engineering.optimize import optimize
from main import app
from pipeline import run_pipeline

client = TestClient(app)


def _brief():
    return {**EXAMPLE_BRIEF,
            "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                          "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                         "opening_deg": 90, "segments": 12}}}


def test_optimize_cost_ranks_gate_passing_only():
    out = optimize(_brief(), "cost", run_pipeline)
    assert out["evaluated"] > 5
    assert out["best"] is not None
    for c in out["candidates"]:
        if c is out["best"]:
            continue
    # Best must pass gates and stay in budget.
    assert out["best"]["gates_pass"] is True
    assert out["best"]["over_budget"] is False
    # Best beats (or matches) the unmodified design.
    assert out["best"]["value"] <= out["base"]["value"]
    assert out["improvement_pct"] >= 0


def test_optimize_weight_goal():
    out = optimize(_brief(), "weight", run_pipeline)
    assert out["best"]["mass_kg"] <= out["base"]["mass_kg"]


def test_optimize_bad_goal_422():
    resp = client.post("/api/optimize",
                       json={"brief": _brief(), "goal": "prettiness"})
    assert resp.status_code == 422


def test_optimize_endpoint():
    resp = client.post("/api/optimize",
                       json={"brief": _brief(), "goal": "pump_power"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["goal"] == "pump_power"
    assert body["best"]["gates_pass"] is True


def test_pareto_front():
    from engineering.optimize import optimize as opt
    out = opt(_brief(), "pareto", run_pipeline)
    assert out["front"]
    # Non-dominated: sorted by cost, weight must strictly decrease... no —
    # along the front, cheaper means heavier or equal is impossible; weight
    # must strictly decrease as cost increases.
    for a, b in zip(out["front"], out["front"][1:]):
        assert b["weight"] < a["weight"]
