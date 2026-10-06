"""Cost engine v1 (PLAN.md §7).

Itemized rollup tree, every line traceable to a calculation or an editable
JSON catalog in backend/data/. Tree order follows PLAN.md §7:
SHELL / ARMATURE / FOUNDATION / BASIN / MECHANICAL / ELECTRICAL /
TRANSPORT & INSTALL -> subtotal -> contingency 10% -> margin 15% -> TOTAL.
"""

import json
import math
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

CONTINGENCY_PCT = 10.0
MARGIN_PCT = 15.0
OPEX_HOURS_PER_DAY = 10.0
OPEX_TARIFF_PER_KWH = 0.15
WATERPROOFING_PER_M2 = 25.0
INSTALL_DAY_RATE_USD = 1200.0


def _load(name: str) -> dict:
    with (DATA_DIR / name).open("r", encoding="utf-8") as f:
        return json.load(f)


def _item(label: str, qty: float, unit: str, unit_price: float) -> dict:
    return {"label": label, "qty": round(qty, 3), "unit": unit,
            "unit_price": unit_price, "amount": round(qty * unit_price, 2)}


def estimate(brief: dict, sculpture_meta: dict, basin_meta: dict | None,
             hydraulics: dict, structural: dict | None = None,
             skeleton: dict | None = None, panels: dict | None = None,
             lighting: dict | None = None) -> dict:
    materials = _load("materials.json")
    basin_materials = _load("basin_materials.json")
    equipment = _load("equipment.json")
    rates = _load("fabrication_rates.json")
    labor = rates["labor_rate_per_h"]

    sculpture = brief.get("sculpture") or {}
    material_key = sculpture.get("material", "stainless_316l")
    material = materials[material_key]
    finish = sculpture.get("finish", "brushed")
    height_m = sculpture.get("height_m", 2.0)
    mass_kg = sculpture_meta["mass_kg"]
    surface_area = sculpture_meta["surface_area_m2"]

    sections: list[dict] = []

    # SCULPTURE SHELL
    polish_h_per_m2 = rates["polish_hours_per_m2"].get(finish, 3.0)
    shell_items = [
        _item(f"Shell material ({material['name']})", mass_kg, "kg",
              material["cost_per_kg"]),
        _item("Panelization labor", surface_area * rates["panelization_hours_per_m2"],
              "h", labor),
        _item(f"Finish labor ({finish})", surface_area * polish_h_per_m2, "h", labor),
    ]
    # Panelization v2 (scope §16/§18/§19): real panel data adds CNC cutting
    # and welding length. Cutting length ~ 2x weld seam (two panel edges per seam).
    if panels:
        seam_m = panels["total_weld_seam_m"]
        shell_items.append(_item("CNC cutting (flat patterns)", seam_m * 2.0, "m",
                                 rates["cnc_cutting_cost_per_m"]))
        shell_items.append(_item(f"Welding ({panels['panel_count']} panels)",
                                 seam_m, "m", rates["welding_cost_per_m"]))
    sections.append({"key": "shell", "label": "SCULPTURE SHELL", "items": shell_items})

    # ARMATURE (generated skeleton when available, then structural calc,
    # else 25% heuristic)
    armature = rates["armature"]
    if skeleton:
        steel_kg = skeleton["total_steel_kg"]
        steel_label = (f"Skeleton steel ({skeleton['member_count']} members, "
                       f"{skeleton['section']})")
    elif structural:
        steel_kg = structural["armature"]["steel_kg"]
        steel_label = (f"Structural steel (slenderness "
                       f"{structural['armature']['slenderness']:.1f}, "
                       f"x{structural['armature']['slenderness_factor']:.2f})")
    else:
        steel_kg = mass_kg * armature["mass_fraction_of_sculpture"]
        steel_label = "Structural steel (25% of shell mass)"
    sections.append({"key": "armature", "label": "ARMATURE", "items": [
        _item(steel_label, steel_kg, "kg", armature["steel_cost_per_kg"]),
    ]})

    # FOUNDATION (structural pad sizing when available, else v1 heuristic)
    f = rates["foundation"]
    if structural:
        fd = structural["foundation"]
        side = fd["pad_side_m"]
        concrete_m3 = fd["concrete_m3"]
        rebar_kg = fd["rebar_kg"]
        pad_depth = fd["pad_depth_m"]
        plate = structural["base_plate"]
        foundation_items = [
            _item(f"Concrete pad {side:.2f} m x {side:.2f} m x {pad_depth:.2f} m",
                  concrete_m3, "m3", f["concrete_per_m3"]),
            _item("Rebar", rebar_kg, "kg", f["rebar_per_kg"]),
            _item(f"Base plate {plate['side_m']:.2f} m + {plate['bolt_count']} anchors",
                  1, "lot", f.get("base_plate_lot_usd", 250.0)),
        ]
    else:
        side = max(f["pad_min_side_m"], height_m * f["pad_side_per_height"])
        concrete_m3 = side**2 * f["pad_depth_m"]
        rebar_kg = concrete_m3 * f["rebar_kg_per_m3"]
        foundation_items = [
            _item(f"Concrete pad {side:.2f} m x {side:.2f} m x {f['pad_depth_m']} m",
                  concrete_m3, "m3", f["concrete_per_m3"]),
            _item("Rebar", rebar_kg, "kg", f["rebar_per_kg"]),
        ]
    sections.append({"key": "foundation", "label": "FOUNDATION",
                     "items": foundation_items})

    # BASIN
    basin_items: list[dict] = []
    if basin_meta:
        inner = basin_meta["inner"]
        wt = basin_meta["wall_thickness_m"]
        if "radius_m" in inner:
            r_i = inner["radius_m"]
            rim_area = math.pi * ((r_i + wt)**2 - r_i**2)
        else:
            rim_area = ((inner["length_m"] + 2 * wt) * (inner["width_m"] + 2 * wt)
                        - inner["length_m"] * inner["width_m"])
        clad_area = basin_meta["wetted_area_m2"] + rim_area
        basin_key = (brief.get("water", {}).get("basin") or {}).get("material",
                                                                    "black_granite")
        clad_rate = basin_materials.get(basin_key, basin_materials["black_granite"])
        basin_items.append(_item(f"Cladding ({clad_rate['name']})", clad_area, "m2",
                                 clad_rate["cladding_per_m2"]))
        basin_items.append(_item("Waterproofing", basin_meta["wetted_area_m2"], "m2",
                                 WATERPROOFING_PER_M2))
    sections.append({"key": "basin", "label": "BASIN", "items": basin_items})

    # MECHANICAL (pumps, nozzles, valves, filtration, piping)
    mech_items: list[dict] = []
    motor_kw = hydraulics["motor_kw"]
    if motor_kw > 0:
        pump_cost = equipment["pump"]["base_usd"] + motor_kw * equipment["pump"]["per_kw_usd"]
        mech_items.append({"label": f"Pump {motor_kw:.2f} kW", "qty": 1, "unit": "ea",
                           "unit_price": round(pump_cost, 2),
                           "amount": round(pump_cost, 2)})
    nozzles = _load("nozzles.json")
    for feat in hydraulics["features"]:
        if feat.get("nozzle"):
            price = nozzles[feat["nozzle"]]["unit_price_usd"]
            mech_items.append(_item(f"{nozzles[feat['nozzle']]['name']}",
                                    feat["count"], "ea", price))
        if feat.get("valve"):
            vkey = "valve_ball_usd" if feat["valve"]["type"] == "ball" else "valve_butterfly_usd"
            mech_items.append(_item(f"Valve DN{feat['valve']['dn']} ({feat['valve']['type']})",
                                    1, "ea", equipment[vkey]))
        if feat.get("flow_lps", 0) > 0:
            mech_items.append(_item(f"Piping ({feat['type']})", 1, "lot",
                                    equipment["piping_per_feature_usd"]))
    if hydraulics.get("manifold") and hydraulics["manifold"]["branches"]:
        mech_items.append(_item(f"Manifold DN{hydraulics['manifold']['dn']} "
                                f"x{hydraulics['manifold']['branches']} branches",
                                1, "lot", equipment["manifold_lot_usd"]))
    if hydraulics.get("filtration"):
        filt = hydraulics["filtration"]
        mech_items.append(_item(f"Sand filter {filt['filter_area_m2']} m2",
                                filt["filter_area_m2"], "m2",
                                equipment["sand_filter_per_m2_usd"]))
    sections.append({"key": "mechanical", "label": "MECHANICAL", "items": mech_items})

    # ELECTRICAL (engineered lighting schedule when available, else counts)
    light_brief = brief.get("lighting") or {}
    if lighting:
        catalog = _load("lighting.json")
        ctrl = lighting["controls"]
        elec_items = []
        by_name: dict[str, int] = {}
        for row in ctrl["schedule"]:
            by_name[row["fixture"]] = by_name.get(row["fixture"], 0) + 1
        for name, qty in by_name.items():
            cat_key = next(k for k, v in catalog.items() if v["name"] == name)
            elec_items.append(_item(name, qty, "ea",
                                    catalog[cat_key]["unit_price_usd"]))
        elec_items.append(_item(f"PSU 24V {ctrl['psu_wattage']:.0f}W",
                                ctrl["psu_count"], "ea",
                                equipment["psu_320w"]["unit_price_usd"]))
        if ctrl["dmx_universes"]:
            elec_items.append(_item("DMX controller",
                                    ctrl["dmx_universes"], "ea",
                                    equipment["dmx_controller"]["unit_price_usd"]))
        cable_m = sum(r["cable_run_m"] for r in ctrl["schedule"])
        elec_items.append(_item("Cable (engineered runs)", cable_m, "m",
                                equipment["cable_per_m_usd"]))
    else:
        uplights = light_brief.get("sculpture_uplights", 0)
        submersible = light_brief.get("submersible_rgb", 0)
        elec_items = [
            _item("LED uplight", uplights, "ea",
                  equipment["led_uplight"]["unit_price_usd"]),
            _item("Submersible RGB", submersible, "ea",
                  equipment["submersible_rgb"]["unit_price_usd"]),
        ]
        light_total = sum(i["amount"] for i in elec_items)
        elec_items.append(_item("Drivers, cabling, panels (15%)",
                                light_total * equipment["electrical_balance_fraction"],
                                "lot", 1.0))
    sections.append({"key": "electrical", "label": "ELECTRICAL", "items": elec_items})

    # TRANSPORT & INSTALL
    install_days = max(1, math.ceil(height_m / 3.0))
    sections.append({"key": "install", "label": "TRANSPORT & INSTALL", "items": [
        _item(f"Cranage + site crew ({install_days} d)", install_days, "day",
              INSTALL_DAY_RATE_USD),
    ]})

    for s in sections:
        s["amount"] = round(sum(i["amount"] for i in s["items"]), 2)

    subtotal = round(sum(s["amount"] for s in sections), 2)
    contingency = round(subtotal * CONTINGENCY_PCT / 100.0, 2)
    margin = round((subtotal + contingency) * MARGIN_PCT / 100.0, 2)
    total = round(subtotal + contingency + margin, 2)

    budget = (brief.get("project") or {}).get("budget_usd")
    opex = round(motor_kw * OPEX_HOURS_PER_DAY * 365.0 * OPEX_TARIFF_PER_KWH, 2)

    return {
        "currency": "USD",
        "sections": sections,
        "subtotal_usd": subtotal,
        "contingency_pct": CONTINGENCY_PCT,
        "contingency_usd": contingency,
        "margin_pct": MARGIN_PCT,
        "margin_usd": margin,
        "total_usd": total,
        "budget_usd": budget,
        "over_budget": (total > budget) if budget is not None else None,
        "budget_delta_usd": round(total - budget, 2) if budget is not None else None,
        "opex_annual_usd": opex,
        "opex_assumptions": {"hours_per_day": OPEX_HOURS_PER_DAY,
                             "tariff_per_kwh": OPEX_TARIFF_PER_KWH},
    }
