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

# Fitting K-factors per branch type (elbow 0.9, valve 0.3, tee 1.0, entrance 0.5).
BRANCH_FITTINGS_K = {
    "bubbler_field": 2 * 0.9 + 0.3 + 0.5,        # 2 elbows + valve + entrance
    "foam_jet_field": 2 * 0.9 + 0.3 + 0.5,
    "water_sheet": 4 * 0.9 + 0.3 + 0.5,          # riser up the sculpture
    "curtain_from_sculpture": 4 * 0.9 + 0.3 + 0.5,
    "curtain_between_elements": 3 * 0.9 + 0.3 + 0.5,
    "rain_curtain": 3 * 0.9 + 0.3 + 0.5,
}
BRANCH_LENGTH_M = {
    "bubbler_field": 12.0, "foam_jet_field": 12.0,
    "water_sheet": 25.0, "curtain_from_sculpture": 25.0,
    "curtain_between_elements": 22.0, "rain_curtain": 22.0,
}
VELOCITY_COEFF = 0.95        # nozzle velocity coefficient
JET_AIR_LOSS = 0.90          # jet height derating in air
FILTER_RATE_M3H_PER_M2 = 25.0   # sand-filter filtration velocity
FILTER_SIZES_M2 = [0.5, 1.0, 1.5, 2.0, 3.0, 4.5]


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


def _pump_duty_point(total_m3s: float, tdh_m: float, motor_kw: float) -> dict | None:
    """Duty point: intersection of pump curve H = H0*(1-(Q/Qmax)^2) with the
    system curve. If the intersection doesn't meet demand with >=10% margin,
    the pump class is upsized (bigger shutoff + run-out) and re-checked."""
    if total_m3s <= 0 or motor_kw <= 0:
        return None
    h_static = tdh_m * 0.55                # static+nozzle share (approx)
    k_sys = (tdh_m - h_static) / total_m3s**1.852

    def h_sys(q):
        return h_static + k_sys * q**1.852

    for scale in (1.0, 1.25, 1.6, 2.0, 2.6, 3.4):
        h0 = tdh_m * 1.35 * scale
        qmax = total_m3s * 1.6 * scale

        def h_pump(q):
            return h0 * (1.0 - (q / qmax) ** 2)

        lo, hi = 0.001 * qmax, 0.999 * qmax
        for _ in range(60):
            mid = (lo + hi) / 2
            if h_pump(mid) > h_sys(mid):
                lo = mid
            else:
                hi = mid
        q_duty = (lo + hi) / 2
        margin = (q_duty - total_m3s) / total_m3s
        if margin >= 0.10:
            return {
                "pump_class": f"{motor_kw * scale:.1f} kW class",
                "shutoff_head_m": round(h0, 2),
                "runout_flow_lps": round(qmax * 1000.0, 1),
                "duty_flow_lps": round(q_duty * 1000.0, 1),
                "duty_head_m": round(h_pump(q_duty), 2),
                "flow_margin_pct": round(margin * 100.0, 1),
                "duty_ok": True,
                "upsize_count": (1.0, 1.25, 1.6, 2.0, 2.6, 3.4).index(scale),
            }
    return {"duty_ok": False,
            "note": "no catalog class meets demand with 10% margin — "
                    "split into two duty pumps"}


