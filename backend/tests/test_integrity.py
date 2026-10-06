import pytest

from engineering import integrity
from geometry.archetypes import generate


def _mesh(family, params, material="stainless_316l", height=4.0):
    return generate(family, params, material, height)


def test_open_ring_passes_integrity():
    mesh = _mesh("open_ring", {"diameter_m": 4.0, "tube_radius_m": 0.15,
                               "opening_deg": 90, "segments": 24})
    r = integrity.validate_mesh(mesh["vertices"], mesh["faces"])
    assert r["passed"] is True
    assert r["watertight"] is True
    assert r["open_edges"] == 0
    assert r["non_manifold_edges"] == 0
    assert r["degenerate_faces"] == 0
    assert r["components"] == 1
    assert r["errors"] == []


def test_broken_mesh_fails_integrity():
    mesh = _mesh("open_ring", {"diameter_m": 4.0, "tube_radius_m": 0.15,
                               "opening_deg": 90, "segments": 16})
    faces = mesh["faces"][:-10]  # chop faces -> holes
    r = integrity.validate_mesh(mesh["vertices"], faces)
    assert r["passed"] is False
    assert r["open_edges"] > 0
    assert any("open edges" in e for e in r["errors"])


def test_multi_body_sculpture_warns_not_fails():
    mesh = _mesh("stacked_rings", {}, "stainless_316l", 4.0)
    r = integrity.validate_mesh(mesh["vertices"], mesh["faces"])
    assert r["passed"] is True            # warnings don't fail the gate
    assert r["components"] > 1
    assert any("disconnected bodies" in w for w in r["warnings"])


def test_all_archetypes_pass_integrity():
    from geometry.archetypes import GENERATORS
    for family in GENERATORS:
        mesh = _mesh(family, {}, "stainless_316l", 3.0)
        r = integrity.validate_mesh(mesh["vertices"], mesh["faces"])
        assert r["passed"] is True, f"{family}: {r['errors']}"
