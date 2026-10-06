import hashlib
import io
import json
import struct
import zipfile

from deliverables import bom, export_3d, package, report
from geometry.archetypes.open_ring import generate_open_ring
from geometry.basin import generate_basin


def _inputs():
    brief = {
        "project": {"name": "Pkg Test", "budget_usd": 250000},
        "sculpture": {"family": "open_ring", "height_m": 4.0,
                      "material": "stainless_316l", "finish": "mirror_polish_8",
                      "parameters": {"diameter_m": 4.0, "tube_radius_m": 0.15,
                                     "opening_deg": 60, "segments": 24}},
        "water": {"features": [{"type": "bubbler_field", "count": 12}],
                  "basin": {"shape": "circular", "diameter_m": 6.0, "depth_m": 0.45,
                            "material": "black_granite", "overflow": "perimeter_weir"}},
        "lighting": {"sculpture_uplights": 4, "submersible_rgb": 12},
    }
    ring = generate_open_ring(**brief["sculpture"]["parameters"])
    basin = generate_basin(brief["water"]["basin"], brief["water"]["features"])
    from engineering import geo_calc, hydraulics
    geo = {
        "surface_area_m2": geo_calc.surface_area(ring["vertices"], ring["faces"]),
        "volume_m3": geo_calc.volume(ring["vertices"], ring["faces"]),
        "bounding_box": geo_calc.bounding_box(ring["vertices"]),
        "center_of_gravity_m": geo_calc.center_of_gravity(ring["vertices"], ring["faces"]),
    }
    hyd = hydraulics.compute_hydraulics(brief, basin["metadata"])
    from cost import estimator
    cost = estimator.estimate(brief, ring["metadata"], basin["metadata"], hyd)
    return brief, ring, basin, geo, hyd, cost


def test_stl_parses(tmp_path):
    ring = generate_open_ring(segments=8)
    stl_path = tmp_path / "out.stl"
    export_3d.write_stl_ascii(stl_path, [{"name": "ring", "vertices": ring["vertices"],
                                          "faces": ring["faces"]}])
    text = stl_path.read_text()
    assert text.startswith("solid ring")
    assert text.count("facet normal") == len(ring["faces"])
    assert text.count("vertex ") == 3 * len(ring["faces"])
    assert text.strip().endswith("endsolid ring")


def test_glb_structure():
    ring = generate_open_ring(segments=8)
    glb = export_3d.build_glb(ring["vertices"], ring["faces"])
    assert glb[:4] == b"glTF"
    version, total_len = struct.unpack_from("<II", glb, 4)
    assert version == 2
    assert total_len == len(glb)
    json_len, json_type = struct.unpack_from("<II", glb, 12)
    assert json_type == 0x4E4F534A  # "JSON"
    gltf = json.loads(glb[20:20 + json_len])
    assert gltf["asset"]["version"] == "2.0"
    assert gltf["accessors"][0]["count"] == len(ring["vertices"])
    assert gltf["accessors"][1]["count"] == 3 * len(ring["faces"])
    assert gltf["accessors"][0]["min"][1] < 0 < gltf["accessors"][0]["max"][1]


def test_xlsx_is_valid_zip_with_sheet():
    data = bom.build_xlsx([["hello", 1, 2.5], ["world", 3, 4]])
    zf = zipfile.ZipFile(io.BytesIO(data))
    assert "xl/worksheets/sheet1.xml" in zf.namelist()
    assert "xl/workbook.xml" in zf.namelist()
    sheet = zf.read("xl/worksheets/sheet1.xml").decode()
    assert "hello" in sheet and "<v>2.5</v>" in sheet


def test_pdf_valid_envelope():
    pdf = report.build_pdf([[("Cover line", 18), ("detail", 11)], [("Page two", 12)]])
    assert pdf.startswith(b"%PDF-")
    assert pdf.rstrip().endswith(b"%%EOF")
    assert b"/Type /Page" in pdf
    assert b"Cover line" in pdf


def test_package_zip_manifest_hashes():
    brief, ring, basin, geo, hyd, cost = _inputs()
    zip_bytes = package.build_package(
        brief, {"vertices": ring["vertices"], "faces": ring["faces"]},
        ring["metadata"], geo, basin, basin["metadata"], hyd, cost)
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = set(zf.namelist())
    assert {"brief.json", "sculpture_basin.stl", "sculpture.glb", "bom.xlsx",
            "report.pdf", "manifest.json"} <= names
    manifest = json.loads(zf.read("manifest.json"))
    for name, digest in manifest.items():
        assert hashlib.sha256(zf.read(name)).hexdigest() == digest
    assert zf.read("sculpture.glb")[:4] == b"glTF"
    assert zf.read("report.pdf").startswith(b"%PDF-")