def compute_hydraulics(brief: dict, basin_meta: dict | None = None) -> dict:
    """Full network: branch flows/losses, manifold, valves, filtration,
    TDH, pump duty, equipment schedules (scope §9/§11)."""
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
            head = pressure * BAR_TO_M_HEAD
            exit_v = VELOCITY_COEFF * math.sqrt(2.0 * GRAVITY * head)
            jet_h = exit_v**2 / (2 * GRAVITY) * JET_AIR_LOSS
            per_feature.append({
                "type": ftype, "count": count, "nozzle": nozzle_key,
                "pressure_bar": pressure, "flow_lps": flow_lps,
                "static_lift_m": 0.5,
                "pressure_head_m": head,
                "exit_velocity_ms": round(exit_v, 2),
                "jet_height_m": round(jet_h, 2),
                # Splash zone (scope §10): radius grows with jet height.
                "splash_radius_m": round(0.35 + 0.25 * jet_h, 2),
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

    # ── Branch network: per-feature pipe, friction + fitting losses ─────
    active = [f for f in per_feature if f["flow_lps"] > 0]
    for f in active:
        q = f["flow_lps"] / 1000.0
        branch = select_pipe_dn(q)
        f["pipe"] = branch
        length = BRANCH_LENGTH_M.get(f["type"], 15.0)
        friction = hazen_williams_headloss_m(q, length, branch["inner_d_m"])
        k = BRANCH_FITTINGS_K.get(f["type"], 3.0)
        fitting = k * branch["velocity_ms"]**2 / (2 * GRAVITY)
        f["branch_length_m"] = length
        f["branch_friction_m"] = round(friction, 3)
        f["fitting_loss_m"] = round(fitting, 3)
        f["branch_loss_m"] = round(friction + fitting, 3)
        f["valve"] = {"dn": branch["dn"],
                      "type": "ball" if branch["dn"] <= 50 else "butterfly"}

    total_m3s = sum(f["flow_lps"] for f in per_feature) / 1000.0
    pipe = select_pipe_dn(total_m3s) if total_m3s > 0 else None

    # Manifold: one size up from the main when 3+ branches.
    manifold = None
    if pipe and len(active) >= 3:
        idx = STANDARD_DN.index(pipe["dn"])
        manifold_dn = STANDARD_DN[min(idx + 1, len(STANDARD_DN) - 1)]
        manifold = {"dn": manifold_dn, "branches": len(active)}
    elif pipe:
        manifold = {"dn": pipe["dn"], "branches": len(active)}

    friction = (hazen_williams_headloss_m(total_m3s, DEFAULT_PIPE_LENGTH_M,
                                          pipe["inner_d_m"])
                if pipe else 0.0)
    static_lift = max((f["static_lift_m"] for f in per_feature), default=0.0)
    nozzle_head = max((f["pressure_head_m"] for f in per_feature), default=0.0)
    worst_branch = max((f.get("branch_loss_m", 0.0) for f in per_feature),
                       default=0.0)
    fitting_loss = max((f.get("fitting_loss_m", 0.0) for f in per_feature),
                       default=0.0)
    tdh = static_lift + friction + worst_branch + nozzle_head

    hydraulic_kw = RHO_WATER * GRAVITY * total_m3s * tdh / 1000.0
    motor_kw = hydraulic_kw / PUMP_EFFICIENCY

    volume = (basin_meta or {}).get("water_volume_m3")
    turnover_min = (volume / total_m3s / 60.0) if volume and total_m3s > 0 else None

    # Filtration: size a sand filter on the full recirculation flow.
    filtration = None
    if total_m3s > 0 and volume:
        flow_m3h = total_m3s * 3600.0
        area_req = flow_m3h / FILTER_RATE_M3H_PER_M2
        area = next((a for a in FILTER_SIZES_M2 if a >= area_req),
                    FILTER_SIZES_M2[-1])
        filtration = {"flow_m3h": round(flow_m3h, 1),
                      "filter_area_m2": area,
                      "type": "sand filter",
                      "backwash_note": "size backwash water supply + drain"}

    # Equipment schedules (scope §11).
    schedules = {
        "pump": None if motor_kw <= 0 else {
            "duty_flow_lps": round(total_m3s * 1000.0, 1),
            "duty_head_m": round(tdh, 2),
            "motor_kw": round(motor_kw, 2),
            "efficiency": PUMP_EFFICIENCY,
        },
        "nozzles": [{"type": f["type"], "nozzle": f.get("nozzle"),
                     "count": f.get("count"),
                     "flow_lps": round(f["flow_lps"], 2)}
                    for f in active if f.get("nozzle")],
        "valves": [{"branch": f["type"], "dn": f["valve"]["dn"],
                    "type": f["valve"]["type"]} for f in active],
        "pipes": ([{"run": "main", "dn": pipe["dn"],
                    "velocity_ms": round(pipe["velocity_ms"], 2),
                    "length_m": DEFAULT_PIPE_LENGTH_M}] if pipe else [])
                 + [{"run": f["type"], "dn": f["pipe"]["dn"],
                     "velocity_ms": round(f["pipe"]["velocity_ms"], 2),
                     "length_m": f["branch_length_m"]} for f in active],
    }

    return {
        "features": per_feature,
        "total_flow_lps": total_m3s * 1000.0,
        "main_pipe": pipe,
        "manifold": manifold,
        "pipe_length_m": DEFAULT_PIPE_LENGTH_M,
        "static_lift_m": static_lift,
        "friction_head_m": friction,
        "fitting_loss_m": round(fitting_loss, 3),
        "worst_branch_loss_m": round(worst_branch, 3),
        "nozzle_pressure_head_m": nozzle_head,
        "tdh_m": tdh,
        "pump_hydraulic_kw": hydraulic_kw,
        "motor_kw": motor_kw,
        "pump_efficiency": PUMP_EFFICIENCY,
        "turnover_min": turnover_min,
        "filtration": filtration,
        "duty_point": _pump_duty_point(total_m3s, tdh, motor_kw),
        "schedules": schedules,
    }
