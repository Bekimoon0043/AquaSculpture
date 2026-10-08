"""Lighting engineering (scope §11 fixtures, §12 illumination, §15 controls).

Placement: uplights ring the sculpture footprint aimed at the form centroid;
submersible RGB fixtures sit in the basin aiming up.

Illumination (simplified point-source model): candela from lumens/beam cone,
lux at each shell face centroid = I * cos / d^2, only inside the beam cone.

Controls: total load, 24 V PSU sizing with headroom, DMX address map +
universes, home-run cable lengths, voltage-drop check.
"""

import json
import math
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parents[1] / "data" / "lighting.json"
CATALOG = json.loads(DATA.read_text(encoding="utf-8"))

PSU_WATTAGE = 320.0
PSU_HEADROOM = 1.25
DMX_UNIVERSE_CH = 512
CABLE_TAIL_M = 10.0          # average route beyond the basin edge
CABLE_AREA_MM2 = 2.5
COPPER_RESISTIVITY = 0.0175  # ohm mm2 / m
VDROP_LIMIT_V = 1.2          # 5% of 24 V
MIN_LUX = 50.0               # accent-lighting floor on the sculpture


def _aim(pos, target):
    v = np.subtract(target, pos, dtype=float)
    n = float(np.linalg.norm(v))
    return (v / n).tolist() if n > 0 else [0.0, 1.0, 0.0]


def place_fixtures(brief: dict, geo: dict, basin_meta: dict | None) -> list[dict]:
    lighting = brief.get("lighting") or {}
    n_up = lighting.get("sculpture_uplights", 4)
    n_sub = lighting.get("submersible_rgb", 0)

    (x0, y0, z0), (x1, y1, z1) = geo["bounding_box"]["min"], geo["bounding_box"]["max"]
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    height = y1 - y0
    footprint = max(x1 - x0, z1 - z0) / 2.0
    target = [cx, y0 + 0.6 * height, cz]

    fixtures: list[dict] = []
    for i in range(n_up):
        a = 2 * math.pi * i / max(n_up, 1)
        pos = [cx + (footprint + 0.8) * math.cos(a), 0.05,
               cz + (footprint + 0.8) * math.sin(a)]
        fixtures.append({
            "id": f"U{i + 1:02d}", "catalog": "uplight_36w_rgbw",
            "position": [round(p, 3) for p in pos],
            "aim": [round(v, 3) for v in _aim(pos, target)],
        })
    if basin_meta and n_sub:
        floor = basin_meta.get("floor_thickness_m", 0.15)
        r = footprint + 0.4
        for i in range(n_sub):
            a = 2 * math.pi * i / n_sub + 0.3
            pos = [cx + r * math.cos(a), floor + 0.05, cz + r * math.sin(a)]
            fixtures.append({
                "id": f"S{i + 1:02d}", "catalog": "submersible_12w_rgb",
                "position": [round(p, 3) for p in pos],
                "aim": [round(v, 3) for v in _aim(pos, target)],
            })
    return fixtures


def illuminate(fixtures: list[dict], vertices, faces) -> dict:
    """Lux estimate over the shell (scope §12: illuminance, falloff, hotspots)."""
    if not fixtures:
        return {"avg_lux": 0.0, "max_lux": 0.0, "coverage_pct": 0.0,
                "min_lux_target": MIN_LUX, "wasted_fixtures": 0,
                "face_lux": [],
                "hotspots": {"count": 0, "max_ratio": 0.0}}
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    tris = v[f]
    cents = tris.mean(axis=1)
    norms = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(norms, axis=1, keepdims=True)
    ln[ln < 1e-15] = 1e-15
    norms = norms / ln

    lux = np.zeros(len(cents))
    wasted = 0
    for fx in fixtures:
        spec = CATALOG[fx["catalog"]]
        omega = 2 * math.pi * (1 - math.cos(math.radians(spec["beam_angle_deg"] / 2)))
        candela = spec["lumens"] / omega
        pos = np.asarray(fx["position"])
        aim = np.asarray(fx["aim"])
        to_pts = cents - pos
        d = np.linalg.norm(to_pts, axis=1)
        d[d < 0.05] = 0.05
        dirs = to_pts / d[:, None]
        in_beam = (dirs @ aim) > math.cos(math.radians(spec["beam_angle_deg"] / 2))
        cos_inc = np.clip(-(dirs * norms).sum(axis=1), 0.0, 1.0)
        contribution = np.where(in_beam, candela * cos_inc / d**2, 0.0)
        # Fixture lighting <1% of the shell is badly placed/aimed (scope §12:
        # an engineering answer to where lights should actually be installed).
        if (contribution >= MIN_LUX).mean() < 0.01:
            wasted += 1
        lux += contribution

    lit = lux[lux > 0]
    hotspot_ratio = float(lit.max() / lit.mean()) if len(lit) else 0.0
    return {
        "avg_lux": round(float(lux.mean()), 1),
        "max_lux": round(float(lux.max()), 1),
        "coverage_pct": round(float((lux >= MIN_LUX).mean()) * 100.0, 1),
        "min_lux_target": MIN_LUX,
        "wasted_fixtures": wasted,
        "face_lux": [round(float(x), 1) for x in lux],  # heat-map overlay
        # Glare screen: faces lit > 4x the lit-average read as hotspots.
        "hotspots": {"count": int((lux > 4 * lit.mean()).sum()) if len(lit) else 0,
                     "max_ratio": round(hotspot_ratio, 1)},
    }


