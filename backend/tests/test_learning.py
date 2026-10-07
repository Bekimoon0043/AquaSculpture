import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from learning import store
from main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_store(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "STORE", tmp_path / "runs.jsonl")
    yield


def _brief():
    return {**EXAMPLE_BRIEF,
            "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                          "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                         "opening_deg": 90, "segments": 12}}}


def test_run_logged_with_run_id():
    resp = client.post("/api/engineering/run", json=_brief())
    assert resp.status_code == 200
    run_id = resp.json()["run_id"]
    rows = store.history()
    assert len(rows) == 1
    assert rows[0]["run_id"] == run_id
    assert rows[0]["predicted"]["total_usd"] > 0
    assert rows[0]["actuals"] is None


def test_record_actuals_computes_deltas():
    resp = client.post("/api/engineering/run", json=_brief())
    run_id = resp.json()["run_id"]
    pred = resp.json()["cost"]["total_usd"]
    resp2 = client.post("/api/learning/actuals",
                        json={"run_id": run_id,
                              "actuals": {"total_usd": pred * 1.1,
                                          "crew_days": 20.0}})
    assert resp2.status_code == 200
    deltas = resp2.json()["delta_analysis"]
    assert deltas["total_usd"]["error_pct"] == pytest.approx(10.0, abs=0.1)
    assert deltas["crew_days"]["predicted"] > 0


def test_similar_projects_filter():
    client.post("/api/engineering/run", json=_brief())
    tall = _brief()
    tall["sculpture"]["height_m"] = 8.0
    tall["sculpture"]["parameters"]["diameter_m"] = 8.0
    client.post("/api/engineering/run", json=tall)

    near = client.get("/api/learning/similar?family=open_ring&height_m=4.0")
    assert len(near.json()["matches"]) == 1
    far = client.get("/api/learning/similar?family=twisted_torus")
    assert len(far.json()["matches"]) == 0


def test_unknown_run_id_404():
    resp = client.post("/api/learning/actuals",
                       json={"run_id": "nope", "actuals": {}})
    assert resp.status_code == 404
