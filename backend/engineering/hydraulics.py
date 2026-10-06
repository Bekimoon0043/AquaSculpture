"""Hydraulics v1 (PLAN.md §6 — hydraulics).

- Bubbler/foam jets: Q = K * sqrt(P) per jet (K from data/nozzles.json)
- Sculpture-borne sheets/curtains: Francis weir Q = 1.84 * L * h^1.5 (SI, m3/s)
- Pipe sizing: smallest standard DN keeping velocity <= 2.5 m/s
- Friction: Hazen-Williams (C = 150)
- TDH = static lift + friction + nozzle pressure head; motor kW at eta = 0.7
- Basin turnover = water volume / total flow

Internal units SI (m, m3/s); reported flows in L/s.
"""

import json
import math
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

GRAVITY = 9.81
RHO_WATER = 1000.0
PUMP_EFFICIENCY = 0.70
BAR_TO_M_HEAD = 10.2
HAZEN_WILLIAMS_C = 150.0
MAX_VELOCITY_MS = 2.5
DEFAULT_PIPE_LENGTH_M = 20.0
DEFAULT_WEIR_HEAD_M = 0.02
DEFAULT_SPILL_EDGE_M = 3.0

# Nominal DN (mm) -> approximate inner diameter (m).
STANDARD_DN = [25, 32, 40, 50, 65, 80, 100, 125, 150, 200, 250, 300]

JET_FEATURES = {"bubbler_field", "foam_jet_field"}
WEIR_FEATURES = {"water_sheet", "curtain_from_sculpture", "curtain_between_elements",
                 "rain_curtain"}

_NOZZLE_FOR_FEATURE = {
    "bubbler_field": "bubbler_dn25",
    "foam_jet_field": "foam_jet_dn40",
}


def load_nozzles() -> dict:
    with (DATA_DIR / "nozzles.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def jet_flow_lps(nozzle_key: str, pressure_bar: float) -> float:
    """Q = K * sqrt(P), L/s."""
    k = load_nozzles()[nozzle_key]["k_lps_per_sqrt_bar"]
    return k * math.sqrt(pressure_bar)


def weir_flow_m3s(length_m: float, head_m: float) -> float:
    """Francis weir: Q = 1.84 * L * h^1.5 (m3/s)."""
    return 1.84 * length_m * head_m**1.5


def select_pipe_dn(flow_m3s: float) -> dict:
    """Smallest standard DN with velocity <= 2.5 m/s."""
    for dn in STANDARD_DN:
        d = dn / 1000.0
        area = math.pi * d**2 / 4.0
        velocity = flow_m3s / area
        if velocity <= MAX_VELOCITY_MS:
            return {"dn": dn, "inner_d_m": d, "velocity_ms": velocity}
    dn = STANDARD_DN[-1]
    d = dn / 1000.0
    return {"dn": dn, "inner_d_m": d,
            "velocity_ms": flow_m3s / (math.pi * d**2 / 4.0)}


def hazen_williams_headloss_m(flow_m3s: float, length_m: float, inner_d_m: float,
                              c: float = HAZEN_WILLIAMS_C) -> float:
    """hf = 10.67 * L * Q^1.852 / (C^1.852 * d^4.87) — meters of head."""
    return 10.67 * length_m * flow_m3s**1.852 / (c**1.852 * inner_d_m**4.87)


def compute_hydraulics(brief: dict, basin_meta: dict | None = None) -> dict:
    """Feature-by-feature flows, pipe sizes, TDH, pump duty, turnover."""
    water = brief.get("water") or {}
    features = water.get("features") or []
    sculpture_height = (brief.get("sculpture") or {}).get("height_m", 2.0)
    nozzles = load_nozzles()

    per_feature: list[dict] = []
    for feat in features:
        ftype = feat.get("type")
        if ftype in JET_FEATURES:
            count = feat.get("count", 1)
            nozzle_key = _NOZZLE_FOR_FEATURE[ftype]
            nozzle = nozzles[nozzle_key]
            pressure = nozzle["design_pressure_bar"]
            flow_lps = count * nozzle["k_lps_per_sqrt_bar"] * math.sqrt(pressure)
            per_feature.append({
                "type": ftype, "count": count, "nozzle": nozzle_key,
                "pressure_bar": pressure, "flow_lps": flow_lps,
                "static_lift_m": 0.5,
                "pressure_head_m": pressure * BAR_TO_M_HEAD,
            })
        elif ftype in WEIR_FEATURES:
            length = feat.get("spill_edge_length_m", DEFAULT_SPILL_EDGE_M)
            head = feat.get("head_m", DEFAULT_WEIR_HEAD_M)
            flow_m3s = weir_flow_m3s(length, head)
            per_feature.append({
                "type": ftype, "spill_edge_length_m": length, "head_m": head,
                "flow_lps": flow_m3s * 1000.0,
                "static_lift_m": sculpture_height,
                "pressure_head_m": head,
            })
        else:
            per_feature.append({"type": ftype, "flow_lps": 0.0,
                                "static_lift_m": 0.0, "pressure_head_m": 0.0})

    total_m3s = sum(f["flow_lps"] for f in per_feature) / 1000.0
    pipe = select_pipe_dn(total_m3s) if total_m3s > 0 else None
    friction = (hazen_williams_headloss_m(total_m3s, DEFAULT_PIPE_LENGTH_M,
                                          pipe["inner_d_m"])
                if pipe else 0.0)
    static_lift = max((f["static_lift_m"] for f in per_feature), default=0.0)
    nozzle_head = max((f["pressure_head_m"] for f in per_feature), default=0.0)
    tdh = static_lift + friction + nozzle_head

    hydraulic_kw = RHO_WATER * GRAVITY * total_m3s * tdh / 1000.0
    motor_kw = hydraulic_kw / PUMP_EFFICIENCY

    if pipe:
        for f in per_feature:
            f["pipe"] = (select_pipe_dn(f["flow_lps"] / 1000.0)
                         if f["flow_lps"] > 0 else None)

    volume = (basin_meta or {}).get("water_volume_m3")
    turnover_min = (volume / total_m3s / 60.0) if volume and total_m3s > 0 else None

    return {
        "features": per_feature,
        "total_flow_lps": total_m3s * 1000.0,
        "main_pipe": pipe,
        "pipe_length_m": DEFAULT_PIPE_LENGTH_M,
        "static_lift_m": static_lift,
        "friction_head_m": friction,
        "nozzle_pressure_head_m": nozzle_head,
        "tdh_m": tdh,
        "pump_hydraulic_kw": hydraulic_kw,
        "motor_kw": motor_kw,
        "pump_efficiency": PUMP_EFFICIENCY,
        "turnover_min": turnover_min,
    }
