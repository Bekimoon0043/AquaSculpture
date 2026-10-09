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


# ── Human gates G1/G10 via recorded approvals (scope §28, Onshape lesson) ──

def _approval(by="Burook", note=""):
    return {"by": by, "at": "2026-10-09T10:00:00Z", "note": note}


def test_g1_passes_once_concept_is_approved():
    b = _brief(approvals={"G1": _approval()})
    resp = client.post("/api/engineering/run", json=b)
    assert resp.status_code == 200
    gates = {g["id"]: g for g in resp.json()["gates"]["gates"]}
    assert gates["G1"]["status"] == "pass"
    assert "Burook" in gates["G1"]["note"]
    assert gates["G10"]["status"] == "not_evaluated"
    assert resp.json()["gates"]["production_ready"] is False  # G10 still open


def test_g10_approval_makes_design_production_ready_when_gates_pass():
    b = _brief(approvals={"G1": _approval(), "G10": _approval(note="client signed")})
    body = client.post("/api/engineering/run", json=b).json()
    gates = {g["id"]: g for g in body["gates"]["gates"]}
    if body["gates"]["hard_fail"]:
        assert gates["G10"]["status"] == "fail"          # approval void
        assert body["gates"]["production_ready"] is False
    else:
        assert gates["G10"]["status"] == "pass"
        assert body["gates"]["production_ready"] is True


def test_g10_approval_is_void_when_an_engineering_gate_fails():
    b = _brief(approvals={"G10": _approval()})
    b["project"] = {**b["project"], "budget_usd": 1000}   # forces G9 fail
    body = client.post("/api/engineering/run", json=b).json()
    gates = {g["id"]: g for g in body["gates"]["gates"]}
    assert gates["G9"]["status"] == "fail"
    assert gates["G10"]["status"] == "fail"
    assert "void" in gates["G10"]["note"]
    assert body["gates"]["production_ready"] is False


def test_approvals_validate_against_schema_and_are_stripped_from_variants():
    from engineering.copilot import scaled_brief
    b = _brief(approvals={"G1": _approval()})
    assert client.post("/api/brief/validate", json=b).json()["valid"] is True
    assert "approvals" not in scaled_brief(b, 1.2)
    concepts = client.post("/api/concepts", json={"brief": b, "count": 1}).json()["concepts"]
    assert "approvals" not in concepts[0]["brief"]
    h = concepts[0]["headline"]
    for key in ("mass_kg", "steel_kg", "total_usd", "base_moment_knm",
                "deflection_mm", "pump_kw", "panels", "weld_m", "gates"):
        assert key in h, key
    assert h["gates"]["G1"] == "not_evaluated"
