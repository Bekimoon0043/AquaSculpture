"""Fabrication sequence generator (scope §22).

Turns the engineered design into a manufacturing method statement: ordered
steps with quantities pulled from the real pipeline results, crew sizing and
duration estimates. Foundation first, installation last — every step carries
the numbers it needs (concrete m3, member count, weld metres, ...).
"""

STEPS = [
    ("foundation", "Excavate + cast foundation pad, set anchor bolts"),
    ("base_frame", "Fabricate and level base frame / base plate"),
    ("skeleton", "Erect primary skeleton (spine + ribs)"),
    ("internal_services", "Install internal pipework + electrical conduits"),
    ("panels", "Form and fit shell panels"),
    ("welding", "Weld seams (sequence: root -> fill -> cap)"),
    ("finishing", "Grind, polish/passivate, final finish"),
    ("lighting", "Install lighting + terminate DMX"),
    ("water_equipment", "Install nozzles, valves, pump, filtration"),
    ("testing", "Pressure test, dry-run, light check, water balancing"),
    ("transport", "Segment, crate, transport to site"),
    ("installation", "Crane in, bolt down, align, grout, commission"),
]

# Crew-days per unit of work.
RATE = {
    "concrete_m3": 0.8,      # crew-days per m3
    "member": 0.15,          # per skeleton member
    "panel": 0.35,           # per shell panel
    "weld_m": 0.06,          # per weld metre
    "fixture": 0.25,         # per light fixture
    "valve_or_nozzle": 0.2,
}


def _days(*terms):
    return round(sum(terms), 1)


def generate_method_statement(result: dict) -> dict:
    struct = result.get("structural") or {}
    skel = result.get("skeleton") or {}
    panels = result.get("panelization") or {}
    hyd = result.get("hydraulics") or {}
    light = result.get("lighting") or {}
    routing = result.get("routing") or {}
    cost = result.get("cost") or {}

    concrete = struct.get("foundation", {}).get("concrete_m3", 0.0)
    members = skel.get("member_count", 0)
    n_panels = panels.get("panel_count", 0)
    weld_m = panels.get("total_weld_seam_m", 0.0)
    n_fixtures = (light.get("controls") or {}).get("fixture_count", 0)
    n_nozzles = sum(f.get("count", 0) for f in hyd.get("features", []))
    n_valves = len(hyd.get("schedules", {}).get("valves", []))
    n_routes = len(routing.get("routes", []))

    qty = {
        "foundation": f"{concrete:.1f} m3 concrete",
        "base_frame": f"{struct.get('base_plate', {}).get('side_m', 0):.2f} m plate",
        "skeleton": f"{members} members ({skel.get('section', '-')})",
        "internal_services": f"{n_routes} routes",
        "panels": f"{n_panels} panels",
        "welding": f"{weld_m:.0f} m weld",
        "finishing": f"{result['sculpture']['metadata']['surface_area_m2']:.1f} m2",
        "lighting": f"{n_fixtures} fixtures",
        "water_equipment": f"{n_nozzles} nozzles, {n_valves} valves",
        "testing": "pressure + dry run",
        "transport": f"{result['sculpture']['metadata']['mass_kg']:.0f} kg shell",
        "installation": "crane + bolt-down",
    }
    days = {
        "foundation": _days(1.0, concrete * RATE["concrete_m3"]),
        "base_frame": _days(0.5),
        "skeleton": _days(members * RATE["member"]),
        "internal_services": _days(0.3 * n_routes),
        "panels": _days(n_panels * RATE["panel"]),
        "welding": _days(weld_m * RATE["weld_m"]),
        "finishing": _days(n_panels * 0.2),
        "lighting": _days(n_fixtures * RATE["fixture"]),
        "water_equipment": _days((n_nozzles + n_valves) * RATE["valve_or_nozzle"]),
        "testing": _days(1.0),
        "transport": _days(0.5),
        "installation": _days(1.5),
    }

    steps = [{"order": i + 1, "key": key, "task": task,
              "quantity": qty[key], "crew_days": days[key]}
             for i, (key, task) in enumerate(STEPS)]
    return {
        "steps": steps,
        "total_crew_days": round(sum(d for d in days.values()), 1),
        "note": "Method statement v1 — crew-day rates are editable heuristics",
    }
