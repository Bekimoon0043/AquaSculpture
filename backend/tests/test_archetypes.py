import math
from collections import Counter

import pytest

from engineering import geo_calc
from geometry.archetypes import GENERATORS, generate


def _edge_counts(faces):
    counts = Counter()
    for a, b, c in faces:
        for e in ((a, b), (b, c), (c, a)):
            counts[tuple(sorted(e))] += 1
    return counts


def _assert_common(mesh, watertight=True):
    assert mesh["metadata"]["mass_kg"] > 0
    assert mesh["metadata"]["surface_area_m2"] > 0
    if watertight:
        counts = _edge_counts(mesh["faces"])
        assert all(n == 2 for n in counts.values())
    # Signed volume positive => outward winding.
    assert geo_calc.volume(mesh["vertices"], mesh["faces"]) > 0


def test_twisted_torus():
    mesh = generate("twisted_torus", {"major_radius_m": 1.0, "section_width_m": 0.4,
                                      "section_depth_m": 0.25, "twist_count": 2,
                                      "morph": 0.3, "segments": 48},
                    "grc", 0.0)
    _assert_common(mesh)
    bbox = geo_calc.bounding_box(mesh["vertices"])
    max_ext = math.hypot(0.2, 0.125)
    assert 2.0 < bbox["size"][0] <= 2.0 * (1.0 + max_ext) + 1e-6
    assert bbox["size"][1] == pytest.approx(bbox["size"][0], rel=0.05)
    cog = geo_calc.center_of_gravity(mesh["vertices"], mesh["faces"])
    assert abs(cog[0]) < 0.05 and abs(cog[2]) < 0.05
    pappus = 2 * math.pi * 1.0 * mesh["metadata"]["section_area_m2"]
    assert geo_calc.volume(mesh["vertices"], mesh["faces"]) == pytest.approx(
        pappus, rel=0.15)


@pytest.mark.parametrize("preset", ["figure_eight", "flame", "wave"])
def test_ribbon_knot_presets(preset):
    mesh = generate("ribbon_knot", {"height_m": 4.0, "width_m": 0.6,
                                    "thickness_m": 0.08, "preset": preset,
                                    "taper": 0.3, "twist_deg": 180,
                                    "segments": 48}, "bronze", 4.0)
    _assert_common(mesh)
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert 3.0 < bbox["size"][1] <= 4.5
    cog = geo_calc.center_of_gravity(mesh["vertices"], mesh["faces"])
    assert 0.0 < cog[1] < 4.0
    assert mesh["metadata"]["arc_length_m"] > 4.0


def test_organic_flame():
    mesh = generate("organic_flame", {"height_m": 3.5, "base_radius_m": 0.8,
                                      "lobe_count": 4, "segments": 24,
                                      "radial_segments": 16}, "bronze", 3.5)
    _assert_common(mesh)
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert bbox["size"][1] == pytest.approx(3.5, abs=1e-6)
    assert bbox["min"][1] == pytest.approx(0.0, abs=1e-6)
    spills = mesh["metadata"]["spill_edges_m"]
    assert len(spills) == 2 and all(s > 0 for s in spills)


def test_stacked_rings():
    mesh = generate("stacked_rings", {}, "stainless_316l", 0.0)
    _assert_common(mesh)
    meta = mesh["metadata"]
    assert meta["element_count"] == 5
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert bbox["size"][1] == pytest.approx(meta["total_height_m"], abs=1e-6)
    assert bbox["size"][0] == pytest.approx(3.2, rel=0.05)  # largest ring


def test_crescent_inner():
    mesh = generate("crescent_inner", {"diameter_m": 2.0, "tube_radius_m": 0.1,
                                       "opening_deg": 90.0, "segments": 32},
                    "stainless_316l", 2.0)
    _assert_common(mesh)
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert bbox["size"][0] == pytest.approx(2.0, rel=0.05)
    assert mesh["metadata"]["inner_size_m"] == pytest.approx(2.0 - 0.4 - 0.3)


