import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from engineering import geo_calc, kinetics
from geometry.archetypes import generate
from main import app

client = TestClient(app)


def _ring():
    mesh = generate("open_ring", {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                  "opening_deg": 60, "segments": 24},
                    "stainless_316l", 4.0)
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    return mesh, geo


def test_inertia_matches_hoop_approximation():
    # Thin ring rotating about its central Y axis: I ~ M*R^2 (order).
    mesh, _ = _ring()
    mass = mesh["metadata"]["mass_kg"]
    I = kinetics.mesh_inertia_about_axis(mesh["vertices"], mesh["faces"],
                                         mass, "y")
    r_approx = 2.0
    assert 0.3 * mass * r_approx**2 < I < 1.3 * mass * r_approx**2


def test_rotation_drive_train():
    mesh, geo = _ring()
    brief = {"kinetics": {"motion": "rotation", "axis": "y", "rpm": 3.0,
                          "ramp_time_s": 5.0}}
    mass = mesh["metadata"]["mass_kg"] + 200.0
    k = kinetics.design_kinetics(brief, geo, mesh["vertices"], mesh["faces"],
                                 mass)
    assert k["inertia_kg_m2"] > 0
    assert k["peak_torque_nm"] > 0
    assert k["motor_kw"] >= 0.25
    assert k["gearbox_ratio"] > 1
    assert k["shaft_diameter_mm"] >= 20
    assert k["bearing_l10_hours"] > 0
    assert k["motion_envelope"]["radius_m"] > 1.0


def test_oscillation_motion():
    mesh, geo = _ring()
    brief = {"kinetics": {"motion": "oscillation", "amplitude_deg": 20,
                          "rpm": 2.0}}
    k = kinetics.design_kinetics(brief, geo, mesh["vertices"], mesh["faces"],
                                 500.0)
    assert "oscillation" in k["motion"]
    assert k["peak_torque_nm"] > 0


def test_pipeline_with_kinetics():
    brief = {**EXAMPLE_BRIEF,
             "kinetics": {"motion": "rotation", "rpm": 2.0},
             "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                           "parameters": {"diameter_m": 4.0,
                                          "tube_radius_m": 0.15,
                                          "opening_deg": 90, "segments": 12}}}
    resp = client.post("/api/engineering/run", json=brief)
    assert resp.status_code == 200
    body = resp.json()
    assert body["kinetics"]["motor_kw"] > 0
    labels = [i["label"] for s in body["cost"]["sections"] for i in s["items"]]
    assert any("Motor" in l for l in labels)
    assert any("Gearbox" in l for l in labels)


def test_brief_with_kinetics_validates():
    resp = client.post("/api/brief/validate", json={
        **EXAMPLE_BRIEF,
        "kinetics": {"motion": "rotation", "axis": "y", "rpm": 2.0}})
    assert resp.json()["valid"] is True
