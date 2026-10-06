import json

from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from integration.aquaflow import build_luxexchange
from main import app
from pipeline import run_pipeline

client = TestClient(app)


def _result():
    brief = {**EXAMPLE_BRIEF,
             "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                           "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                          "opening_deg": 90, "segments": 16}}}
    return run_pipeline(brief)


def test_envelope_shape():
    env = build_luxexchange(_result())
    assert env["platform"] == "LuxuryForm"
    assert env["version"] == "1.0"
    assert env["payload_type"] == "scene3d"
    payload = env["payload"]
    assert payload["scene"]["upAxis"] == "Y"
    assert payload["scene"]["unit"] == "meter"
    assert payload["stats"]["fixtureCount"] == len(payload["fixtures"])


def test_fixture_manifest_contents():
    env = build_luxexchange(_result())
    fixtures = env["payload"]["fixtures"]
    kinds = {f["kind"] for f in fixtures}
    assert "nozzle" in kinds
    assert "light" in kinds
    assert "equipment" in kinds

    nozzle = next(f for f in fixtures if f["kind"] == "nozzle")
    assert nozzle["engineering"]["flow_lps"] > 0
    assert nozzle["position"]["x"] is not None

    light = next(f for f in fixtures if f["kind"] == "light")
    assert light["engineering"]["dmx_address"] >= 1
    assert light["engineering"]["dmx_channels"] > 0

    pump = next(f for f in fixtures if f["type"] == "pump")
    assert pump["engineering"]["motor_kw"] > 0


def test_embedded_gltf_valid():
    env = build_luxexchange(_result())
    gltf = env["payload"]["gltf"]
    assert gltf["asset"]["version"] == "2.0"
    uri = gltf["buffers"][0]["uri"]
    assert uri.startswith("data:application/octet-stream;base64,")
    assert gltf["accessors"][0]["count"] > 0


def test_api_endpoint_downloads_envelope():
    brief = {**EXAMPLE_BRIEF,
             "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                           "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                          "opening_deg": 90, "segments": 16}}}
    resp = client.post("/api/integration/aquaflow", json=brief)
    assert resp.status_code == 200
    assert "luxexchange" in resp.headers["content-disposition"]
    env = resp.json()
    assert env["platform"] == "LuxuryForm"
    assert env["payload"]["stats"]["fixtureCount"] > 0
