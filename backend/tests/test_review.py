from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from engineering.review import chief_engineer, review_design
from main import app
from pipeline import run_pipeline

client = TestClient(app)


def _brief(**kw):
    b = {**EXAMPLE_BRIEF,
         "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                       "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                      "opening_deg": 90, "segments": 12}}}
    b.update(kw)
    return b


def test_six_reviewers_report():
    out = review_design(_brief(), run_pipeline)
    assert set(out["reviews"]) == {"designer", "structural", "hydraulic",
                                   "lighting", "fabrication", "cost"}
    for findings in out["reviews"].values():
        assert findings
        for f in findings:
            assert f["severity"] in ("info", "warning", "critical")
    assert out["chief_engineer"]["verdict"] in (
        "APPROVED", "APPROVED WITH CONDITIONS",
        "REJECTED — resolve critical findings")


def test_over_budget_triggers_critical_and_rejection():
    b = _brief()
    b["project"] = {**b["project"], "budget_usd": 1000}
    out = review_design(b, run_pipeline)
    assert out["chief_engineer"]["critical_count"] >= 1
    assert "REJECTED" in out["chief_engineer"]["verdict"]
    assert any("optimize" in a for a in out["chief_engineer"]["actions"])


def test_chief_engineer_precedence():
    reviews = {
        "designer": [{"severity": "warning", "message": "frame too visible",
                      "recommendation": "shrink members"}],
        "structural": [{"severity": "critical", "message": "yield SF 1.1",
                        "recommendation": "upsize members"}],
    }
    verdict = chief_engineer(reviews)
    assert "REJECTED" in verdict["verdict"]
    # Safety action must come before the aesthetic one.
    assert verdict["actions"][0] == "upsize members"


def test_review_endpoint():
    resp = client.post("/api/review", json=_brief())
    assert resp.status_code == 200
    assert "chief_engineer" in resp.json()
