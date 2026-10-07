"""Wind drift analysis (scope §10): where the water actually lands.

Model (as AquaFlow): droplet flight time from jet height, horizontal drift =
wind speed x flight time; splash ellipse elongated downwind. Produces the
exclusion zone a designer must keep dry (walkways, glazing).
"""

import math

DRAG_FACTOR = 0.65       # droplets don't fully reach wind speed
GRAVITY = 9.81
WIND_ZONE_MS = {"low": 35.0, "moderate": 45.0, "high": 55.0, "extreme": 65.0}
# Design drift uses a fraction of the storm wind (operating condition).
OPERATING_FRACTION = 0.35


def jet_drift(jet_height_m: float, wind_zone: str, indoor: bool) -> dict:
    if indoor or jet_height_m <= 0:
        return {"drift_m": 0.0, "flight_time_s": 0.0, "exclusion_radius_m": 0.0}
    t_up = math.sqrt(2 * jet_height_m / GRAVITY)
    flight = 2 * t_up                       # up and back to nozzle level
    v_wind = WIND_ZONE_MS.get(wind_zone, 45.0) * OPERATING_FRACTION
    drift = v_wind * DRAG_FACTOR * flight
    return {
        "flight_time_s": round(flight, 2),
        "drift_m": round(drift, 2),
        "drift_direction": "prevailing wind",
        "exclusion_radius_m": round(drift + 0.35 + 0.25 * jet_height_m, 2),
    }


def analyze_drift(brief: dict, hydraulics: dict) -> dict:
    constraints = brief.get("constraints") or {}
    wind_zone = constraints.get("wind_zone", "moderate")
    indoor = bool(constraints.get("indoor", False))
    per_feature = []
    worst = 0.0
    for f in hydraulics.get("features", []):
        if f.get("jet_height_m"):
            d = jet_drift(f["jet_height_m"], wind_zone, indoor)
            per_feature.append({"type": f["type"], **d})
            worst = max(worst, d["exclusion_radius_m"])
    return {
        "per_feature": per_feature,
        "max_exclusion_radius_m": round(worst, 2),
        "note": "keep walkways/glazing outside the exclusion radius or add "
                "wind-sensing pump cutoff",
    }
