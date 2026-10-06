from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from main import app

client = TestClient(app)


def _brief(family="open_ring", **over):
    b = {**EXAMPLE_BRIEF,
         "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": family,
                       "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                      "opening_deg": 90, "segments": 24}
                       if family == "open_ring" else {}}}
    for k, v in over.items():
        b[k] = v
    return b


def test_gates_present_in_engineering_run():
    resp = client.post("/api/engineering/run", json=_brief())
    assert resp.status_code == 200
    body = resp.json()
    assert "gates" in body and "integrity" in body
    gates = {g["id"]: g for g in body["gates"]["gates"]}
    assert len(gates) == 11                      # G0..G10
    assert gates["G0"]["status"] == "pass"
    assert gates["G2"]["status"] in ("pass", "warning")
    assert gates["G4"]["status"] in ("pass", "fail")
    assert gates["G6"]["status"] in ("pass", "warning", "fail")  # lighting live
    assert gates["G8"]["status"] in ("pass", "warning", "fail")  # maintainability live
    assert gates["G1"]["status"] == "not_evaluated"
    assert gates["G10"]["status"] == "not_evaluated"
    assert isinstance(body["gates"]["production_ready"], bool)


def test_gate_g9_fails_over_budget():
    b = _brief()
    b["project"] = {**b["project"], "budget_usd": 1000}  # absurdly low
    resp = client.post("/api/engineering/run", json=b)
    gates = {g["id"]: g for g in resp.json()["gates"]["gates"]}
    assert gates["G9"]["status"] == "fail"
    assert resp.json()["gates"]["hard_fail"] is True
    assert resp.json()["gates"]["production_ready"] is False


def test_water_viz_payload():
    resp = client.post("/api/engineering/run", json=_brief())
    viz = resp.json()["water_viz"]
    assert viz is not None
    assert viz["water_level_m"] > 0
    assert len(viz["jets"]) == 12
    for jet in viz["jets"]:
        assert jet["exit_velocity_ms"] > 0
        assert jet["jet_height_m"] > 0
    assert len(viz["curtains"]) >= 1
    assert viz["curtains"][0]["top_y"] > viz["curtains"][0]["bottom_y"]
