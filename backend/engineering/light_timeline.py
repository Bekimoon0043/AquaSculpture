"""Dynamic light design (scope §14) — show timeline engine.

The brief carries an optional lighting.show: a list of timed segments with
effects (fade, pulse, chase, gradient, wave, sparkle, strobe, transition).
This module compiles it into a per-fixture keyframe program that travels to
AquaFlow inside the LUXEXCHANGE envelope (scope §31: AquaFlow owns show
control; LuxuryForm only authors the program).

If the brief has no show, a sensible default (warm welcome -> cool wave ->
pulse finale) is generated from the fixture count.
"""

EFFECTS = ("fade", "pulse", "chase", "gradient", "wave", "sparkle", "strobe",
           "transition")

import math
import random

DEFAULT_SHOW = [
    {"start_s": 0.0, "duration_s": 10.0, "effect": "fade",
     "color": "#ffb85c", "color_to": "#ffdca8", "zones": ["all"]},
    {"start_s": 10.0, "duration_s": 10.0, "effect": "wave",
     "color": "#3c82ff", "color_to": "#9fd4ff", "zones": ["all"]},
    {"start_s": 20.0, "duration_s": 8.0, "effect": "pulse",
     "color": "#ff4d6d", "zones": ["basin"]},
]

SAMPLE_HZ = 4  # keyframes per second per fixture


def _hex_rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return (int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255)


def _mix(c1, c2, t):
    return tuple(round(a + (b - a) * t, 4) for a, b in zip(c1, c2))


def compile_show(brief: dict, lighting: dict) -> dict:
    """Brief show (or default) -> per-fixture keyframe program."""
    segments = ((brief.get("lighting") or {}).get("show")) or DEFAULT_SHOW
    fixtures = (lighting.get("controls") or {}).get("schedule", [])
    n = len(fixtures)

    # Validate segments.
    for seg in segments:
        if seg["effect"] not in EFFECTS:
            raise ValueError(f"unknown effect '{seg['effect']}'")
        if seg["duration_s"] <= 0:
            raise ValueError("segment duration must be positive")

    program: dict[str, list] = {f["id"]: [] for f in fixtures}
    for seg in segments:
        c1 = _hex_rgb(seg.get("color", "#ffffff"))
        c2 = _hex_rgb(seg.get("color_to", seg.get("color", "#ffffff")))
        steps = max(2, int(seg["duration_s"] * SAMPLE_HZ))
        zone = seg.get("zones", ["all"])
        for fi, f in enumerate(fixtures):
            fzone = "sculpture" if f["id"].startswith("U") else "basin"
            if "all" not in zone and fzone not in zone:
                continue
            for s in range(steps):
                t01 = s / (steps - 1)
                t_abs = seg["start_s"] + t01 * seg["duration_s"]
                eff = seg["effect"]
                if eff == "fade" or eff == "transition":
                    rgb = _mix(c1, c2, t01)
                elif eff == "pulse":
                    rgb = _mix(c1, c2, 0.5 - 0.5 * math.cos(t01 * 2 * math.pi))
                elif eff == "chase":
                    rgb = c1 if (s + fi) % 4 == 0 else _mix(c1, (0, 0, 0), 0.8)
                elif eff == "gradient":
                    rgb = _mix(c1, c2, fi / max(n - 1, 1))
                elif eff == "wave":
                    rgb = _mix(c1, c2, 0.5 + 0.5 * math.sin(
                        t01 * 2 * math.pi + fi * 0.8))
                elif eff == "sparkle":
                    rnd = random.Random(fi * 1000 + s)
                    rgb = c1 if rnd.random() < 0.2 else _mix(c1, (0, 0, 0), 0.7)
                else:  # strobe
                    rgb = c1 if s % 2 == 0 else (0.0, 0.0, 0.0)
                program[f["id"]].append([round(t_abs, 2), *rgb])

    return {
        "segments": segments,
        "fixture_count": n,
        "total_duration_s": max(s["start_s"] + s["duration_s"] for s in segments),
        "sample_hz": SAMPLE_HZ,
        "program": program,
        "note": "Authored in LuxuryForm; played by AquaFlow (scope §31)",
    }
