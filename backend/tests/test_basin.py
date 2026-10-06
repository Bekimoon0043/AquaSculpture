import math
from collections import Counter

import pytest

from geometry.basin import (FREEBOARD_M, FLOOR_THICKNESS_M, generate_basin,
                            place_bubblers)


def _edge_counts(faces):
    counts = Counter()
    for a, b, c in faces:
        for e in ((a, b), (b, c), (c, a)):
            counts[tuple(sorted(e))] += 1
    return counts


def test_circular_basin_watertight():
    basin = generate_basin({"shape": "circular", "diameter_m": 6.0, "depth_m": 0.45})
    counts = _edge_counts(basin["faces"])
    assert all(n == 2 for n in counts.values())


def test_circular_basin_volume_analytic():
    basin = generate_basin({"shape": "circular", "diameter_m": 6.0, "depth_m": 0.45,
                            "overflow": "perimeter_weir"})
    meta = basin["metadata"]
    water_depth = 0.45 - FLOOR_THICKNESS_M - FREEBOARD_M
    assert meta["water_volume_m3"] == pytest.approx(math.pi * 9.0 * water_depth)
    assert meta["wetted_area_m2"] == pytest.approx(
        math.pi * 9.0 + 2.0 * math.pi * 3.0 * water_depth)
    assert meta["weir_length_m"] == pytest.approx(2.0 * math.pi * 3.0)


def test_no_weir_length_without_perimeter_overflow():
    basin = generate_basin({"shape": "circular", "diameter_m": 6.0, "depth_m": 0.45,
                            "overflow": "skimmer"})
    assert basin["metadata"]["weir_length_m"] is None


def test_rectangular_basin_volume():
    basin = generate_basin({"shape": "rectangular", "length_m": 5.0, "width_m": 3.0,
                            "depth_m": 0.5})
    meta = basin["metadata"]
    water_depth = 0.5 - FLOOR_THICKNESS_M - FREEBOARD_M
    assert meta["water_volume_m3"] == pytest.approx(15.0 * water_depth)
    assert meta["inner"] == {"length_m": 5.0, "width_m": 3.0}


def test_bubbler_placement_clearances():
    positions = place_bubblers(12, footprint_radius_m=0.3,
                               inner={"radius_m": 3.0})
    assert len(positions) == 12
    for x, _, z in positions:
        r = math.hypot(x, z)
        assert r >= 0.3 + 0.6 - 1e-9        # sculpture clearance
        assert r <= 3.0 - 0.4 + 1e-9        # basin edge clearance
    for i in range(len(positions)):
        for j in range(i + 1, len(positions)):
            d = math.dist(positions[i], positions[j])
            assert d >= 0.75                 # ~min_spacing (0.8) with stagger


def test_bubbler_placement_impossible_raises():
    with pytest.raises(ValueError):
        place_bubblers(500, footprint_radius_m=0.5, inner={"radius_m": 1.2})


def test_basin_brief_features_generate_nozzles():
    basin = generate_basin(
        {"shape": "circular", "diameter_m": 6.0, "depth_m": 0.45},
        features=[{"type": "bubbler_field", "count": 8}],
        footprint_radius_m=0.3)
    assert len(basin["metadata"]["nozzle_positions"]) == 8
