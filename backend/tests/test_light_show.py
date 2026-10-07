import pytest
from fastapi.testclient import TestClient

from api.routes.brief import EXAMPLE_BRIEF
from engineering import light_timeline
from main import app

client = TestClient(app)


def _brief():
    return {**EXAMPLE_BRIEF,
            "sculpture": {**EXAMPLE_BRIEF["sculpture"], "family": "open_ring",
                          "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                         "opening_deg": 90, "segments": 16}}}


def _lighting():
    from engineering import geo_calc, lighting
    from geometry.archetypes import generate
    mesh = generate("open_ring", {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                  "opening_deg": 60, "segments": 16},
                    "stainless_316l", 4.0)
    geo = {"bounding_box": geo_calc.bounding_box(mesh["vertices"])}
    return lighting.design_lighting(_brief(), geo, mesh["vertices"],
                                    mesh["faces"], None)


def test_default_show_compiles():
    show = light_timeline.compile_show(_brief(), _lighting())
    assert show["fixture_count"] > 0
    assert show["total_duration_s"] == 28.0
    assert show["program"]
    # Every keyframe: [t, r, g, b] with normalized colors.
    for frames in show["program"].values():
        if frames:
            t, r, g, b = frames[0]
            assert 0.0 <= r <= 1.0 and 0.0 <= g <= 1.0 and 0.0 <= b <= 1.0


def test_custom_show_from_brief():
    b = _brief()
    b["lighting"] = {"sculpture_uplights": 4,
                     "show": [{"start_s": 0.0, "duration_s": 5.0,
                               "effect": "chase", "color": "#ff0000",
                               "zones": ["all"]}]}
    show = light_timeline.compile_show(b, _lighting())
    assert show["total_duration_s"] == 5.0
    assert show["segments"][0]["effect"] == "chase"


def test_unknown_effect_rejected():
    b = _brief()
    b["lighting"] = {"show": [{"start_s": 0.0, "duration_s": 5.0,
                               "effect": "explode", "zones": ["all"]}]}
    with pytest.raises(ValueError):
        light_timeline.compile_show(b, _lighting())


def test_zone_filtering():
    b = _brief()
    b["lighting"] = {"sculpture_uplights": 2, "submersible_rgb": 2,
                     "show": [{"start_s": 0.0, "duration_s": 4.0,
                               "effect": "fade", "color": "#ffffff",
                               "zones": ["sculpture"]}]}
    show = light_timeline.compile_show(b, _lighting())
    uplight_frames = [len(frames) for fid, frames in show["program"].items()
                      if fid.startswith("U")]
    sub_frames = [len(frames) for fid, frames in show["program"].items()
                  if fid.startswith("S")]
    assert all(n > 0 for n in uplight_frames)
    assert all(n == 0 for n in sub_frames)


def test_show_travels_in_luxexchange():
    resp = client.post("/api/integration/aquaflow", json=_brief())
    env = resp.json()
    program = env["payload"]["show_program"]
    assert program is not None
    # Program keys match light fixture ids.
    light_ids = {f["id"] for f in env["payload"]["fixtures"]
                 if f["kind"] == "light"}
    assert light_ids <= set(program.keys())
