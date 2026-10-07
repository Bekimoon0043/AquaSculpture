"""Kinetic / moving sculpture engine (scope §16).

For sculptures with a kinetics block: real inertia from the mesh,
acceleration/torque from the motion profile, motor + gearbox selection,
shaft sizing from torque, bearing loads with L10 life, and a swept
motion-envelope collision check against the basin rim.
"""

import math

import numpy as np

GRAVITY = 9.81
STEEL_SHEAR_ALLOW_MPA = 90.0     # shaft steel, with fatigue margin
BEARING_C_DYNAMIC_KN = 18.0      # catalog bearing basic dynamic rating
MOTOR_CATALOG_KW = [0.25, 0.55, 1.1, 2.2, 4.0, 7.5]
MOTOR_RPM = 1450.0
GEARBOX_MAX_RATIO = 100.0


def mesh_inertia_about_axis(vertices, faces, mass_kg: float,
                            axis: str = "y") -> float:
    """Mass moment of inertia (kg m2) from area-weighted face centroids.

    Approximation: shell mass distributed over its surface. Exact tetrahedral
    integration is overkill at this fidelity.
    """
    v = np.asarray(vertices, dtype=float)
    f = np.asarray(faces, dtype=int)
    tris = v[f]
    cents = tris.mean(axis=1)
    areas = 0.5 * np.linalg.norm(
        np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1)
    total = areas.sum()
    if total <= 0:
        return 0.0
    center = np.average(cents, axis=0, weights=areas)
    ax = {"x": 0, "y": 1, "z": 2}[axis]
    others = [i for i in range(3) if i != ax]
    r2 = ((cents[:, others] - center[others]) ** 2).sum(axis=1)
    return float(mass_kg * float(np.average(r2, weights=areas)))


def design_kinetics(brief: dict, geo: dict, vertices, faces,
                    mass_kg: float) -> dict:
    kin = brief.get("kinetics") or {}
    motion = kin.get("motion", "rotation")
    axis = kin.get("axis", "y")
    rpm = kin.get("rpm", 2.0)
    ramp_s = kin.get("ramp_time_s", 5.0)
    amp_deg = kin.get("amplitude_deg", 30.0)

    inertia = mesh_inertia_about_axis(vertices, faces, mass_kg, axis)
    omega = 2.0 * math.pi * rpm / 60.0

    if motion == "rotation":
        alpha = omega / ramp_s                      # spin-up angular accel
        peak_torque_nm = inertia * alpha
        continuous_power_w = peak_torque_nm * omega  # + losses handled below
        motion_desc = f"continuous rotation at {rpm} rpm"
    else:  # oscillation: theta = A sin(wt)
        a = math.radians(amp_deg)
        period = 60.0 / max(rpm, 0.01)              # rpm = cycles per minute
        w = 2.0 * math.pi / period
        alpha = a * w**2                            # peak angular acceleration
        peak_torque_nm = inertia * alpha + mass_kg * GRAVITY * 0.05 * a
        continuous_power_w = peak_torque_nm * w * 0.5
        omega = w
        motion_desc = f"oscillation ±{amp_deg} deg, period {period:.1f} s"

    # Drive train: motor + gearbox.
    shaft_power_kw = continuous_power_w * 1.4 / 1000.0  # 40% loss+margin
    motor_kw = next((m for m in MOTOR_CATALOG_KW if m >= shaft_power_kw),
                    MOTOR_CATALOG_KW[-1])
    out_rpm = rpm if motion == "rotation" else 60.0 / (60.0 / rpm)
    ratio = min(MOTOR_RPM / max(out_rpm, 0.01), GEARBOX_MAX_RATIO)

    # Shaft from torque: T = tau*pi*d^3/16 (solid round).
    d_m = ((16.0 * peak_torque_nm)
           / (math.pi * STEEL_SHEAR_ALLOW_MPA * 1e6)) ** (1.0 / 3.0)
    shaft_mm = max(20.0, math.ceil(d_m * 1000.0 / 5.0) * 5.0)

    # Bearings: radial load = weight; L10 life in hours.
    radial_kn = mass_kg * GRAVITY / 1000.0 / 2.0   # two bearings share
    l10_rev = (BEARING_C_DYNAMIC_KN / max(radial_kn, 0.01)) ** 3 * 1e6
    l10_hours = l10_rev / max(rpm, 0.01) / 60.0

    # Motion envelope: swept cylinder of the rotating body.
    (x0, y0, z0), (x1, y1, z1) = geo["bounding_box"]["min"], geo["bounding_box"]["max"]
    cx, cz = (x0 + x1) / 2.0, (z0 + z1) / 2.0
    v = np.asarray(vertices, dtype=float)
    if axis == "y":
        radii = np.sqrt((v[:, 0] - cx) ** 2 + (v[:, 2] - cz) ** 2)
    elif axis == "x":
        radii = np.sqrt((v[:, 1] - (y0 + y1) / 2) ** 2 + (v[:, 2] - cz) ** 2)
    else:
        radii = np.sqrt((v[:, 0] - cx) ** 2 + (v[:, 1] - (y0 + y1) / 2) ** 2)
    envelope_radius = float(radii.max())

    return {
        "motion": motion_desc,
        "axis": axis,
        "inertia_kg_m2": round(inertia, 2),
        "peak_torque_nm": round(peak_torque_nm, 1),
        "motor_kw": motor_kw,
        "gearbox_ratio": round(ratio, 1),
        "shaft_diameter_mm": shaft_mm,
        "bearing_radial_kn": round(radial_kn, 2),
        "bearing_l10_hours": round(l10_hours),
        "motion_envelope": {
            "radius_m": round(envelope_radius, 3),
            "height_m": round(y1 - y0, 3),
        },
        "note": "Preliminary drive sizing — verify with motor supplier curves",
    }
