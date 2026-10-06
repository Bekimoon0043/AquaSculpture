"""Bundle deliverables into one ZIP with a SHA-256 manifest (PLAN.md §8)."""

import hashlib
import io
import json
import zipfile

from deliverables import bom, export_3d, report


def build_package(brief: dict, sculpture_mesh: dict, sculpture_meta: dict,
                  geo: dict, basin_mesh: dict | None, basin_meta: dict | None,
                  hydraulics: dict, cost: dict, structural: dict | None = None
                  ) -> bytes:
    """Returns ZIP bytes: brief.json, sculpture.stl, sculpture.glb, bom.xlsx,
    report.pdf, manifest.json (SHA-256 of every artifact)."""
    meshes = [{"name": "sculpture", **sculpture_mesh}]
    if basin_mesh:
        meshes.append({"name": "basin", **basin_mesh})

    stl_bytes = export_3d.build_stl(meshes).encode("utf-8")
    glb_bytes = export_3d.build_glb(sculpture_mesh["vertices"], sculpture_mesh["faces"])
    xlsx_bytes = bom.build_xlsx(bom.cost_tree_rows(cost))
    pdf_bytes = report.build_pdf(
        report.engineering_report_pages(brief, sculpture_meta, geo, basin_meta,
                                        hydraulics, cost, structural))
    brief_bytes = json.dumps(brief, indent=2).encode("utf-8")

    artifacts = {
        "brief.json": brief_bytes,
        "sculpture_basin.stl": stl_bytes,
        "sculpture.glb": glb_bytes,
        "bom.xlsx": xlsx_bytes,
        "report.pdf": pdf_bytes,
    }
    manifest = {name: hashlib.sha256(data).hexdigest()
                for name, data in artifacts.items()}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in artifacts.items():
            z.writestr(name, data)
        z.writestr("manifest.json", json.dumps(manifest, indent=2))
    return buf.getvalue()
