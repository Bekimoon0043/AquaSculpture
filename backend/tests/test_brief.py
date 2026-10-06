from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from main import app

client = TestClient(app)


def test_example_brief_endpoint():
    resp = client.get("/api/brief/example")
    assert resp.status_code == 200
    body = resp.json()
    assert body["sculpture"]["family"] == "stacked_c_rings"
    assert body["project"]["budget_usd"] == 250000


def test_validate_valid_brief():
    resp = client.post("/api/brief/validate", json=EXAMPLE_BRIEF)
    assert resp.status_code == 200
    body = resp.json()
    assert body["valid"] is True
    assert body["errors"] == []


def test_validate_invalid_family_enum():
    bad = {**EXAMPLE_BRIEF, "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "dragon"}}
    body = client.post("/api/brief/validate", json=bad).json()
    assert body["valid"] is False
    assert any("family" in e for e in body["errors"])


def test_validate_missing_required_section():
    bad = {k: v for k, v in EXAMPLE_BRIEF.items() if k != "water"}
    body = client.post("/api/brief/validate", json=bad).json()
    assert body["valid"] is False
    assert any("water" in e for e in body["errors"])


def test_validate_rejects_additional_properties():
    bad = {**EXAMPLE_BRIEF, "surprise": 42}
    body = client.post("/api/brief/validate", json=bad).json()
    assert body["valid"] is False


def test_validate_rejects_bad_basin_shape():
    bad = {
        **EXAMPLE_BRIEF,
        "water": {**EXAMPLE_BRIEF["water"],
                  "basin": {**EXAMPLE_BRIEF["water"]["basin"], "shape": "hexagonal"}},
    }
    body = client.post("/api/brief/validate", json=bad).json()
    assert body["valid"] is False
