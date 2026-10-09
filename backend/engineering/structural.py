"""Structural v2 (scope §5 loads, §6 analysis — simplified hand calcs).

Loads:
- Dead: shell + armature self-weight.
- Wind: q = 0.613*V^2, gust factor, drag coefficient by form, solidity
  correction (open/mesh sculptures pass wind; solid forms catch it).
- Water: jet reaction rho*Q*v applied at the sculpture top (conservative).
- Seismic: simplified base shear Z*W.

Analysis (cantilever model on an equivalent armature column):
- base moment, deflection, extreme-fibre stress, Euler buckling,
  natural frequency + vortex-shedding resonance screen.
- Safety factors: overturning, sliding, anchor tension, buckling, yield.

PRELIMINARY — requires licensed engineer review (scope §6: FEA later).
"""

import math

GRAVITY = 9.81
WIND_ZONE_MS = {"low": 35.0, "moderate": 45.0, "high": 55.0, "extreme": 65.0}
GUST_FACTOR = 1.15
SEISMIC_ZONE_FACTOR = 0.15        # simplified base-shear coefficient
STEEL_DENSITY = 7850.0
STEEL_E_PA = 200e9
ARMATURE_FY_PA = 250e6            # mild-steel armature yield
BOLT_COUNT = 4
BOLT_ALLOWABLE_KN = 25.0          # M16 gr.8.8 simplified allowable tension
REBAR_KG_PER_M3 = 110.0
ARMATURE_MASS_FRACTION = 0.25
FRICTION_BASE = 0.4               # steel-on-concrete sliding coefficient
BEARING_ALLOWABLE_KPA = 150.0     # typical soil allowable bearing
SF_REQUIRED = 1.5
STROUHAL = 0.2

# Solidity = solid fraction of the bbox silhouette (scope §5: mesh sculptures
# need different aerodynamic treatment from solid sculptures).
SOLIDITY = {
    "open_ring": 0.15,
    "crescent_inner": 0.35,
    "ribbon_knot": 0.30,
    "organic_flame": 0.80,
    "stacked_rings": 0.35,
    "stacked_c_rings": 0.35,
    "twisted_torus": 0.50,
    "arc_fin_array": 0.50,
    "relief_panel": 0.95,
    "buddha_seated": 0.85,
    "standing_figure": 0.85,
}
DRAG_SOLID = 1.3                  # bluff solid body
DRAG_OPEN = 0.9                   # open/perforated frame


def wind_pressure_pa(wind_zone: str, indoor: bool = False,
                     site_wind_ms: float | None = None) -> tuple[float, float]:
    """(wind speed m/s, velocity pressure Pa). Site-measured speed wins."""
    if indoor:
        return 0.0, 0.0
    v = site_wind_ms or WIND_ZONE_MS.get(wind_zone, WIND_ZONE_MS["moderate"])
    return v, 0.613 * v**2


