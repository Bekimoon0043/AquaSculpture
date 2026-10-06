import math
from collections import Counter

import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from engineering import geo_calc
from geometry.archetypes.open_ring import generate_open_ring
from main import app

client = TestClient(app)

DIAMETER = 4.0
TUBE_R = 0.15


@pytest.fixture(scope="module")
def ring():
    return generate_open_ring(diameter_m=DIAMETER, tube_radius_m=TUBE_R,
                              opening_deg=60.0, segments=64)


def _edge_counts(faces):
    counts = Counter()
    for a, b, c in faces:
        for e in ((a, b), (b, c), (c, a)):
            counts[tuple(sorted(e))] += 1
    return counts


def test_mesh_is_watertight(ring):
    counts = _edge_counts(ring["faces"])
    assert all(n == 2 for n in counts.values())


def test_bbox_matches_diameter(ring):
    bbox = geo_calc.bounding_box(ring["vertices"])
    assert bbox["size"][0] == pytest.approx(DIAMETER, rel=0.02)
    # With a 60 deg opening at the bottom, height = (R + r) * (1 + cos(opening/2)).
    assert bbox["size"][1] == pytest.approx((DIAMETER / 2.0) * (1 + math.cos(math.radians(30.0))),
                                            rel=0.02)
    assert bbox["size"][2] == pytest.approx(2 * TUBE_R, rel=0.01)


def test_volume_matches_swept_tube(ring):
    radius = DIAMETER / 2.0 - TUBE_R
    sweep = math.radians(300.0)
    # Faceted section: inscribed 12-gon area instead of the smooth circle.
    n = 12
    section_area = 0.5 * n * TUBE_R**2 * math.sin(2 * math.pi / n)
    expected = radius * sweep * section_area
    assert geo_calc.volume(ring["vertices"], ring["faces"]) == pytest.approx(expected, rel=0.01)


def test_center_of_gravity_sane(ring):
    cog = geo_calc.center_of_gravity(ring["vertices"], ring["faces"])
    assert abs(cog[0]) < 0.01 * DIAMETER  # symmetric about the Y axis
    assert abs(cog[2]) < 1e-9
    assert 0.0 < cog[1] < DIAMETER / 2.0  # gap at the bottom shifts mass upward


def test_metadata_mass(ring):
    meta = ring["metadata"]
    assert meta["shell_thickness_m"] > 0
    assert meta["mass_kg"] == pytest.approx(
        meta["surface_area_m2"] * meta["shell_thickness_m"] * 7990, rel=1e-6)


def test_rectangular_section():
    ring = generate_open_ring(diameter_m=3.0, tube_radius_m=None,
                              width_m=0.3, depth_m=0.2, opening_deg=90.0,
                              segments=32, tube_segments=8)
    counts = _edge_counts(ring["faces"])
    assert all(n == 2 for n in counts.values())
    bbox = geo_calc.bounding_box(ring["vertices"])
    assert bbox["size"][0] == pytest.approx(3.0, rel=0.05)
    assert ring["metadata"]["section"] == "rectangular"


def _open_ring_brief():
    brief = {**EXAMPLE_BRIEF,
             "sculpture": {**EXAMPLE_BRIEF["sculpture"],
                           "family": "open_ring",
                           "parameters": {"diameter_m": 2.0, "tube_radius_m": 0.1,
                                          "opening_deg": 90.0, "segments": 32}}}
    return brief


def test_api_generate_roundtrip():
    resp = client.post("/api/geometry/generate", json=_open_ring_brief())
    assert resp.status_code == 200
    body = resp.json()
    mesh = body["mesh"]
    assert len(mesh["vertices"]) > 0
    assert len(mesh["faces"]) > 0
    assert all(n == 2 for n in _edge_counts(mesh["faces"]).values())
    bbox = body["geo"]["bounding_box"]
    assert bbox["size"][0] == pytest.approx(2.0, rel=0.05)
    assert 0.0 < body["geo"]["center_of_gravity_m"][1] < 1.0
    assert body["metadata"]["mass_kg"] > 0


def test_api_rejects_unsupported_family():
    brief = {**EXAMPLE_BRIEF,
             "sculpture": {**EXAMPLE_BRIEF["sculpture"],
                           "family": "nonexistent_widget"}}
    resp = client.post("/api/geometry/generate", json=brief)
    assert resp.status_code == 400
