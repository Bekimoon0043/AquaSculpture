import numpy as np
from fastapi import APIRouter
from fastapi.responses import Response

from deliverables import package
from pipeline import run_pipeline

router = APIRouter(prefix="/deliverables", tags=["deliverables"])


@router.post("/package")
def get_package(brief: dict):
    """Run the pipeline and return the full deliverables ZIP."""
    result = run_pipeline(brief)

    # Seat the sculpture on the basin floor for the exported geometry.
    sculpture_mesh = {
        "vertices": (np.asarray(result["sculpture"]["mesh"]["vertices"])
                     + np.array([0.0, result["sculpture_offset_m"], 0.0])).tolist(),
        "faces": result["sculpture"]["mesh"]["faces"],
    }
    basin_mesh = result["basin"]
    if basin_mesh:
        basin_mesh = {"vertices": basin_mesh["vertices"], "faces": basin_mesh["faces"]}

    zip_bytes = package.build_package(
        brief=result["brief"],
        sculpture_mesh=sculpture_mesh,
        sculpture_meta=result["sculpture"]["metadata"],
        geo=result["geo_quantities"],
        basin_mesh=basin_mesh,
        basin_meta=result["basin"]["metadata"] if result["basin"] else None,
        hydraulics=result["hydraulics"],
        cost=result["cost"],
        structural=result["structural"],
        panels=result.get("panels"),
        lighting=result.get("lighting"),
    )
    name = (result["brief"].get("project") or {}).get("name", "sculptflow")
    safe = "".join(c if c.isalnum() or c in " _-" else "_" for c in name)
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{safe}_package.zip"'},
    )