def control_engineering(fixtures: list[dict], basin_meta: dict | None) -> dict:
    """Loads, PSUs, DMX map, cable + voltage drop (scope §15)."""
    schedule: list[dict] = []
    addr = 1
    total_w = 0.0
    worst_drop = 0.0
    for fx in fixtures:
        spec = CATALOG[fx["catalog"]]
        total_w += spec["power_w"]
        d_run = math.sqrt(fx["position"][0]**2 + fx["position"][2]**2) + CABLE_TAIL_M
        current = spec["power_w"] / spec["voltage_v"]
        vdrop = 2 * d_run * current * COPPER_RESISTIVITY / CABLE_AREA_MM2
        worst_drop = max(worst_drop, vdrop)
        schedule.append({
            "id": fx["id"], "fixture": spec["name"],
            "power_w": spec["power_w"], "ip": spec["ip_rating"],
            "dmx_address": addr, "dmx_channels": spec["dmx_channels"],
            "cable_run_m": round(d_run, 1),
            "voltage_drop_v": round(vdrop, 2),
        })
        addr += spec["dmx_channels"]

    total_ch = addr - 1
    return {
        "fixture_count": len(fixtures),
        "total_load_w": round(total_w, 1),
        "psu_count": math.ceil(total_w * PSU_HEADROOM / PSU_WATTAGE) if total_w else 0,
        "psu_wattage": PSU_WATTAGE,
        "dmx_universes": math.ceil(total_ch / DMX_UNIVERSE_CH) if total_ch else 0,
        "dmx_channels_used": total_ch,
        "max_voltage_drop_v": round(worst_drop, 2),
        "voltage_drop_ok": worst_drop <= VDROP_LIMIT_V,
        "schedule": schedule,
    }


def design_lighting(brief: dict, geo: dict, vertices, faces,
                    basin_meta: dict | None) -> dict:
    fixtures = place_fixtures(brief, geo, basin_meta)
    illum = illuminate(fixtures, vertices, faces)

    # Auto-aim refinement (scope §12/§13): re-aim the least-useful fixture at
    # the darkest surface region; keep it if coverage improves.
    if fixtures and illum["coverage_pct"] < 80:
        import numpy as np
        v = np.asarray(vertices, dtype=float)
        f = np.asarray(faces, dtype=int)
        cents = v[f].mean(axis=1)
        lux = np.asarray(illum["face_lux"])
        dark = cents[lux < illum["min_lux_target"]]
        if len(dark):
            target = dark.mean(axis=0)
            wasted_ids = []
            for i, fx in enumerate(fixtures):
                if _fixture_hit_share(fx, lux_min=illum["min_lux_target"],
                                      cents=cents, v=v, f=f) < 0.01:
                    wasted_ids.append(i)
            if wasted_ids:
                fx = fixtures[wasted_ids[0]]
                fx["aim"] = _aim(fx["position"], target.tolist())
                fx["auto_aimed"] = True
                improved = illuminate(fixtures, vertices, faces)
                if improved["coverage_pct"] > illum["coverage_pct"]:
                    improved["auto_aim_note"] = (
                        f"fixture {fx['id']} re-aimed at darkest region: "
                        f"coverage {illum['coverage_pct']:.0f}% -> "
                        f"{improved['coverage_pct']:.0f}%")
                    illum = improved

    return {
        "fixtures": fixtures,
        "illumination": illum,
        "controls": control_engineering(fixtures, basin_meta),
    }


def _fixture_hit_share(fx, lux_min, cents, v, f) -> float:
    """Share of shell this fixture lights above the lux floor."""
    import math
    import numpy as np
    spec = CATALOG[fx["catalog"]]
    pos = np.asarray(fx["position"])
    aim = np.asarray(fx["aim"])
    dirs = cents - pos
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True).clip(1e-9)
    in_beam = (dirs @ aim) > math.cos(math.radians(spec["beam_angle_deg"] / 2))
    return float(in_beam.mean())
