import io
import json
import zipfile

import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from main import app

client = TestClient(app)


def _open_ring_brief():
    return {
        **EXAMPLE_BRIEF,
        "sculpture": {**EXAMPLE_BRIEF["sculpture"],
                      "family": "open_ring",
                      "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                     "opening_deg": 90.0, "segments": 24}},
    }


def test_engineering_run_happy_path():
    resp = client.post("/api/engineering/run", json=_open_ring_brief())
    assert resp.status_code == 200
    body = resp.json()
    for key in ("sculpture", "basin", "geo_quantities", "hydraulics", "cost"):
        assert key in body, key
    assert body["sculpture"]["metadata"]["mass_kg"] > 0
    assert body["hydraulics"]["total_flow_lps"] > 0
    assert body["hydraulics"]["motor_kw"] > 0
    assert body["hydraulics"]["turnover_min"] > 0
    assert body["cost"]["total_usd"] > 0
    assert body["cost"]["over_budget"] in (True, False)
    assert len(body["basin"]["metadata"]["nozzle_positions"]) == 12


def test_engineering_run_unsupported_family():
    brief = {**EXAMPLE_BRIEF,
             "sculpture": {**EXAMPLE_BRIEF["sculpture"],
                           "family": "nonexistent_widget"}}
    resp = client.post("/api/engineering/run", json=brief)
    assert resp.status_code == 400


def test_package_endpoint_returns_zip():
    resp = client.post("/api/deliverables/package", json=_open_ring_brief())
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert "attachment" in resp.headers["content-disposition"]
    assert resp.content[:2] == b"PK"
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    assert "manifest.json" in zf.namelist()
    manifest = json.loads(zf.read("manifest.json"))
    assert len(manifest) == 5
