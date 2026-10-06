"""Dependency-free minimal PDF writer — Helvetica text pages, valid xref."""


def _esc(text: str) -> str:
    return (str(text).replace("\\", "\\\\").replace("(", "\\(")
            .replace(")", "\\)").encode("latin-1", "replace").decode("latin-1"))


def build_pdf(pages: list[list[tuple[str, int]]]) -> bytes:
    """pages: list of pages; each page a list of (text, font_size) lines."""
    objects: list[bytes] = []

    page_ids = []
    content_ids = []
    n_pages = len(pages)
    # Object numbering: 1 catalog, 2 pages, 3 font, then page/content pairs.
    for i in range(n_pages):
        page_ids.append(4 + 2 * i)
        content_ids.append(5 + 2 * i)

    kids = " ".join(f"{p} 0 R" for p in page_ids)
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {n_pages} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    for i, lines in enumerate(pages):
        page = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                f"/Resources << /Font << /F1 3 0 R >> >> "
                f"/Contents {content_ids[i]} 0 R >>").encode()
        objects.append(page)

        stream_lines = []
        y = 790
        for text, size in lines:
            leading = int(size * 1.6)
            if y < 60:
                break
            stream_lines.append(f"BT /F1 {size} Tf 56 {y} Td ({_esc(text)}) Tj ET")
            y -= leading
        stream = "\n".join(stream_lines).encode("latin-1")
        objects.append(b"<< /Length " + str(len(stream)).encode()
                       + b" >>\nstream\n" + stream + b"\nendstream")

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for num, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{num} 0 obj\n".encode() + body + b"\nendobj\n"

    xref_pos = len(out)
    count = len(objects) + 1
    out += f"xref\n0 {count}\n".encode()
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += f"{off:010d} 00000 n \n".encode()
    out += (f"trailer\n<< /Size {count} /Root 1 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n").encode()
    return bytes(out)