def test_arc_fin_array():
    mesh = generate("arc_fin_array", {"fin_count": 6, "height_m": 2.0,
                                      "arc_radius_m": 3.0,
                                      "layout_diameter_m": 2.0},
                    "stainless_304", 0.0)
    _assert_common(mesh)
    meta = mesh["metadata"]
    assert meta["fin_count"] == 6
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert 1.8 < bbox["size"][1] < 2.3  # fin tips at height_m
    # Fins reach beyond the layout radius as they bow outward.
    assert bbox["size"][0] > 2.0
    assert meta["led_channel_grooves"] == 6


def test_relief_panel():
    mesh = generate("relief_panel", {"thickness_m": 0.1}, "stainless_304", 0.0)
    _assert_common(mesh)
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert bbox["size"][2] == pytest.approx(0.1, abs=1e-9)
    assert bbox["min"][1] == pytest.approx(0.0, abs=1e-9)
    perf = mesh["metadata"]["perforation"]
    assert perf["estimated_dot_count"] > 0
    assert mesh["metadata"]["panel_area_m2"] > 0


def test_registry_covers_all_eight_families():
    expected = {"open_ring", "twisted_torus", "ribbon_knot", "organic_flame",
                "stacked_rings", "crescent_inner", "arc_fin_array", "relief_panel"}
    assert expected <= set(GENERATORS)


def test_registry_unknown_family_raises():
    with pytest.raises(KeyError):
        generate("dragon", {}, "bronze", 1.0)


def test_registry_param_filtering_ignores_unknown_keys():
    mesh = generate("open_ring", {"diameter_m": 2.0, "tube_radius_m": 0.1,
                                  "opening_deg": 60, "segments": 16,
                                  "bogus_param": 999}, "stainless_316l", 2.0)
    _assert_common(mesh)


def test_buddha_seated():
    from engineering import geo_calc
    mesh = generate("buddha_seated", {"height_m": 2.0}, "bronze", 2.0)
    meta = mesh["metadata"]
    assert meta["family"] == "buddha_seated"
    assert meta["mass_kg"] > 0
    assert meta["surface_area_m2"] > 1.0
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert bbox["size"][1] == pytest.approx(2.0, rel=0.05)
    # Seated figure: width/depth should be a sane fraction of height
    assert 0.3 < bbox["size"][0] / bbox["size"][1] < 0.75


def test_standing_figure_liberty_proportions():
    from engineering import geo_calc
    mesh = generate("standing_figure", {"height_m": 6.0}, "bronze", 6.0)
    meta = mesh["metadata"]
    assert meta["family"] == "standing_figure"
    assert meta["pose"] == "torch_raised" and meta["crown_rays"] == 7
    assert meta["mass_kg"] > 0
    bbox = geo_calc.bounding_box(mesh["vertices"])
    assert bbox["size"][1] == pytest.approx(6.0, rel=1e-3)
    assert bbox["min"][1] == pytest.approx(0.0, abs=1e-6)
    # Slender standing figure: width a small fraction of height.
    assert 0.25 < bbox["size"][0] / bbox["size"][1] < 0.5
    # The torch is the highest point and sits to the figure's right (+x).
    v = __import__("numpy").asarray(mesh["vertices"])
    top = v[v[:, 1].argmax()]
    assert top[0] > 0.05 * 6.0


def test_standing_figure_variants_and_validation():
    from engineering import geo_calc
    plain = generate("standing_figure",
                     {"height_m": 4.0, "pedestal": False, "raised_arm": False,
                      "torch": False, "tablet": False, "crown_rays": 0},
                     "stainless_316l", 4.0)
    bbox = geo_calc.bounding_box(plain["vertices"])
    assert bbox["size"][1] == pytest.approx(4.0, rel=1e-3)
    assert plain["metadata"]["pose"] == "arms_down"
    with_ped = generate("standing_figure", {"height_m": 4.0, "pedestal": True}, "bronze", 4.0)
    assert with_ped["metadata"]["mass_kg"] > plain["metadata"]["mass_kg"]
    with pytest.raises(ValueError):
        generate("standing_figure", {"height_m": 4.0, "pedestal_ratio": 0.9}, "bronze", 4.0)
