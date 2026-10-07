import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from engineering.copilot import scale_consequences, scaled_brief
from fabrication import sequencing
from main import app
from pipeline import run_pipeline

client = TestClient(app)


def _brief():
    return {**EXAMPLE_BRIEF,
            "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                          "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                         "opening_deg": 90, "segments": 16}}}


def test_method_statement_order_and_quantities():
    result = run_pipeline(_brief())
    ms = result["method_statement"]
    keys = [s["key"] for s in ms["steps"]]
    assert keys[0] == "foundation"
    assert keys[-1] == "installation"
    assert keys.index("skeleton") < keys.index("panels")
    assert keys.index("panels") < keys.index("welding")
    assert keys.index("welding") < keys.index("finishing")
    for s in ms["steps"]:
        assert s["crew_days"] > 0
        assert s["quantity"]
    assert ms["total_crew_days"] > 5


def test_scaled_brief_scales_size_params():
    b = scaled_brief(_brief(), 1.2)
    assert b["sculpture"]["height_m"] == pytest.approx(4.0 * 1.2)
    assert b["sculpture"]["parameters"]["diameter_m"] == pytest.approx(4.8)
    # Basin (site work) must NOT scale.
    assert b["water"]["basin"] == EXAMPLE_BRIEF["water"]["basin"]


def test_scale_consequences_taller_is_heavier_and_tippier():
    out = scale_consequences(_brief(), 1.2, run_pipeline)
    by_metric = {c["metric"]: c for c in out["consequences"]}
    assert by_metric["shell_mass"]["change_pct"] > 0
    # Moment grows faster than mass: taller lever arm + bigger sail area.
    assert by_metric["overturning_moment"]["change_pct"] \
        > by_metric["shell_mass"]["change_pct"]
    assert by_metric["total_cost_usd"]["change_pct"] > 0
    assert out["scaled_gates_pass"] in (True, False)
    assert out["notes"]


def test_copilot_endpoint():
    resp = client.post("/api/copilot/scale",
                       json={"brief": _brief(), "factor": 1.2})
    assert resp.status_code == 200
    body = resp.json()
    assert body["factor"] == 1.2
    assert len(body["consequences"]) == 5


def test_copilot_rejects_silly_factor():
    resp = client.post("/api/copilot/scale",
                       json={"brief": _brief(), "factor": 20.0})
    assert resp.status_code == 422