def compute_structural(brief: dict, geo: dict, sculpture_meta: dict,
                       hydraulics: dict | None = None) -> dict:
    constraints = brief.get("constraints") or {}
    wind_zone = constraints.get("wind_zone", "moderate")
    indoor = bool(constraints.get("indoor", False))
    wind_speed, q_pa = wind_pressure_pa(
        wind_zone, indoor,
        site_wind_ms=constraints.get("site_wind_ms"))

    size = geo["bounding_box"]["size"]
    height_m = max(size[1], 0.1)
    width_m = max(size[0], size[2], 0.1)
    projected_area_m2 = width_m * height_m

    # ── Wind load (gust + drag + solidity) ──────────────────────────────
    family = sculpture_meta.get("family", "")
    solidity = SOLIDITY.get(family, 0.8)
    drag = DRAG_SOLID if solidity > 0.6 else DRAG_OPEN
    effective_area_m2 = projected_area_m2 * solidity
    wind_kn = q_pa * GUST_FACTOR * drag * effective_area_m2 / 1000.0
    wind_moment_knm = wind_kn * height_m / 2.0

    # ── Armature (needed before dead load) ──────────────────────────────
    slenderness = height_m / width_m
    slenderness_factor = min(max(slenderness / 3.0, 1.0), 2.0)
    armature_kg = (sculpture_meta["mass_kg"] * ARMATURE_MASS_FRACTION
                   * slenderness_factor)

    # ── Dead load ───────────────────────────────────────────────────────
    total_mass_kg = sculpture_meta["mass_kg"] + armature_kg
    weight_kn = total_mass_kg * GRAVITY / 1000.0

    # ── Water jet reaction (scope §5: jet reaction forces) ──────────────
    jet_kn = 0.0
    if hydraulics:
        q_m3s = hydraulics.get("total_flow_lps", 0.0) / 1000.0
        head_m = hydraulics.get("nozzle_pressure_head_m", 0.0)
        if q_m3s > 0 and head_m > 0:
            v = math.sqrt(2.0 * GRAVITY * head_m)
            jet_kn = 1000.0 * q_m3s * v / 1000.0  # rho*Q*v
    jet_moment_knm = jet_kn * height_m  # applied at top (conservative)

    # ── Seismic (simplified base shear) ─────────────────────────────────
    seismic_kn = 0.0 if indoor else SEISMIC_ZONE_FACTOR * weight_kn
    seismic_moment_knm = seismic_kn * height_m / 2.0

    # ── Snow + maintenance + thermal (scope §5: other loads) ────────────
    snow_kn = 0.0
    if not indoor:
        # Horizontal projected area x 0.5 kN/m2 fresh-snow blanket.
        horiz_area = max(size[0], 0.1) * max(size[2], 0.1)
        snow_kn = 0.5 * horiz_area * solidity
    maintenance_kn = 0.9 if constraints.get("public_access") else 0.0
    # Thermal: expansion of the longest member over ±40 C swing.
    thermal = {}
    if sculpture_meta.get("material"):
        import json as _json
        from config import DATA_DIR as _DATA_DIR
        mats = _json.loads((_DATA_DIR / "materials.json").read_text())
        alpha = (mats.get(sculpture_meta["material"]) or {}).get(
            "thermal_expansion_per_k", 1.2e-5)
        longest = max(size)
        thermal = {"expansion_mm": round(alpha * 40.0 * longest * 1000.0, 1),
                   "delta_t_k": 40,
                   "note": "provide slip joints / slotted holes at anchors"
                   if alpha * 40.0 * longest > 0.01 else "negligible"}

    # ── Combined base loads ─────────────────────────────────────────────
    h_force_kn = wind_kn + jet_kn + seismic_kn
    moment_knm = wind_moment_knm + jet_moment_knm + seismic_moment_knm

    # ── Cantilever analysis on equivalent armature column ───────────────
    # Equivalent thin-wall SHS: side a = 0.3*width, area from armature mass,
    # I ~ A*a^2/6 (thin-wall approximation).
    a_col = max(0.3 * width_m, 0.05)
    a_steel_m2 = armature_kg / (STEEL_DENSITY * height_m)
    i_col_m4 = a_steel_m2 * a_col**2 / 6.0

    deflection_mm = (h_force_kn * 1000.0 * height_m**3
                     / (3.0 * STEEL_E_PA * i_col_m4) * 1000.0)
    stress_mpa = (moment_knm * 1000.0 * (a_col / 2.0) / i_col_m4) / 1e6
    p_cr_kn = math.pi**2 * STEEL_E_PA * i_col_m4 / (4.0 * height_m**2) / 1000.0

    # Natural frequency (cantilever, modal mass 0.24 of total) and vortex
    # shedding screen (scope §6: natural frequency, resonance risk).
    modal_mass = 0.24 * total_mass_kg
    fn_hz = (1.0 / (2.0 * math.pi)) * math.sqrt(
        3.0 * STEEL_E_PA * i_col_m4 / (modal_mass * height_m**3))
    vortex_hz = (STROUHAL * wind_speed / width_m) if wind_speed > 0 else 0.0
    resonance_risk = (vortex_hz > 0
                      and abs(fn_hz - vortex_hz) / vortex_hz < 0.20)

    # ── Safety factors ──────────────────────────────────────────────────
    # Freestanding (gravity-only) stability uses the FOOTPRINT depth, not
    # the full silhouette width — a 4 m ring is only ~0.3 m thick.
    footprint_m = max(min(size[0], size[2]), 0.15)
    sf_overturning = ((0.5 * weight_kn * footprint_m) / moment_knm
                      if moment_knm > 0 else float("inf"))
    sf_sliding = ((FRICTION_BASE * weight_kn) / h_force_kn
                  if h_force_kn > 0 else float("inf"))
    sf_buckling = p_cr_kn / weight_kn if weight_kn > 0 else float("inf")
    sf_yield = ARMATURE_FY_PA / (stress_mpa * 1e6) if stress_mpa > 0 else float("inf")

    # ── Base plate + anchor bolts (couple model) ────────────────────────
    plate_side_m = min(max(0.4, width_m * 0.8), 2.0)
    bolt_spacing_m = plate_side_m * 0.7
    bolt_tension_kn = (moment_knm / (2.0 * bolt_spacing_m)
                       if bolt_spacing_m > 0 else 0.0)
    bolts_ok = bolt_tension_kn <= BOLT_ALLOWABLE_KN
    sf_bolts = (BOLT_ALLOWABLE_KN / bolt_tension_kn
                if bolt_tension_kn > 0 else float("inf"))

    # ── Foundation pad: overturning heuristic + bearing check ───────────
    pad_side_m = max(1.0, 1.5 * (moment_knm / 25.0) ** (1.0 / 3.0))
    pad_depth_m = max(0.5, 0.4 * pad_side_m)
    # Grow pad until soil bearing is within the allowable pressure.
    while (weight_kn / pad_side_m**2) > BEARING_ALLOWABLE_KPA and pad_side_m < 8.0:
        pad_side_m += 0.25
        pad_depth_m = max(0.5, 0.4 * pad_side_m)
    concrete_m3 = pad_side_m**2 * pad_depth_m
    rebar_kg = concrete_m3 * REBAR_KG_PER_M3

    def _sf(value):
        return None if value == float("inf") else round(value, 2)

    deflection_limit_mm = height_m * 1000.0 / 100.0
    sf_deflection = (deflection_limit_mm / deflection_mm
                     if deflection_mm > 0 else float("inf"))

    safety_factors = {
        "overturning": _sf(sf_overturning),      # freestanding (gravity only)
        "sliding": _sf(sf_sliding),              # freestanding (friction only)
        "anchor_tension": _sf(sf_bolts),
        "buckling": _sf(sf_buckling),
        "yield": _sf(sf_yield),
        "deflection": _sf(sf_deflection),
        "required": SF_REQUIRED,
    }
    # Anchored sculptures: anchors resist overturning/shear, so pass/fail is
    # judged on anchors + member checks; freestanding SFs stay informational.
    anchored = True
    anchored_keys = ("anchor_tension", "buckling", "yield", "deflection")
    freestanding_keys = ("overturning", "sliding")
    check_keys = anchored_keys if anchored else anchored_keys + freestanding_keys
    safety_factors["anchored"] = anchored
    safety_factors["all_pass"] = all(
        safety_factors[k] is None or safety_factors[k] >= SF_REQUIRED
        for k in check_keys)

    return {
        "wind_zone": wind_zone,
        "indoor": indoor,
        "wind_speed_ms": wind_speed,
        "velocity_pressure_pa": round(q_pa, 1),
        "gust_factor": GUST_FACTOR,
        "solidity": solidity,
        "drag_coefficient": drag,
        "projected_area_m2": round(projected_area_m2, 3),
        "effective_area_m2": round(effective_area_m2, 3),
        "loads": {
            "wind_kn": round(wind_kn, 3),
            "jet_reaction_kn": round(jet_kn, 3),
            "seismic_kn": round(seismic_kn, 3),
            "dead_kn": round(weight_kn, 3),
            "snow_kn": round(snow_kn, 3),
            "maintenance_kn": round(maintenance_kn, 2),
            "thermal": thermal,
            "total_horizontal_kn": round(h_force_kn, 3),
        },
        # Back-compat keys (wind-only) used by report/estimator:
        "wind_force_kn": round(wind_kn, 3),
        "overturning_moment_knm": round(moment_knm, 3),
        "total_base_moment_knm": round(moment_knm, 3),
        "analysis": {
            "model": "cantilever on equivalent SHS armature column",
            "column_side_m": round(a_col, 3),
            "deflection_mm": round(deflection_mm, 1),
            "deflection_limit_mm": round(height_m * 1000.0 / 100.0, 1),  # h/100
            "stress_mpa": round(stress_mpa, 2),
            "euler_buckling_load_kn": round(p_cr_kn, 2),
            "natural_frequency_hz": round(fn_hz, 3),
            "vortex_shedding_hz": round(vortex_hz, 3),
            "resonance_risk": resonance_risk,
        },
        "safety_factors": safety_factors,
        "base_plate": {
            "side_m": round(plate_side_m, 3),
            "bolt_count": BOLT_COUNT,
            "bolt_spacing_m": round(bolt_spacing_m, 3),
            "bolt_tension_kn": round(bolt_tension_kn, 3),
            "bolt_allowable_kn": BOLT_ALLOWABLE_KN,
            "bolts_ok": bolts_ok,
        },
        "foundation": {
            "pad_side_m": round(pad_side_m, 3),
            "pad_depth_m": round(pad_depth_m, 3),
            "concrete_m3": round(concrete_m3, 3),
            "rebar_kg": round(rebar_kg, 1),
            "bearing_kpa": round(weight_kn / pad_side_m**2, 1),
            "bearing_allowable_kpa": BEARING_ALLOWABLE_KPA,
        },
        "armature": {
            "slenderness": round(slenderness, 3),
            "slenderness_factor": round(slenderness_factor, 3),
            "steel_kg": round(armature_kg, 2),
        },
        "disclaimer": "Preliminary — requires licensed engineer review.",
    }