def engineering_report_pages(brief: dict, sculpture_meta: dict, geo: dict,
                             basin_meta: dict | None, hydraulics: dict,
                             cost: dict, structural: dict | None = None,
                             lighting: dict | None = None
                             ) -> list[list[tuple[str, int]]]:
    project = brief.get("project") or {}
    sculpture = brief.get("sculpture") or {}

    cover = [
        ("SculptFlow Studio — Engineering Report", 20),
        ("", 10),
        (f"Project: {project.get('name', '-')}", 14),
        (f"Site: {project.get('site', '-')}", 12),
        (f"Budget: USD {project.get('budget_usd', '-')}", 12),
        (f"Sculpture: {sculpture.get('family')} / {sculpture.get('material')} / "
         f"{sculpture.get('finish')}, H = {sculpture.get('height_m')} m", 12),
        ("", 10),
        ("PRELIMINARY — requires licensed engineer review.", 12),
    ]

    bbox = geo["bounding_box"]
    geometry = [
        ("Geometry quantities", 16),
        (f"Family: {sculpture_meta['family']}", 11),
        (f"Surface area: {geo['surface_area_m2']:.2f} m2", 11),
        (f"Swept volume: {geo['volume_m3']:.3f} m3", 11),
        (f"Shell thickness: {sculpture_meta['shell_thickness_m'] * 1000:.1f} mm", 11),
        (f"Shell mass: {sculpture_meta['mass_kg']:.1f} kg", 11),
        (f"Bounding box: {bbox['size'][0]:.2f} x {bbox['size'][1]:.2f} x "
         f"{bbox['size'][2]:.2f} m", 11),
        (f"Center of gravity: ({geo['center_of_gravity_m'][0]:.3f}, "
         f"{geo['center_of_gravity_m'][1]:.3f}, {geo['center_of_gravity_m'][2]:.3f}) m",
         11),
    ]
    if basin_meta:
        geometry += [
            ("", 8),
            (f"Basin: {basin_meta['shape']}, water volume "
             f"{basin_meta['water_volume_m3']:.2f} m3, wetted area "
             f"{basin_meta['wetted_area_m2']:.2f} m2", 11),
        ]
        if basin_meta.get("weir_length_m"):
            geometry.append((f"Perimeter weir length: {basin_meta['weir_length_m']:.2f} m", 11))

    hyd = [("Hydraulics", 16)]
    for feat in hydraulics["features"]:
        hyd.append((f"{feat['type']}: {feat['flow_lps']:.2f} L/s", 11))
    hyd += [
        (f"Total flow: {hydraulics['total_flow_lps']:.2f} L/s", 11),
        (f"TDH: {hydraulics['tdh_m']:.2f} m (static {hydraulics['static_lift_m']:.2f} + "
         f"friction {hydraulics['friction_head_m']:.2f} + nozzle "
         f"{hydraulics['nozzle_pressure_head_m']:.2f})", 11),
        (f"Pump motor: {hydraulics['motor_kw']:.2f} kW", 11),
    ]
    if hydraulics.get("main_pipe"):
        hyd.append((f"Main pipe: DN{hydraulics['main_pipe']['dn']} at "
                    f"{hydraulics['main_pipe']['velocity_ms']:.2f} m/s", 11))
    if hydraulics.get("turnover_min"):
        hyd.append((f"Basin turnover: {hydraulics['turnover_min']:.1f} min", 11))

    cost_page = [("Cost summary", 16)]
    for s in cost["sections"]:
        cost_page.append((f"{s['label']}: USD {s['amount']:,.0f}", 11))
    cost_page += [
        ("", 8),
        (f"Subtotal: USD {cost['subtotal_usd']:,.0f}", 11),
        (f"Contingency {cost['contingency_pct']:.0f}%: USD {cost['contingency_usd']:,.0f}", 11),
        (f"Margin {cost['margin_pct']:.0f}%: USD {cost['margin_usd']:,.0f}", 11),
        (f"TOTAL: USD {cost['total_usd']:,.0f}", 13),
    ]
    if cost.get("budget_usd") is not None:
        flag = "OVER BUDGET" if cost["over_budget"] else "within budget"
        cost_page.append((f"Budget USD {cost['budget_usd']:,.0f} — {flag} "
                          f"(delta {cost['budget_delta_usd']:,.0f})", 11))
    cost_page.append((f"Annual operating cost (energy): USD {cost['opex_annual_usd']:,.0f}", 11))

    pages = [cover, geometry, hyd]

    if structural:
        plate = structural["base_plate"]
        fdn = structural["foundation"]
        ana = structural["analysis"]
        sf = structural["safety_factors"]
        loads = structural["loads"]
        pages.append([
            ("Structural (preliminary)", 16),
            (f"Wind zone: {structural['wind_zone']}"
             + (" (indoor — no wind load)" if structural["indoor"] else ""), 11),
            (f"Velocity pressure q = {structural['velocity_pressure_pa']:.0f} Pa "
             f"(V = {structural['wind_speed_ms']:.0f} m/s), gust "
             f"{structural['gust_factor']}, Cd {structural['drag_coefficient']}, "
             f"solidity {structural['solidity']}", 11),
            (f"Loads — wind {loads['wind_kn']:.2f} kN, jet reaction "
             f"{loads['jet_reaction_kn']:.2f} kN, seismic {loads['seismic_kn']:.2f} kN, "
             f"dead {loads['dead_kn']:.2f} kN", 11),
            (f"Base moment: {structural['total_base_moment_knm']:.2f} kNm", 11),
            (f"Deflection {ana['deflection_mm']:.1f} mm (limit "
             f"{ana['deflection_limit_mm']:.0f} mm), stress "
             f"{ana['stress_mpa']:.1f} MPa", 11),
            (f"Natural frequency {ana['natural_frequency_hz']:.2f} Hz vs vortex "
             f"{ana['vortex_shedding_hz']:.2f} Hz — resonance risk: "
             f"{'YES' if ana['resonance_risk'] else 'no'}", 11),
            (f"Base plate {plate['side_m']:.2f} m, {plate['bolt_count']} bolts: "
             f"tension {plate['bolt_tension_kn']:.1f} kN vs allowable "
             f"{plate['bolt_allowable_kn']:.0f} kN — "
             f"{'OK' if plate['bolts_ok'] else 'FAIL'}", 11),
            (f"Foundation pad {fdn['pad_side_m']:.2f} x {fdn['pad_side_m']:.2f} x "
             f"{fdn['pad_depth_m']:.2f} m = {fdn['concrete_m3']:.2f} m3 concrete, "
             f"rebar {fdn['rebar_kg']:.0f} kg, bearing {fdn['bearing_kpa']:.0f} kPa",
             11),
            (f"Armature steel: {structural['armature']['steel_kg']:.1f} kg "
             f"(slenderness {structural['armature']['slenderness']:.1f})", 11),
            ("Safety factors (required " + f"{sf['required']})" +
             ": overturning {ov}, sliding {sl}, anchors {an}, buckling {bu}, "
             "yield {yi} — {verdict}".format(
                 ov=sf["overturning"] if sf["overturning"] is not None else "n/a",
                 sl=sf["sliding"] if sf["sliding"] is not None else "n/a",
                 an=sf["anchor_tension"] if sf["anchor_tension"] is not None else "n/a",
                 bu=sf["buckling"] if sf["buckling"] is not None else "n/a",
                 yi=sf["yield"] if sf["yield"] is not None else "n/a",
                 verdict="ALL PASS" if sf["all_pass"] else "CHECK FAILURES"), 11),
            ("", 8),
            (structural["disclaimer"], 10),
        ])

    pages.append(cost_page)
    if lighting:
        illum = lighting["illumination"]
        ctrl = lighting["controls"]
        page = [
            ("Lighting engineering", 16),
            (f"Fixtures: {ctrl['fixture_count']}  |  total load "
             f"{ctrl['total_load_w']:.0f} W  |  PSUs: {ctrl['psu_count']} x "
             f"{ctrl['psu_wattage']:.0f} W", 11),
            (f"Illuminance on shell: avg {illum['avg_lux']:.0f} lux, max "
             f"{illum['max_lux']:.0f} lux, coverage {illum['coverage_pct']:.0f}% "
             f"above {illum['min_lux_target']:.0f} lux", 11),
            (f"DMX: {ctrl['dmx_channels_used']} channels / "
             f"{ctrl['dmx_universes']} universe(s); max voltage drop "
             f"{ctrl['max_voltage_drop_v']} V — "
             f"{'OK' if ctrl['voltage_drop_ok'] else 'FAIL'}", 11),
            ("", 6),
            ("Fixture schedule:", 12),
        ]
        for r in ctrl["schedule"]:
            page.append((f"  {r['id']}  {r['fixture']}  {r['power_w']} W  "
                         f"DMX {r['dmx_address']}  cable {r['cable_run_m']} m",
                         10))
        pages.append(page)

    return pages
